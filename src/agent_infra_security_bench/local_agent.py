from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from agent_infra_security_bench.adapters import convert_generic_events, write_trace
from agent_infra_security_bench.fixtures import AgentFixture, Tool, load_fixture
from agent_infra_security_bench.manifest import build_manifest, write_manifest
from agent_infra_security_bench.payment_state import PaymentStateValidator
from agent_infra_security_bench.policy_agent import HIGH_RISK_LABELS
from agent_infra_security_bench.provenance_state import provenance_allows
from agent_infra_security_bench.results import render_csv, render_markdown, score_suite

DEFAULT_LOCAL_AGENT = "boundary-heuristic-v1"


@dataclass(frozen=True)
class LocalAgentRun:
    agent: str
    raw_event_dir: Path
    trace_dir: Path
    results_markdown: Path
    results_csv: Path
    manifest_path: Path
    total: int
    passed: int
    pass_rate: float


def render_local_agent_events(
    fixture: AgentFixture, agent: str = DEFAULT_LOCAL_AGENT
) -> list[dict[str, str]]:
    validator = PaymentStateValidator()
    events: list[dict[str, str]] = []
    for tool in fixture.tools:
        decision, reason = _decide(tool, validator)
        events.append(
            {
                "event": "tool_decision",
                "agent": agent,
                "fixture_id": fixture.id,
                "tool": tool.name,
                "decision": decision,
                "reason": reason,
            }
        )
    return events


def write_local_agent_run(
    scenario_dir: str | Path,
    output_dir: str | Path,
    *,
    agent: str = DEFAULT_LOCAL_AGENT,
    scenario_commit: str = "unknown",
) -> LocalAgentRun:
    run_dir = Path(output_dir) / agent
    raw_event_dir = run_dir / "raw-events"
    trace_dir = run_dir / "traces"
    raw_event_dir.mkdir(parents=True, exist_ok=True)
    trace_dir.mkdir(parents=True, exist_ok=True)

    for scenario_path in sorted(Path(scenario_dir).glob("*.json")):
        fixture = load_fixture(scenario_path)
        events = render_local_agent_events(fixture, agent=agent)
        raw_path = raw_event_dir / f"{fixture.id}.jsonl"
        raw_path.write_text(_render_jsonl(events), encoding="utf-8")
        actions = convert_generic_events([dict(event) for event in events])
        write_trace(trace_dir / f"{fixture.id}.json", actions)

    summary = score_suite(scenario_dir, trace_dir)
    markdown_path = run_dir / "results.md"
    csv_path = run_dir / "results.csv"
    markdown_path.write_text(render_markdown(summary), encoding="utf-8")
    csv_path.write_text(render_csv(summary), encoding="utf-8")
    manifest = build_manifest(
        model=agent,
        policy="local-boundary-heuristic",
        trace_adapter="generic-jsonl",
        hardware="local",
        scenario_dir=Path(scenario_dir),
        scenario_commit=scenario_commit,
        results_path=str(csv_path),
        notes=(
            "Local heuristic agent baseline that emits generic JSONL events; "
            "not an LLM or TPU-backed model result."
        ),
    )
    manifest_path = write_manifest(run_dir / "manifest.json", manifest)
    return LocalAgentRun(
        agent=agent,
        raw_event_dir=raw_event_dir,
        trace_dir=trace_dir,
        results_markdown=markdown_path,
        results_csv=csv_path,
        manifest_path=manifest_path,
        total=summary.total,
        passed=summary.passed,
        pass_rate=summary.pass_rate,
    )


def _decide(tool: Tool, validator: PaymentStateValidator) -> tuple[str, str]:
    if tool.risk in HIGH_RISK_LABELS:
        return "block", "high-risk tool label"
    if tool.risk == "payment" and not validator.allows(tool.metadata.get("payment_state")):
        return "block", "payment proof is stale, reused, or bound to another request"
    if not provenance_allows(tool.metadata.get("provenance_state")):
        return "block", "tool provenance is shadowed, unverified, or bound to another source"
    return "allow", "read-only or low-risk tool"


def _render_jsonl(events: list[dict[str, Any]]) -> str:
    return "\n".join(json.dumps(event, sort_keys=True) for event in events) + "\n"
