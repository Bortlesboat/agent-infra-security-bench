from __future__ import annotations

import csv
from datetime import datetime
import json
from pathlib import Path
from typing import Any


def annotate_manifest_costs(
    manifest_path: str | Path,
    *,
    pricing_snapshot: dict[str, Any],
    timing: dict[str, Any],
    reliability: dict[str, Any] | None = None,
    output_path: str | Path | None = None,
    root_path: str | Path | None = None,
) -> Path:
    source = Path(manifest_path)
    with source.open("r", encoding="utf-8-sig") as handle:
        manifest = json.load(handle)
    if not isinstance(manifest, dict):
        raise ValueError(f"Run manifest must be a JSON object: {source}")

    root = Path(root_path) if root_path is not None else Path.cwd()
    reliability_payload = reliability or {}
    manifest["pricing_snapshot"] = pricing_snapshot
    manifest["timing"] = timing
    manifest["reliability"] = reliability_payload
    manifest["derived_costs"] = derive_run_costs(
        manifest,
        pricing_snapshot=pricing_snapshot,
        timing=timing,
        reliability=reliability_payload,
        root_path=root,
        manifest_path=source,
    )

    destination = Path(output_path) if output_path is not None else source
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return destination


def derive_run_costs(
    manifest: dict[str, Any],
    *,
    pricing_snapshot: dict[str, Any],
    timing: dict[str, Any],
    reliability: dict[str, Any] | None = None,
    root_path: str | Path | None = None,
    manifest_path: str | Path | None = None,
) -> dict[str, float | int | None]:
    root = Path(root_path) if root_path is not None else Path.cwd()
    manifest_file = Path(manifest_path) if manifest_path is not None else root / "manifest.json"
    hourly_meter = _required_number(pricing_snapshot, "full_node_hourly_meter_usd")
    billable_seconds = _billable_seconds(timing)
    billable_hours = billable_seconds / 3600
    successful_run_cost = _round_money(hourly_meter * billable_hours)
    friction_cost = _friction_cost_usd(reliability or {}, hourly_meter)
    economic_run_cost = _round_money(successful_run_cost + friction_cost)

    results = _summarize_results(
        _resolve_path(_required_str(manifest, "results_path"), root_path=root, manifest_path=manifest_file)
    )
    coverage = _load_coverage(manifest, root_path=root, manifest_path=manifest_file)
    total_tools = _optional_int(coverage, "total_tools")
    decided_tools = _optional_int(coverage, "decided_tools")
    fully_covered = (
        total_tools is not None
        and decided_tools is not None
        and total_tools > 0
        and decided_tools == total_tools
    )

    return {
        "billable_seconds": float(billable_seconds),
        "billable_hours": _round_money(billable_hours),
        "successful_run_cost_usd": successful_run_cost,
        "friction_cost_usd": friction_cost,
        "economic_run_cost_usd": economic_run_cost,
        "fixture_count": results["total"],
        "passed_fixture_count": results["passed"],
        "total_tool_count": total_tools,
        "decided_tool_count": decided_tools,
        "cost_per_fixture_usd": _per_unit(successful_run_cost, results["total"]),
        "cost_per_passed_fixture_usd": _per_unit(successful_run_cost, results["passed"]),
        "cost_per_covered_tool_decision_usd": _per_unit(successful_run_cost, decided_tools),
        "cost_per_fully_covered_tool_decision_usd": _per_unit(successful_run_cost, total_tools)
        if fully_covered
        else None,
        "economic_cost_per_fixture_usd": _per_unit(economic_run_cost, results["total"]),
        "economic_cost_per_passed_fixture_usd": _per_unit(economic_run_cost, results["passed"]),
        "economic_cost_per_covered_tool_decision_usd": _per_unit(economic_run_cost, decided_tools),
        "economic_cost_per_fully_covered_tool_decision_usd": _per_unit(economic_run_cost, total_tools)
        if fully_covered
        else None,
    }


def load_json_object(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    with source.open("r", encoding="utf-8-sig") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {source}")
    return payload


def _billable_seconds(timing: dict[str, Any]) -> float:
    explicit = timing.get("billable_seconds")
    if isinstance(explicit, (int, float)):
        return float(explicit)

    for start_key, end_key in (
        ("create_requested_at", "delete_verified_at"),
        ("benchmark_started_at", "benchmark_finished_at"),
    ):
        start = timing.get(start_key)
        end = timing.get(end_key)
        if isinstance(start, str) and isinstance(end, str):
            return (_parse_timestamp(end) - _parse_timestamp(start)).total_seconds()

    raise ValueError(
        "Timing metadata must include billable_seconds or timestamp pairs "
        "create_requested_at/delete_verified_at or benchmark_started_at/benchmark_finished_at"
    )


def _friction_cost_usd(reliability: dict[str, Any], hourly_meter: float) -> float:
    explicit = reliability.get("friction_cost_usd")
    if isinstance(explicit, (int, float)):
        return _round_money(float(explicit))

    friction_seconds = sum(
        _optional_number(reliability, key)
        for key in (
            "friction_billable_seconds",
            "failed_allocation_billable_seconds",
            "preempted_bootstrap_billable_seconds",
        )
    )
    operator_minutes = _optional_number(reliability, "operator_minutes")
    operator_rate = _optional_number(reliability, "operator_rate_usd_per_minute")
    return _round_money((friction_seconds / 3600 * hourly_meter) + (operator_minutes * operator_rate))


def _summarize_results(path: Path) -> dict[str, int]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return {
        "total": len(rows),
        "passed": sum(1 for row in rows if row.get("passed") == "true"),
    }


def _load_coverage(
    manifest: dict[str, Any],
    *,
    root_path: Path,
    manifest_path: Path,
) -> dict[str, Any] | None:
    raw_path = manifest.get("coverage_path")
    if not isinstance(raw_path, str) or not raw_path:
        return None
    coverage_path = _resolve_path(raw_path, root_path=root_path, manifest_path=manifest_path)
    with coverage_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"Coverage summary must be a JSON object: {coverage_path}")
    return payload


def _resolve_path(raw_path: str, *, root_path: Path, manifest_path: Path) -> Path:
    path = Path(raw_path)
    if path.is_absolute() and path.exists():
        return path
    candidates = [
        root_path / path,
        manifest_path.parent / path,
        manifest_path.parent / path.name,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise ValueError(f"Referenced run artifact does not exist for {manifest_path}: {raw_path}")


def _parse_timestamp(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


def _required_str(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"Required string field missing or empty: {key}")
    return value


def _required_number(data: dict[str, Any], key: str) -> float:
    value = data.get(key)
    if not isinstance(value, (int, float)):
        raise ValueError(f"Required numeric field missing: {key}")
    return float(value)


def _optional_number(data: dict[str, Any], key: str) -> float:
    value = data.get(key)
    return float(value) if isinstance(value, (int, float)) else 0.0


def _optional_int(data: dict[str, Any] | None, key: str) -> int | None:
    if data is None:
        return None
    value = data.get(key)
    return value if isinstance(value, int) else None


def _per_unit(cost: float, denominator: int | None) -> float | None:
    if denominator is None or denominator <= 0:
        return None
    return _round_money(cost / denominator)


def _round_money(value: float) -> float:
    return round(float(value), 6)
