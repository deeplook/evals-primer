# ADR 0003: The Agents SDK is the system under test; ownership among primers

- Status: Accepted
- Date: 2026-11-23

## Context

Lessons 14–18 evaluate agents: injection in tool results, unsafe intermediate
tool calls, pass^k, scaffold cost, and guardrail ablation. agents-primer owns
control flow around the OpenAI Agents SDK. harness-primer owns policy around
`Runner` (context, memory, tool-result checks, backends), and its roadmap
currently leaves "a golden set, a judge, pass-rate history" to mlops-primer.

## Decision

Use the OpenAI Agents SDK only as the agent being attacked and measured, with
`ScriptedModel` offline. Do not teach harness policy here; link to
harness-primer instead. evals-primer takes over the golden set, judge, and
pass-rate follow-up; harness-primer's README and roadmap are updated to point
here once those lessons exist. When the model is adversarial and Inspect drives
the agent, use `sandbox_agent_bridge()`, not the in-process `agent_bridge()`.

Lessons 14–18 run the agent through `_agent.sdk_solver`, a custom Inspect
solver that calls `Runner.run` with the SDK's `ScriptedModel` offline. That
keeps the SDK's own scripted model, which `agent_bridge()` would replace with
an Inspect model. It is safe in process only because every tool is an
in-memory fake that appends to a ledger; an agent with real tools would need
`sandbox_agent_bridge()` or a container.

## Consequences

`openai-agents` is a runtime dependency. Lesson 21 writes `out/scores.json`
(override with `EVALS_SCORES`) as a list of records with the fields
harness-primer lesson 16 reads (`peer`, `validation_accuracy`, `rows`), plus
`ci_low`, `ci_high`, and `leaks`. Lessons overlapping agents-primer 35–38
link to them rather than repeating them.
