from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from agent_infra_security_bench.fixtures import load_fixture
from agent_infra_security_bench.manifest import build_manifest, write_manifest
from agent_infra_security_bench.results import render_csv, render_markdown, score_suite
from agent_infra_security_bench.scoring import score_trace
from agent_infra_security_bench.synthetic import write_synthetic_traces


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="agent-bench",
        description="Score agent security traces against benchmark fixtures.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    score_parser = subparsers.add_parser("score", help="Score one fixture and trace JSON file")
    score_parser.add_argument("fixture", type=Path)
    score_parser.add_argument("trace", type=Path)

    run_parser = subparsers.add_parser("run", help="Score a scenario directory against trace files")
    run_parser.add_argument("scenario_dir", type=Path)
    run_parser.add_argument("trace_dir", type=Path)
    run_parser.add_argument("--markdown", type=Path)
    run_parser.add_argument("--csv", type=Path)

    generate_parser = subparsers.add_parser(
        "generate-traces", help="Write synthetic pass/fail traces for a scenario directory"
    )
    generate_parser.add_argument("scenario_dir", type=Path)
    generate_parser.add_argument("trace_dir", type=Path)
    generate_parser.add_argument("--mode", choices=["pass", "fail"], default="pass")

    manifest_parser = subparsers.add_parser(
        "write-manifest", help="Write reproducibility metadata for a benchmark run"
    )
    manifest_parser.add_argument("output", type=Path)
    manifest_parser.add_argument("--model", required=True)
    manifest_parser.add_argument("--policy", required=True)
    manifest_parser.add_argument("--trace-adapter", required=True)
    manifest_parser.add_argument("--hardware", required=True)
    manifest_parser.add_argument("--scenario-dir", type=Path, default=Path("scenarios"))
    manifest_parser.add_argument("--scenario-commit", default="unknown")
    manifest_parser.add_argument("--results")
    manifest_parser.add_argument("--notes")

    args = parser.parse_args(argv)
    if args.command == "score":
        fixture = load_fixture(args.fixture)
        with args.trace.open("r", encoding="utf-8") as handle:
            trace = json.load(handle)
        if not isinstance(trace, list):
            raise ValueError("Trace root must be a JSON array")
        result = score_trace(fixture, _trace_actions(trace))
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
        return 0 if result.passed else 2
    if args.command == "run":
        summary = score_suite(args.scenario_dir, args.trace_dir)
        if args.markdown:
            args.markdown.parent.mkdir(parents=True, exist_ok=True)
            args.markdown.write_text(render_markdown(summary), encoding="utf-8")
        if args.csv:
            args.csv.parent.mkdir(parents=True, exist_ok=True)
            args.csv.write_text(render_csv(summary), encoding="utf-8")
        print(json.dumps(summary.to_dict(), indent=2, sort_keys=True))
        return 0
    if args.command == "generate-traces":
        written = write_synthetic_traces(args.scenario_dir, args.trace_dir, mode=args.mode)
        print(
            json.dumps(
                {"mode": args.mode, "written": [str(path) for path in written]},
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    if args.command == "write-manifest":
        manifest = build_manifest(
            model=args.model,
            policy=args.policy,
            trace_adapter=args.trace_adapter,
            hardware=args.hardware,
            scenario_dir=args.scenario_dir,
            scenario_commit=args.scenario_commit,
            results_path=args.results,
            notes=args.notes,
        )
        path = write_manifest(args.output, manifest)
        print(json.dumps({"path": str(path), "run_id": manifest.run_id}, indent=2, sort_keys=True))
        return 0

    return 1


def _trace_actions(trace: list[Any]) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    for item in trace:
        if not isinstance(item, dict):
            raise ValueError("Every trace item must be a JSON object")
        actions.append(item)
    return actions


if __name__ == "__main__":
    raise SystemExit(main())
