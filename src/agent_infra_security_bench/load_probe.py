from __future__ import annotations

import csv
import json
import math
import os
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


Transport = Callable[[str, str, str, int, float, str | None], dict[str, Any]]


@dataclass(frozen=True)
class ProbeConfig:
    base_url: str
    model: str
    prompt: str
    concurrency_levels: tuple[int, ...]
    requests_per_level: int
    max_tokens: int
    timeout: float
    label: str = "openai-compatible-serving-probe"
    api_key: str | None = None
    additional_prompts: tuple[str, ...] = ()


def parse_concurrency_levels(value: str) -> tuple[int, ...]:
    levels: list[int] = []
    for item in value.split(","):
        item = item.strip()
        if not item:
            continue
        level = int(item)
        if level < 1:
            raise ValueError("Concurrency levels must be positive integers")
        levels.append(level)
    if not levels:
        raise ValueError("At least one concurrency level is required")
    return tuple(levels)


def resolve_api_key(api_key: str | None = None, api_key_env: str | None = None) -> str | None:
    if api_key:
        return api_key
    if api_key_env:
        return os.environ.get(api_key_env)
    return None


def load_prompt(prompt: str | None = None, prompt_file: Path | None = None) -> str:
    if prompt is not None and prompt_file is not None:
        raise ValueError("Pass either prompt or prompt_file, not both")
    if prompt_file is not None:
        return prompt_file.read_text(encoding="utf-8")
    if prompt is not None:
        return prompt
    return "Return one concise sentence about boundary-layer agent safety."


def load_prompts(
    prompt: str | None = None,
    prompt_file: Path | None = None,
    prompt_files: tuple[Path, ...] = (),
) -> tuple[str, ...]:
    sources = sum(1 for item in (prompt, prompt_file) if item is not None)
    if prompt_files:
        sources += 1
    if sources > 1:
        raise ValueError("Pass only one prompt source: prompt, prompt_file, or prompt_files")
    if prompt_files:
        return tuple(path.read_text(encoding="utf-8") for path in prompt_files)
    return (load_prompt(prompt, prompt_file),)


def openai_chat_transport(
    base_url: str,
    model: str,
    prompt: str,
    max_tokens: int,
    timeout: float,
    api_key: str | None,
) -> dict[str, Any]:
    url = f"{base_url.rstrip('/')}/chat/completions"
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": max_tokens,
    }
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    started = time.perf_counter()
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            payload = json.loads(raw) if raw else {}
            usage = payload.get("usage") if isinstance(payload, dict) else None
            if not isinstance(usage, dict):
                usage = {}
            return {
                "ok": True,
                "status": getattr(response, "status", 200),
                "latency_s": time.perf_counter() - started,
                "completion_tokens": _optional_int(usage.get("completion_tokens")),
                "prompt_tokens": _optional_int(usage.get("prompt_tokens")),
                "total_tokens": _optional_int(usage.get("total_tokens")),
                "error": None,
            }
    except urllib.error.HTTPError as exc:
        return {
            "ok": False,
            "status": exc.code,
            "latency_s": time.perf_counter() - started,
            "completion_tokens": None,
            "prompt_tokens": None,
            "total_tokens": None,
            "error": exc.reason,
        }
    except Exception as exc:  # pragma: no cover - exact network failures are platform-specific
        return {
            "ok": False,
            "status": None,
            "latency_s": time.perf_counter() - started,
            "completion_tokens": None,
            "prompt_tokens": None,
            "total_tokens": None,
            "error": str(exc),
        }


def run_probe(config: ProbeConfig, transport: Transport = openai_chat_transport) -> dict[str, Any]:
    started_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    levels: list[dict[str, Any]] = []
    prompts = (config.prompt, *config.additional_prompts)
    prompt_lengths = [len(prompt) for prompt in prompts]

    for concurrency in config.concurrency_levels:
        level_start = time.perf_counter()
        results: list[dict[str, Any]] = []
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = [
                executor.submit(
                    transport,
                    config.base_url,
                    config.model,
                    prompts[index % len(prompts)],
                    config.max_tokens,
                    config.timeout,
                    config.api_key,
                )
                for index in range(config.requests_per_level)
            ]
            for future in as_completed(futures):
                results.append(future.result())
        wall_time_s = time.perf_counter() - level_start
        levels.append(summarize_level(concurrency, wall_time_s, results))

    return {
        "schema_version": "agent-infra-security-bench/openai-serving-probe/v1",
        "label": config.label,
        "created_at": started_at,
        "base_url": config.base_url,
        "model": config.model,
        "max_tokens": config.max_tokens,
        "timeout_s": config.timeout,
        "prompt_chars": len(config.prompt),
        "prompt_count": len(prompts),
        "prompt_chars_min": min(prompt_lengths),
        "prompt_chars_max": max(prompt_lengths),
        "levels": levels,
    }


def summarize_level(concurrency: int, wall_time_s: float, results: list[dict[str, Any]]) -> dict[str, Any]:
    latencies = [float(item["latency_s"]) for item in results if item.get("latency_s") is not None]
    ok_results = [item for item in results if item.get("ok")]
    total_tokens = _sum_optional_ints(item.get("total_tokens") for item in ok_results)
    completion_tokens = _sum_optional_ints(item.get("completion_tokens") for item in ok_results)

    return {
        "concurrency": concurrency,
        "requests": len(results),
        "ok": len(ok_results),
        "failed": len(results) - len(ok_results),
        "wall_time_s": round(wall_time_s, 6),
        "requests_per_second": round(len(results) / wall_time_s, 6) if wall_time_s > 0 else None,
        "ok_requests_per_second": round(len(ok_results) / wall_time_s, 6) if wall_time_s > 0 else None,
        "latency_p50_s": _round_optional(percentile(latencies, 50)),
        "latency_p95_s": _round_optional(percentile(latencies, 95)),
        "latency_max_s": _round_optional(max(latencies) if latencies else None),
        "total_tokens": total_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens_per_second": (
            round(total_tokens / wall_time_s, 6)
            if total_tokens is not None and wall_time_s > 0
            else None
        ),
        "completion_tokens_per_second": (
            round(completion_tokens / wall_time_s, 6)
            if completion_tokens is not None and wall_time_s > 0
            else None
        ),
    }


def percentile(values: list[float], percentile_value: float) -> float | None:
    if not values:
        return None
    if percentile_value < 0 or percentile_value > 100:
        raise ValueError("percentile must be between 0 and 100")
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    rank = (percentile_value / 100) * (len(ordered) - 1)
    low = math.floor(rank)
    high = math.ceil(rank)
    if low == high:
        return ordered[low]
    weight = rank - low
    return ordered[low] * (1 - weight) + ordered[high] * weight


def write_probe_json(path: Path, report: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    return path


def write_probe_csv(path: Path, report: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = list(report["levels"])
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()) if rows else [])
        if rows:
            writer.writeheader()
            writer.writerows(rows)
    return path


def render_probe_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# {report['label']}",
        "",
        f"- Model: `{report['model']}`",
        f"- Base URL: `{report['base_url']}`",
        f"- Prompt chars: `{report['prompt_chars']}`",
        f"- Prompt count: `{report.get('prompt_count', 1)}`",
        f"- Max tokens: `{report['max_tokens']}`",
        "",
        "| Concurrency | Requests | OK | Failed | Req/s | P50 Latency | P95 Latency | Total Tok/s | Completion Tok/s |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for level in report["levels"]:
        lines.append(
            "| {concurrency} | {requests} | {ok} | {failed} | {rps} | {p50} | {p95} | {ttps} | {ctps} |".format(
                concurrency=level["concurrency"],
                requests=level["requests"],
                ok=level["ok"],
                failed=level["failed"],
                rps=_format_optional(level["ok_requests_per_second"]),
                p50=_format_optional(level["latency_p50_s"]),
                p95=_format_optional(level["latency_p95_s"]),
                ttps=_format_optional(level["total_tokens_per_second"]),
                ctps=_format_optional(level["completion_tokens_per_second"]),
            )
        )
    lines.append("")
    return "\n".join(lines)


def write_probe_markdown(path: Path, report: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_probe_markdown(report), encoding="utf-8")
    return path


def _sum_optional_ints(values: Any) -> int | None:
    total = 0
    seen = False
    for value in values:
        if value is None:
            continue
        total += int(value)
        seen = True
    return total if seen else None


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)


def _round_optional(value: float | None) -> float | None:
    return round(value, 6) if value is not None else None


def _format_optional(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)
