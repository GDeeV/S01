"""The answer pipeline: route -> retrieve -> generate (or extract) -> cite."""
import re
from dataclasses import dataclass, field

from . import safety
from .library import Library, load_cards
from .llm import LocalModel, citations_valid


@dataclass
class Answer:
    question: str
    kind: str                        # emergency | refusal | none | model | extractive
    text: str = ""
    passages: list = field(default_factory=list)
    card_id: str = None


def extract(passages, n=2, sentences=3):
    """Model-free fallback: quote the opening sentences of the best passage,
    plus the next one only if it comes from the same document."""
    parts = []
    for i, p in enumerate(passages[:n], 1):
        if i > 1 and p.doc_id != passages[0].doc_id:
            break
        sents = re.split(r"(?<=[.!?])\s+", " ".join(p.text.split()))
        parts.append(" ".join(sents[:sentences]) + f" [{i}]")
    return " ".join(parts)


class Engine:
    def __init__(self, use_model=True, model=None):
        self.library = Library()
        self.cards = load_cards()
        self.model = None
        if use_model:
            m = LocalModel(model) if model else LocalModel()
            self.model = m if m.ok else None

    @property
    def mode(self):
        return "MODEL" if self.model else "LIBRARY ONLY"

    def ask(self, question):
        r = safety.route(question)
        if r.kind == "emergency":
            return Answer(question, "emergency", card_id=r.card_id)

        passages = self.library.search(question)
        if r.kind == "edibility":
            return Answer(question, "refusal", safety.EDIBILITY_MESSAGE, passages)
        if not passages:
            return Answer(question, "none", safety.NO_INFO_MESSAGE)
        if r.kind == "dose" or not self.model:
            return Answer(question, "extractive", extract(passages), passages)

        text = self.model.answer(question, passages)
        if not text or "NOT_IN_LIBRARY" in text:
            return Answer(question, "none", safety.NO_INFO_MESSAGE)
        if not citations_valid(text, len(passages)):
            # The model ignored the rules: fall back to quoting the library.
            return Answer(question, "extractive", extract(passages), passages)
        return Answer(question, "model", text, passages)
