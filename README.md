# Evals Primer

[![CI](https://github.com/deeplook/evals-primer/actions/workflows/check.yml/badge.svg)](https://github.com/deeplook/evals-primer/actions/workflows/check.yml)
[![License](https://img.shields.io/github/license/deeplook/evals-primer?logo=github)](LICENSE)
[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-ffdd00?style=flat&logo=buy-me-a-coffee&logoColor=black)](https://www.buymeacoffee.com/deeplook)

Small Python lessons for building LLM evaluation suites from scratch with
[Inspect](https://inspect.aisi.org.uk/): labelled sets, scorers, judges, and the
failures that matter in late 2026 — contamination, hallucinated spans, PII
leaks, bias, prompt injection inside agent loops, and jailbreaks.

**Offline runs test the scorer, not the model.** The default path uses
Inspect's scripted `mockllm/model`. Every fixture plants known failures, and
each lesson raises unless its scorers flag exactly those cases. `--live` runs
the same task against a real model, and the lesson reports numbers instead of
asserting them. See [docs/adr](docs/adr/README.md) for the decisions behind
this.

It complements the sibling primers: `agents-primer` and `harness-primer` build
and wrap agents with the OpenAI Agents SDK; this repo measures them.
`openai-primer` covers the hosted API (including moderation), `rag-primer`
covers retrieval metrics, and `llamacpp-primer` runs local models.

## Setup

```bash
uv sync --all-groups
uv run python examples/01_exact_match.py
make check-all
```

Python 3.12. Offline runs need no API key, no GPU, and no model server.

```bash
export OPENAI_API_KEY="..."
export EVALS_MODEL=openai/gpt-6-luna   # any Inspect model name
uv run python examples/04_live_api.py --live
```

`--live` uses API credits. Without a key it prints `SKIP:` and exits 0.

```bash
uv run python examples/03_local_model.py --local   # Ollama or llama-server
LOCAL_BASE_URL=http://localhost:8080/v1 EVALS_LOCAL_MODEL=my-model \
  uv run python examples/03_local_model.py --local
```

`--local` probes `LOCAL_BASE_URL`, then Ollama (`localhost:11434`), then
llama-server (`localhost:8080`), and uses `EVALS_LOCAL_MODEL` or the first chat
model the server lists. With no server it prints `SKIP:`.

## Modules

| File | Topic |
|---|---|
| `01_exact_match.py` | Score recorded answers with exact match and a regex extractor, no model |
| `02_scripted_model.py` | The same set and scorers as an Inspect task on a scripted model |
| `03_local_model.py` | The same task against Ollama or llama-server (`--local`) |
| `04_live_api.py` | The same task against a hosted model (`--live`) |

Lessons 01–04 share one question set (`examples/_qa.py`) and change only where
the answers come from. Lessons 05–21 are planned: contamination,
hallucination, toxicity, PII, refusal, bias, LLM judges and their reliability,
direct and indirect injection, jailbreaks, multi-turn red-teaming with garak,
agent pass^k, guardrail ablation, long context, multilingual checks, and a CI
gate.

## Generated files

Inspect writes one log per run to `out/inspect-logs/` (`INSPECT_LOG_DIR`).
`make clean` removes `out/`. Browse logs with `uv run inspect view --log-dir
out/inspect-logs`.

## Commands

| Target | Purpose |
|---|---|
| `help` | List targets |
| `install` | `uv sync --all-groups` |
| `run` | Run one example (`EXAMPLE=examples/01_exact_match.py`) |
| `format` | Apply Ruff |
| `lint` | Check format and lint |
| `typecheck` | Strict mypy |
| `test` | Offline pytest over every lesson |
| `check-all` | `lint`, then `typecheck`, then `test` |
| `live-core` | Hosted-API lessons with `--live` (uses API credits) |
| `local` | Lessons that can use Ollama or llama-server |
| `clean` | Remove caches and `out/` |

`check-all` does not modify the tree and does not need a network.

## Not covered

Full public benchmarks (HarmBench, JailbreakBench, SWE-bench), leaderboards,
hosted observability products, and computer-use evals. Datasets here stay tiny
and hand-written on purpose: public benches are contaminated and saturating.

## Further reading

- [Inspect documentation](https://inspect.aisi.org.uk/)
- [garak](https://github.com/NVIDIA/garak), LLM vulnerability scanner
- [DeepEval](https://deepeval.com/) and [pytest-evals](https://github.com/AlmogBaku/pytest-evals), pytest-style alternatives
- Sibling primers: [agents-primer](https://github.com/deeplook/agents-primer), [harness-primer](https://github.com/deeplook/harness-primer), [openai-primer](https://github.com/deeplook/openai-primer), [llamacpp-primer](https://github.com/deeplook/llamacpp-primer)

## License

MIT
