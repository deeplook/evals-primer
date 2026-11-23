"""Long context beyond the needle: scattered evidence, not length, is the hard part.

A needle test hides one fact in filler and asks for it back. Most models pass.
LURCH (2026) found that context length alone does not explain failures:
performance degrades sharply when the evidence for an answer is *dispersed*
through the context, and stays relatively stable when it is localised.

Two haystacks of identical length are built from the same filler and the same
facts. In the *local* one each chain of facts sits together; in the
*scattered* one its facts are far apart. A needle question and two two-hop
questions are asked against each. The scripted model answers every needle and
every local question, and fails the scattered two-hop ones.

Keep haystacks short on a 24 GB machine (`EVALS_HAYSTACK_WORDS`, default
1500). Ollama's default context window can be shorter than the haystack, and
it truncates silently; check the model's `num_ctx` (raise it in a Modelfile)
before trusting a longer local run.
"""

from __future__ import annotations

import random
from typing import Any

from _shared import (
    check_scorer,
    explanations,
    lesson_model,
    offline,
    run_eval,
    setting,
)
from inspect_ai import Task
from inspect_ai.dataset import Sample
from inspect_ai.solver import generate, system_message

WORDS = int(setting("EVALS_HAYSTACK_WORDS", "1500"))
SYSTEM = "Answer from the notes only, with the bare value."

# Each chain is a list of facts that must be combined, then its question.
CHAINS = {
    "needle": (["The wifi password for the lab is heron42."],
               "What is the wifi password for the lab?", "heron42"),
    "key": (["The archive key is held by Ines Brandt.",
             "Ines Brandt works in Building 4.",
             "Building 4 closes at 18:30."],
            "When does the building of the archive key holder close?", "18:30"),
    "badge": (["Badge 7731 belongs to Tomas Reyes.",
               "Tomas Reyes reports to the night shift lead.",
               "The night shift lead is Aiko Mori."],
              "Who is the night shift lead for the owner of badge 7731?", "Aiko Mori"),
}  # fmt: skip
PLANTED_MISSES = {"scattered-key", "scattered-badge"}

SUBJECTS = [
    "The cafeteria",
    "The loading dock",
    "The east stairwell",
    "Room 112",
    "The print queue",
    "The visitor desk",
    "The parking deck",
    "The mailroom",
]
EVENTS = [
    "was repainted",
    "was inspected",
    "changed its hours",
    "got a new sign",
    "was cleaned",
    "was mentioned in a memo",
    "had a short outage",
    "was moved",
]
DAYS = ["on Monday", "on Tuesday", "last week", "in spring", "after the audit"]  # fmt: skip


def filler(count: int, seed: int = 7) -> list[str]:
    rng = random.Random(seed)
    return [
        f"Note {i}: {rng.choice(SUBJECTS)} {rng.choice(EVENTS)} {rng.choice(DAYS)}."
        for i in range(count)
    ]


def haystack(scattered: bool) -> str:
    facts = [fact for chain, _, _ in CHAINS.values() for fact in chain]
    lines = filler(max(WORDS // 9 - len(facts), 10))
    slots = len(lines)
    if scattered:
        # Spread every chain over the whole context: early, middle, late.
        for c, (chain, _, _) in enumerate(CHAINS.values()):
            for f, fact in enumerate(chain):
                lines.insert((f * slots) // len(chain) + c, fact)
    else:
        # Keep each chain's facts together at one point.
        for c, (chain, _, _) in enumerate(CHAINS.values()):
            at = ((c + 1) * slots) // (len(CHAINS) + 1)
            lines[at:at] = chain
    return " ".join(lines)


def prompt(layout: str, question: str) -> str:
    return f"Notes: {haystack(layout == 'scattered')}\n\nQuestion: {question}"


def answered(completion: str, meta: dict[str, Any]) -> str | None:
    return None if meta["answer"].lower() in completion.lower() else "wrong"


def main() -> None:
    local_len, scattered_len = len(haystack(False)), len(haystack(True))
    if local_len != scattered_len:
        raise AssertionError(f"haystacks differ: {local_len} vs {scattered_len}")

    dataset, scripted = [], {}
    for layout in ("local", "scattered"):
        for key, (_, question, answer) in CHAINS.items():
            sample_id = f"{layout}-{key}"
            text = prompt(layout, question)
            dataset.append(
                Sample(id=sample_id, input=text, metadata={"answer": answer})
            )
            scripted[text] = "I don't know." if sample_id in PLANTED_MISSES else answer

    task = Task(
        dataset=dataset,
        solver=[system_message(SYSTEM), generate()],
        scorer=check_scorer("answered", answered),
    )
    missed = set(explanations(run_eval(task, lesson_model(scripted)), "answered"))

    def accuracy(layout: str) -> float:
        return 1 - len({m for m in missed if m.startswith(layout)}) / len(CHAINS)

    if offline() and missed != PLANTED_MISSES:
        raise AssertionError(f"missed {missed}")
    print(
        f"OK: {local_len} chars each; local={accuracy('local'):.2f} "
        f"scattered={accuracy('scattered'):.2f}; missed={sorted(missed)}"
    )


if __name__ == "__main__":
    main()
