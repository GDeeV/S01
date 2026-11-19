"""Test the answer pipeline from the terminal, no window.  python ask.py "question" """
import sys

from s01.answer import Engine

engine = Engine()
print(f"[mode: {engine.mode}]")
a = engine.ask(" ".join(sys.argv[1:]) or "how do I purify stream water")
print(f"\n{a.kind.upper()}")
if a.kind == "emergency":
    card = engine.cards[a.card_id]
    print(card["title"])
    for i, s in enumerate(card["steps"], 1):
        print(f"  {i}. {s}")
else:
    print(a.text)
    for i, p in enumerate(a.passages, 1):
        print(f"  [{i}] {p.title} — {p.section} ({p.source})")
