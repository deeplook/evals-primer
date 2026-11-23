# ADR 0006: What each run mode asserts

- Status: Accepted
- Date: 2026-11-23

## Context

Lessons run in three modes: scripted (default), `--local` (Ollama or
llama-server), and `--live` (a hosted API). ADR 0002 says offline runs assert
planted results and real runs report. Building lessons 01–12 surfaced more
rules. Running lesson 09 against a local model first compared that model's
replies with hand labels written for the scripted replies, which produced
meaningless "detector misread" results.

## Decision

- Real models are opt-in through explicit flags. A lesson never probes for a
  server or a key on its own; without its flag it prints `SKIP:` and exits 0.
  The offline tests therefore cannot reach a model by accident.
- In scripted mode a lesson raises unless every scorer flags exactly the
  planted cases, then prints `OK:` with what was caught.
- In `--local` and `--live` mode a lesson reports rates and flagged IDs and
  asserts nothing about the model's behaviour.
- Hand labels describe the scripted replies. They are never compared with a
  real model's replies.
- When the subject is an evaluator (a judge or classifier, as in lessons 07,
  11 and 12), only the evaluator is swapped. The answers stay scripted, so the
  gold labels still apply and the evaluator is measured in every mode.
- Lessons from 05 on write each check as a plain Python function
  `(completion, metadata) -> reason | None` and wrap it with
  `_shared.check_scorer`. The reason becomes the score's explanation, which
  `inspect view` shows per sample.

## Alternatives considered

- Auto-detecting a running Ollama in tests. Convenient locally, but CI results
  would depend on the machine, and a developer's test run would call a model.
- Writing an `@scorer` per check. More Inspect surface in every lesson and
  harder to read than a ten-line function.

## Consequences

`make check-all` is deterministic. A real-model run can still expose a bug in
a check (lesson 09's apostrophe bug was found that way); the fix is to plant
that case in the scripted fixture so the scripted run keeps catching it.
`make local` lists the lessons that accept `--local`.

## References

- [Shared helpers](../../examples/_shared.py)
- [ADR 0002](0002-offline-lessons-test-the-scorer.md)
