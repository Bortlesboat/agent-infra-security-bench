import json

from agent_infra_security_bench import cli


def test_cli_boundarypay_demo_base_surface_writes_artifacts(tmp_path, capsys):
    output_dir = tmp_path / "boundarypay-base"

    exit_code = cli.main(
        ["boundarypay-demo", str(output_dir), "--mode", "fixture", "--surface", "base"]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["project"] == "BoundaryPay Guard"
    assert payload["mode"] == "fixture"
    assert payload["surface"] == "base"
    assert payload["allowed"] == 1
    assert payload["blocked"] >= 4
    assert (output_dir / "boundarypay-report.json").exists()
    assert (output_dir / "DX-REPORT.md").exists()
