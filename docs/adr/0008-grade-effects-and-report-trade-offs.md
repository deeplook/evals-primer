# ADR 0008: Grade executed effects, and never report a safety number alone

- Status: Accepted
- Date: 2026-11-23

## Context

Lessons 13–18 evaluate attacks, defences, and agents. Three shortcuts kept
producing wrong answers while they were built:

- A transcript is not an action. In lesson 17 a grader that read the final
  message passed 9/9 runs, including a double refund, a refund claimed but
  never made, and refunds against policy. In lesson 15 a local model sent 500
  messages and then wrote a refusal.
- A security number alone rewards a useless system. A model that refuses
  everything has zero attack success.
- An accuracy number alone hides its price. A planner scaffold can win by
  spending more model calls.

## Decision

- Agent tools in this repo are in-memory fakes that append to a `Ledger`.
  Scorers grade what the ledger says was executed. The calls the model
  requested are kept in sample metadata for reading, and the transcript is
  never the evidence for an action.
- Attack lessons report attack success together with clean-task utility, and
  utility under attack where it applies (13, 14, 18). A defence is measured
  off and on, with both numbers each time.
- Agent comparisons report accuracy with model calls, tokens, and wall time
  (17). Offline, `_agent.SCRIPTED_USAGE` charges each scripted model call a
  fixed 460 tokens, so cost differences are visible without a real model.
- Repeated runs report pass^k (every run succeeds) next to pass@k.

## Consequences

Every agent lesson needs a fake tool layer that records effects, and every
attack lesson needs clean cases as well as attacks. Offline token counts are
illustrative, not measured; real counts come from `--local` or `--live`.

## References

- [Agent harness](../../examples/_agent.py)
- [Lesson 17](../../examples/17_agent_passk.py)
- [Lesson 18](../../examples/18_guardrail_ablation.py)
