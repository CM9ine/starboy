"""Persist one complete JSONL record for each agent invocation."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from starboy.agent import AgentResult, run_agent
from starboy.cost import calculate_cost


@dataclass(frozen=True)
class AgentCallContext:
    """Workflow facts known before an agent invocation begins."""

    run_id: str
    issue: int | None
    phase: str
    sequence: int
    harness: str
    model: str


def log_agent_call(
    log_path: Path, context: AgentCallContext, result: AgentResult
) -> None:
    """Append a complete, JSON-serialisable record of an agent call."""

    billed_model = result.resolved_model or context.model
    cost, pricing_version = calculate_cost(result.usage, billed_model)
    record = {
        **asdict(context),
        "requested_model": context.model,
        "resolved_model": result.resolved_model,
        "session_id": result.session_id,
        "tool_calls": result.tool_calls,
        **asdict(result.usage),
        "cost_usd": str(cost),
        "pricing_version": pricing_version,
        "seconds": str(result.seconds),
        "outcome": result.outcome,
    }
    del record["model"]
    with log_path.open("a") as log_file:
        log_file.write(json.dumps(record) + "\n")


def run_agent_logged(
    context: AgentCallContext, log_path: Path, prompt: str, cwd: Path
) -> AgentResult:
    """Run an agent and append its result using the caller's workflow context."""

    result = run_agent(context.harness, context.model, prompt, cwd)
    log_agent_call(log_path, context, result)
    return result
