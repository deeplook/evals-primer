"""Local model: the same task against Ollama or llama-server, with `--local`.

Both servers speak the OpenAI chat API, so Inspect's generic `openai-api`
provider reaches either one; only the base URL changes. The lesson probes
`LOCAL_BASE_URL`, then Ollama on port 11434, then llama-server on port 8080,
and uses `EVALS_LOCAL_MODEL` or the first chat model the server lists.

A real model is not scripted, so nothing is asserted about which samples
fail. The lesson reports both scorers' accuracy; the gap between them is how
often the model was right but did not follow the format instruction.
Without `--local`, or with no server up, it prints `SKIP:`.
"""

from __future__ import annotations

from _qa import qa_task
from _shared import failed_ids, local_model, run_eval


def main() -> None:
    model = local_model()
    log = run_eval(qa_task(), model)
    total = len(log.samples or [])
    strict = 1 - len(failed_ids(log, "match")) / total
    lenient = 1 - len(failed_ids(log, "pattern")) / total
    print(f"OK: {model.name} match={strict:.2f} pattern={lenient:.2f} n={total}")


if __name__ == "__main__":
    main()
