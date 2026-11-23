# ADR 0007: Fixtures are inline, hand-written, and never actionable

- Status: Accepted
- Date: 2026-11-23

## Context

The plan listed a `data/` directory for fixtures. Lessons 01–12 never needed
it: each set has four to eight items and reads best next to the check that
uses it. Lessons 13–16 cover prompt injection, jailbreaks, and a garak scan,
where fixtures could easily become a collection of working attacks or harmful
content.

## Decision

- Fixtures live in the lesson file, or in a small `examples/_*.py` module when
  several lessons share one set (as `_qa.py` does for 01–04). There is no
  `data/` directory.
- Fixtures are hand-written for this repo, not copied from public benchmarks,
  because public sets are contaminated (lesson 05).
- Harmful requests are worded only as specifically as a lesson needs.
  Harmful replies are `[stub]` placeholders; the scorer sees the shape of a
  compliance or a refusal, never usable content.
- Injection payloads are benign markers: an instruction to call a harmless
  tool, reveal a fake canary, or append a fixed string. Success is detected by
  that marker.
- Jailbreak lessons that use a public benchmark refer to a small subset by
  behaviour ID and fetch nothing at test time. Benchmark prompts are not
  copied into the repo.
- garak output goes to `out/`, which is gitignored.

## Consequences

The repo can be read, run, and published without containing working attacks
or harmful text. Attack success rates are measured on markers, which is
exactly what a scorer needs. Readers who want realistic attack strength run
garak or a benchmark subset locally against their own model.

## References

- [Lesson 09](../../examples/09_refusal.py)
- [ADR 0004](0004-garak-via-uvx.md)
