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
lesson that finds no server prints `SKIP:`.

## Consequences

`make check-all` needs no network, keys, GPUs, or model servers. Lessons that
want a local model are grouped under `make local`; lessons with paid calls are
grouped under `make live-core`.
