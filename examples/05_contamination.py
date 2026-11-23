"""Contamination: compare a public set with a rewritten twin, and plant a canary.

A model that saw a benchmark in training can score well by recalling answers.
Two cheap checks catch it. First, a *twin*: the same problems with new numbers,
so a recalled answer is now wrong. A gap between public and twin accuracy is
the signal, and a twin answer that equals the *public* target names the
memorised item. Second, a *canary*: a unique string published with the data.
If a model can complete it, the data was in its training set.

The scripted model has memorised the public set: it is perfect there, repeats
two public answers on the twin, and completes the canary.
"""

from __future__ import annotations

import re
from typing import Any

from _shared import (
    check_scorer,
    completions,
    explanations,
    lesson_model,
    offline,
    run_eval,
)
from inspect_ai import Task
from inspect_ai.dataset import Sample
from inspect_ai.solver import generate, system_message

SYSTEM = "Answer with the number only."
CANARY = "evals-primer canary 6f1c2a9e-0b7d-4e55-9a3c-d1e8f0b42c17"
CANARY_PROMPT = f"Continue this string exactly: {CANARY[:24]}"

# (id, public question, public answer, twin question, twin answer)
PAIRS = [
    ("train", "A train goes 60 km/h for 3 hours. How many km?", "180",
     "A train goes 70 km/h for 3 hours. How many km?", "210"),
    ("apples", "Tom has 12 apples and gives away 5. How many are left?", "7",
     "Tom has 15 apples and gives away 5. How many are left?", "10"),
    ("eggs", "A box holds 8 rows of 6 eggs. How many eggs?", "48",
     "A box holds 7 rows of 6 eggs. How many eggs?", "42"),
    ("pages", "Sara reads 15 pages a day for 4 days. How many pages?", "60",
     "Sara reads 12 pages a day for 4 days. How many pages?", "48"),
]  # fmt: skip

SCRIPTED = (
    {public_q: public_a for _, public_q, public_a, _, _ in PAIRS}
    | {
        PAIRS[0][3]: "180",  # recalled the public answer
        PAIRS[1][3]: "10",
        PAIRS[2][3]: "48",  # recalled the public answer
        PAIRS[3][3]: "48",
        CANARY_PROMPT: CANARY[24:],
    }
)
MEMORISED = {"twin-train", "twin-eggs"}


def last_number(text: str) -> str | None:
    found = re.findall(r"-?\d+", text)
    return found[-1] if found else None


def correct(completion: str, meta: dict[str, Any]) -> str | None:
    if meta["split"] == "canary":
        return "completed the canary" if CANARY[24:] in completion else None
    answer = last_number(completion)
    if answer == meta["target"]:
        return None
    if meta["split"] == "twin" and answer == meta["public_target"]:
        return f"memorised: gave public answer {answer}"
    return f"wrong: {answer}"


def samples() -> list[Sample]:
    rows = []
    for key, public_q, public_a, twin_q, twin_a in PAIRS:
        rows.append(
            Sample(
                id=f"public-{key}",
                input=public_q,
                metadata={"split": "public", "target": public_a},
            )
        )
        rows.append(
            Sample(
                id=f"twin-{key}",
                input=twin_q,
                metadata={"split": "twin", "target": twin_a, "public_target": public_a},
            )
        )
    rows.append(Sample(id="canary", input=CANARY_PROMPT, metadata={"split": "canary"}))
    return rows


def main() -> None:
    task = Task(
        dataset=samples(),
        solver=[system_message(SYSTEM), generate()],
        scorer=check_scorer("correct", correct),
    )
    log = run_eval(task, lesson_model(SCRIPTED))
    reasons = explanations(log, "correct")
    total = len(completions(log))
    split_size = (total - 1) // 2

    def accuracy(split: str) -> float:
        wrong = [key for key in reasons if key.startswith(split)]
        return 1 - len(wrong) / split_size

    public, twin = accuracy("public"), accuracy("twin")
    memorised = {key for key, why in reasons.items() if why.startswith("memorised")}
    canary_hit = "canary" in reasons

    if offline() and (memorised != MEMORISED or not canary_hit or public != 1.0):
        raise AssertionError(f"unexpected results: {reasons}")
    print(
        f"OK: public={public:.2f} twin={twin:.2f} gap={public - twin:.2f}; "
        f"memorised={sorted(memorised)} canary={'leaked' if canary_hit else 'clean'}"
    )


if __name__ == "__main__":
    main()
