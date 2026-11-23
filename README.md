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
model the server lists. Set `EVALS_LOCAL_MODEL` explicitly: the first listed
model may be larger than you want. With no server it prints `SKIP:`.

## Modules

| File | Topic |
|---|---|
| `01_exact_match.py` | Score recorded answers with exact match and a regex extractor, no model |
| `02_scripted_model.py` | The same set and scorers as an Inspect task on a scripted model |
| `03_local_model.py` | The same task against Ollama or llama-server (`--local`) |
| `04_live_api.py` | The same task against a hosted model (`--live`) |
| `05_contamination.py` | A public set against a rewritten twin, plus a canary string |
| `06_span_hallucination.py` | Flag unsupported sentences; ground against the source, not the agent's trace |
| `07_toxicity.py` | Measure a word-list toxicity classifier against hand labels |
| `08_pii_leaks.py` | Planted PII in the system prompt: shape, verbatim, and normalised detectors |
| `09_refusal.py` | Under-refusal and over-refusal, with a refusal detector checked first |
| `10_bias_fairness.py` | Counterfactual swaps, combined attributes, and a biased pressure note |
| `11_llm_as_judge.py` | A rubric judge with `model_graded_qa`, graded against human gold labels |
| `12_judge_reliability.py` | Pairwise judging in AB and BA order; position flips and Cohen's kappa |
| `13_direct_injection.py` | Leak and hijack attacks in the user's text; attack success and clean utility |
| `14_indirect_injection_agent.py` | An injected tool result in an SDK agent loop; attack success and utility together |
| `15_jailbreaks.py` | Jailbreaks as chat and as an agent; score executed tool calls, not only the reply |
| `16_multiturn_garak.py` | A crescendo attack against a single-turn ask; `make redteam` runs a narrow garak scan |
| `17_agent_passk.py` | End-state grading, pass@k against pass^k, and what a planner scaffold costs |
| `18_guardrail_ablation.py` | SDK tool-input and input guardrails off and on: attack success and utility |

Lessons 01–04 share one question set (`examples/_qa.py`) and change only where
the answers come from. From lesson 05 on, each lesson writes a small Python
check, wraps it as an Inspect scorer (`_shared.check_scorer`), and plants the
cases it must catch. Lessons 05, 06, and 08–18 also accept `--local` and
`--live`; they then report what they find instead of asserting it. In 11 and
12 only the judge changes; the answers and human labels stay fixed, so the
judge is still measured against gold.

Lessons 14–18 run an OpenAI Agents SDK agent as the system under test inside
an Inspect solver (`examples/_agent.py`). Offline, the SDK's `ScriptedModel`
plays planted tool calls and the SDK executes the tools and guardrails; the
tools are in-memory fakes that record what they did, and the scorers read that
ledger rather than the transcript.

Lessons 19–21 are planned: long context, multilingual checks, and a CI gate.

## Red-teaming with garak

```bash
make redteam                                   # llama3.2:latest on Ollama
make redteam EVALS_LOCAL_MODEL=qwen3:8b GARAK_SPEC=probes.dan.DanInTheWild
```

`make redteam` runs garak 0.17.1 through `uvx`, so it never enters `uv.lock`.
The first run downloads several hundred MB (garak pulls in torch). The default
probe sends 256 hijack prompts and took about three minutes against
`llama3.2` on Ollama. Reports land in `out/garak/`; garak also writes its own
log to `~/.local/share/garak/`.

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
| `redteam` | Narrow garak scan against a local Ollama model |
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
