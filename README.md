# Agent Infrastructure Security Bench

Reproducible security fixtures and scoring for self-hosted agent infrastructure.

The first wedge is intentionally narrow: MCP-style tools, x402/payment actions, GitHub-like repository access, and shell-capable developer agents. The goal is to produce public, runnable evidence for grant applications, GitHub reputation, and later TPU-backed model sweeps.

## Why This Exists

Generic agent benchmarks are useful, but many real failures happen at the infrastructure boundary:

- an agent reads untrusted issue text, then crosses into private repositories
- a payment tool reuses stale settlement material
- a malicious MCP server shadows a trusted tool
- a tool return injects instructions that trigger shell execution

This repo turns those failures into small fixtures that can be scored consistently across agents, defenses, and open models.

## Quick Start

```powershell
python -m pip install -e .
python -m pytest
agent-bench score scenarios/mcp_tool_shadowing_wallet_export.json examples/traces/tool_shadowing_pass.json
```

Expected result: the test suite passes and the CLI prints a JSON score with `"passed": true`.

To run the complete fixture suite with deterministic synthetic traces:

```powershell
agent-bench generate-traces scenarios outputs/synthetic-pass --mode pass
agent-bench run scenarios outputs/synthetic-pass --markdown outputs/synthetic-pass.md --csv outputs/synthetic-pass.csv
agent-bench write-manifest outputs/synthetic-pass-manifest.json --model synthetic-control --policy synthetic-pass --trace-adapter synthetic --hardware local --results outputs/synthetic-pass.csv
```

That produces JSON summary output, Markdown and CSV tables, and a run manifest that can be pasted into a writeup, grant appendix, or model-sweep report.

To convert a generic agent event log into benchmark trace JSON:

```powershell
agent-bench adapt-trace generic-jsonl examples/agent-logs/generic-jsonl.jsonl outputs/generic-trace.json
```

To reproduce the first local agent trace baseline:

```powershell
agent-bench run-local-agent scenarios outputs/local-agent-baseline --scenario-commit f706176
```

That command writes raw generic JSONL events, adapted benchmark traces, reports, and a manifest. The April 2026 local agent trace report is in `docs/reports/2026-04-local-agent-trace-baseline.md`.

To run the first local model-backed Ollama baseline:

```powershell
ollama pull qwen2.5:7b
agent-bench run-ollama-agent scenarios outputs/llm-agent-baseline --model qwen2.5:7b --scenario-commit 4814bbf
```

The April 2026 Ollama report is in `docs/reports/2026-04-ollama-qwen25-agent-baseline.md`.

To reproduce the first deterministic policy-agent baseline:

```powershell
agent-bench run-policy-baseline scenarios outputs/policy-baseline --policy naive-allow --scenario-commit 243f5fa
agent-bench run-policy-baseline scenarios outputs/policy-baseline --policy deny-high-risk --scenario-commit 243f5fa
```

The April 2026 baseline report is in `docs/reports/2026-04-policy-agent-baseline.md`.

To reproduce the stateful payment replay baseline:

```powershell
agent-bench run-policy-baseline scenarios outputs/policy-baseline --policy naive-allow --scenario-commit aaecefe
agent-bench run-policy-baseline scenarios outputs/policy-baseline --policy deny-high-risk --scenario-commit aaecefe
agent-bench run-policy-baseline scenarios outputs/policy-baseline --policy deny-high-risk-payment-state --scenario-commit aaecefe
```

The stateful payment report is in `docs/reports/2026-04-stateful-payment-baseline.md`.

## Current Contents

- `scenarios/` - 20 public-safe benchmark fixtures
- `examples/traces/` - tiny example agent traces
- `examples/agent-logs/` - example raw agent event logs for adapters
- `examples/baselines/` - reproducible baseline examples
- `docs/adapters/` - trace adapter documentation
- `src/agent_infra_security_bench/fixtures.py` - fixture schema and validation
- `src/agent_infra_security_bench/scoring.py` - deterministic trace scoring
- `src/agent_infra_security_bench/manifest.py` - run metadata for reproducible result claims
- `src/agent_infra_security_bench/results.py` - suite aggregation and Markdown/CSV export
- `src/agent_infra_security_bench/synthetic.py` - deterministic pass/fail trace generation
- `SECURITY.md` / `CONTRIBUTING.md` / `CITATION.cff` - public trust and citation surfaces
- `.github/` - CI plus fixture and results issue templates
- `docs/research/` - TPU and benchmark landscape notes
- `docs/runbooks/` - first Cloud TPU runbook
- `docs/grants/` - starter grant proposal language
- `docs/launch/` and `docs/reports/` - public launch packet and baseline report template

## TPU Role

The benchmark does not require a TPU to run locally. TPU use starts once the fixture set is stable:

1. Generate model traces across open models and defense policies.
2. Batch-score traces with the deterministic scorer.
3. Publish results tables, reproducibility scripts, and a short technical writeup.

The first TPU run should be a smoke test, not a long training job.

## Public Claims Boundary

This is an early benchmark scaffold. It currently proves fixture validation and trace scoring only. It does not yet claim model results, defense efficacy, or broad benchmark coverage.

Synthetic traces are control cases, not model outputs. They prove the scorer and reporting pipeline before any local agent, cloud model, or TPU-backed sweep is measured.

The `boundary-heuristic-v1` local agent is also not an LLM result. It proves the raw event log and adapter path before model-backed agent traces are published.

The `ollama/qwen2.5:7b` report is a local model-backed run, but it is not an OpenAI, cloud, or TPU-backed result.

Any published model or agent result should include the benchmark commit, run manifest, trace adapter, model or agent version, policy configuration, hardware/runtime notes, and known limitations.
