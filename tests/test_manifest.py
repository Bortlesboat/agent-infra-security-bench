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
