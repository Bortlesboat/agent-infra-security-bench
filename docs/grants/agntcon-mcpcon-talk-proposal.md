# AGNTCon + MCPCon Talk Proposal Draft

## Working Title

Static Tool Risk Labels Are Not Enough: Reproducible Boundary Evals for MCP and Payment-Aware Agents

## Format

Technical session or short talk with live repo walkthrough.

## Abstract

Tool-using agents increasingly cross MCP servers, repositories, payment APIs, browsers, CI systems, and shell-capable developer environments. Many failures do not look like traditional model jailbreaks. They happen when untrusted context crosses into a privileged tool boundary: a poisoned tool description, a malicious tool return, a reused payment proof, or a repository instruction that causes cross-context access.

This talk introduces Agent Infrastructure Security Bench, a small open benchmark for reproducing those boundary failures with public-safe fixtures, deterministic traces, and manifest-backed reports. The first result compares three transparent baselines across 20 fixtures: `naive-allow` passes 0/20, `deny-high-risk` passes 19/20, and `deny-high-risk-payment-state` passes 20/20. The gap is an x402 replay fixture: static tool risk labels catch obvious high-risk categories, but miss protocol-state failures unless the agent runtime validates freshness and request binding. A first local model-backed run with `ollama/qwen2.5:7b` then passes 14/20 with zero unsafe approvals and six over-blocked expected-safe actions, showing the practical safety/utility split.

The session will show the fixture format, scorer, generic trace adapter, policy baselines, and how MCP/runtime builders can contribute scenarios or publish comparable results without sharing secrets.

## Audience

- MCP client/server builders
- agent runtime maintainers
- security and platform engineers building tool approval layers
- eval builders who want reproducible traces and narrow claims boundaries

## Takeaways

- How to separate model behavior from runtime boundary enforcement in an agent eval.
- Why static tool risk labels are useful but insufficient for protocol-state failures.
- A reusable public-safe fixture shape for MCP, repository, payment, browser, CI, and shell boundaries.
- How to publish agent/security results with commit hashes, manifests, adapters, and limitations.

## Demo Outline

1. Show the `x402.replay_payment.basic` fixture.
2. Run `deny-high-risk` and show the 19/20 failure.
3. Run `deny-high-risk-payment-state` and show the 20/20 follow-up result.
4. Show the `ollama/qwen2.5:7b` trace path and the 14/20 safety/utility result.
5. Show the generic JSONL adapter path for model-backed traces.
6. Point contributors to GitHub issues for new fixtures, model comparisons, and TPU smoke manifests.

## Claims Boundary

This is not a claim that any model or runtime is generally safe. The benchmark is a narrow reproducibility harness for boundary failures and runtime controls. The deterministic baselines are control policies, not LLM results.

## Useful Links

- Repo: https://github.com/Bortlesboat/agent-infra-security-bench
- Stateful payment baseline: `docs/reports/2026-04-stateful-payment-baseline.md`
- Ollama model baseline: `docs/reports/2026-04-ollama-qwen25-agent-baseline.md`
- Fixture contribution issue: https://github.com/Bortlesboat/agent-infra-security-bench/issues/4
