# Agent Infrastructure Security Bench

Reproducible security fixtures and scoring for self-hosted agent infrastructure.

The first wedge is intentionally narrow: MCP-style tools, x402/payment actions, GitHub-like repository access, and shell-capable developer agents. The near-term goal is development-first evidence: build a stronger benchmark and defense harness before spending energy on public outreach.

The current frontier agenda is in `docs/roadmap/frontier-research-agenda.md`. Its stated goal is to make this repo the most useful open, reproducible benchmark for stateful agent infrastructure boundary failures: payment proof freshness and replay, repository privilege crossing, MCP tool provenance, CI/shell execution, memory leakage, and runtime policy gaps.

The public-good layer is [BoundaryBench Commons](docs/commons/README.md). It indexes reusable fixtures, traces, reports, and runbooks so people without TPU or multi-machine model access can still use the compute-backed evidence.

## Why This Exists

Generic agent benchmarks are useful, but many real failures happen at the infrastructure boundary:

- an agent reads untrusted issue text, then crosses into private repositories
- a payment tool reuses stale settlement material
- a malicious MCP server shadows a trusted tool
- a tool return injects instructions that trigger shell execution

This repo turns those failures into small fixtures that can be scored consistently across agents, defenses, and open models.

The benchmark now treats three dimensions as first-class:

- safety: unsafe approvals
- utility: missed expected-safe or expected-blocked actions
- completeness: whether the model produced one decision per listed tool

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

To validate model-generated candidate fixtures before human curation:

```powershell
agent-bench validate-candidates candidates
```

After review changes a candidate's status to `accepted`, promote it into the curated suite with:

```powershell
agent-bench promote-candidate candidates/generated/<accepted-candidate>.json scenarios
```

The candidate workflow is documented in `candidates/README.md`.

The first generated-candidate promotion report is in `docs/reports/2026-04-generated-candidate-promotion.md`. It reviews eight quarantined candidates, promotes four into the curated fixture suite, and reruns deterministic baselines on the expanded 34-scenario matrix.

To write one comparable sweep index from run manifests:

```powershell
agent-bench write-sweep-index docs/reports/2026-04-34-fixture-policy-sweep.json `
  outputs/policy-baseline/naive-allow/manifest.json `
  outputs/policy-baseline/deny-high-risk/manifest.json `
  --name "34-Fixture Policy Sweep" `
  --markdown docs/reports/2026-04-34-fixture-policy-sweep.md `
  --root .
```

The first sweep-index report is in `docs/reports/2026-04-34-fixture-policy-sweep.md`.

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

To compare prompt and runtime defenses for the same local model:

```powershell
agent-bench run-ollama-agent scenarios outputs/llm-defense-sweep --model qwen2.5:7b --scenario-commit 9f2b415 --prompt-profile setup-aware --runtime-policy none
agent-bench run-ollama-agent scenarios outputs/llm-defense-sweep --model qwen2.5:7b --scenario-commit 9f2b415 --prompt-profile baseline --runtime-policy risk-floor
```

The April 2026 defense sweep is in `docs/reports/2026-04-ollama-defense-sweep.md`.

The first local cross-model comparison, including Mac mini `qwen2.5:14b` and `qwen2.5-coder:14b` runs, is in `docs/reports/2026-04-local-cross-model-baselines.md`.

To run the first hosted NVIDIA NIM baseline:

```powershell
agent-bench run-nvidia-agent scenarios outputs/nvidia-nim-baseline-34 `
  --env-file <private-env-file-outside-repo> `
  --model nvidia/nemotron-mini-4b-instruct `
  --scenario-commit 25adfc6 `
  --prompt-profile setup-aware `
  --runtime-policy risk-floor
```

The April 2026 hosted NVIDIA NIM report is in `docs/reports/2026-04-nvidia-nim-hosted-baseline.md`. The original setup-aware plus risk-floor hosted row scored `31/34`; the follow-up `checklist` prompt plus the same runtime policy reached `34/34` with full `70/70` tool-decision coverage. Keep `NVIDIA_API_KEY` in a private env file or shell environment; do not commit provider credentials.

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

The original stateful payment report is in `docs/reports/2026-04-stateful-payment-baseline.md`. The expanded x402 payment-state matrix is in `docs/reports/2026-04-x402-payment-state-matrix.md`.

To reproduce the provenance-state matrix:

```powershell
agent-bench run-policy-baseline scenarios outputs/policy-baseline --policy naive-allow --scenario-commit 96eb9f2
agent-bench run-policy-baseline scenarios outputs/policy-baseline --policy deny-high-risk --scenario-commit 96eb9f2
agent-bench run-policy-baseline scenarios outputs/policy-baseline --policy deny-high-risk-payment-state --scenario-commit 96eb9f2
agent-bench run-policy-baseline scenarios outputs/policy-baseline --policy deny-high-risk-stateful --scenario-commit 96eb9f2
```

The April 2026 provenance-state report is in `docs/reports/2026-04-provenance-state-matrix.md`.

To reproduce the generated-candidate promotion matrix:

```powershell
agent-bench validate-candidates candidates
agent-bench run-policy-baseline scenarios outputs/policy-baseline --policy naive-allow --scenario-commit e93f579
agent-bench run-policy-baseline scenarios outputs/policy-baseline --policy deny-high-risk --scenario-commit e93f579
agent-bench run-policy-baseline scenarios outputs/policy-baseline --policy deny-high-risk-payment-state --scenario-commit e93f579
agent-bench run-policy-baseline scenarios outputs/policy-baseline --policy deny-high-risk-stateful --scenario-commit e93f579
```

The April 2026 generated-candidate promotion report is in `docs/reports/2026-04-generated-candidate-promotion.md`.

The 34-fixture policy sweep index is in `docs/reports/2026-04-34-fixture-policy-sweep.md`, with machine-readable JSON at `docs/reports/2026-04-34-fixture-policy-sweep.json`.

The first 34-fixture cross-machine model sweep is in `docs/reports/2026-04-34-fixture-cross-machine-model-sweep.md`. It compares deterministic policy baselines against Windows `ollama/qwen2.5:7b`, Mac mini `ollama/qwen2.5-coder:14b`, and Mac mini `ollama/gemma3:12b` runs, including the new `checklist` prompt profile that lifts Gemma to `34/34`.

To classify failed expected actions by cause:

```powershell
agent-bench analyze-failures scenarios outputs/34-model-sweep/ollama-gemma3-12b-prompt-setup-aware-runtime-risk-floor/traces --markdown outputs/gemma-failure-analysis.md --json outputs/gemma-failure-analysis.json
```

The Gemma defended miss analysis is in `docs/reports/2026-04-gemma-defended-miss-analysis.md`. It shows the remaining `gemma3:12b` setup-aware defended failures were omitted safe decisions, not unsafe approvals; the follow-up `exhaustive` prompt improved Gemma to `33/34`.

To measure whether a run produced one decision per listed tool:

```powershell
agent-bench analyze-coverage scenarios outputs/34-model-sweep/ollama-gemma3-12b-prompt-checklist-runtime-risk-floor/traces --markdown outputs/gemma-coverage.md --json outputs/gemma-coverage.json
```

The first tool-decision coverage report is in `docs/reports/2026-04-gemma-checklist-coverage-analysis.md`. It shows the Mac mini `gemma3:12b` checklist run reached `70/70` decided tools with zero omissions and zero duplicate tool decisions.

The sweep surfaces also now include coverage directly. The 34-fixture policy sweep and cross-machine sweep both show pass/fail plus coverage, omitted-tool count, and duplicate-decision count so “model missed the task” and “model skipped the tool” are no longer blurred together.

To validate the public compute commons index:

```powershell
agent-bench validate-commons commons/index.json --root .
```

Expected result: the command prints a JSON summary with zero missing paths.

To write the first BoundaryPay Guard submission artifact for Jupiter/Solana-aligned hackathons and bounties:

```powershell
agent-bench boundarypay-demo outputs/boundarypay-guard --mode fixture
agent-bench boundarypay-demo outputs/boundarypay-guard-live --mode live
```

That writes a public-safe demo report, trace, reviewer README, and DX-report scaffold. The demo is documented in `docs/demos/boundarypay-guard/README.md`.

## Current Contents

- `scenarios/` - 34 public-safe benchmark fixtures
- `candidates/` - quarantined generated fixture proposals plus the review/promotion gate
- `examples/traces/` - tiny example agent traces
- `examples/agent-logs/` - example raw agent event logs for adapters
- `examples/baselines/` - reproducible baseline examples
- `docs/adapters/` - trace adapter documentation
- `docs/commons/` and `commons/index.json` - public compute commons docs and machine-readable artifact index
- `src/agent_infra_security_bench/fixtures.py` - fixture schema and validation
- `src/agent_infra_security_bench/scoring.py` - deterministic trace scoring
- `src/agent_infra_security_bench/failure_analysis.py` - failure classification for omitted decisions, unsafe approvals, and wrong blocks
- `src/agent_infra_security_bench/coverage_analysis.py` - per-tool decision coverage analysis for omitted and duplicate tool decisions
- `src/agent_infra_security_bench/manifest.py` - run metadata for reproducible result claims
- `src/agent_infra_security_bench/sweeps.py` - cross-run sweep indexes for comparing models, policies, prompts, runtimes, hardware, and adapters
- `src/agent_infra_security_bench/results.py` - suite aggregation and Markdown/CSV export
- `src/agent_infra_security_bench/synthetic.py` - deterministic pass/fail trace generation
- `SECURITY.md` / `CONTRIBUTING.md` / `CITATION.cff` - public trust and citation surfaces
- `.github/` - CI plus fixture and results issue templates
- `docs/research/` - TPU and benchmark landscape notes
- `docs/roadmap/` - development-first research agenda and milestone plan
- `docs/demos/` - submission-ready public demos such as BoundaryPay Guard
- `docs/runbooks/` - first Cloud TPU runbook
- `docs/grants/` - starter grant proposal language
- `docs/launch/` and `docs/reports/` - public launch packet and baseline report template

## TPU Role

The benchmark does not require a TPU to run locally. Accelerator use should scale evidence, not distract from the benchmark:

1. Use the Mac mini and local GPU box for fast model baselines, cross-machine reproducibility, and candidate fixture generation.
2. Use TPU Research Cloud only after confirmation arrives, starting with a smoke run and then batch model/defense sweeps.
3. Keep outputs hardware-neutral: raw JSONL traces, deterministic scores, result tables, and run manifests.
4. Publish a technical report only after the fixture suite and sweep surface are strong enough.

The first TPU run should be a smoke test, not a long training job.

## Public Claims Boundary

This is an early benchmark scaffold. It currently proves fixture validation, trace scoring, candidate review/promotion, and sweep-index reporting. It does not yet claim broad benchmark coverage.

Synthetic traces are control cases, not model outputs. They prove the scorer and reporting pipeline before any local agent, cloud model, or TPU-backed sweep is measured.

The `boundary-heuristic-v1` local agent is also not an LLM result. It proves the raw event log and adapter path before model-backed agent traces are published.

The `ollama/qwen2.5:7b` report is a local model-backed run, but it is not an OpenAI, cloud, or TPU-backed result.

Any published model or agent result should include the benchmark commit, run manifest, trace adapter, model or agent version, policy configuration, hardware/runtime notes, and known limitations.
