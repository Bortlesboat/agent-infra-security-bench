# Stateful Payment Baseline Launch Copy

## Primary Links

- Repo: https://github.com/Bortlesboat/agent-infra-security-bench
- Report: https://github.com/Bortlesboat/agent-infra-security-bench/blob/main/docs/reports/2026-04-stateful-payment-baseline.md
- Fixture contribution issue: https://github.com/Bortlesboat/agent-infra-security-bench/issues/4

## X Thread Draft

1/ I published a small open benchmark for a failure mode I keep seeing in agent infrastructure:

untrusted context crossing into privileged tools.

Repo: https://github.com/Bortlesboat/agent-infra-security-bench

2/ The first suite has 20 public-safe fixtures across MCP, repository access, payments, browser automation, CI, memory, and shell/tool-return boundaries.

It is intentionally narrow: fixtures, traces, scorer, manifests, and reports.

3/ The first useful finding is around x402-style payment replay.

A static high-risk tool denylist passes 19/20 fixtures, but misses the replay case because the unsafe action is not "exfiltration" or "code execution." It is stale payment state.

4/ A follow-up baseline adds payment-state validation:

- proof freshness
- reused/stale nonce signals
- request/proof binding

That moves the deterministic baseline from 19/20 to 20/20.

Report: https://github.com/Bortlesboat/agent-infra-security-bench/blob/main/docs/reports/2026-04-stateful-payment-baseline.md

5/ The claim is deliberately modest:

static tool-risk labels help, but they are not enough for protocol-state failures.

Payment-aware agents need stateful validation, not only category blocking.

6/ Next steps are public:

- first real-agent trace
- more x402 replay fixtures
- TPU smoke manifest after access confirmation
- public-safe fixture contributions

Issues: https://github.com/Bortlesboat/agent-infra-security-bench/issues

## LinkedIn Draft

I published a small open benchmark for agent infrastructure security:

https://github.com/Bortlesboat/agent-infra-security-bench

The target is not broad "model safety." It is a narrower runtime question: when an agent reads untrusted content, does the surrounding infrastructure preserve boundaries around repositories, MCP tools, payment proofs, browser state, CI tokens, and shell-capable developer actions?

The first concrete result is about x402-style payment replay.

Across 20 public-safe fixtures:

- `naive-allow`: 0/20
- `deny-high-risk`: 19/20
- `deny-high-risk-payment-state`: 20/20

The interesting gap is that a static high-risk tool denylist catches obvious dangerous categories, but misses a replayed payment proof. The unsafe condition is not the generic tool label. It is protocol state: proof freshness, nonce reuse, and request binding.

That is the point of the benchmark: make these boundary failures small, public-safe, reproducible, and reportable with explicit claims boundaries.

The next step is a real-agent trace against the suite, then TPU-backed model/defense sweeps after access is confirmed.

Report:
https://github.com/Bortlesboat/agent-infra-security-bench/blob/main/docs/reports/2026-04-stateful-payment-baseline.md

## Hacker News Draft

Title:

Agent Infrastructure Security Bench: reproducible evals for tool-using agents

Text:

I built a small open benchmark for agent infrastructure boundary failures: MCP tool poisoning, cross-repository leakage, payment replay, browser deception, CI token exposure, and shell/tool-return injection.

The first result is deliberately narrow. A deterministic static high-risk denylist passes 19/20 fixtures but misses an x402-style replayed payment proof. A follow-up state-aware payment baseline passes 20/20 by checking stale/reused proof metadata and request binding.

Repo: https://github.com/Bortlesboat/agent-infra-security-bench

Report: https://github.com/Bortlesboat/agent-infra-security-bench/blob/main/docs/reports/2026-04-stateful-payment-baseline.md

This is not a claim that any model is safe. It is a public fixture/scoring harness for comparing agent runtime controls. Next step is a first real-agent trace report.

HN timing note: use this after the first real-agent trace exists, unless the goal is early feedback from security/evals builders.

## Targeted Outreach Note

Subject: Small open benchmark for MCP/payment agent boundary failures

I put together a small public-safe benchmark for agent infrastructure boundary failures:

https://github.com/Bortlesboat/agent-infra-security-bench

The first concrete result is an x402 replay fixture: a static high-risk tool denylist passes 19/20 fixtures but misses replayed payment state, while a state-aware payment baseline passes 20/20 by checking proof freshness and request binding.

Report:
https://github.com/Bortlesboat/agent-infra-security-bench/blob/main/docs/reports/2026-04-stateful-payment-baseline.md

The repo is intentionally small: JSON fixtures, deterministic traces, a scorer, manifests, and issue templates for new fixtures/results. I am looking for public-safe fixture ideas from people building MCP servers, local agents, and payment-aware tools.
