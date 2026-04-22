from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from agent_infra_security_bench.fixtures import AgentFixture, load_fixture

PolicyName = Literal["deny-high-risk", "naive-allow"]

HIGH_RISK_LABELS = {
    "code_execution",
    "credential_theft",
    "exfiltration",
    "financial_loss",
    "network_exfiltration",
    "privilege_escalation",
    "secret_exposure",
    "supply_chain_execution",
}


def available_policies() -> list[str]:
    return ["deny-high-risk", "naive-allow"]


def render_policy_trace(fixture: AgentFixture, policy: PolicyName) -> list[dict[str, str]]:
    if policy not in available_policies():
        raise ValueError(f"Unknown policy: {policy}")
    risks = {tool.name: tool.risk for tool in fixture.tools}
    actions: list[dict[str, str]] = []
    for expected in fixture.expected_actions:
        risk = risks.get(expected.tool, "")
        actions.append({"tool": expected.tool, "decision": _decision(policy, risk)})
    return actions


def write_policy_traces(
    scenario_dir: str | Path, trace_dir: str | Path, policy: PolicyName
) -> list[Path]:
    output_dir = Path(trace_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for scenario_path in sorted(Path(scenario_dir).glob("*.json")):
        fixture = load_fixture(scenario_path)
        trace_path = output_dir / f"{fixture.id}.json"
        trace_path.write_text(
            json.dumps(render_policy_trace(fixture, policy), indent=2) + "\n",
            encoding="utf-8",
        )
        written.append(trace_path)
    return written


def _decision(policy: PolicyName, risk: str) -> str:
    if policy == "naive-allow":
        return "allow"
    return "block" if risk in HIGH_RISK_LABELS else "allow"
