from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any
from uuid import uuid4

SCHEMA_VERSION = "agent-infra-security-bench/run-manifest/v1"


@dataclass(frozen=True)
class RunManifest:
    run_id: str
    created_at: str
    model: str
    policy: str
    trace_adapter: str
    hardware: str
    scenario_count: int
    scenario_commit: str
    results_path: str | None
    coverage_path: str | None
    notes: str | None
    pricing_snapshot: dict[str, Any] | None = None
    timing: dict[str, Any] | None = None
    reliability: dict[str, Any] | None = None
    derived_costs: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "run_id": self.run_id,
            "created_at": self.created_at,
            "model": self.model,
            "policy": self.policy,
            "trace_adapter": self.trace_adapter,
            "hardware": self.hardware,
            "scenario_count": self.scenario_count,
            "scenario_commit": self.scenario_commit,
            "results_path": self.results_path,
            "coverage_path": self.coverage_path,
            "notes": self.notes,
        }
        if self.pricing_snapshot is not None:
            payload["pricing_snapshot"] = self.pricing_snapshot
        if self.timing is not None:
            payload["timing"] = self.timing
        if self.reliability is not None:
            payload["reliability"] = self.reliability
        if self.derived_costs is not None:
            payload["derived_costs"] = self.derived_costs
        return payload


def build_manifest(
    *,
    model: str,
    policy: str,
    trace_adapter: str,
    hardware: str,
    scenario_dir: str | Path,
    scenario_commit: str = "unknown",
    results_path: str | None = None,
    coverage_path: str | None = None,
    notes: str | None = None,
    pricing_snapshot: dict[str, Any] | None = None,
    timing: dict[str, Any] | None = None,
    reliability: dict[str, Any] | None = None,
    derived_costs: dict[str, Any] | None = None,
) -> RunManifest:
    return RunManifest(
        run_id=f"run-{uuid4().hex[:12]}",
        created_at=datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        model=model,
        policy=policy,
        trace_adapter=trace_adapter,
        hardware=hardware,
        scenario_count=count_scenarios(scenario_dir),
        scenario_commit=scenario_commit,
        results_path=results_path,
        coverage_path=coverage_path,
        notes=notes,
        pricing_snapshot=pricing_snapshot,
        timing=timing,
        reliability=reliability,
        derived_costs=derived_costs,
    )


def write_manifest(path: str | Path, manifest: RunManifest) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest.to_dict(), indent=2) + "\n", encoding="utf-8")
    return output


def count_scenarios(path: str | Path) -> int:
    scenario_dir = Path(path)
    if not scenario_dir.exists():
        return 0
    return sum(1 for item in scenario_dir.glob("*.json") if item.is_file())
