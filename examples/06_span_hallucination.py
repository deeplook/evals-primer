"""Span-level hallucination: mark the exact sentences a context does not support.

A whole-answer "faithful or not" label hides where the problem is. Here each
answer is split into sentences, and a sentence is unsupported when it names a
number or a proper noun that the evidence does not contain. This check is
deliberately crude; it catches invented facts, not paraphrased contradictions.
Lesson 11 replaces it with a judge.

The last sample is an agent trace. A tool returned a wrong berth count and the
answer repeated it. Grounded against the *trace*, the answer looks supported.
Grounded against the *trusted source*, it is not. Evidence has to be the source
you trust, not whatever the agent happened to read.
"""

from __future__ import annotations

import re
from typing import Any

from _shared import Check, check_scorer, explanations, lesson_model, offline, run_eval
from inspect_ai import Task
from inspect_ai.dataset import Sample
from inspect_ai.solver import generate, system_message

SOURCE = (
    "Harbor Station opened in 1987. It has 412 berths and is run by the "
    "Port Authority of Lund."
)
SYSTEM = "Answer from the context only, in one or two sentences."
COMMON = {"It", "The", "A", "An", "This", "There"}

# (id, question, tool output seen by the agent, scripted answer)
CASES = [
    ("opened", "When did Harbor Station open?", "",
     "Harbor Station opened in 1987."),
    ("berths", "Who runs Harbor Station, and how many berths does it have?", "",
     "It is run by the Port Authority of Lund. It has 512 berths."),
    ("designer", "Tell me about Harbor Station's history.", "",
     "Harbor Station opened in 1987. It was designed by Elena Marsh."),
    ("trace", "How many berths does Harbor Station have? Use the lookup tool.",
     "lookup(berth_count) -> 214",
     "Harbor Station has 214 berths."),
]  # fmt: skip

# Which samples each scorer must flag, and the sentence it must point at.
EXPECTED_SOURCE = {
    "berths": "It has 512 berths.",
    "designer": "It was designed by Elena Marsh.",
    "trace": "Harbor Station has 214 berths.",
}
EXPECTED_TRACE = {key: EXPECTED_SOURCE[key] for key in ("berths", "designer")}


def prompt(question: str, tool_output: str) -> str:
    trace = f"\nTool output: {tool_output}" if tool_output else ""
    return f"Context: {SOURCE}{trace}\nQuestion: {question}"


def claims(sentence: str) -> set[str]:
    """Numbers and capitalised words: the checkable facts in a sentence."""
    words = re.findall(r"[A-Za-z]+|\d+", sentence)
    return {w for w in words if w.isdigit() or (w[0].isupper() and w not in COMMON)}


def unsupported(answer: str, evidence: str) -> list[str]:
    known = set(re.findall(r"[A-Za-z]+|\d+", evidence))
    sentences = re.split(r"(?<=[.!?])\s+", answer.strip())
    return [s for s in sentences if s and not claims(s) <= known]


def grounded_in(field: str) -> Check:
    def check(completion: str, meta: dict[str, Any]) -> str | None:
        bad = unsupported(completion, meta[field])
        return " | ".join(bad) if bad else None

    return check


def main() -> None:
    dataset = [
        Sample(
            id=key,
            input=prompt(question, tool),
            metadata={"source": SOURCE, "trace": f"{SOURCE} {tool}"},
        )
        for key, question, tool, _ in CASES
    ]
    scripted = {prompt(q, tool): answer for _, q, tool, answer in CASES}
    task = Task(
        dataset=dataset,
        solver=[system_message(SYSTEM), generate()],
        scorer=[
            check_scorer("source", grounded_in("source")),
            check_scorer("trace", grounded_in("trace")),
        ],
    )
    log = run_eval(task, lesson_model(scripted))
    by_source = explanations(log, "source")
    by_trace = explanations(log, "trace")

    if offline():
        if by_source != EXPECTED_SOURCE:
            raise AssertionError(f"source grounding flagged {by_source}")
        if by_trace != EXPECTED_TRACE:
            raise AssertionError(f"trace grounding flagged {by_trace}")
    for key, spans in by_source.items():
        print(f"  {key}: unsupported -> {spans}")
    missed = sorted(set(by_source) - set(by_trace))
    print(
        f"OK: source flagged {len(by_source)}/{len(CASES)}, trace flagged "
        f"{len(by_trace)}; trace grounding missed {missed}"
    )


if __name__ == "__main__":
    main()
