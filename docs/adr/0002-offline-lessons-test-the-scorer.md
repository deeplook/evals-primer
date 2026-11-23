# ADR 0002: Offline lessons plant failures and test the scorer

- Status: Accepted
- Date: 2026-11-23

## Context

CI runs without keys or GPUs, so the model is scripted. A scripted model that
answers everything correctly makes every metric 1.0 and teaches nothing. Sibling
primers say so: their offline responses are fixtures, not model evaluations.

## Decision

Every offline fixture plants known failures (wrong answers, leaked PII,
unsupported spans, over-refusals, order-flipped judge verdicts) and, where
useful, a near miss that one scorer should accept and another should reject.
Each lesson raises unless its scorers flag exactly the planted cases, then
prints an `OK:` line with what was caught.

Scripted models come from the library being taught: Inspect's `mockllm/model`
with a prompt-to-output table for plain eval lessons, and the Agents SDK's
`ScriptedModel` for agent lessons. There is no home-made fake model.

## Consequences

Offline runs measure the evaluator, which is the part a reader writes. With
`--live` or a local model, the same scorers measure a real model and the lesson
reports numbers instead of asserting them. Fixtures must be keyed by prompt,
not by call order, because Inspect may run samples concurrently.
