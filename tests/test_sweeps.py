import csv
import json

from agent_infra_security_bench.sweeps import build_sweep_index, render_sweep_markdown


def test_build_sweep_index_summarizes_manifest_results(tmp_path):
    results = tmp_path / "results.csv"
    _write_results(
        results,
        [
            {"fixture_id": "one", "passed": "true", "score": "1.000", "unsafe_count": "0", "missed_count": "0"},
            {"fixture_id": "two", "passed": "false", "score": "0.500", "unsafe_count": "1", "missed_count": "0"},
        ],
    )
    manifest = tmp_path / "manifest.json"
    coverage = tmp_path / "coverage.json"
    coverage.write_text(
        json.dumps(
            {
                "total_fixtures": 2,
                "total_tools": 4,
                "decided_tools": 3,
                "omitted_tools": 1,
                "duplicate_decision_tools": 0,
                "coverage_rate": 0.75,
                "details": [],
            }
        ),
        encoding="utf-8",
    )
    manifest.write_text(
        json.dumps(
            {
                "schema_version": "agent-infra-security-bench/run-manifest/v1",
                "run_id": "run-demo",
                "created_at": "2026-04-23T05:00:00Z",
                "model": "ollama/qwen2.5:7b",
                "policy": "model-decisions; prompt=setup-aware; runtime=risk-floor",
                "trace_adapter": "generic-jsonl",
                "hardware": "mac-mini",
                "scenario_count": 2,
                "scenario_commit": "abc1234",
                "results_path": str(results),
                "coverage_path": str(coverage),
                "notes": "Prompt profile: setup-aware. Runtime policy: risk-floor.",
            }
        ),
        encoding="utf-8",
    )

    sweep = build_sweep_index("Local sweep", [manifest], root=tmp_path)

    assert sweep.to_dict()["schema_version"] == "agent-infra-security-bench/sweep-index/v1"
    assert sweep.name == "Local sweep"
    assert sweep.run_count == 1
    row = sweep.runs[0]
    assert row.model == "ollama/qwen2.5:7b"
    assert row.prompt_profile == "setup-aware"
    assert row.runtime_policy == "risk-floor"
    assert row.passed == 1
    assert row.total == 2
    assert row.pass_rate == 0.5
    assert row.average_score == 0.75
    assert row.unsafe_count == 1
    assert row.missed_count == 0
    assert row.coverage_rate == 0.75
    assert row.total_tools == 4
    assert row.decided_tools == 3
    assert row.omitted_tools == 1
    assert row.duplicate_decision_tools == 0


def test_render_sweep_markdown_lists_comparable_runs(tmp_path):
    first_results = tmp_path / "first.csv"
    second_results = tmp_path / "second.csv"
    _write_results(
        first_results,
        [{"fixture_id": "one", "passed": "true", "score": "1.000", "unsafe_count": "0", "missed_count": "0"}],
    )
    _write_results(
        second_results,
        [{"fixture_id": "one", "passed": "false", "score": "0.500", "unsafe_count": "1", "missed_count": "0"}],
    )
    manifests = [
        _write_manifest(tmp_path / "first.json", "run-one", "policy-one", first_results),
        _write_manifest(tmp_path / "second.json", "run-two", "policy-two", second_results),
    ]

    markdown = render_sweep_markdown(build_sweep_index("Policy ladder", manifests, root=tmp_path))

    assert "# Policy ladder" in markdown
    assert "| Run | Model | Policy | Prompt | Runtime | Hardware | Commit | Passed | Pass Rate | Avg Score | Unsafe | Missed | Coverage | Omitted | Duplicates |" in markdown
    assert "| run-one | deterministic-policy-agent | policy-one | n/a | n/a | local | abc1234 | 1/1 | 1.000 | 1.000 | 0 | 0 | n/a | n/a | n/a |" in markdown
    assert "| run-two | deterministic-policy-agent | policy-two | n/a | n/a | local | abc1234 | 0/1 | 0.000 | 0.500 | 1 | 0 | n/a | n/a | n/a |" in markdown


def test_build_sweep_index_accepts_utf8_sig_manifest(tmp_path):
    results = tmp_path / "results.csv"
    _write_results(
        results,
        [{"fixture_id": "one", "passed": "true", "score": "1.000", "unsafe_count": "0", "missed_count": "0"}],
    )
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "schema_version": "agent-infra-security-bench/run-manifest/v1",
                "run_id": "run-bom",
                "created_at": "2026-04-23T05:00:00Z",
                "model": "ollama/qwen2.5-coder:14b",
                "policy": "model-decisions",
                "trace_adapter": "generic-jsonl",
                "hardware": "mac-mini",
                "scenario_count": 1,
                "scenario_commit": "abc1234",
                "results_path": str(results),
                "notes": "edited on Windows",
            }
        ),
        encoding="utf-8-sig",
    )

    sweep = build_sweep_index("BOM sweep", [manifest], root=tmp_path)

    assert sweep.runs[0].run_id == "run-bom"


def test_build_sweep_index_uses_sibling_coverage_file_when_manifest_omits_path(tmp_path):
    results = tmp_path / "results.csv"
    _write_results(
        results,
        [{"fixture_id": "one", "passed": "true", "score": "1.000", "unsafe_count": "0", "missed_count": "0"}],
    )
    coverage = tmp_path / "coverage.json"
    coverage.write_text(
        json.dumps(
            {
                "total_fixtures": 1,
                "total_tools": 2,
                "decided_tools": 2,
                "omitted_tools": 0,
                "duplicate_decision_tools": 0,
                "coverage_rate": 1.0,
                "details": [],
            }
        ),
        encoding="utf-8",
    )
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "schema_version": "agent-infra-security-bench/run-manifest/v1",
                "run_id": "run-sibling",
                "created_at": "2026-04-23T05:00:00Z",
                "model": "ollama/gemma3:12b",
                "policy": "model-decisions; prompt=checklist; runtime=risk-floor",
                "trace_adapter": "generic-jsonl",
                "hardware": "mac-mini",
                "scenario_count": 1,
                "scenario_commit": "abc1234",
                "results_path": str(results),
                "notes": "coverage lives beside results",
            }
        ),
        encoding="utf-8",
    )

    sweep = build_sweep_index("Sibling coverage", [manifest], root=tmp_path)

    assert sweep.runs[0].coverage_rate == 1.0
    assert sweep.runs[0].total_tools == 2


def test_sweep_index_surfaces_cost_fields_when_manifest_has_derived_costs(tmp_path):
    results = tmp_path / "results.csv"
    _write_results(
        results,
        [{"fixture_id": "one", "passed": "true", "score": "1.000", "unsafe_count": "0", "missed_count": "0"}],
    )
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
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
                "derived_costs": {
                    "billable_hours": 0.5,
                    "successful_run_cost_usd": 2.546,
                    "economic_run_cost_usd": 3.796,
                    "cost_per_fixture_usd": 2.546,
                    "cost_per_passed_fixture_usd": 2.546,
                    "cost_per_covered_tool_decision_usd": None,
                },
                "notes": "costed",
            }
        ),
        encoding="utf-8",
    )

    sweep = build_sweep_index("Cost sweep", [manifest], root=tmp_path)
    markdown = render_sweep_markdown(sweep)

    row = sweep.to_dict()["runs"][0]
    assert row["billable_hours"] == 0.5
    assert row["successful_run_cost_usd"] == 2.546
    assert row["economic_run_cost_usd"] == 3.796
    assert "| Billable Hours | Run Cost | Economic Cost | $/Fixture | $/Pass | $/Covered Tool |" in markdown
    assert "| run-costed | 0.500 | 2.546 | 3.796 | 2.546 | 2.546 | n/a |" in markdown


def _write_manifest(path, run_id, policy, results_path):
    path.write_text(
        json.dumps(
            {
                "schema_version": "agent-infra-security-bench/run-manifest/v1",
                "run_id": run_id,
                "created_at": "2026-04-23T05:00:00Z",
                "model": "deterministic-policy-agent",
                "policy": policy,
                "trace_adapter": "policy-agent",
                "hardware": "local",
                "scenario_count": 1,
                "scenario_commit": "abc1234",
                "results_path": str(results_path),
                "coverage_path": None,
                "notes": "test",
            }
        ),
        encoding="utf-8",
    )
    return path


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
            payload = {
                "domain": "mcp",
                "attack_type": "tool_shadowing",
                **row,
            }
            writer.writerow(payload)
