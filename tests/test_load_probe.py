from __future__ import annotations

from pathlib import Path

from agent_infra_security_bench.load_probe import (
    ProbeConfig,
    parse_concurrency_levels,
    percentile,
    render_probe_markdown,
    run_probe,
    write_probe_csv,
)


def test_parse_concurrency_levels() -> None:
    assert parse_concurrency_levels("1, 2,4") == (1, 2, 4)


def test_percentile_interpolates() -> None:
    assert percentile([1.0, 3.0, 5.0], 50) == 3.0
    assert percentile([1.0, 3.0], 50) == 2.0


def test_run_probe_with_fake_transport() -> None:
    def fake_transport(*_args: object) -> dict[str, object]:
        return {
            "ok": True,
            "status": 200,
            "latency_s": 0.25,
            "completion_tokens": 5,
            "prompt_tokens": 10,
            "total_tokens": 15,
            "error": None,
        }

    report = run_probe(
        ProbeConfig(
            base_url="http://127.0.0.1:8000/v1",
            model="example/model",
            prompt="hello",
            concurrency_levels=(1, 2),
            requests_per_level=3,
            max_tokens=16,
            timeout=5,
        ),
        transport=fake_transport,
    )

    assert report["schema_version"] == "agent-infra-security-bench/openai-serving-probe/v1"
    assert [level["concurrency"] for level in report["levels"]] == [1, 2]
    assert report["levels"][0]["ok"] == 3
    assert report["levels"][0]["total_tokens"] == 45
    assert report["levels"][0]["latency_p95_s"] == 0.25


def test_probe_writers(tmp_path: Path) -> None:
    report = {
        "label": "probe",
        "model": "example/model",
        "base_url": "http://127.0.0.1:8000/v1",
        "prompt_chars": 5,
        "max_tokens": 16,
        "levels": [
            {
                "concurrency": 1,
                "requests": 2,
                "ok": 2,
                "failed": 0,
                "wall_time_s": 1.0,
                "requests_per_second": 2.0,
                "ok_requests_per_second": 2.0,
                "latency_p50_s": 0.4,
                "latency_p95_s": 0.5,
                "latency_max_s": 0.6,
                "total_tokens": 40,
                "completion_tokens": 20,
                "total_tokens_per_second": 40.0,
                "completion_tokens_per_second": 20.0,
            }
        ],
    }
    markdown = render_probe_markdown(report)
    assert "example/model" in markdown
    assert "| 1 | 2 | 2 | 0 |" in markdown

    csv_path = write_probe_csv(tmp_path / "probe.csv", report)
    assert csv_path.read_text(encoding="utf-8").startswith("concurrency,requests")
