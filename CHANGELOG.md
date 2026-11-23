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
- Offline test harness, Makefile, CI, and the first architecture decision
  records under `docs/adr/`.
