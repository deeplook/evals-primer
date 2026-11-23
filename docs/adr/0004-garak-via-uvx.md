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
locked with the project; the Makefile target pins it explicitly.
