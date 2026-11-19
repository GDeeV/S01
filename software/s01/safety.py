"""Routing rules that run before any model call. These are hard-coded on
purpose: the riskiest questions never reach the language model."""
import re
from dataclasses import dataclass
from typing import Optional

EMERGENCY = {
    "mushroom-ingestion": [r"\bate (a |some )?(wild )?mushroom", r"mushroom poison",
                           r"\bate (a |some )?(wild )?(plant|berr)"],
    "severe-bleeding": [r"bleed", r"blood (won'?t|will not) stop", r"hemorrhag", r"tourniquet"],
    "snakebite": [r"snake ?bite", r"bit(ten)? by (a )?(rattle)?snake", r"(rattle)?snake bit"],
    "anaphylaxis": [r"anaphyla", r"allergic reaction", r"throat (is )?(closing|swelling)",
                    r"epi ?pen", r"can'?t breathe after"],
    "hypothermia": [r"hypotherm", r"can'?t (get|stop) (warm|shiver)", r"stopped shivering"],
}

EDIBLE_VERB = re.compile(r"\b(eat|eaten|edible|eatable|consume|forage|poisonous|toxic|safe)\b")
EDIBLE_THING = re.compile(r"\b(mushroom|fung(us|i)|toadstool|plant|berr(y|ies)|lea(f|ves)|"
                          r"root|flower|seed|nut|weed|herb|greens)s?\b")
DOSE = re.compile(r"\b(dose|doses|dosage|dosing|mg|milligrams?)\b|"
                  r"how (much|many)\b.*\b(take|give|pills?|tablets?)\b")

EDIBILITY_MESSAGE = (
    "This device cannot confirm that any wild plant or mushroom is safe to eat. "
    "Deadly species have edible lookalikes, and a description is not enough to tell them apart. "
    "Below is what the library says about related species and their lookalikes."
)
NO_INFO_MESSAGE = (
    "The library doesn't cover this, so I won't guess. "
    "Try different words, or browse the library by topic."
)


@dataclass
class Route:
    kind: str                 # emergency | edibility | dose | normal
    card_id: Optional[str] = None


def route(question: str) -> Route:
    q = question.lower()
    for card_id, patterns in EMERGENCY.items():
        if any(re.search(p, q) for p in patterns):
            return Route("emergency", card_id)
    if EDIBLE_VERB.search(q) and EDIBLE_THING.search(q):
        return Route("edibility")
    if DOSE.search(q):
        return Route("dose")
    return Route("normal")
