# Evals Primer

[![CI](https://github.com/deeplook/evals-primer/actions/workflows/check.yml/badge.svg)](https://github.com/deeplook/evals-primer/actions/workflows/check.yml)
[![License](https://img.shields.io/github/license/deeplook/evals-primer?logo=github)](LICENSE)
[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-ffdd00?style=flat&logo=buy-me-a-coffee&logoColor=black)](https://www.buymeacoffee.com/deeplook)

Small Python lessons for building LLM evaluation suites from scratch with
[Inspect](https://inspect.aisi.org.uk/): labelled sets, scorers, judges, and the
failures that matter in late 2026 — contamination, hallucinated spans, PII
leaks, bias, prompt injection inside agent loops, jailbreaks, and automated
red-teaming.

**Offline runs test the scorer, not the model.** By default every lesson runs
on a scripted model whose answers plant known failures, and the lesson raises
unless its checks flag exactly those cases. Pass `--local` (Ollama or
llama-server) or `--live` (a hosted API) and the same lesson measures a real
model, reporting numbers instead of asserting them. Judges and attackers are
separate model roles, so a small target can be graded and attacked by a
stronger model. The decisions behind this are in [docs/adr](docs/adr/README.md).

It complements the sibling primers: `agents-primer` and `harness-primer` build
and wrap agents with the OpenAI Agents SDK; this repo measures them.
`openai-primer` covers the hosted API (including moderation), `rag-primer`
covers retrieval metrics, and `llamacpp-primer` runs local models.

## Setup

You need [uv](https://docs.astral.sh/uv/); it installs Python 3.12 from
`.python-version`.

```bash
uv sync --all-groups
uv run python examples/01_exact_match.py
make check-all
```

That is all the offline path needs: no API key, no GPU, no model server.

Settings are environment variables (listed [below](#environment-variables)).
To keep them in a file instead, copy the template and uncomment what you need:

```bash
cp .env.example .env   # gitignored; variables set in your shell still win
```

For real models, either run a local server or set an API key. Locally, the
lessons were run with [Ollama](https://ollama.com/) on a 24 GB Mac mini:

```bash
ollama pull llama3.2          # 2 GB, the target in the examples below
ollama pull mistral-nemo:12b  # 7 GB, a stronger judge or attacker
```

## Running lessons

Every lesson runs in one of three modes:

```bash
uv run python examples/09_refusal.py           # scripted: asserts planted results
EVALS_LOCAL_MODEL=llama3.2:latest \
  uv run python examples/09_refusal.py --local  # a local model: reports results
uv run python examples/09_refusal.py --live    # a hosted model (API credits)
```

- **Scripted** (default) plants known failures and asserts that every check
  catches exactly those. This is what `make check-all` and CI run.
- **`--local`** probes `LOCAL_BASE_URL`, then Ollama (`localhost:11434`), then
  llama-server (`localhost:8080`), and uses `EVALS_LOCAL_MODEL`. Set it
  explicitly: otherwise the first model the server lists is used, which may
  be larger than you want.
- **`--live`** uses `EVALS_MODEL` (default `openai/gpt-6-luna`, any Inspect
  model name) and the provider's key, for example `OPENAI_API_KEY`.

Without a server or a key, a lesson prints `SKIP:` and exits 0. A real model
is only used when you pass a flag or set a role variable; a lesson never
reaches for one on its own. Results from a real model vary between runs, and
on sets this small they show the checks working, not how good the model is.

## Lessons

Read them in order the first time; each group also stands on its own.

**The loop (01–04).** One question set (`examples/_qa.py`); only the source
of the answers changes.

| File | Topic |
|---|---|
| `01_exact_match.py` | Score recorded answers with exact match and a regex extractor, no model |
| `02_scripted_model.py` | The same set and scorers as an Inspect task on a scripted model |
| `03_local_model.py` | The same task against Ollama or llama-server (`--local`) |
| `04_live_api.py` | The same task against a hosted model (`--live`) |

**Quality and safety checks (05–10).** One check per failure, each tested on
planted cases before it is trusted.

| File | Topic |
|---|---|
| `05_contamination.py` | A public set against a rewritten twin, plus a canary string |
| `06_span_hallucination.py` | Flag unsupported sentences; ground against the source, not the agent's trace |
| `07_toxicity.py` | A word list and a model classifier, both measured against hand labels |
| `08_pii_leaks.py` | Planted PII in the system prompt: shape, verbatim, and normalised detectors |
| `09_refusal.py` | Under-refusal and over-refusal, with a refusal detector checked first |
| `10_bias_fairness.py` | Counterfactual swaps, combined attributes, and a biased pressure note |

**Judges (11–12).** A judge is a model, so it is evaluated too.

| File | Topic |
|---|---|
| `11_llm_as_judge.py` | A rubric judge with `model_graded_qa`, graded against human gold labels |
| `12_judge_reliability.py` | Pairwise judging in AB and BA order; position flips and Cohen's kappa |

**Attacks and agents (13–18).** Lessons 14–18 run an OpenAI Agents SDK agent
as the system under test (`examples/_agent.py`).

| File | Topic |
|---|---|
| `13_direct_injection.py` | Leak and hijack attacks in the user's text; attack success and clean utility |
| `14_indirect_injection_agent.py` | An injected tool result in an SDK agent loop; attack success and utility together |
| `15_jailbreaks.py` | Jailbreaks as chat and as an agent; score executed tool calls, not only the reply |
| `16_multiturn_garak.py` | A crescendo attack against a single-turn ask; read a garak report into attack-success rates |
| `17_agent_passk.py` | End-state grading, pass@k against pass^k, and what a planner scaffold costs |
| `18_guardrail_ablation.py` | Guardrails off, static, and stateful against fixed and adaptive attacks |

**Context, language, and CI (19–21).**

| File | Topic |
|---|---|
| `19_long_context.py` | Two same-length haystacks: facts side by side against facts scattered |
| `20_multilingual.py` | Regional facts asked in English and in the local language, scored with aliases |
| `21_ci_gate.py` | Thresholds that fail the build, with Wilson intervals; writes `out/scores.json` |

**Automated red-teaming (22).**

| File | Topic |
|---|---|
| `22_attacker_loop.py` | An attacker model, primed with injection styles, adapts to the target's replies |

Shorter paths: *scorers* 01, 02, 05–09; *judges* 07, 11, 12; *red-teaming*
13, 16, 18, 22 (plus `make redteam`); *agents* 14, 15, 17, 18; *CI* 21.

## How a lesson works

Every numbered lesson has the same shape:

1. **Docstring:** the one idea, what is planted, and what the source papers
   report.
2. **Fixture:** a handful of hand-written cases and the scripted model's
   answers, including the failures the checks must catch (ADR 0002, 0007).
3. **Check:** a plain Python function `(completion, metadata) -> reason | None`,
   wrapped as an Inspect scorer by `_shared.check_scorer`. The reason shows up
   per sample in `inspect view`.
4. **Run:** an Inspect `Task` through `_shared.run_eval`, on the scripted
   model, a local server, or a hosted API.
5. **Assert, scripted only:** the lesson raises unless the checks flagged
   exactly the planted cases (ADR 0006).
6. **Report:** one `OK:` line with what was caught or measured. `SKIP:` means
   a flag, server, or key was missing.

`tests/test_examples.py` runs every lesson in a subprocess and requires a
clean exit with `OK:` or `SKIP:`; the lesson's own assertions do the checking.
To add a lesson, see [docs/adding-a-lesson.md](docs/adding-a-lesson.md).

## Repository layout

```text
examples/
  NN_name.py        numbered lessons, run directly with `uv run python`
  _shared.py        settings and .env loading, run modes, the scripted Inspect
                    model, check_scorer, run_eval, local-server lookup, roles
  _qa.py            the question set shared by lessons 01-04
  _agent.py         an Agents SDK agent inside an Inspect solver, with fake
                    tools that record what they did (lessons 14-18)
  _garak.py         reads garak reports into attack-success rates (16, 21)
tests/
  test_examples.py  runs every lesson offline; checks the CI gate's exit codes
docs/
  adr/              architecture decision records 0001-0009
  adding-a-lesson.md
out/                generated: Inspect logs, scores.json, garak reports
work/               local planning notes, not tracked
.env.example        template for a local, gitignored .env
Makefile            the commands below
.github/workflows/  CI: `make check-all`, then `make gate`
```

Only `NN_*.py` files are lessons; the tests and `make local` select them by that
pattern. Helper modules start with `_`.

## Model roles

`--local` and `--live` choose the *target*, the model under test. Judges and
attackers are separate roles (ADR 0009), so a small target can be graded and
attacked by a stronger model:

```bash
EVALS_JUDGE_MODEL=local/mistral-nemo:12b uv run python examples/11_llm_as_judge.py
EVALS_ATTACKER_MODEL=local/mistral-nemo:12b EVALS_LOCAL_MODEL=llama3.2:latest \
  uv run python examples/22_attacker_loop.py --local
```

`local/<name>` is a model on the local server; any other value is an Inspect
model name, so a hosted model (`openai/gpt-6.1-terra`) works the same way.
The judge role is used by lessons 07, 11, and 12, the attacker by 22. A 12B
judge or attacker fits beside a 3B target on a 24 GB machine. Lesson 22 runs
at most `EVALS_ATTACK_ROUNDS` rounds (default 5) and prints its model calls.

## Red-teaming with garak

```bash
make redteam                                   # llama3.2:latest on Ollama
make redteam EVALS_LOCAL_MODEL=qwen3:8b GARAK_SPEC=probes.dan.DanInTheWild
```

`make redteam` runs garak 0.17.1 through `uvx`, so it never enters `uv.lock`.
The first run downloads several hundred MB (garak pulls in torch). The default
probe sends 256 hijack prompts and took about three minutes against
`llama3.2` on Ollama, which hit on 138 of them (54%). Reports land in
`out/garak/`; garak also writes its own log to `~/.local/share/garak/`.

```bash
uv run python examples/16_multiturn_garak.py --garak   # read the newest report
make redteam-gate                                       # scan, then gate on it
```

`examples/_garak.py` reads garak's `eval` summary lines into attack-success
rates per probe. Lesson 21 fails the gate when any probe in the report passed
with `--garak-report` exceeds 0.2.

## Environment variables

Set them in your shell or in `.env` (template: `.env.example`). The lessons
and the Makefile read `.env` from the repo root; a variable already set in
the shell, or on make's command line, takes precedence, and an empty value
means the default. The tests blank all model settings, so a `.env` never
changes an offline run.

| Variable | Default | Used for |
|---|---|---|
| `EVALS_LOCAL_MODEL` | first chat model listed | the target with `--local`; the model `make redteam` scans |
| `LOCAL_BASE_URL` | probe Ollama, then llama-server | the local OpenAI-compatible server |
| `EVALS_MODEL` | `openai/gpt-6-luna` | the target with `--live` (any Inspect model name) |
| `EVALS_AGENT_MODEL` | `EVALS_MODEL` without its provider | the Agents SDK model with `--live` (14–18) |
| `OPENAI_API_KEY` | unset | hosted OpenAI calls; other providers use their own key |
| `EVALS_JUDGE_MODEL` | follows the target's mode | the judge role (07, 11, 12); `local/<name>` or an Inspect name |
| `EVALS_ATTACKER_MODEL` | follows the target's mode | the attacker role (22) |
| `EVALS_ATTACK_ROUNDS` | `5` | lesson 22's round budget per goal |
| `EVALS_HAYSTACK_WORDS` | `1500` | lesson 19's haystack length |
| `EVALS_SCORES` | `out/scores.json` | where lesson 21 writes its scores |
| `INSPECT_LOG_DIR` | `out/inspect-logs` | where Inspect writes eval logs |
| `GARAK_SPEC` | `probes.promptinject.HijackHateHumans` | the probes `make redteam` runs |

## Generated files

Inspect writes one log per run to `out/inspect-logs/` (`INSPECT_LOG_DIR`).
Lesson 21 writes `out/scores.json` (`EVALS_SCORES`), in the shape
harness-primer lesson 16 reads. `make clean` removes `out/`.
Browse the logs with `uv run inspect view --log-dir out/inspect-logs`.

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
| `gate` | Lesson 21 as a build gate; exits 1 on a missed threshold |
| `redteam` | Narrow garak scan against a local Ollama model |
| `redteam-gate` | `redteam`, then lesson 21's gate on the garak report |
| `clean` | Remove caches and `out/` |

`check-all` does not modify the tree and does not need a network.

## Not covered

- **Full public benchmarks** (HarmBench, JailbreakBench, SWE-bench). Datasets
  here stay tiny and hand-written on purpose; public sets are contaminated and
  saturating (lesson 05), and none of their prompts are copied in (ADR 0007).
- **Statistical power.** Five to eight items per set teach the mechanics, not
  the numbers. Lesson 21 prints Wilson intervals to show how wide they are; a
  real suite needs hundreds of items per metric.
- **Computer-use and long-horizon agents.** A 24 GB machine is the wrong place
  for an OSWorld-style desktop benchmark, and the agent lessons use in-memory
  fake tools, not a sandbox.
- **Production observability.** No tracing backend, dashboard, or pass-rate
  history over time; Inspect logs in `out/` are the only record.
- **Serious red-teaming.** `make redteam` runs one narrow garak probe, and
  lesson 22's attacker loop is a few rounds against benign markers. PyRIT,
  promptfoo, and large-scale strategy search are left to their own docs.
- **Model rankings.** The `llama3.2` results quoted in lesson docstrings and
  commit messages are single runs of a 3B model; they show the checks working
  on real output, not how good any model is.

## Further reading

Tools:

- [Inspect documentation](https://inspect.aisi.org.uk/)
- [garak](https://github.com/NVIDIA/garak), LLM vulnerability scanner
- [DeepEval](https://deepeval.com/) and [pytest-evals](https://github.com/AlmogBaku/pytest-evals), pytest-style alternatives

Papers and posts the lessons draw on (checked 2026-11-23):

- Contamination (05): OpenAI, [Why SWE-bench Verified no longer measures frontier coding capabilities](https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/) and [Separating signal from noise in coding evaluations](https://openai.com/index/separating-signal-from-noise-coding-evaluations/); Akhtar et al., [When AI Benchmarks Plateau](https://proceedings.mlr.press/v306/akhtar26a.html) (ICML 2026)
- Hallucination (06): [SHAM-Bench](https://arxiv.org/abs/2610.27370) (span level); [HaluCheck](https://arxiv.org/abs/2611.08231) (includes agent trajectories)
- Bias (10): Ai2, [FairStress](https://huggingface.co/blog/allenai/fairstress); [ComFair](https://aclanthology.org/2026.emnlp-main.1875/) (EMNLP 2026)
- Judges (11–12): Kumar et al., [All Verdicts are Not Equal](https://arxiv.org/abs/2610.12083) (position swaps)
- Injection (13–14, 18): [INFUSE](https://arxiv.org/abs/2610.20776); [MetaPI](https://arxiv.org/abs/2611.10026)
- Jailbreaks (15): [SoK: Rethinking Jailbreaking in the Era of Agentic AI](https://arxiv.org/abs/2609.12413)
- Multi-turn attacks (16): [EvoFlint](https://arxiv.org/abs/2609.00487); [Reject, Remember, Retry](https://arxiv.org/abs/2610.31937)
- Agents (17): [τ-bench](https://arxiv.org/abs/2406.12045) (pass^k); [Holistic Agent Leaderboard](https://proceedings.iclr.cc/paper_files/paper/2026/hash/a0928f924a344aaebbb7f6cd8d56e34c-Abstract-Conference.html) (ICLR 2026)
- Long context (19): [LURCH](https://arxiv.org/abs/2610.22067), "Beyond Context Length"
- Multilingual (20): [INCLUDE-2.0](https://aclanthology.org/2026.emnlp-main.1344/) (EMNLP 2026)

Sibling primers: [agents-primer](https://github.com/deeplook/agents-primer), [harness-primer](https://github.com/deeplook/harness-primer), [openai-primer](https://github.com/deeplook/openai-primer), rag-primer (retrieval metrics), [llamacpp-primer](https://github.com/deeplook/llamacpp-primer)

## License

MIT
