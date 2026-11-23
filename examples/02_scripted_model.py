"""Scripted model: the same set and scorers as an Inspect task, no GPU or key.

Lesson 01 scored a list by hand. Inspect names the same parts: a dataset of
`Sample`s, a solver that asks the model, and scorers. The model here is
Inspect's own `mockllm/model`, answering each prompt from the planted table,
so the full Inspect pipeline runs and writes a log under `out/inspect-logs/`.
Inspect's `match` and `pattern` scorers must flag the same samples as lesson
01's hand-written ones.
"""

from __future__ import annotations

from _qa import FORMAT_ONLY, PLANTED, SCRIPTED, qa_task
from _shared import failed_ids, run_eval, scripted_model


def main() -> None:
    log = run_eval(qa_task(), scripted_model(SCRIPTED))
    by_match = failed_ids(log, "match")
    by_pattern = failed_ids(log, "pattern")
    if by_match != PLANTED | FORMAT_ONLY:
        raise AssertionError(f"match flagged {sorted(by_match)}")
    if by_pattern != PLANTED:
        raise AssertionError(f"pattern flagged {sorted(by_pattern)}")
    print(
        f"OK: Inspect match flagged {len(by_match)}, pattern flagged "
        f"{len(by_pattern)}; same samples as lesson 01"
    )


if __name__ == "__main__":
    main()
