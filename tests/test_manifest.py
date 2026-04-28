import json

from agent_infra_security_bench.manifest import RunManifest, count_scenarios, write_manifest


def test_run_manifest_serializes_reproducibility_fields(tmp_path):
    scenario_dir = tmp_path / "scenarios"
    scenario_dir.mkdir()
    (scenario_dir / "one.json").write_text("{}", encoding="utf-8")
    (scenario_dir / "two.json").write_text("{}", encoding="utf-8")

    manifest = RunManifest(
        run_id="local-smoke",
        created_at="2026-04-22T17:30:00Z",
        model="synthetic-control",
        policy="synthetic-pass",
        trace_adapter="synthetic",
        hardware="local",
        scenario_count=count_scenarios(scenario_dir),
        scenario_commit="8e7e33e",
        results_path="outputs/synthetic-pass.csv",
        coverage_path="outputs/synthetic-pass-coverage.json",
        notes="Control run only; not model output.",
    )

    assert manifest.to_dict() == {
        "schema_version": "agent-infra-security-bench/run-manifest/v1",
        "run_id": "local-smoke",
        "created_at": "2026-04-22T17:30:00Z",
        "model": "synthetic-control",
        "policy": "synthetic-pass",
        "trace_adapter": "synthetic",
        "hardware": "local",
        "scenario_count": 2,
        "scenario_commit": "8e7e33e",
        "results_path": "outputs/synthetic-pass.csv",
        "coverage_path": "outputs/synthetic-pass-coverage.json",
        "notes": "Control run only; not model output.",
    }


def test_run_manifest_serializes_optional_cost_metadata():
    manifest = RunManifest(
        run_id="costed-run",
        created_at="2026-04-27T12:00:00Z",
        model="openai-compatible/Qwen/Qwen2.5-7B-Instruct",
        policy="model-decisions; prompt=checklist; runtime=none",
        trace_adapter="generic-jsonl",
        hardware="tpu-v6e",
        scenario_count=9,
        scenario_commit="abc1234-frontier-v2",
        results_path="outputs/tpu/results.csv",
        coverage_path="outputs/tpu/coverage.json",
        notes="Costed TPU row.",
        pricing_snapshot={
            "provider": "google-cloud",
            "zone": "europe-west4-a",
            "provisioning_model": "spot",
            "accelerator_type": "v6e-8",
            "full_node_hourly_meter_usd": 5.990592,
        },
        timing={
            "create_requested_at": "2026-04-27T12:00:00Z",
            "delete_verified_at": "2026-04-27T12:30:00Z",
            "billable_seconds": 1800,
        },
        reliability={"preemption_count": 0, "teardown_verified": True},
        derived_costs={"successful_run_cost_usd": 2.995296, "cost_per_fixture_usd": 0.332811},
    )

    payload = manifest.to_dict()

    assert payload["pricing_snapshot"]["accelerator_type"] == "v6e-8"
    assert payload["timing"]["billable_seconds"] == 1800
    assert payload["reliability"]["teardown_verified"] is True
    assert payload["derived_costs"]["successful_run_cost_usd"] == 2.995296


def test_write_manifest_writes_json(tmp_path):
    output = tmp_path / "manifest.json"
    manifest = RunManifest(
        run_id="smoke",
        created_at="2026-04-22T17:30:00Z",
        model="synthetic-control",
        policy="synthetic-pass",
        trace_adapter="synthetic",
        hardware="local",
        scenario_count=0,
        scenario_commit="unknown",
        results_path=None,
        coverage_path=None,
        notes=None,
    )

    write_manifest(output, manifest)

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["run_id"] == "smoke"
    assert payload["scenario_commit"] == "unknown"
    assert payload["results_path"] is None
    assert payload["coverage_path"] is None
