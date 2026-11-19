"""The device UI. Hardware-independent: it receives abstract control events
and produces screen images. The emulator and the real device both drive it.

Events: up, down, left, right, ok, back, home, knob+, knob-
Returns a refresh hint for the display: "full", "partial", "ask" or None.
"""
from . import config
from .render import (BODY, HEAD, ITEM, LABEL, SMALL, STEP, Page, canvas, menu, quantize)

KNOB_STEP = 180     # pixels per knob detent
PAD_STEP = 420      # pixels per pad press (about half a screen)

HOME_ITEMS = [
    ("Ask a question", "Hold PTT and speak", "ask"),
    ("Emergency cards", "Bleeding, snakebite, cold, allergy, poisoning", "cards"),
    ("Browse library", "Core guides and the regional pack", "library"),
    ("About this device", "Sources, limits, safety rules", "about"),
]

HINTS_MENU = [("▲▼", "Move"), ("OK", "Open"), ("PTT", "Ask")]
HINTS_READ = [("KNOB", "Scroll"), ("BACK", ""), ("HOME", "")]


class App:
    def __init__(self, engine):
        self.engine = engine
        self.stack = [{"name": "home", "sel": 0}]
        self._pages = {}

    # navigation -----------------------------------------------------------
    @property
    def s(self):
        return self.stack[-1]

    def push(self, screen):
        self.stack.append(screen)
        return "full"

    def handle(self, ev):
        s, name = self.s, self.s["name"]
        if ev == "home":
            self.stack = self.stack[:1]
            return "full"
        if ev == "back":
            if len(self.stack) > 1 and name != "thinking":
                self.stack.pop()
                return "full"
            return None

        if name in ("home", "cards", "library"):
            n = len(self._menu_items(name))
            if ev in ("down", "knob+"):
                s["sel"] = (s["sel"] + 1) % n
                return "partial"
            if ev in ("up", "knob-"):
                s["sel"] = (s["sel"] - 1) % n
                return "partial"
            if ev == "ok":
                return self._open(name, s["sel"])
            return None

        if name == "ask" and ev == "ok":
            return "ask"

        if name in ("answer", "source", "card", "doc", "about"):
            step = {"knob+": KNOB_STEP, "knob-": -KNOB_STEP,
                    "down": PAD_STEP, "up": -PAD_STEP}.get(ev)
            if step:
                s["scroll"] = max(0, s.get("scroll", 0) + step)
                return "partial"
            if name == "answer" and s["ans"].passages:
                n = len(s["ans"].passages)
                if ev in ("left", "right"):
                    s["src"] = (s["src"] + (1 if ev == "right" else -1)) % n
                    return "partial"
                if ev == "ok":
                    return self.push({"name": "source", "p": s["ans"].passages[s["src"]], "scroll": 0})
        return None

    def _menu_items(self, name):
        if name == "home":
            return [(a, b) for a, b, _ in HOME_ITEMS]
        if name == "cards":
            return [(c["title"], None) for c in self.engine.cards.values()]
        if name == "library":
            return [(t, "Regional: " + config.REGION_LABEL if r != "core" else "Core")
                    for _, t, r in self.engine.library.docs()]

    def _open(self, name, sel):
        if name == "home":
            target = HOME_ITEMS[sel][2]
            if target in ("cards", "library"):
                return self.push({"name": target, "sel": 0})
            return self.push({"name": target, "scroll": 0})
        if name == "cards":
            card = list(self.engine.cards.values())[sel]
            return self.push({"name": "card", "card": card, "scroll": 0})
        if name == "library":
            doc_id = self.engine.library.docs()[sel][0]
            return self.push({"name": "doc", "doc": doc_id, "scroll": 0})

    # asking ---------------------------------------------------------------
    def begin_query(self, question):
        if self.s["name"] == "ask":
            self.stack.pop()
        self.stack.append({"name": "thinking", "q": question})

    def finish_query(self, ans):
        if self.s["name"] == "thinking":
            self.stack.pop()
        if ans.kind == "emergency":
            card = self.engine.cards[ans.card_id]
            self.stack.append({"name": "card", "card": card, "scroll": 0, "asked": ans.question})
        else:
            self.stack.append({"name": "answer", "ans": ans, "scroll": 0, "src": 0})

    # drawing --------------------------------------------------------------
    def render(self):
        s, name = self.s, self.s["name"]
        status = f"{self.engine.mode}  ·  BAT 74%"

        if name in ("home", "cards", "library"):
            titles = {"home": "Home", "cards": "Emergency cards", "library": "Library"}
            img = canvas(titles[name], HINTS_MENU, status)
            sub = {"home": f"Region: {config.REGION_LABEL}   ·   Library v{config.LIBRARY_VERSION}",
                   "cards": "Pre-written steps. No AI involved.",
                   "library": None}[name]
            return quantize(menu(img, self._menu_items(name), s["sel"], sub))

        if name == "ask":
            img = canvas("Ask", [("PTT", "Hold and speak"), ("BACK", "")], status)
            p = Page()
            p.add("Hold the PTT button and ask your question.", HEAD, gap=40)
            p.add("Answers come only from the library, with the source shown. "
                  "For emergencies, the device opens a pre-written card instead.", BODY)
            p.draw(img, 0)
            return quantize(img)

        if name == "thinking":
            img = canvas("Searching", [], status)
            p = Page()
            p.add("You asked", LABEL, gap=6)
            p.add(s["q"], BODY, gap=50)
            p.add("Searching the library…", HEAD)
            p.draw(img, 0)
            return quantize(img)

        p, hints, title, sel = Page(), HINTS_READ, name.title(), None
        if name == "answer":
            a = s["ans"]
            title = {"refusal": "Cannot confirm", "none": "Not in library"}.get(a.kind, "Answer")
            p.add("You asked", LABEL, gap=6)
            p.add(a.question, SMALL, gap=30)
            if a.kind == "refusal":
                p.add("Cannot confirm", HEAD, gap=16)
            elif a.kind == "extractive":
                p.add("Quoted from the library", LABEL, gap=12)
            p.add(a.text, BODY, gap=30)
            if a.passages:
                p.rule()
                p.add("Sources  (◀ ▶ select, OK read)", LABEL, gap=16)
                for i, src in enumerate(a.passages):
                    flag = "" if src.vetted else "  ·  NOT YET REVIEWED"
                    p.add(f"[{i + 1}] {src.title} — {src.section}\n{src.source}  ·  {src.date}{flag}",
                          SMALL, gap=18, invert=i)
                sel = s["src"]
                hints = [("KNOB", "Scroll"), ("◀▶", "Source"), ("OK", "Read"), ("BACK", "")]
        elif name == "source":
            src = s["p"]
            title = "Source"
            p.add(src.title, HEAD, gap=8)
            p.add(src.section, ITEM, gap=16)
            flag = "" if src.vetted else "  ·  NOT YET REVIEWED"
            p.add(f"{src.source}  ·  {src.date}{flag}", SMALL, gap=30)
            p.add(src.text, BODY)
        elif name == "card":
            c = s["card"]
            title = "Emergency"
            if s.get("asked"):
                p.add("You asked", LABEL, gap=6)
                p.add(s["asked"], SMALL, gap=24)
            p.add(c["title"], HEAD, gap=28)
            for i, step in enumerate(c["steps"], 1):
                p.add(f"{i}.  {step}", STEP, gap=24)
            if c["notes"]:
                p.rule()
                p.add("Do not", LABEL, gap=10)
                for n in c["notes"]:
                    p.add(f"×  {n}", BODY, gap=12)
            p.rule()
            flag = "" if c["vetted"] else "  ·  NOT YET REVIEWED"
            p.add(f"{c['source']}{flag}", SMALL)
        elif name == "doc":
            secs = self.engine.library.doc_sections(s["doc"])
            title = "Library"
            p.add(secs[0].title, HEAD, gap=8)
            flag = "" if secs[0].vetted else "  ·  NOT YET REVIEWED"
            p.add(f"{secs[0].source}  ·  {secs[0].date}{flag}", SMALL, gap=30)
            for sec in secs:
                if sec.section != sec.title:
                    p.add(sec.section, ITEM, gap=10)
                p.add(sec.text, BODY, gap=30)
        elif name == "about":
            title = "About"
            p.add("S-01 survival reference", HEAD, gap=20)
            for line in [
                "Answers come only from the library on this device. Every answer shows its source.",
                "Emergencies open pre-written cards. The AI model is not involved.",
                "It will never confirm that a wild plant or mushroom is safe to eat.",
                "It will not generate medication doses. It only quotes them from sources.",
                "If the library doesn't cover something, it says so instead of guessing.",
                "This is a reference, not a rescue device. Carry a satellite messenger or PLB.",
            ]:
                p.add("•  " + line, BODY, gap=18)

        s["scroll"] = min(s.get("scroll", 0), p.max_scroll)
        img = canvas(title, hints, status)
        p.draw(img, s["scroll"], sel)
        return quantize(img)
