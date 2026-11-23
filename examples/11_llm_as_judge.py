"""LLM as judge: grade answers with a rubric, then grade the judge against gold.

Exact match fails when a correct answer can be phrased many ways. A judge model
reads the question, the reference, and the submission, and returns a grade.
Inspect's `model_graded_qa` scorer does this; the rubric goes in
`instructions`, and any model can be the judge.

A judge is a model, so it has to be evaluated too. Each answer here carries a
human gold label. The scripted judge has two planted faults that published
judges show: it passes a long, confident, wrong answer (verbosity bias) and
fails a terse, correct one. Agreement with gold, the false-pass rate, and the
false-fail rate tell you whether the judge's numbers can be trusted.

The answers stay scripted in every mode, so the gold labels always apply.
`--local` or `--live` replaces only the judge, and the lesson measures it.
"""

from __future__ import annotations

import re

from _shared import lesson_model, offline, run_eval, scripted_model
from inspect_ai import Task
from inspect_ai.dataset import Sample
from inspect_ai.scorer import model_graded_qa
from inspect_ai.solver import generate

RUBRIC = (
    "Grade C if the submission states the same fact as the criterion, even in a "
    "single word. Grade I if it states a different fact, however long, fluent, "
    "or confident it is. Length and style do not matter. Reason briefly, then "
    "end with 'GRADE: C' or 'GRADE: I'."
)

FLUENT_WRONG = (
    "Charlotte Brontë wrote it in 1813; it remains a landmark of English "
    "literature and shaped the modern novel of manners."
)

# (id, question, reference, scripted answer, gold: is the answer correct?)
CASES = [
    ("boil", "Boiling point of water at sea level in Celsius?", "100",
     "100 °C.", True),
    ("austen", "Who wrote 'Pride and Prejudice'?", "Jane Austen",
     FLUENT_WRONG, False),
    ("root", "What is the square root of 81?", "9", "9", True),
    ("canberra", "What is the capital of Australia?", "Canberra", "Sydney.", False),
    ("continents", "How many continents in the seven-continent model?", "7",
     "There are seven continents.", True),
    ("water", "Chemical formula of water?", "H2O",
     "H2O: two hydrogen atoms and one oxygen atom.", True),
]  # fmt: skip

# Planted judge faults: passes the fluent wrong answer, fails the terse right one.
JUDGE = {
    answer: "GRADE: C" if gold else "GRADE: I" for _, _, _, answer, gold in CASES
} | {CASES[1][3]: "GRADE: C", CASES[2][3]: "GRADE: I"}
EXPECTED_FALSE_PASS, EXPECTED_FALSE_FAIL = {"austen"}, {"root"}

SUBMISSION = re.compile(
    r"\[BEGIN SUBMISSION \([^)]*\)\]\n(.*?)\n\[END SUBMISSION", re.DOTALL
)


def submission(judge_prompt: str) -> str:
    found = SUBMISSION.search(judge_prompt)
    return found.group(1) if found else judge_prompt


def main() -> None:
    answers = {question: answer for _, question, _, answer, _ in CASES}
    judge = lesson_model(JUDGE, key=submission)
    task = Task(
        dataset=[
            Sample(id=key, input=question, target=reference)
            for key, question, reference, _, _ in CASES
        ],
        solver=generate(),
        scorer=model_graded_qa(instructions=RUBRIC, model=judge),
    )
    log = run_eval(task, scripted_model(answers))
    gold = {key: label for key, *_, label in CASES}
    grade = {
        str(s.id): s.scores["model_graded_qa"].value == "C"
        for s in log.samples or []
        if s.scores
    }
    false_pass = {k for k in gold if grade[k] and not gold[k]}
    false_fail = {k for k in gold if not grade[k] and gold[k]}
    agreement = 1 - (len(false_pass) + len(false_fail)) / len(gold)

    if offline() and (
        false_pass != EXPECTED_FALSE_PASS or false_fail != EXPECTED_FALSE_FAIL
    ):
        raise AssertionError(f"false pass={false_pass} false fail={false_fail}")
    print(
        f"OK: judge agrees with gold {agreement:.2f}; "
        f"false pass={sorted(false_pass)} false fail={sorted(false_fail)}"
    )


if __name__ == "__main__":
    main()
