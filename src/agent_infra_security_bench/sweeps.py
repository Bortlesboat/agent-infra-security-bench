from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

RUN_MANIFEST_SCHEMA = "agent-infra-security-bench/run-manifest/v1"
SWEEP_INDEX_SCHEMA = "agent-infra-security-bench/sweep-index/v1"


@dataclass(frozen=True)
class SweepRun:
    manifest_path: str
    run_id: str
    created_at: str
    model: str
    policy: str
    prompt_profile: str | None
    runtime_policy: str | None
    trace_adapter: str
    hardware: str
    scenario_count: int
    scenario_commit: str
    results_path: str
    coverage_path: str | None
    total: int
    passed: int
    pass_rate: float
    average_score: float
    unsafe_count: int
    missed_count: int
    total_tools: int | None
    decided_tools: int | None
    coverage_rate: float | None
    omitted_tools: int | None
    duplicate_decision_tools: int | None
    billable_hours: float | None
    successful_run_cost_usd: float | None
    economic_run_cost_usd: float | None
    cost_per_fixture_usd: float | None
    cost_per_passed_fixture_usd: float | None
    cost_per_covered_tool_decision_usd: float | None
    notes: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "manifest_path": self.manifest_path,
            "run_id": self.run_id,
            "created_at": self.created_at,
            "model": self.model,
            "policy": self.policy,
            "prompt_profile": self.prompt_profile,
            "runtime_policy": self.runtime_policy,
            "trace_adapter": self.trace_adapter,
            "hardware": self.hardware,
            "scenario_count": self.scenario_count,
            "scenario_commit": self.scenario_commit,
            "results_path": self.results_path,
            "coverage_path": self.coverage_path,
            "total": self.total,
            "passed": self.passed,
            "pass_rate": self.pass_rate,
            "average_score": self.average_score,
            "unsafe_count": self.unsafe_count,
            "missed_count": self.missed_count,
            "total_tools": self.total_tools,
            "decided_tools": self.decided_tools,
            "coverage_rate": self.coverage_rate,
            "omitted_tools": self.omitted_tools,
            "duplicate_decision_tools": self.duplicate_decision_tools,
            "billable_hours": self.billable_hours,
            "successful_run_cost_usd": self.successful_run_cost_usd,
            "economic_run_cost_usd": self.economic_run_cost_usd,
            "cost_per_fixture_usd": self.cost_per_fixture_usd,
            "cost_per_passed_fixture_usd": self.cost_per_passed_fixture_usd,
            "cost_per_covered_tool_decision_usd": self.cost_per_covered_tool_decision_usd,
            "notes": self.notes,
        }


@dataclass(frozen=True)
class SweepIndex:
    name: str
    generated_at: str
    runs: tuple[SweepRun, ...]

    @property
    def run_count(self) -> int:
        return len(self.runs)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": SWEEP_INDEX_SCHEMA,
            "name": self.name,
            "generated_at": self.generated_at,
            "run_count": self.run_count,
            "runs": [run.to_dict() for run in self.runs],
        }


def build_sweep_index(
    name: str,
    manifests: list[str | Path],
    *,
    root: str | Path | None = None,
) -> SweepIndex:
    root_path = Path(root) if root is not None else Path.cwd()
    runs = tuple(_load_sweep_run(Path(manifest), root_path=root_path) for manifest in manifests)
    return SweepIndex(
        name=name,
        generated_at=datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        runs=tuple(sorted(runs, key=lambda run: (run.scenario_commit, run.model, run.policy))),
    )


def write_sweep_index(path: str | Path, sweep: SweepIndex) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(sweep.to_dict(), indent=2) + "\n", encoding="utf-8")
    return output


def render_sweep_markdown(sweep: SweepIndex) -> str:
    lines = [
        f"# {sweep.name}",
        "",
        f"- Runs: {sweep.run_count}",
        f"- Generated: {sweep.generated_at}",
        "",
        "| Run | Model | Policy | Prompt | Runtime | Hardware | Commit | Passed | Pass Rate | Avg Score | Unsafe | Missed | Coverage | Omitted | Duplicates |",
        "| --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for run in sweep.runs:
        lines.append(
            "| "
            + " | ".join(
                [
                    run.run_id,
                    run.model,
                    run.policy,
                    run.prompt_profile or "n/a",
                    run.runtime_policy or "n/a",
                    run.hardware,
                    run.scenario_commit,
                    f"{run.passed}/{run.total}",
                    f"{run.pass_rate:.3f}",
                    f"{run.average_score:.3f}",
                    str(run.unsafe_count),
                    str(run.missed_count),
                    _format_float(run.coverage_rate),
                    _format_int(run.omitted_tools),
                    _format_int(run.duplicate_decision_tools),
                ]
            )
            + " |"
        )
    if any(run.successful_run_cost_usd is not None for run in sweep.runs):
        lines.extend(
            [
                "",
                "## Cost",
                "",
                "| Run | Billable Hours | Run Cost | Economic Cost | $/Fixture | $/Pass | $/Covered Tool |",
                "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for run in sweep.runs:
            lines.append(
                "| "
                + " | ".join(
                    [
                        run.run_id,
                        _format_float(run.billable_hours),
                        _format_float(run.successful_run_cost_usd),
                        _format_float(run.economic_run_cost_usd),
                        _format_float(run.cost_per_fixture_usd),
                        _format_float(run.cost_per_passed_fixture_usd),
                        _format_float(run.cost_per_covered_tool_decision_usd),
                    ]
                )
                + " |"
            )
    return "\n".join(lines) + "\n"


def _load_sweep_run(manifest_path: Path, *, root_path: Path) -> SweepRun:
    with manifest_path.open("r", encoding="utf-8-sig") as handle:
        manifest = json.load(handle)
    if not isinstance(manifest, dict):
        raise ValueError(f"Run manifest must be a JSON object: {manifest_path}")
    schema_version = manifest.get("schema_version")
    if schema_version != RUN_MANIFEST_SCHEMA:
        raise ValueError(f"Unsupported run manifest schema_version: {schema_version}")

    raw_results_path = _required_str(manifest, "results_path")
    results_path = _resolve_results_path(raw_results_path, manifest_path=manifest_path, root_path=root_path)
    result_summary = _summarize_results(results_path)
    coverage_path = _resolve_coverage_path(
        manifest.get("coverage_path"),
        manifest_path=manifest_path,
        root_path=root_path,
        results_path=results_path,
    )
    coverage_summary = _load_coverage_summary(coverage_path) if coverage_path is not None else None
    policy = _required_str(manifest, "policy")
    prompt_profile, runtime_policy = _parse_policy_details(policy)
    derived_costs = manifest.get("derived_costs") if isinstance(manifest.get("derived_costs"), dict) else {}
    return SweepRun(
        manifest_path=str(manifest_path),
        run_id=_required_str(manifest, "run_id"),
        created_at=_required_str(manifest, "created_at"),
        model=_required_str(manifest, "model"),
        policy=policy,
        prompt_profile=prompt_profile,
        runtime_policy=runtime_policy,
        trace_adapter=_required_str(manifest, "trace_adapter"),
        hardware=_required_str(manifest, "hardware"),
        scenario_count=int(manifest.get("scenario_count", 0)),
        scenario_commit=_required_str(manifest, "scenario_commit"),
        results_path=str(results_path),
        coverage_path=str(coverage_path) if coverage_path is not None else None,
        total=result_summary["total"],
        passed=result_summary["passed"],
        pass_rate=result_summary["pass_rate"],
        average_score=result_summary["average_score"],
        unsafe_count=result_summary["unsafe_count"],
        missed_count=result_summary["missed_count"],
        total_tools=_coverage_int(coverage_summary, "total_tools"),
        decided_tools=_coverage_int(coverage_summary, "decided_tools"),
        coverage_rate=_coverage_float(coverage_summary, "coverage_rate"),
        omitted_tools=_coverage_int(coverage_summary, "omitted_tools"),
        duplicate_decision_tools=_coverage_int(coverage_summary, "duplicate_decision_tools"),
        billable_hours=_optional_float(derived_costs, "billable_hours"),
        successful_run_cost_usd=_optional_float(derived_costs, "successful_run_cost_usd"),
        economic_run_cost_usd=_optional_float(derived_costs, "economic_run_cost_usd"),
        cost_per_fixture_usd=_optional_float(derived_costs, "cost_per_fixture_usd"),
        cost_per_passed_fixture_usd=_optional_float(derived_costs, "cost_per_passed_fixture_usd"),
        cost_per_covered_tool_decision_usd=_optional_float(derived_costs, "cost_per_covered_tool_decision_usd"),
        notes=manifest.get("notes") if isinstance(manifest.get("notes"), str) else None,
    )


def _summarize_results(path: Path) -> dict[str, int | float]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    total = len(rows)
    passed = sum(1 for row in rows if row.get("passed") == "true")
    scores = [_float(row.get("score")) for row in rows]
    return {
        "total": total,
        "passed": passed,
        "pass_rate": passed / total if total else 0.0,
        "average_score": sum(scores) / total if total else 0.0,
        "unsafe_count": sum(_int(row.get("unsafe_count")) for row in rows),
        "missed_count": sum(_int(row.get("missed_count")) for row in rows),
    }


def _resolve_results_path(raw_path: str, *, manifest_path: Path, root_path: Path) -> Path:
    results_path = Path(raw_path)
    if results_path.is_absolute() and results_path.exists():
        return results_path
    candidates = [
        root_path / results_path,
        manifest_path.parent / results_path,
        manifest_path.parent / results_path.name,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise ValueError(f"Run results path does not exist for {manifest_path}: {raw_path}")


def _resolve_coverage_path(
    raw_path: Any,
    *,
    manifest_path: Path,
    root_path: Path,
    results_path: Path,
) -> Path | None:
    if isinstance(raw_path, str) and raw_path:
        coverage_path = Path(raw_path)
        if coverage_path.is_absolute() and coverage_path.exists():
            return coverage_path
        candidates = [
            root_path / coverage_path,
            manifest_path.parent / coverage_path,
            manifest_path.parent / coverage_path.name,
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
    sibling = results_path.parent / "coverage.json"
    if sibling.exists():
        return sibling
    return None


def _load_coverage_summary(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"Coverage summary must be a JSON object: {path}")
    return payload


def _parse_policy_details(policy: str) -> tuple[str | None, str | None]:
    prompt_profile: str | None = None
    runtime_policy: str | None = None
    if policy == "model-decisions":
        return "baseline", "none"
    for part in policy.split(";"):
        part = part.strip()
        if part.startswith("prompt="):
            prompt_profile = part.removeprefix("prompt=")
        if part.startswith("runtime="):
            runtime_policy = part.removeprefix("runtime=")
    return prompt_profile, runtime_policy


def _required_str(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"Required string field missing or empty: {key}")
    return value


def _float(value: Any) -> float:
    if not isinstance(value, str):
        return 0.0
    return float(value)


def _int(value: Any) -> int:
    if not isinstance(value, str):
        return 0
    return int(value)


def _coverage_int(summary: dict[str, Any] | None, key: str) -> int | None:
    if summary is None:
        return None
    value = summary.get(key)
    return value if isinstance(value, int) else None


def _coverage_float(summary: dict[str, Any] | None, key: str) -> float | None:
    if summary is None:
        return None
    value = summary.get(key)
    return value if isinstance(value, (int, float)) else None


def _optional_float(summary: dict[str, Any], key: str) -> float | None:
    value = summary.get(key)
    return float(value) if isinstance(value, (int, float)) else None


def _format_float(value: float | None) -> str:
    return f"{value:.3f}" if value is not None else "n/a"


def _format_int(value: int | None) -> str:
    return str(value) if value is not None else "n/a"
