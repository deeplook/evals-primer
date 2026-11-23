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
# Keep Inspect's generated logs under out/, which `make clean` removes.
LOG_DIR = Path(os.environ.get("INSPECT_LOG_DIR", ROOT / "out" / "inspect-logs"))
LIVE_MODEL = os.environ.get("EVALS_MODEL", "openai/gpt-6-luna")
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
    concurrently. `key` extracts the lookup key from a longer prompt, for
    example the submission inside a judge's grading template.
    """

    def respond(
        messages: list[ChatMessage],
        tools: list[ToolInfo],
        tool_choice: ToolChoice,
        config: GenerateConfig,
    ) -> ModelOutput:
        prompt = key(messages[-1].text)
        if prompt not in outputs:
            raise KeyError(f"no scripted output for prompt: {prompt!r}")
        return ModelOutput.from_content(model="mockllm", content=outputs[prompt])

    return get_model("mockllm/model", custom_outputs=respond)


def live_model() -> str:
    """The hosted model name for `--live`; SKIP without a key."""
    if not os.environ.get("OPENAI_API_KEY"):
        skip("--live needs OPENAI_API_KEY")
    return LIVE_MODEL


def _list_models(base_url: str) -> list[str] | None:
    try:
        with urllib.request.urlopen(f"{base_url}/models", timeout=2) as response:
            payload = json.load(response)
    except (OSError, urllib.error.URLError, ValueError):
        return None
    return [str(entry["id"]) for entry in payload.get("data", [])]


def local_model() -> Model:
    """A model on a local OpenAI-compatible server for `--local`; SKIP if none."""
    if not local():
        skip("pass --local to use Ollama or llama-server")
    configured = os.environ.get("LOCAL_BASE_URL")
    for base_url in [configured] if configured else LOCAL_CANDIDATES:
        names = _list_models(base_url)
        if names is None:
            continue
        chat = [name for name in names if "embed" not in name]
        name = os.environ.get("EVALS_LOCAL_MODEL") or (chat[0] if chat else None)
        if name is None:
            skip(f"{base_url} lists no chat model")
        return get_model(f"openai-api/local/{name}", base_url=base_url, api_key="local")
    skip("no local OpenAI-compatible server found")


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
