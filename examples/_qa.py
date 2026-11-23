"""The labelled question set shared by lessons 01–04, with its planted answers.

Lessons 01–04 keep the data and scorers fixed and change only where the answers
come from: a recorded list, a scripted model, a local server, a hosted API.
"""

from __future__ import annotations

from dataclasses import dataclass

from inspect_ai import Task
from inspect_ai.dataset import Sample
from inspect_ai.scorer import match, pattern
from inspect_ai.solver import generate, system_message

SYSTEM = "Answer with the bare value only, no sentence."


@dataclass(frozen=True)
class Item:
    id: str
    question: str
    target: str
    scripted: str  # the planted answer the offline path returns


ITEMS = [
    Item("capital", "Capital of France?", "Paris", "Paris"),
    Item("sum", "What is 17 + 25?", "42", "43"),
    Item("symbol", "Chemical symbol for gold?", "Au", "The symbol is Au."),
    Item("year", "Year the Berlin Wall fell?", "1989", "1991"),
    Item("planet", "Largest planet in the solar system?", "Jupiter", "Jupiter"),
]

# "sum" is off by one and "year" is a near miss: real errors.
PLANTED = {"sum", "year"}
# "symbol" is right but wrapped in a sentence: only a strict scorer rejects it.
FORMAT_ONLY = {"symbol"}

SCRIPTED = {item.question: item.scripted for item in ITEMS}

# Extract the last word or number, ignoring a surrounding sentence and period.
LAST_TOKEN = r"(\w+)\W*$"


def qa_task() -> Task:
    """The question set as an Inspect task with a strict and a lenient scorer."""
    return Task(
        dataset=[
            Sample(id=item.id, input=item.question, target=item.target)
            for item in ITEMS
        ],
        solver=[system_message(SYSTEM), generate()],
        scorer=[match(location="exact"), pattern(LAST_TOKEN)],
    )
