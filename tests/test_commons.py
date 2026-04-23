import json
from pathlib import Path

from agent_infra_security_bench.cli import main
from agent_infra_security_bench.commons import load_commons_index


def test_load_commons_index_validates_published_artifact_paths():
    root = Path(__file__).resolve().parents[1]

    index = load_commons_index(root / "commons" / "index.json", root=root)

    assert index.schema_version == "agent-infra-security-bench/compute-commons/v1"
    assert index.name == "BoundaryBench Commons"
    assert len(index.artifacts) >= 5
    assert index.missing_paths == []
    assert {artifact.kind for artifact in index.artifacts} >= {
        "fixture_set",
        "model_sweep",
        "defense_sweep",
    }


def test_validate_commons_cli_prints_machine_readable_summary(capsys):
    root = Path(__file__).resolve().parents[1]

    exit_code = main(["validate-commons", str(root / "commons" / "index.json"), "--root", str(root)])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["schema_version"] == "agent-infra-security-bench/compute-commons/v1"
    assert payload["artifact_count"] >= 5
    assert payload["missing_paths"] == []
