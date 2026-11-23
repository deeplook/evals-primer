# ADR 0005: Script-only primer layout and local endpoints

- Status: Accepted
- Date: 2026-11-23

## Context

`uv init --package` produced a `src/` package, a build backend, and a console
script. Readers run numbered scripts; nothing is installed from an index.

## Decision

Follow `primer-standards`: `[tool.uv] package = false`, no `[build-system]`,
numbered lessons under `examples/`, offline tests under `tests/`, generated
output under `out/`. Local models are reached only through OpenAI-compatible
endpoints (Ollama, llama-server) whose URLs come from the environment; a
lesson that finds no server prints `SKIP:`. Without `EVALS_LOCAL_MODEL`, the
first chat model the server lists is used. That can be a larger model than
intended, so the README recommends setting `EVALS_LOCAL_MODEL`.

Settings are environment variables, optionally kept in a gitignored `.env`
at the repo root; `.env.example` is the committed template. `_shared.py`
loads that `.env` at import without overriding the shell, and reads every
setting through `setting()`, where an empty value means the default. Inspect
loads a `.env` as well, but only when an eval starts and searching up the
directory tree; loading ours first keeps our code and Inspect consistent.
The Makefile reads the few settings it needs from `.env` with the same
precedence. The tests blank every model setting, so a developer's `.env`
cannot change an offline run.

## Consequences

`make check-all` needs no network, keys, GPUs, or model servers. Lessons that
want a local model are grouped under `make local`; lessons with paid calls are
grouped under `make live-core`.
