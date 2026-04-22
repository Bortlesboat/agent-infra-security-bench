from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Literal

from agent_infra_security_bench.fixtures import AgentFixture, load_fixture

SyntheticMode = Literal["pass", "fail"]


def render_synthetic_trace(
    fixture: AgentFixture, mode: SyntheticMode = "pass"
) -> list[dict[str, str]]:
    if mode not in {"pass", "fail"}:
        raise ValueError(f"Synthetic mode must be pass or fail: {mode}")
    return [
        {"tool": action.tool, "decision": _decision_for_mode(action.decision, mode)}
        for action in fixture.expected_actions
    ]


def write_synthetic_traces(
    source: str | Path | Iterable[AgentFixture],
    trace_dir: str | Path,
    mode: SyntheticMode = "pass",
) -> list[Path]:
    fixtures = _load_fixtures(source)
    output_dir = Path(trace_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    for fixture in fixtures:
        trace_path = output_dir / f"{fixture.id}.json"
        trace_path.write_text(
            json.dumps(render_synthetic_trace(fixture, mode), indent=2) + "\n",
            encoding="utf-8",
        )
        written.append(trace_path)
    return written


def _load_fixtures(source: str | Path | Iterable[AgentFixture]) -> list[AgentFixture]:
    if isinstance(source, str | Path):
        return [load_fixture(path) for path in sorted(Path(source).glob("*.json"))]
    return sorted(source, key=lambda fixture: fixture.id)


def _decision_for_mode(decision: str, mode: SyntheticMode) -> str:
    if mode == "pass":
        return decision
    return "block" if decision == "allow" else "allow"
