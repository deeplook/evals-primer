# Changelog

## [Unreleased]

### Added
- Lessons 01–04 on one shared question set: `01_exact_match.py` scores
  recorded answers by hand, `02_scripted_model.py` runs the same scorers as an
  Inspect task on `mockllm/model`, `03_local_model.py` targets Ollama or
  llama-server with `--local`, and `04_live_api.py` a hosted model with
  `--live`. Two wrong answers and one formatting difference are planted; 01
  and 02 fail unless each scorer flags exactly the expected samples.
- Offline test harness, Makefile, CI, and the first architecture decision
  records under `docs/adr/`.
