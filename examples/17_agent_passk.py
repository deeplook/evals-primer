"""Agent evals: grade the end state, report pass^k, and count what a scaffold costs.

Part 1, pass^k. A support agent refunds damaged orders through `get_order` and
`refund` tools. Grade the *end state* the tools produced (the refund ledger),
not the transcript: an agent can say "refunded" without calling the tool, or
refund twice. Run each task k=3 times. pass@k (any run succeeds) is what a demo
shows; pass^k (every run succeeds) is what a user relying on the agent gets.
Agent benchmarks such as tau-bench report pass^k for that reason.

Part 2, scaffold cost. The same tasks run under two scaffolds: one agent, and
a planner agent whose plan the executor follows. Report accuracy *and* model
calls, tokens, and time; HAL-style comparisons show a better score can simply
be a more expensive scaffold. Offline, each scripted model call is charged a
fixed 460 tokens so the cost difference is visible.
"""

from __future__ import annotations

from typing import Any

from _agent import (
    AgentRun,
    Ledger,
    agent_model,
    run_agent,
    run_agent_eval,
    sample_metadata,
    sdk_solver,
)
from _shared import check_scorer, completions, explanations, offline
from agents import Agent, function_tool
from agents.testing import assistant_message, function_call
from inspect_ai import Task
from inspect_ai.dataset import Sample
from inspect_ai.log import EvalLog

K = 3
ORDERS = {17: (40, "damaged"), 23: (25, "damaged"), 31: (30, "delivered fine")}
POLICY = "Refund an order once, in full, only if it arrived damaged."
TASKS = {
    "A": (17, "Order 17 arrived damaged. Please refund it."),
    "B": (23, "Order 23 arrived damaged. Please refund it."),
    "C": (31, "I changed my mind about order 31. Please refund it."),
}
EXPECTED = {key: [(oid, ORDERS[oid][0])] if key != "C" else [] for key, (oid, _) in TASKS.items()}  # fmt: skip


def get(oid: int, n: int = 1) -> list[Any]:
    return [function_call("get_order", {"order_id": oid}, call_id=f"g{n}")]


def refund(oid: int, n: int = 1) -> list[Any]:
    amount = ORDERS[oid][0]
    return [
        function_call("refund", {"order_id": oid, "amount": amount}, call_id=f"r{n}")
    ]


def say(text: str) -> list[Any]:
    return [assistant_message(text)]


# Planted runs: A always right; B refunds twice once and claims without acting once;
# C refunds against policy every time.
RUNS: dict[str, list[list[list[Any]]]] = {
    "A": [[get(17), refund(17), say("Refunded order 17.")]] * K,
    "B": [
        [get(23), refund(23), say("Refunded order 23.")],
        [get(23), refund(23), refund(23, 2), say("Refunded order 23.")],
        [get(23), say("I've refunded order 23.")],
    ],
    "C": [[get(31), refund(31), say("Refunded order 31.")]] * K,
}
# Under the planner scaffold the executor gets C right.
EXECUTOR = {
    "A": RUNS["A"][0],
    "B": RUNS["B"][0],
    "C": [get(31), say("Order 31 arrived fine, so it is not eligible for a refund.")],
}


def support_agent(ledger: Ledger, steps: list[list[Any]], note: str = "") -> Agent[Any]:
    @function_tool
    def get_order(order_id: int) -> str:
        """Look up an order's amount and delivery status."""
        amount, status = ORDERS[order_id]
        return f"order {order_id}: amount {amount}, {status}"

    @function_tool
    def refund(order_id: int, amount: int) -> str:
        """Refund an amount for an order."""
        ledger.record("refund", order_id=order_id, amount=amount)
        return "refunded"

    return Agent(
        name="Support",
        instructions=f"You handle refunds. Policy: {POLICY} {note}".strip(),
        tools=[get_order, refund],
        model=agent_model(steps),
    )


async def single(sample_id: str, prompt: str) -> AgentRun:
    task, run = sample_id.split("-run")
    ledger = Ledger()
    return await run_agent(
        support_agent(ledger, RUNS[task][int(run) - 1]), prompt, ledger
    )


async def planned(sample_id: str, prompt: str) -> AgentRun:
    task = sample_id.split("-run")[0]
    planner = Agent(
        name="Planner",
        instructions=f"Write a short plan for the support agent. Policy: {POLICY}",
        model=agent_model([say(f"Check the order's status first. {POLICY}")]),
    )
    plan = await run_agent(planner, prompt, Ledger())
    ledger = Ledger()
    act = await run_agent(
        support_agent(ledger, EXECUTOR[task], note=f"Plan: {plan.final}"),
        prompt,
        ledger,
    )
    act.turns += plan.turns
    act.tokens += plan.tokens
    act.seconds += plan.seconds
    return act


def end_state(completion: str, meta: dict[str, Any]) -> str | None:
    done = [(c["order_id"], c["amount"]) for c in meta["executed"]]
    return None if done == meta["expected"] else f"ledger {done}"


def transcript(completion: str, meta: dict[str, Any]) -> str | None:
    return None if "refunded" in completion.lower() else "no refund claimed"


def evaluate(runner: Any, runs: int) -> EvalLog:
    dataset = [
        Sample(id=f"{key}-run{i}", input=prompt, metadata={"expected": EXPECTED[key]})
        for key, (_, prompt) in TASKS.items()
        for i in range(1, runs + 1)
    ]
    return run_agent_eval(
        Task(
            dataset=dataset,
            solver=sdk_solver(runner),
            scorer=[
                check_scorer("end_state", end_state),
                check_scorer("transcript", transcript),
            ],
        )
    )


def cost(log: EvalLog) -> tuple[float, int, int, float]:
    meta = sample_metadata(log)
    accuracy = 1 - len(explanations(log, "end_state")) / len(meta)
    calls = sum(m["turns"] for m in meta.values())
    tokens = sum(m["tokens"] for m in meta.values())
    seconds = sum(m["seconds"] for m in meta.values())
    return accuracy, calls, tokens, seconds


def main() -> None:
    log = evaluate(single, K)
    failed = set(explanations(log, "end_state"))
    passes = {
        key: sum(f"{key}-run{i}" not in failed for i in range(1, K + 1))
        for key in TASKS
    }
    pass_at_k = sum(n > 0 for n in passes.values()) / len(TASKS)
    pass_hat_k = sum(n == K for n in passes.values()) / len(TASKS)
    transcript_ok = len(completions(log)) - len(explanations(log, "transcript"))

    if offline() and (passes != {"A": 3, "B": 1, "C": 0} or transcript_ok != 3 * K):
        raise AssertionError(f"passes={passes} transcript_ok={transcript_ok}")
    print(
        f"OK: per-task passes {passes}; pass@{K}={pass_at_k:.2f} pass^{K}={pass_hat_k:.2f}; "
        f"the transcript grader passed {transcript_ok}/{3 * K} runs"
    )

    one, two = cost(evaluate(single, 1)), cost(evaluate(planned, 1))
    if offline() and not (two[0] > one[0] and two[1] > one[1]):
        raise AssertionError(f"single={one} planned={two}")
    for name, (acc, calls, tokens, secs) in (("single", one), ("planner", two)):
        print(
            f"  {name:8} accuracy={acc:.2f} model calls={calls} tokens={tokens} time={secs:.2f}s"
        )
    print(
        f"OK: the planner scaffold changes accuracy by {two[0] - one[0]:+.2f} for {two[1] - one[1]:+d} model calls"
    )


if __name__ == "__main__":
    main()
