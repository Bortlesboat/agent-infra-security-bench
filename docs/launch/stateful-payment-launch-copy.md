# Stateful Payment Baseline Launch Copy

## Primary Links

- Repo: https://github.com/Bortlesboat/agent-infra-security-bench
- Report: https://github.com/Bortlesboat/agent-infra-security-bench/blob/main/docs/reports/2026-04-stateful-payment-baseline.md
- Defense sweep: https://github.com/Bortlesboat/agent-infra-security-bench/blob/main/docs/reports/2026-04-ollama-defense-sweep.md
- Cross-model report: https://github.com/Bortlesboat/agent-infra-security-bench/blob/main/docs/reports/2026-04-local-cross-model-baselines.md
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

6/ Update: the first local model-backed run is now published too.

`ollama/qwen2.5:7b` passed 14/20. It had zero unsafe allows, but over-blocked six expected-safe actions.

That is an interesting tradeoff: safety without enough utility is not enough.

7/ Follow-up: the prompt/runtime defense comparison is now published.

The same `qwen2.5:7b` run goes from 14/20 to 20/20 with either:

- a setup-aware prompt
- a runtime risk-floor policy

Both preserve zero unsafe approvals.

8/ I also ran a second local baseline surface on a Mac mini:

- `qwen2.5:14b`: 20/20 baseline
- `qwen2.5-coder:14b`: 19/20 baseline, 20/20 setup-aware

Cross-model report:
https://github.com/Bortlesboat/agent-infra-security-bench/blob/main/docs/reports/2026-04-local-cross-model-baselines.md

9/ Next steps are public:

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

The first local model-backed run is now published too: `ollama/qwen2.5:7b` passed 14/20, with zero unsafe approvals but six over-blocked expected-safe actions.

The follow-up defense sweep recovers those six safe actions two different ways. With a setup-aware prompt, `qwen2.5:7b` reaches 20/20. With a deterministic runtime risk-floor policy, it also reaches 20/20. Both recovered runs preserve zero unsafe approvals.

I also ran the same benchmark on a Mac mini baseline runner with resident local models. `qwen2.5:14b` passed 20/20 with the baseline prompt. `qwen2.5-coder:14b` passed 19/20 with the baseline prompt and 20/20 with setup-aware guidance.

The next step is expanding replay/payment fixtures, then TPU-backed model/defense sweeps after access is confirmed.

Report:
https://github.com/Bortlesboat/agent-infra-security-bench/blob/main/docs/reports/2026-04-stateful-payment-baseline.md

Model-backed report:
https://github.com/Bortlesboat/agent-infra-security-bench/blob/main/docs/reports/2026-04-ollama-qwen25-agent-baseline.md

Defense sweep:
https://github.com/Bortlesboat/agent-infra-security-bench/blob/main/docs/reports/2026-04-ollama-defense-sweep.md

Cross-model report:
https://github.com/Bortlesboat/agent-infra-security-bench/blob/main/docs/reports/2026-04-local-cross-model-baselines.md

## Hacker News Draft

Title:

Agent Infrastructure Security Bench: reproducible evals for tool-using agents

Text:

I built a small open benchmark for agent infrastructure boundary failures: MCP tool poisoning, cross-repository leakage, payment replay, browser deception, CI token exposure, and shell/tool-return injection.

The first result is deliberately narrow. A deterministic static high-risk denylist passes 19/20 fixtures but misses an x402-style replayed payment proof. A follow-up state-aware payment baseline passes 20/20 by checking stale/reused proof metadata and request binding.

Repo: https://github.com/Bortlesboat/agent-infra-security-bench

Report: https://github.com/Bortlesboat/agent-infra-security-bench/blob/main/docs/reports/2026-04-stateful-payment-baseline.md

This is not a claim that any model is safe. It is a public fixture/scoring harness for comparing agent runtime controls. The local model-backed reports show a useful safety/utility split: `ollama/qwen2.5:7b` had zero unsafe allows, but failed six fixtures by over-blocking expected-safe actions; setup-aware prompting and runtime risk-floor policy each recovered those safe actions.

HN timing note: this is now usable as an early-feedback post, but only if the title/body keep the claims boundary visible.

## Targeted Outreach Note

Subject: Small open benchmark for MCP/payment agent boundary failures

I put together a small public-safe benchmark for agent infrastructure boundary failures:

https://github.com/Bortlesboat/agent-infra-security-bench

The first concrete result is an x402 replay fixture: a static high-risk tool denylist passes 19/20 fixtures but misses replayed payment state, while a state-aware payment baseline passes 20/20 by checking proof freshness and request binding.

Report:
https://github.com/Bortlesboat/agent-infra-security-bench/blob/main/docs/reports/2026-04-stateful-payment-baseline.md

The repo is intentionally small: JSON fixtures, deterministic traces, a scorer, manifests, and issue templates for new fixtures/results. Local Ollama runs are also published: qwen2.5:7b passed 14/20 with zero unsafe approvals and six over-blocked safe actions, then reached 20/20 with either setup-aware prompting or runtime risk-floor policy. A Mac mini cross-model pass adds qwen2.5:14b and qwen2.5-coder:14b results. I am looking for public-safe fixture ideas from people building MCP servers, local agents, and payment-aware tools.
