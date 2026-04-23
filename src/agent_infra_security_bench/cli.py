from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from agent_infra_security_bench.adapters import (
    convert_generic_events,
    load_generic_events,
    write_trace,
)
from agent_infra_security_bench.candidates import promote_candidate, validate_candidate_dir
from agent_infra_security_bench.commons import load_commons_index
from agent_infra_security_bench.fixtures import load_fixture
from agent_infra_security_bench.jupiter_guard import write_boundarypay_demo
from agent_infra_security_bench.local_agent import DEFAULT_LOCAL_AGENT, write_local_agent_run
from agent_infra_security_bench.llm_agent import (
    DEFAULT_OLLAMA_HOST,
    DEFAULT_OLLAMA_MODEL,
    PROMPT_PROFILES,
    RUNTIME_POLICIES,
    write_ollama_agent_run,
)
from agent_infra_security_bench.manifest import build_manifest, write_manifest
from agent_infra_security_bench.policy_agent import available_policies, write_policy_traces
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

    commons_parser = subparsers.add_parser(
        "validate-commons", help="Validate the public compute commons index"
    )
    commons_parser.add_argument("index", type=Path)
    commons_parser.add_argument("--root", type=Path)

    candidates_parser = subparsers.add_parser(
        "validate-candidates", help="Validate candidate fixtures before curation"
    )
    candidates_parser.add_argument("candidate_dir", type=Path)

    promote_parser = subparsers.add_parser(
        "promote-candidate", help="Promote an accepted candidate into a scenario fixture"
    )
    promote_parser.add_argument("candidate", type=Path)
    promote_parser.add_argument("scenario_dir", type=Path)
    promote_parser.add_argument("--overwrite", action="store_true")

    adapt_parser = subparsers.add_parser(
        "adapt-trace", help="Convert an agent event log into benchmark trace JSON"
    )
    adapt_parser.add_argument("adapter", choices=["generic-jsonl"])
    adapt_parser.add_argument("source", type=Path)
    adapt_parser.add_argument("output", type=Path)

    policy_parser = subparsers.add_parser(
        "run-policy-baseline", help="Run a transparent deterministic policy baseline"
    )
    policy_parser.add_argument("scenario_dir", type=Path)
    policy_parser.add_argument("output_dir", type=Path)
    policy_parser.add_argument("--policy", choices=available_policies(), required=True)
    policy_parser.add_argument("--scenario-commit", default="unknown")

    local_agent_parser = subparsers.add_parser(
        "run-local-agent", help="Run a local heuristic agent and adapt raw JSONL events"
    )
    local_agent_parser.add_argument("scenario_dir", type=Path)
    local_agent_parser.add_argument("output_dir", type=Path)
    local_agent_parser.add_argument("--agent", default=DEFAULT_LOCAL_AGENT)
    local_agent_parser.add_argument("--scenario-commit", default="unknown")

    ollama_parser = subparsers.add_parser(
        "run-ollama-agent", help="Run an Ollama-backed model agent and adapt raw JSONL events"
    )
    ollama_parser.add_argument("scenario_dir", type=Path)
    ollama_parser.add_argument("output_dir", type=Path)
    ollama_parser.add_argument("--model", default=DEFAULT_OLLAMA_MODEL)
    ollama_parser.add_argument("--host", default=DEFAULT_OLLAMA_HOST)
    ollama_parser.add_argument("--scenario-commit", default="unknown")
    ollama_parser.add_argument("--prompt-profile", choices=PROMPT_PROFILES, default="baseline")
    ollama_parser.add_argument("--runtime-policy", choices=RUNTIME_POLICIES, default="none")

    boundarypay_parser = subparsers.add_parser(
        "boundarypay-demo", help="Write BoundaryPay Guard Jupiter/Solana submission artifacts"
    )
    boundarypay_parser.add_argument("output_dir", type=Path)
    boundarypay_parser.add_argument("--mode", choices=["fixture", "live"], default="fixture")

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
    if args.command == "validate-commons":
        index = load_commons_index(args.index, root=args.root)
        print(json.dumps(index.to_summary_dict(), indent=2, sort_keys=True))
        return 0 if not index.missing_paths else 2
    if args.command == "validate-candidates":
        summary = validate_candidate_dir(args.candidate_dir)
        print(json.dumps(summary.to_dict(), indent=2, sort_keys=True))
        return 0 if not summary.invalid_candidates else 2
    if args.command == "promote-candidate":
        output = promote_candidate(args.candidate, args.scenario_dir, overwrite=args.overwrite)
        fixture = load_fixture(output)
        print(
            json.dumps(
                {"fixture_id": fixture.id, "output": str(output)},
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    if args.command == "adapt-trace":
        events = load_generic_events(args.source)
        actions = convert_generic_events(events)
        output = write_trace(args.output, actions)
        print(
            json.dumps(
                {"adapter": args.adapter, "actions": len(actions), "output": str(output)},
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    if args.command == "run-policy-baseline":
        run_dir = args.output_dir / args.policy
        trace_dir = run_dir / "traces"
        write_policy_traces(args.scenario_dir, trace_dir, args.policy)
        summary = score_suite(args.scenario_dir, trace_dir)
        markdown_path = run_dir / "results.md"
        csv_path = run_dir / "results.csv"
        markdown_path.write_text(render_markdown(summary), encoding="utf-8")
        csv_path.write_text(render_csv(summary), encoding="utf-8")
        manifest = build_manifest(
            model="deterministic-policy-agent",
            policy=args.policy,
            trace_adapter="policy-agent",
            hardware="local",
            scenario_dir=args.scenario_dir,
            scenario_commit=args.scenario_commit,
            results_path=str(csv_path),
            notes="Deterministic policy baseline; not an LLM or TPU-backed model result.",
        )
        manifest_path = write_manifest(run_dir / "manifest.json", manifest)
        print(
            json.dumps(
                {
                    "policy": args.policy,
                    "total": summary.total,
                    "passed": summary.passed,
                    "pass_rate": summary.pass_rate,
                    "results": str(csv_path),
                    "manifest": str(manifest_path),
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    if args.command == "run-local-agent":
        run = write_local_agent_run(
            args.scenario_dir,
            args.output_dir,
            agent=args.agent,
            scenario_commit=args.scenario_commit,
        )
        print(
            json.dumps(
                {
                    "agent": run.agent,
                    "total": run.total,
                    "passed": run.passed,
                    "pass_rate": run.pass_rate,
                    "raw_events": str(run.raw_event_dir),
                    "traces": str(run.trace_dir),
                    "results": str(run.results_csv),
                    "manifest": str(run.manifest_path),
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    if args.command == "run-ollama-agent":
        run = write_ollama_agent_run(
            args.scenario_dir,
            args.output_dir,
            model=args.model,
            host=args.host,
            scenario_commit=args.scenario_commit,
            prompt_profile=args.prompt_profile,
            runtime_policy=args.runtime_policy,
        )
        print(
            json.dumps(
                {
                    "agent": run.agent,
                    "total": run.total,
                    "passed": run.passed,
                    "pass_rate": run.pass_rate,
                    "raw_events": str(run.raw_event_dir),
                    "traces": str(run.trace_dir),
                    "results": str(run.results_csv),
                    "manifest": str(run.manifest_path),
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    if args.command == "boundarypay-demo":
        summary = write_boundarypay_demo(args.output_dir, mode=args.mode)
        print(json.dumps(summary, indent=2, sort_keys=True))
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
