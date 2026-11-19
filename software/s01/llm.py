"""Local model via Ollama's HTTP API (no extra Python packages needed).
On the device this can be swapped for llama.cpp behind the same interface."""
import json
import re
import urllib.request

from . import config

SYSTEM = """You are the answer engine of an offline survival reference device.
Rules:
- Answer ONLY from the numbered passages provided. Add nothing from memory.
- Put a citation like [1] or [2] after every claim.
- If the passages do not answer the question, reply exactly: NOT_IN_LIBRARY
- Never say a wild plant or mushroom is safe to eat.
- Never state a medication dose unless it appears word for word in a passage.
- At most 5 short sentences, plain language. The screen is small."""


class LocalModel:
    def __init__(self, model=config.MODEL, url=config.OLLAMA_URL):
        self.model, self.url = model, url
        self.ok = self._check()

    def _check(self):
        try:
            with urllib.request.urlopen(f"{self.url}/api/tags", timeout=1.5) as r:
                names = [m["name"] for m in json.load(r).get("models", [])]
        except Exception:
            return False
        want = self.model if ":" in self.model else self.model + ":latest"
        return want in names or self.model in names

    def answer(self, question, passages):
        ctx = "\n\n".join(f"[{i}] {p.title} — {p.section}\n{p.text}"
                          for i, p in enumerate(passages, 1))
        body = json.dumps({
            "model": self.model, "stream": False,
            "options": {"temperature": 0.1, "num_predict": 220},
            "messages": [{"role": "system", "content": SYSTEM},
                         {"role": "user", "content": f"Passages:\n{ctx}\n\nQuestion: {question}"}],
        }).encode()
        req = urllib.request.Request(f"{self.url}/api/chat", data=body,
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.load(r)["message"]["content"].strip()
        except Exception:
            return None


def citations_valid(text, n_passages):
    cites = [int(c) for c in re.findall(r"\[(\d+)\]", text)]
    return bool(cites) and all(1 <= c <= n_passages for c in cites)
