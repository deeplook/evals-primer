"""Judge reliability: ask in both orders, and report Cohen's kappa, not agreement.

A pairwise judge answers "which is better, A or B?". Many judges prefer
whichever answer comes first. Ask every pair twice, AB and BA. A consistent
judge names the same answer both times; a judge that names the same *letter*
both times has flipped, and that verdict carries no information.

Raw agreement with human labels also overstates quality, because two raters
that both mostly say "first" agree by chance. Cohen's kappa subtracts that
chance agreement: 1 is perfect, 0 is no better than chance.

The scripted judge always answers "A" on three of eight pairs. In AB order
alone it looks 75% right; kappa is under 0.5, and the BA order exposes all
three flips. `--local`, `--live`, or `EVALS_JUDGE_MODEL` swaps in a real
judge; the answers and human labels are fixed, so the comparison still holds.
"""

from __future__ import annotations

from _shared import completions, role_model, run_eval
from inspect_ai import Task
from inspect_ai.dataset import Sample
from inspect_ai.solver import generate, system_message

SYSTEM = "You compare two answers to a question. Reply with A or B only."

# (id, question, answer x, answer y, human preference: "x" or "y")
PAIRS = [
    ("p1", "Why is the sky blue?", "Rayleigh scattering of sunlight.",
     "Because it reflects the ocean.", "x"),
    ("p2", "What does HTTP 404 mean?", "The server is overloaded.",
     "The requested resource was not found.", "y"),
    ("p3", "What is a prime number?", "A number with exactly two divisors.",
     "Any odd number.", "x"),
    ("p4", "What does 'idempotent' mean?", "It runs fast.",
     "Applying it twice has the same effect as once.", "y"),
    ("p5", "What is RAM?", "Working memory that loses data without power.",
     "A long-term storage disk.", "x"),
    ("p6", "What is DNS?", "A type of firewall.",
     "A system that maps names to IP addresses.", "y"),
    ("p7", "What is a mutex?", "A lock that lets one thread in at a time.",
     "A kind of loop.", "x"),
    ("p8", "Why use version control?", "To track and revert changes.",
     "To make code run faster.", "x"),
]  # fmt: skip

POSITION_BIASED = {"p5", "p6", "p8"}  # the scripted judge always says "A" here
WRONG_BUT_CONSISTENT = {"p7"}  # the scripted judge prefers y in both orders


def prompt(question: str, first: str, second: str) -> str:
    return f"Question: {question}\nAnswer A: {first}\nAnswer B: {second}\nBetter?"


def scripted_verdicts() -> dict[str, str]:
    verdicts = {}
    for key, question, x, y, human in PAIRS:
        better = "y" if key in WRONG_BUT_CONSISTENT else human
        for first, second, order in ((x, y, "xy"), (y, x, "yx")):
            if key in POSITION_BIASED:
                letter = "A"
            else:
                letter = "A" if order[0] == better else "B"
            verdicts[prompt(question, first, second)] = letter
    return verdicts


def cohen_kappa(a: list[str], b: list[str]) -> float:
    observed = sum(x == y for x, y in zip(a, b, strict=True)) / len(a)
    labels = set(a) | set(b)
    chance = sum((a.count(c) / len(a)) * (b.count(c) / len(b)) for c in labels)
    return (observed - chance) / (1 - chance)


def winner(reply: str, order: str) -> str:
    letter = reply.strip().upper()[:1]
    return order[0] if letter == "A" else order[1]


def main() -> None:
    dataset = []
    for key, question, x, y, _ in PAIRS:
        dataset.append(Sample(id=f"{key}-xy", input=prompt(question, x, y)))
        dataset.append(Sample(id=f"{key}-yx", input=prompt(question, y, x)))
    task = Task(dataset=dataset, solver=[system_message(SYSTEM), generate()])
    judge, scripted = role_model("judge", scripted_verdicts())
    replies = completions(run_eval(task, judge))

    human = [h for *_, h in PAIRS]
    ab = [winner(replies[f"{k}-xy"], "xy") for k, *_ in PAIRS]
    ba = [winner(replies[f"{k}-yx"], "yx") for k, *_ in PAIRS]
    flips = {k for (k, *_), w1, w2 in zip(PAIRS, ab, ba, strict=True) if w1 != w2}
    raw = sum(j == h for j, h in zip(ab, human, strict=True)) / len(human)
    kappa = cohen_kappa(ab, human)
    kept = [
        (j, h) for (k, *_), j, h in zip(PAIRS, ab, human, strict=True) if k not in flips
    ]
    consistent = sum(j == h for j, h in kept) / len(kept) if kept else 0.0

    if scripted and (flips != POSITION_BIASED or not kappa < raw):
        raise AssertionError(f"flips={flips} raw={raw} kappa={kappa}")
    print(
        f"OK: AB-only agreement={raw:.2f} kappa={kappa:.2f}; "
        f"position flips={len(flips)}/{len(PAIRS)} {sorted(flips)}; "
        f"agreement on consistent pairs={consistent:.2f}"
    )


if __name__ == "__main__":
    main()
