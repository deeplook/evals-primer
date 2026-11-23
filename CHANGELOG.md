# Changelog

## [Unreleased]

### Added
- Lessons 01–04 on one shared question set: `01_exact_match.py` scores
  recorded answers by hand, `02_scripted_model.py` runs the same scorers as an
  Inspect task on `mockllm/model`, `03_local_model.py` targets Ollama or
  llama-server with `--local`, and `04_live_api.py` a hosted model with
  `--live`. Two wrong answers and one formatting difference are planted; 01
  and 02 fail unless each scorer flags exactly the expected samples.
- Lessons 05–09: contamination (public set against a rewritten twin, and a
  canary), span-level hallucination (source against trace grounding), a
  toxicity classifier measured against hand labels, PII leak detectors, and
  under- and over-refusal with a refusal detector that handles typographic
  apostrophes.
- Lessons 10–12: bias (single swaps, combined attributes, pressure notes),
  an LLM judge via `model_graded_qa` measured against gold labels, and
  pairwise judge reliability with AB/BA position flips and Cohen's kappa.
- Lessons 13–18: direct injection, indirect injection in an SDK agent loop,
  jailbreaks scored on executed tool calls, a multi-turn crescendo attack,
  end-state grading with pass@k and pass^k plus scaffold cost, and an SDK
  guardrail ablation. `examples/_agent.py` runs the agent inside an Inspect
  solver. `make redteam` runs a narrow garak scan via `uvx`.
- Lessons 19–21: long-context dispersion with same-length haystacks,
  region-aware multilingual checks scored with aliases, and a CI gate with
  Wilson intervals that writes `out/scores.json`. `make gate` runs in CI.
- Lesson 18 measures guardrails off, static, and with a stateful message
  budget against two adaptive attacks (reworded, split) as well as the fixed
  ones, including split calls sent in parallel in one turn and a model that
  retries a rejected tool until `max_turns`. Lesson 16 reads garak reports through `examples/_garak.py`, and
  lesson 21 can gate on them with `--garak-report` (`make redteam-gate`).
- Lesson 22: an attacker model rewrites its attack each round from the
  target's replies, within a round budget, against benign marker goals. It is
  primed with a catalogue of injection styles and reports which style won.
- Judge and attacker model roles (`EVALS_JUDGE_MODEL`, `EVALS_ATTACKER_MODEL`,
  ADR 0009), separate from the target. Lesson 07 measures a model classifier
  next to the word list; lessons 11 and 12 take their judge from the role.
- `.env.example`: settings can live in a gitignored `.env`, loaded by the
  lessons and the Makefile; the shell still takes precedence, and the tests
  ignore it.
- README sections on running lessons, how a lesson works, the repository
  layout, and environment variables; lessons grouped with reading paths; and
  `docs/adding-a-lesson.md`, a checklist for new lessons.
- README "Not covered" and a further-reading list of papers checked against
  their sources on 2026-11-23.
- Offline test harness, Makefile, CI, and the first architecture decision
  records under `docs/adr/`.
