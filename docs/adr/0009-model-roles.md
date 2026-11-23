# ADR 0009: Target, judge, and attacker are separate model roles

- Status: Accepted
- Date: 2026-11-23

## Context

Until lesson 18, `--local` and `--live` swapped the one model a lesson cared
about. Several lessons involve more than one model, in different roles:

- the **target**, the system under test (most lessons);
- the **judge** or classifier that grades it (07, 11, 12);
- the **attacker** that writes attacks against it (22).

They want different models. A realistic setup is a small target you might
ship, graded and attacked by a stronger model. A 3B model judging or
attacking itself shows the mechanics but not much more: run against the same
fixtures, `llama3.2` as judge failed a correct "seven continents" in lesson
11, where `mistral-nemo:12b` agreed with every gold label.

## Decision

- The target follows `--local` (`EVALS_LOCAL_MODEL`) and `--live`
  (`EVALS_MODEL`), as before.
- `EVALS_JUDGE_MODEL` and `EVALS_ATTACKER_MODEL` choose the other roles,
  through `_shared.role_model`. A value of `local/<name>` is a model on the
  local OpenAI-compatible server; anything else is an Inspect model name, so a
  hosted model works the same way. Setting the variable is the explicit
  opt-in ADR 0006 asks for.
- Unset, a role follows `--local` and `--live` like the target, and is
  scripted otherwise. A lesson asserts planted results only while the role it
  measures is scripted.
- Attacker goals are benign markers (ADR 0007): reveal a fake code, or reply
  with a fixed string. A hosted attacker is never asked for real harm, which
  keeps it within provider policies and makes success a string check.
- Attacker loops have a hard round budget and print the number of model calls
  they made.

## Alternatives considered

- One global "strong model" switch. It cannot express a weak target graded by
  a strong judge, which is the point.
- Inspect's `model_roles` on `eval()`. It fits judges inside Inspect scorers,
  but the lessons also need the role model in plain Python (07) and inside a
  solver (22); one helper keeps the three uses the same.

## Consequences

On a 24 GB machine, a 12B judge or attacker (`mistral-nemo:12b`, 7.1 GB) fits
beside a 3B target. Two local models at once are slower; Ollama loads and
unloads them as needed. A stronger judge is still measured against gold
labels; being stronger does not exempt it.

## References

- [Shared helpers](../../examples/_shared.py)
- [Lesson 07](../../examples/07_toxicity.py), [11](../../examples/11_llm_as_judge.py), [12](../../examples/12_judge_reliability.py)
