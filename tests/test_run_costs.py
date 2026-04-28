import csv
import json

from agent_infra_security_bench.run_costs import annotate_manifest_costs, derive_run_costs


def test_derive_run_costs_uses_manifest_results_and_coverage(tmp_path):
    results = tmp_path / "results.csv"
    _write_results(
        results,
        [
            {"fixture_id": "one", "passed": "true", "score": "1.000", "unsafe_count": "0", "missed_count": "0"},
            {"fixture_id": "two", "passed": "false", "score": "0.500", "unsafe_count": "0", "missed_count": "1"},
        ],
    )
    coverage = tmp_path / "coverage.json"
    coverage.write_text(
        json.dumps(
            {
                "total_fixtures": 2,
                "total_tools": 4,
                "decided_tools": 4,
                "omitted_tools": 0,
                "duplicate_decision_tools": 0,
                "coverage_rate": 1.0,
                "details": [],
            }
        ),
        encoding="utf-8",
    )
    manifest = {
        "results_path": str(results),
        "coverage_path": str(coverage),
    }

    costs = derive_run_costs(
        manifest,
        pricing_snapshot={"full_node_hourly_meter_usd": 5.990592},
        timing={"billable_seconds": 1800},
        reliability={"friction_cost_usd": 1.25},
        root_path=tmp_path,
        manifest_path=tmp_path / "manifest.json",
    )

    assert costs == {
        "billable_seconds": 1800.0,
        "billable_hours": 0.5,
        "successful_run_cost_usd": 2.995296,
        "friction_cost_usd": 1.25,
        "economic_run_cost_usd": 4.245296,
        "fixture_count": 2,
        "passed_fixture_count": 1,
        "total_tool_count": 4,
        "decided_tool_count": 4,
        "cost_per_fixture_usd": 1.497648,
        "cost_per_passed_fixture_usd": 2.995296,
        "cost_per_covered_tool_decision_usd": 0.748824,
        "cost_per_fully_covered_tool_decision_usd": 0.748824,
        "economic_cost_per_fixture_usd": 2.122648,
        "economic_cost_per_passed_fixture_usd": 4.245296,
        "economic_cost_per_covered_tool_decision_usd": 1.061324,
        "economic_cost_per_fully_covered_tool_decision_usd": 1.061324,
    }


def test_derive_run_costs_can_compute_billable_seconds_from_timestamps(tmp_path):
    results = tmp_path / "results.csv"
    _write_results(
        results,
        [{"fixture_id": "one", "passed": "true", "score": "1.000", "unsafe_count": "0", "missed_count": "0"}],
    )
    manifest = {"results_path": str(results), "coverage_path": None}

    costs = derive_run_costs(
        manifest,
        pricing_snapshot={"full_node_hourly_meter_usd": 10.0},
        timing={
            "create_requested_at": "2026-04-27T12:00:00Z",
            "delete_verified_at": "2026-04-27T12:06:00Z",
        },
        reliability={},
        root_path=tmp_path,
        manifest_path=tmp_path / "manifest.json",
    )

    assert costs["billable_seconds"] == 360.0
    assert costs["successful_run_cost_usd"] == 1.0
    assert costs["cost_per_fully_covered_tool_decision_usd"] is None


def test_annotate_manifest_costs_writes_public_safe_cost_blocks(tmp_path):
    results = tmp_path / "results.csv"
    _write_results(
        results,
        [{"fixture_id": "one", "passed": "true", "score": "1.000", "unsafe_count": "0", "missed_count": "0"}],
    )
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": "agent-infra-security-bench/run-manifest/v1",
                "run_id": "run-costed",
                "created_at": "2026-04-27T12:00:00Z",
                "model": "openai-compatible/Qwen/Qwen2.5-7B-Instruct",
                "policy": "model-decisions; prompt=checklist; runtime=none",
                "trace_adapter": "generic-jsonl",
                "hardware": "tpu-v6e",
                "scenario_count": 1,
                "scenario_commit": "abc1234",
                "results_path": str(results),
                "coverage_path": None,
                "notes": "test",
            }
        ),
        encoding="utf-8",
    )
    output_path = tmp_path / "annotated.json"

    annotate_manifest_costs(
        manifest_path,
        pricing_snapshot={
            "provider": "google-cloud",
            "zone": "europe-west4-a",
            "full_node_hourly_meter_usd": 23.76,
            "pricing_source_url": "https://cloud.google.com/tpu/pricing",
        },
        timing={"billable_seconds": 60},
        reliability={"teardown_verified": True},
        output_path=output_path,
        root_path=tmp_path,
    )

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["pricing_snapshot"]["provider"] == "google-cloud"
    assert payload["timing"]["billable_seconds"] == 60
    assert payload["reliability"]["teardown_verified"] is True
    assert payload["derived_costs"]["successful_run_cost_usd"] == 0.396


def _write_results(path, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "fixture_id",
                "domain",
                "attack_type",
                "passed",
                "score",
                "unsafe_count",
                "missed_count",
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({"domain": "mcp", "attack_type": "tool_shadowing", **row})
