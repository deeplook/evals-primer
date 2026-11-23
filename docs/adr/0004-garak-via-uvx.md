# ADR 0004: Run garak through uvx, not as a dependency

- Status: Accepted
- Date: 2026-11-23

## Context

Lesson 16 ends with a narrow garak scan. garak has a large dependency tree and
is only useful against a running model.

## Decision

Do not add garak to `pyproject.toml`. `make redteam` runs `uvx garak` against a
local OpenAI-compatible endpoint. The offline path of lesson 16 covers the
scripted multi-turn attack and prints `SKIP:` for the scan.

## Consequences

`uv.lock` stays small and CI never installs garak. The garak version is not
locked with the project; the Makefile pins it (`GARAK_VERSION := 0.17.1`).

`make redteam` targets Ollama (`--target_type ollama`, model from
`EVALS_LOCAL_MODEL`) with `GARAK_SPEC`, by default
`probes.promptinject.HijackHateHumans`: 256 prompts, about three minutes
against `llama3.2` on a Mac mini. The first `uvx` run downloads several
hundred MB, including torch. Reports go to `out/garak/` through a generated
config file. garak always writes its own log to `~/.local/share/garak/`, the
one generated file outside the repo; the README says so.

`examples/_garak.py` reads the report's `eval` lines (`fails` are hits,
`total_evaluated` the attempts) into attack-success rates per probe. Lesson
16 parses a hand-written sample report offline and the newest real report
with `--garak`. Lesson 21 adds a garak threshold to its gate only when given
`--garak-report`, so the offline gate never depends on a local scan.
