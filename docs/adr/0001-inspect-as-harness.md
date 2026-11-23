# ADR 0001: Use Inspect as the eval harness

- Status: Accepted
- Date: 2026-11-23

## Context

Each lesson needs a dataset, a way to ask a model, and a scorer, and it must run
offline in CI. The candidates were Inspect, DeepEval, promptfoo, a pytest plugin
such as pytest-evals, and plain Python. The OpenAI Evals platform shuts down on
30 November 2026 and is not a candidate.

## Decision

Use [Inspect](https://inspect.aisi.org.uk/) (`inspect-ai`, MIT). A lesson builds
an Inspect `Task` from samples, a solver, and one or more scorers, and runs it
through `examples/_shared.py:run_eval`.

## Alternatives considered

- DeepEval. Pytest-native and popular, but its default judge is a hosted model
  and its red-teaming is weaker than garak's.
- promptfoo. Config-driven and TypeScript-first; awkward in a Python series.
- pytest-evals or plain pytest. Lighter, but every lesson would rebuild the
  dataset/solver/scorer structure that Inspect already names.

## Consequences

Lessons teach Inspect's vocabulary, which carries over to real eval suites.
Inspect writes a log per run; `INSPECT_LOG_DIR` sends those to `out/`. The
smoke-test contract stays ordinary pytest over subprocesses (`OK:` lines), so CI
does not depend on `inspect eval`. DeepEval and pytest-evals appear in further
reading.
