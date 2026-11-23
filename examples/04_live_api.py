"""Live API: the same task against a hosted model, with `--live`.

Only the model argument changes from lesson 02. `EVALS_MODEL` takes any
Inspect model name (default `openai/gpt-6-luna`) and the provider reads its
key from the environment. This uses API credits. Without `--live`, or without
`OPENAI_API_KEY`, it prints `SKIP:`.

openai-primer's `31_prompt_eval.py` evaluates a prompt against the hosted API
directly; here the same call sits behind Inspect, so the scorers and logs stay
the same whichever model answers.
"""

from __future__ import annotations

from _qa import qa_task
from _shared import LIVE_MODEL, failed_ids, live, live_model, run_eval, skip


def main() -> None:
    if not live():
        skip("pass --live to call EVALS_MODEL (uses API credits)")
    log = run_eval(qa_task(), live_model())
    total = len(log.samples or [])
    strict = 1 - len(failed_ids(log, "match")) / total
    lenient = 1 - len(failed_ids(log, "pattern")) / total
    print(f"OK: {LIVE_MODEL} match={strict:.2f} pattern={lenient:.2f} n={total}")


if __name__ == "__main__":
    main()
