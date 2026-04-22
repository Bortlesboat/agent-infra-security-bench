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

## Current Contents

- `scenarios/` - public-safe benchmark fixtures
- `examples/traces/` - tiny example agent traces
- `src/agent_infra_security_bench/fixtures.py` - fixture schema and validation
- `src/agent_infra_security_bench/scoring.py` - deterministic trace scoring
- `docs/research/` - TPU and benchmark landscape notes
- `docs/runbooks/` - first Cloud TPU runbook
- `docs/grants/` - starter grant proposal language

## TPU Role

The benchmark does not require a TPU to run locally. TPU use starts once the fixture set is stable:

1. Generate model traces across open models and defense policies.
2. Batch-score traces with the deterministic scorer.
3. Publish results tables, reproducibility scripts, and a short technical writeup.

The first TPU run should be a smoke test, not a long training job.

## Public Claims Boundary

This is an early benchmark scaffold. It currently proves fixture validation and trace scoring only. It does not yet claim model results, defense efficacy, or broad benchmark coverage.
