# Adding a lesson

A checklist distilled from ADRs 0002 and 0006–0009. A lesson that follows it
passes `make check-all` offline, teaches one idea, and measures a real model
honestly with `--local` or `--live`.

## Before writing

- **One idea.** If the docstring needs two "and"s, split the lesson. Lessons 16
  and 17 each hold two parts; each part has its own checks and output.
- **Number and name.** `examples/NN_snake_case.py`, next free number. Add a
  row to the README's lesson table, in the right group.
- **Sources.** If the docstring cites a paper, read it and state only what it
  reports. Six docstrings once overstated their sources; see the further
  reading in the README for what was checked.

## The fixture

- Hand-write a few cases in the lesson file. Share a set through a small
  `examples/_name.py` module only when several lessons use it (ADR 0007).
- **Plant failures.** The scripted answers must include the cases each check
  has to catch, and usually a near miss that one check should accept and
  another reject. A fixture where everything passes tests nothing (ADR 0002).
- Key scripted answers by prompt, not by call order; Inspect may run samples
  concurrently. `scripted_model(outputs, key=...)` takes a function when the
  key has to be extracted from a longer prompt.
- **Nothing actionable.** Harmful replies are `[stub]`. Injection and attack
  goals are benign markers: a fake code, a fixed string, a harmless tool call.

## The check

- Write it as a plain function `(completion, metadata) -> reason | None` and
  wrap it with `_shared.check_scorer(name, check)`.
- For agents, grade what the fake tools recorded in the `Ledger`
  (`metadata["executed"]`), never the transcript, and judge the run's total
  effect rather than each call (ADR 0008).
- Report safety with utility: attack success next to clean-task success, a
  defence off and on, accuracy next to model calls and tokens.
- Guardrails and parsers see raw model output: parse defensively (`"500"`
  arrives as a string, fields go missing, verdicts come back unparseable).

## Modes and roles

- Read settings with `setting("EVALS_…", default)`, never `os.environ`
  directly, and add a new one to `.env.example`, the README table, and the
  tests' `BLANKED` list if it can change an offline run.
- Choose models through the helpers, never directly:
  - the target: `lesson_model(scripted)` (or `agent_model(steps)` for agents);
  - a judge or attacker: `role_model("judge" | "attacker", scripted)`, which
    also says whether it is scripted.
- Assert planted results only while the thing you measure is scripted:
  `if offline(): ...` for the target, the flag `role_model` returns for a
  role. With a real model, report rates and IDs; never compare its replies
  with labels written for the scripted replies (ADR 0006).
- When the subject is an evaluator, swap only the evaluator. Keep the answers
  scripted so the gold labels still apply.
- End with one `OK:` line saying what was caught or measured. Use
  `_shared.skip(reason)` for a missing flag, server, or key.

## Before committing

- `make check-all` passes, and the lesson runs offline in a few seconds.
- Run it once with `--local` (and any role variable it uses) and read the
  replies in `uv run inspect view --log-dir out/inspect-logs`, not only the
  `OK:` line.
- If the real model exposed a bug in a check, fix it and **plant that case in
  the fixture**, so the scripted run keeps catching it.
- Add the lesson to `make local` if it accepts `--local` (the Makefile's
  `LOCAL` pattern), record it in `CHANGELOG.md` under `[Unreleased]`, and
  write an ADR if it introduces a decision more than one lesson will follow.
