import json
from pathlib import Path


def test_frontier_v2_tpu_queues_carry_pricing_snapshots():
    root = Path(__file__).resolve().parents[1]
    queue_paths = sorted((root / "docs" / "runbooks").glob("tpu-frontier-v2-*.json"))

    assert queue_paths
    for queue_path in queue_paths:
        queue = json.loads(queue_path.read_text(encoding="utf-8"))
        for lane in queue["lanes"]:
            pricing = lane.get("pricingSnapshot")
            assert pricing is not None, f"{queue_path.name} lane {lane['name']} missing pricingSnapshot"
            assert pricing["provider"] == "google-cloud"
            assert pricing["pricing_checked_at"] == "2026-04-27"
            assert pricing["pricing_source_url"].startswith("https://cloud.google.com/")
            assert pricing["full_node_hourly_meter_usd"] > 0
            assert pricing["requires_launch_time_refresh"] is True


def test_tpu_strike_script_records_timing_and_annotates_costs():
    root = Path(__file__).resolve().parents[1]
    script = (root / "scripts" / "tpu-strike.ps1").read_text(encoding="utf-8")

    assert "create_requested_at" in script
    assert "delete_verified_at" in script
    assert "pricing.json" in script
    assert "timing.json" in script
    assert "reliability.json" in script
    assert "annotate-run-cost" in script
    assert "[void](Invoke-RunCostAnnotation" in script
    assert "Invoke-TpuGcloudSsh" in script
    assert "--ssh-key-expire-after=2h" in script
    assert "Copy-Item $sourcePublicKey" in script
    assert "uv python install 3.11" in script
    assert "uv venv --python 3.11" in script
    assert "[System.IO.File]::WriteAllText" in script
    assert 'replace "\\r\\n?", "`n"' in script
    assert "New-RemoteWrapperScriptContent" in script
    assert "nohup bash '$RemoteWrapperPath'" in script
    assert "RemotePidPath" in script
    assert "bash -lc" not in script
    assert "pgrep -f" not in script
