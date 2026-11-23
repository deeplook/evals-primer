"""An OpenAI Agents SDK agent as the system under test inside an Inspect eval.

`sdk_solver` runs one SDK agent per sample and hands Inspect the final answer.
The executed tool calls, model turns, and token usage go into the sample's
metadata, where `check_scorer` checks see them. Offline, the SDK's
`ScriptedModel` plays each sample's planted steps; the SDK still executes the
tools and guardrails. `--local` and `--live` swap in a real model.

The tools are in-process fakes that only append to a `Ledger`. Nothing here
touches the network or the file system, which is why the agent can run in the
Inspect process; an agent with real tools belongs in a sandbox (ADR 0003).
"""

from __future__ import annotations

import json
import time
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass, field
from typing import Any

from _shared import live, live_model, local, local_endpoint, run_eval, setting
from agents import (
    Agent,
    InputGuardrailTripwireTriggered,
    MaxTurnsExceeded,
    Model,
    OpenAIChatCompletionsModel,
    RunConfig,
    Runner,
    Usage,
)
from agents.items import ToolCallItem
from agents.testing import ModelStep, ScriptedModel
from inspect_ai import Task
from inspect_ai.log import EvalLog
from inspect_ai.model import ModelOutput, get_model
from inspect_ai.solver import Generate, Solver, TaskState, solver
from openai import AsyncOpenAI
from openai.types.responses import ResponseFunctionToolCall

# One scripted model call costs this much, so offline runs can report tokens.
MAX_TURNS = 6
SCRIPTED_USAGE = Usage(requests=1, input_tokens=400, output_tokens=60, total_tokens=460)


@dataclass
class Ledger:
    """What the fake tools actually did, as (tool, arguments) pairs."""

    effects: list[tuple[str, dict[str, Any]]] = field(default_factory=list)

    def record(self, tool: str, **arguments: Any) -> None:
        self.effects.append((tool, arguments))

    def calls(self, tool: str) -> list[dict[str, Any]]:
        return [args for name, args in self.effects if name == tool]

    def executed(self) -> list[dict[str, Any]]:
        return [{"tool": name, **args} for name, args in self.effects]


@dataclass
class AgentRun:
    final: str
    requested: list[dict[str, Any]]  # tool calls the model asked for
    executed: list[dict[str, Any]]  # tool calls that ran (from the ledger)
    turns: int
    tokens: int
    seconds: float
    blocked: bool = False  # an input guardrail stopped the run
    stopped: bool = False  # the run hit max_turns, e.g. retrying a blocked tool


Steps = Sequence[ModelStep | list[Any]]


def agent_model(steps: Steps) -> Model | str:
    """The SDK's ScriptedModel offline, a local server or hosted model otherwise."""
    if live():
        return setting("EVALS_AGENT_MODEL", live_model().split("/")[-1])
    if local():
        base_url, name = local_endpoint()
        client = AsyncOpenAI(base_url=base_url, api_key="local")
        return OpenAIChatCompletionsModel(model=name, openai_client=client)
    return ScriptedModel(steps, default_usage=SCRIPTED_USAGE)


async def run_agent(agent: Agent[Any], prompt: str, ledger: Ledger) -> AgentRun:
    """Run one agent to completion and summarise what it asked for and did."""
    start = time.perf_counter()
    config = RunConfig(tracing_disabled=not live())
    try:
        result = await Runner.run(agent, prompt, run_config=config, max_turns=MAX_TURNS)
    except InputGuardrailTripwireTriggered:
        seconds = time.perf_counter() - start
        return AgentRun("[blocked by input guardrail]", [], [], 0, 0, seconds, True)
    except MaxTurnsExceeded:
        # A model that keeps retrying a rejected tool ends here. That is an
        # outcome to grade on what the ledger says ran, not an eval error.
        seconds = time.perf_counter() - start
        return AgentRun(
            f"[stopped after {MAX_TURNS} turns]", [], ledger.executed(), MAX_TURNS, 0,
            seconds, stopped=True,
        )  # fmt: skip
    requested = [
        {"tool": item.raw_item.name, **json.loads(item.raw_item.arguments or "{}")}
        for item in result.new_items
        if isinstance(item, ToolCallItem)
        and isinstance(item.raw_item, ResponseFunctionToolCall)
    ]
    usage = result.context_wrapper.usage
    return AgentRun(
        final=str(result.final_output),
        requested=requested,
        executed=ledger.executed(),
        turns=len(result.raw_responses),
        tokens=usage.total_tokens,
        seconds=time.perf_counter() - start,
    )


RunCase = Callable[[str, str], Awaitable[AgentRun]]


def sdk_solver(run_case: RunCase) -> Solver:
    """An Inspect solver that delegates each sample to an SDK agent run."""

    @solver(name="sdk_agent")
    def factory() -> Solver:
        async def solve(state: TaskState, generate: Generate) -> TaskState:
            run = await run_case(str(state.sample_id), state.input_text)
            state.metadata.update(
                requested=run.requested,
                executed=run.executed,
                turns=run.turns,
                tokens=run.tokens,
                seconds=run.seconds,
                blocked=run.blocked,
                stopped=run.stopped,
            )
            state.output = ModelOutput.from_content("openai-agents", run.final)
            return state

        return solve

    return factory()


def run_agent_eval(task: Task) -> EvalLog:
    """Run a task whose solver drives the agent; Inspect's own model is unused."""
    return run_eval(task, get_model("mockllm/model"))


def sample_metadata(log: EvalLog) -> dict[str, dict[str, Any]]:
    """Each sample's metadata after the run, by sample ID."""
    return {str(s.id): dict(s.metadata) for s in log.samples or []}
