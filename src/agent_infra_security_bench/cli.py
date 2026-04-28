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
from agent_infra_security_bench.coverage_analysis import (
    analyze_suite_coverage,
    write_coverage_artifacts,
    write_coverage_analysis_json,
    write_coverage_analysis_markdown,
)
from agent_infra_security_bench.fixtures import load_fixture
from agent_infra_security_bench.failure_analysis import (
    analyze_suite_failures,
    write_failure_analysis_json,
    write_failure_analysis_markdown,
)
from agent_infra_security_bench.jupiter_guard import JupiterPriceFetchError, write_boundarypay_demo
from agent_infra_security_bench.local_agent import DEFAULT_LOCAL_AGENT, write_local_agent_run
from agent_infra_security_bench.llm_agent import (
    DEFAULT_OPENAI_COMPAT_BASE_URL,
    DEFAULT_OPENAI_COMPAT_MODEL,
    DEFAULT_OLLAMA_HOST,
    DEFAULT_OLLAMA_MODEL,
    PROMPT_PROFILES,
    RUNTIME_POLICIES,
    DEFAULT_NVIDIA_NIM_BASE_URL,
    DEFAULT_NVIDIA_NIM_MODEL,
    write_openai_agent_run,
    write_ollama_agent_run,
    write_nvidia_nim_agent_run,
)
from agent_infra_security_bench.load_probe import (
    ProbeConfig,
    load_prompt,
    parse_concurrency_levels,
    render_probe_markdown,
    resolve_api_key,
    run_probe,
    write_probe_csv,
    write_probe_json,
    write_probe_markdown,
)
from agent_infra_security_bench.manifest import build_manifest, write_manifest
from agent_infra_security_bench.policy_agent import available_policies, write_policy_traces
from agent_infra_security_bench.results import render_csv, render_markdown, score_suite
from agent_infra_security_bench.run_costs import annotate_manifest_costs, load_json_object
from agent_infra_security_bench.scoring import score_trace
from agent_infra_security_bench.sweeps import (
    build_sweep_index,
    render_sweep_markdown,
    write_sweep_index,
)
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

    analyze_parser = subparsers.add_parser(
        "analyze-failures", help="Classify failed expected actions in a scored trace directory"
    )
    analyze_parser.add_argument("scenario_dir", type=Path)
    analyze_parser.add_argument("trace_dir", type=Path)
    analyze_parser.add_argument("--json", type=Path)
    analyze_parser.add_argument("--markdown", type=Path)

    coverage_parser = subparsers.add_parser(
        "analyze-coverage", help="Measure per-tool decision coverage in a trace directory"
    )
    coverage_parser.add_argument("scenario_dir", type=Path)
    coverage_parser.add_argument("trace_dir", type=Path)
    coverage_parser.add_argument("--json", type=Path)
    coverage_parser.add_argument("--markdown", type=Path)

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

    sweep_parser = subparsers.add_parser(
        "write-sweep-index", help="Write a cross-run sweep index from run manifests"
    )
    sweep_parser.add_argument("output", type=Path)
    sweep_parser.add_argument("manifests", nargs="+", type=Path)
    sweep_parser.add_argument("--name", default="BoundaryBench Sweep")
    sweep_parser.add_argument("--markdown", type=Path)
    sweep_parser.add_argument("--root", type=Path)

    cost_parser = subparsers.add_parser(
        "annotate-run-cost", help="Add pricing, timing, reliability, and derived costs to a run manifest"
    )
    cost_parser.add_argument("manifest", type=Path)
    cost_parser.add_argument("--pricing-json", type=Path, required=True)
    cost_parser.add_argument("--timing-json", type=Path, required=True)
    cost_parser.add_argument("--reliability-json", type=Path)
    cost_parser.add_argument("--output", type=Path)
    cost_parser.add_argument("--root", type=Path)

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
    ollama_parser.add_argument("--hardware", default="local")

    openai_parser = subparsers.add_parser(
        "run-openai-agent",
        help="Run an OpenAI-compatible model agent and adapt raw JSONL events",
    )
    openai_parser.add_argument("scenario_dir", type=Path)
    openai_parser.add_argument("output_dir", type=Path)
    openai_parser.add_argument("--model", default=DEFAULT_OPENAI_COMPAT_MODEL)
    openai_parser.add_argument("--base-url", default=DEFAULT_OPENAI_COMPAT_BASE_URL)
    openai_parser.add_argument("--api-key")
    openai_parser.add_argument("--api-key-env")
    openai_parser.add_argument("--env-file", type=Path)
    openai_parser.add_argument("--timeout", type=float, default=120)
    openai_parser.add_argument("--scenario-commit", default="unknown")
    openai_parser.add_argument("--prompt-profile", choices=PROMPT_PROFILES, default="baseline")
    openai_parser.add_argument("--runtime-policy", choices=RUNTIME_POLICIES, default="none")
    openai_parser.add_argument("--hardware", default="hosted")

    probe_parser = subparsers.add_parser(
        "probe-openai-serving",
        help="Measure OpenAI-compatible serving latency and throughput under concurrency",
    )
    probe_parser.add_argument("--base-url", default=DEFAULT_OPENAI_COMPAT_BASE_URL)
    probe_parser.add_argument("--model", default=DEFAULT_OPENAI_COMPAT_MODEL)
    probe_parser.add_argument("--api-key")
    probe_parser.add_argument("--api-key-env")
    probe_parser.add_argument("--prompt")
    probe_parser.add_argument("--prompt-file", type=Path)
    probe_parser.add_argument("--concurrency", default="1,2,4")
    probe_parser.add_argument("--requests-per-level", type=int, default=8)
    probe_parser.add_argument("--max-tokens", type=int, default=64)
    probe_parser.add_argument("--timeout", type=float, default=120)
    probe_parser.add_argument("--label", default="openai-compatible-serving-probe")
    probe_parser.add_argument("--json", type=Path)
    probe_parser.add_argument("--csv", type=Path)
    probe_parser.add_argument("--markdown", type=Path)

    nvidia_parser = subparsers.add_parser(
        "run-nvidia-agent", help="Run a NVIDIA NIM hosted model agent and adapt raw JSONL events"
    )
    nvidia_parser.add_argument("scenario_dir", type=Path)
    nvidia_parser.add_argument("output_dir", type=Path)
    nvidia_parser.add_argument("--model", default=DEFAULT_NVIDIA_NIM_MODEL)
    nvidia_parser.add_argument("--base-url", default=DEFAULT_NVIDIA_NIM_BASE_URL)
    nvidia_parser.add_argument("--env-file", type=Path)
    nvidia_parser.add_argument("--timeout", type=float, default=120)
    nvidia_parser.add_argument("--scenario-commit", default="unknown")
    nvidia_parser.add_argument("--prompt-profile", choices=PROMPT_PROFILES, default="baseline")
    nvidia_parser.add_argument("--runtime-policy", choices=RUNTIME_POLICIES, default="none")
    nvidia_parser.add_argument("--hardware", default="hosted")

    boundarypay_parser = subparsers.add_parser(
        "boundarypay-demo", help="Write BoundaryPay Guard Jupiter/Solana submission artifacts"
    )
    boundarypay_parser.add_argument("output_dir", type=Path)
    boundarypay_parser.add_argument("--mode", choices=["fixture", "live"], default="fixture")
    boundarypay_parser.add_argument("--surface", choices=["jupiter", "base"], default="jupiter")

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
    if args.command == "analyze-failures":
        summary = analyze_suite_failures(args.scenario_dir, args.trace_dir)
        if args.json:
            write_failure_analysis_json(args.json, summary)
        if args.markdown:
            write_failure_analysis_markdown(args.markdown, summary)
        print(json.dumps(summary.to_dict(), indent=2, sort_keys=True))
        return 0
    if args.command == "analyze-coverage":
        summary = analyze_suite_coverage(args.scenario_dir, args.trace_dir)
        if args.json:
            write_coverage_analysis_json(args.json, summary)
        if args.markdown:
            write_coverage_analysis_markdown(args.markdown, summary)
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
    if args.command == "write-sweep-index":
        sweep = build_sweep_index(args.name, args.manifests, root=args.root)
        output = write_sweep_index(args.output, sweep)
        markdown_path = None
        if args.markdown:
            args.markdown.parent.mkdir(parents=True, exist_ok=True)
            args.markdown.write_text(render_sweep_markdown(sweep), encoding="utf-8")
            markdown_path = str(args.markdown)
        print(
            json.dumps(
                {"output": str(output), "markdown": markdown_path, "run_count": sweep.run_count},
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    if args.command == "annotate-run-cost":
        output = annotate_manifest_costs(
            args.manifest,
            pricing_snapshot=load_json_object(args.pricing_json),
            timing=load_json_object(args.timing_json),
            reliability=load_json_object(args.reliability_json) if args.reliability_json else None,
            output_path=args.output,
            root_path=args.root,
        )
        annotated = load_json_object(output)
        derived_costs = annotated["derived_costs"]
        print(
            json.dumps(
                {
                    "manifest": str(output),
                    "successful_run_cost_usd": derived_costs["successful_run_cost_usd"],
                    "economic_run_cost_usd": derived_costs["economic_run_cost_usd"],
                },
                indent=2,
                sort_keys=True,
            )
        )
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
        coverage = write_coverage_artifacts(run_dir, scenario_dir=args.scenario_dir, trace_dir=trace_dir)
        manifest = build_manifest(
            model="deterministic-policy-agent",
            policy=args.policy,
            trace_adapter="policy-agent",
            hardware="local",
            scenario_dir=args.scenario_dir,
            scenario_commit=args.scenario_commit,
            results_path=str(csv_path),
            coverage_path=str(coverage.json_path),
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
            hardware=args.hardware,
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
    if args.command == "run-openai-agent":
        run = write_openai_agent_run(
            args.scenario_dir,
            args.output_dir,
            model=args.model,
            base_url=args.base_url,
            api_key=args.api_key,
            api_key_env=args.api_key_env,
            env_file=args.env_file,
            timeout=args.timeout,
            scenario_commit=args.scenario_commit,
            prompt_profile=args.prompt_profile,
            runtime_policy=args.runtime_policy,
            hardware=args.hardware,
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
    if args.command == "probe-openai-serving":
        report = run_probe(
            ProbeConfig(
                base_url=args.base_url,
                model=args.model,
                prompt=load_prompt(args.prompt, args.prompt_file),
                concurrency_levels=parse_concurrency_levels(args.concurrency),
                requests_per_level=args.requests_per_level,
                max_tokens=args.max_tokens,
                timeout=args.timeout,
                label=args.label,
                api_key=resolve_api_key(args.api_key, args.api_key_env),
            )
        )
        if args.json:
            write_probe_json(args.json, report)
        if args.csv:
            write_probe_csv(args.csv, report)
        if args.markdown:
            write_probe_markdown(args.markdown, report)
        print(render_probe_markdown(report))
        return 0
    if args.command == "run-nvidia-agent":
        run = write_nvidia_nim_agent_run(
            args.scenario_dir,
            args.output_dir,
            model=args.model,
            env_file=args.env_file,
            base_url=args.base_url,
            timeout=args.timeout,
            scenario_commit=args.scenario_commit,
            prompt_profile=args.prompt_profile,
            runtime_policy=args.runtime_policy,
            hardware=args.hardware,
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
        try:
            summary_kwargs = {"mode": args.mode}
            if args.surface != "jupiter":
                summary_kwargs["surface"] = args.surface
            summary = write_boundarypay_demo(args.output_dir, **summary_kwargs)
        except JupiterPriceFetchError as exc:
            print(
                json.dumps(
                    {"error": "jupiter_price_fetch_failed", "message": str(exc)},
                    indent=2,
                    sort_keys=True,
                )
            )
            return 2
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
