from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from agent_infra_security_bench.fixtures import AgentFixture, Tool, load_fixture

PolicyName = Literal["deny-high-risk", "deny-high-risk-payment-state", "naive-allow"]

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
    return ["deny-high-risk", "deny-high-risk-payment-state", "naive-allow"]


def render_policy_trace(fixture: AgentFixture, policy: PolicyName) -> list[dict[str, str]]:
    if policy not in available_policies():
        raise ValueError(f"Unknown policy: {policy}")
    tools = {tool.name: tool for tool in fixture.tools}
    payment_validator = PaymentStateValidator()
    actions: list[dict[str, str]] = []
    for expected in fixture.expected_actions:
        tool = tools.get(expected.tool)
        actions.append({"tool": expected.tool, "decision": _decision(policy, tool, payment_validator)})
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


class PaymentStateValidator:
    def __init__(self) -> None:
        self._seen_proofs: set[str] = set()

    def allows(self, tool: Tool) -> bool:
        state = tool.metadata.get("payment_state")
        if not isinstance(state, dict):
            return True

        proof_id = state.get("proof_id")
        if isinstance(proof_id, str) and proof_id in self._seen_proofs:
            return False

        nonce_status = state.get("nonce_status")
        if nonce_status in {"reused", "stale"}:
            return False

        request_id = state.get("request_id")
        approved_request_id = state.get("approved_request_id")
        if (
            isinstance(request_id, str)
            and isinstance(approved_request_id, str)
            and request_id != approved_request_id
        ):
            return False

        if isinstance(proof_id, str):
            self._seen_proofs.add(proof_id)
        return True


def _decision(policy: PolicyName, tool: Tool | None, payment_validator: PaymentStateValidator) -> str:
    if policy == "naive-allow":
        return "allow"
    risk = tool.risk if tool else ""
    if policy == "deny-high-risk-payment-state" and tool and risk == "payment":
        if not payment_validator.allows(tool):
            return "block"
    return "block" if risk in HIGH_RISK_LABELS else "allow"
