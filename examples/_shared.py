"""Shared helpers: mode flags, the scripted Inspect model, and one eval runner.

Offline lessons use Inspect's own `mockllm/model` with a fixture table that maps
each prompt to a planted output. The Inspect pipeline (dataset, solver, scorer,
log) still runs; only the model is scripted. `--local` reaches an
OpenAI-compatible server on this machine; `--live` reaches a hosted API.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any, NoReturn

from dotenv import load_dotenv
from inspect_ai import Task
from inspect_ai import eval as inspect_eval
from inspect_ai.log import EvalLog
from inspect_ai.model import (
    ChatMessage,
    GenerateConfig,
    Model,
    ModelOutput,
    get_model,
)
from inspect_ai.scorer import (
    CORRECT,
    INCORRECT,
    Score,
    Scorer,
    Target,
    accuracy,
    scorer,
)
from inspect_ai.solver import TaskState
from inspect_ai.tool import ToolChoice, ToolInfo

ROOT = Path(__file__).resolve().parents[1]

# Settings come from the environment, optionally from this repo's `.env`
# (copy `.env.example`). Variables already set in the shell win. Inspect loads
# a `.env` too, but only when an eval starts and searching up the directory
# tree; loading this one first makes our code and Inspect see the same values.
load_dotenv(ROOT / ".env", override=False)


def setting(name: str, default: str) -> str:
    """An environment setting; unset or empty means the default."""
    return os.environ.get(name) or default


# Keep Inspect's generated logs under out/, which `make clean` removes.
LOG_DIR = Path(setting("INSPECT_LOG_DIR", str(ROOT / "out" / "inspect-logs")))
LIVE_MODEL = setting("EVALS_MODEL", "openai/gpt-6-luna")
# Probed in order when LOCAL_BASE_URL is unset: Ollama, then llama-server.
LOCAL_CANDIDATES = ["http://localhost:11434/v1", "http://localhost:8080/v1"]


def live() -> bool:
    return "--live" in sys.argv


def local() -> bool:
    return "--local" in sys.argv


def offline() -> bool:
    """True on the default scripted path, where planted results are asserted."""
    return not (live() or local())


def skip(reason: str) -> NoReturn:
    """Print a SKIP: line and exit 0, so the offline test path stays green."""
    print(f"SKIP: {reason}")
    raise SystemExit(0)


def scripted_model(
    outputs: Mapping[str, str], key: Callable[[str], str] = lambda prompt: prompt
) -> Model:
    """An Inspect mock model that answers each prompt from a fixture table.

    Keyed by prompt, not call order, because Inspect may run samples
    concurrently. The prompt is every user turn joined by newlines, so a
    multi-turn conversation has its own key. `key` extracts the lookup key from
    a longer prompt, for example the submission inside a judge's grading
    template.
    """

    def respond(
        messages: list[ChatMessage],
        tools: list[ToolInfo],
        tool_choice: ToolChoice,
        config: GenerateConfig,
    ) -> ModelOutput:
        prompt = key("\n".join(m.text for m in messages if m.role == "user"))
        if prompt not in outputs:
            raise KeyError(f"no scripted output for prompt: {prompt!r}")
        return ModelOutput.from_content(model="mockllm", content=outputs[prompt])

    return get_model("mockllm/model", custom_outputs=respond)


def live_model() -> str:
    """The hosted model name for `--live`; SKIP when its OpenAI key is missing.

    Other providers' keys (for `EVALS_MODEL=anthropic/...` and so on) are
    checked by Inspect itself when the model is first called.
    """
    if LIVE_MODEL.startswith("openai/") and not os.environ.get("OPENAI_API_KEY"):
        skip(f"--live with {LIVE_MODEL} needs OPENAI_API_KEY")
    return LIVE_MODEL


def _list_models(base_url: str) -> list[str] | None:
    try:
        with urllib.request.urlopen(f"{base_url}/models", timeout=2) as response:
            payload = json.load(response)
    except (OSError, urllib.error.URLError, ValueError):
        return None
    return [str(entry["id"]) for entry in payload.get("data", [])]


def find_local_server(wanted: str | None = None) -> tuple[str, str]:
    """(base URL, model name) of a local OpenAI-compatible server; SKIP if none."""
    configured = os.environ.get("LOCAL_BASE_URL")
    for base_url in [configured] if configured else LOCAL_CANDIDATES:
        names = _list_models(base_url)
        if names is None:
            continue
        chat = [name for name in names if "embed" not in name]
        name = wanted or (chat[0] if chat else None)
        if name is None:
            skip(f"{base_url} lists no chat model")
        if wanted and wanted not in names:
            skip(f"{base_url} does not list {wanted}")
        return base_url, name
    skip("no local OpenAI-compatible server found")


def local_endpoint() -> tuple[str, str]:
    """The target model's local server for `--local`; SKIP if none."""
    if not local():
        skip("pass --local to use Ollama or llama-server")
    return find_local_server(os.environ.get("EVALS_LOCAL_MODEL"))


def local_model() -> Model:
    """A model on a local OpenAI-compatible server for `--local`; SKIP if none."""
    base_url, name = local_endpoint()
    return get_model(f"openai-api/local/{name}", base_url=base_url, api_key="local")


def lesson_model(
    outputs: Mapping[str, str], key: Callable[[str], str] = lambda prompt: prompt
) -> Model | str:
    """Scripted by default, a local server with `--local`, a hosted API with `--live`."""
    if live():
        return live_model()
    if local():
        return local_model()
    return scripted_model(outputs, key)


# A check returns None when the sample passes, or a short reason when it fails.
Check = Callable[[str, dict[str, Any]], str | None]


def check_scorer(name: str, check: Check) -> Scorer:
    """Wrap a plain Python check as a named Inspect scorer.

    The check sees the model's completion and the sample's metadata. Its reason
    becomes the score's explanation, which `inspect view` shows per sample.
    """

    @scorer(metrics=[accuracy()], name=name)
    def factory() -> Scorer:
        async def score(state: TaskState, target: Target) -> Score:
            completion = state.output.completion
            reason = check(completion, state.metadata)
            return Score(
                value=CORRECT if reason is None else INCORRECT,
                answer=completion,
                explanation=reason,
            )

        return score

    return factory()


# Roles other than the target: who grades, and who attacks (ADR 0009).
ROLE_VARIABLES = {"judge": "EVALS_JUDGE_MODEL", "attacker": "EVALS_ATTACKER_MODEL"}


def role_model(
    role: str,
    outputs: Mapping[str, str],
    key: Callable[[str], str] = lambda prompt: prompt,
) -> tuple[Model, bool]:
    """The model for a judge or attacker role, and whether it is scripted.

    `EVALS_JUDGE_MODEL` / `EVALS_ATTACKER_MODEL` choose it: `local/<name>` is a
    model on the local server, anything else an Inspect model name (for
    example `openai/gpt-6.1-terra`). Unset, the role follows `--local` and
    `--live` like the target, and is otherwise scripted.
    """
    name = os.environ.get(ROLE_VARIABLES[role], "")
    if name.startswith("local/"):
        base_url, model = find_local_server(name.removeprefix("local/"))
        return get_model(
            f"openai-api/local/{model}", base_url=base_url, api_key="local"
        ), False
    if name:
        return get_model(name), False
    chosen = lesson_model(outputs, key)
    return (get_model(chosen) if isinstance(chosen, str) else chosen), offline()


def run_eval(task: Task, model: Model | str) -> EvalLog:
    """Run one task quietly and return its log; raise if the run itself failed."""
    [log] = inspect_eval(task, model=model, display="none", log_dir=str(LOG_DIR))
    if log.status != "success":
        raise RuntimeError(f"eval {log.eval.task} ended with status {log.status}")
    return log


def failed_ids(log: EvalLog, scorer: str) -> set[str]:
    """IDs of samples the named scorer marked incorrect."""
    return {
        str(sample.id)
        for sample in log.samples or []
        if sample.scores and sample.scores[scorer].value != "C"
    }


def explanations(log: EvalLog, scorer: str) -> dict[str, str]:
    """Failure reasons by sample ID for the named scorer."""
    return {
        str(sample.id): sample.scores[scorer].explanation or ""
        for sample in log.samples or []
        if sample.scores and sample.scores[scorer].value != "C"
    }


def completions(log: EvalLog) -> dict[str, str]:
    """The model's final answer by sample ID."""
    return {str(sample.id): sample.output.completion for sample in log.samples or []}
