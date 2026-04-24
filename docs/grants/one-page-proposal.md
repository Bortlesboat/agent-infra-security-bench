# One-Page Proposal Draft

## Title

Agent Infrastructure Security Bench: reproducible frontier evidence for self-hosted tool-using AI agents

## Summary

Tool-using AI agents increasingly operate across local files, source repositories, MCP servers, payment APIs, browser automation, CI artifacts, memory surfaces, and shell-capable workflows. Existing benchmarks cover important prompt-injection and cyber tasks, but many practical failures still happen at the infrastructure boundary: cross-repository data leakage, MCP provenance drift, replayed payment proofs, stateful workflow continuation errors, omitted tool decisions, and untrusted tool outputs that trigger privileged actions.

This project builds an open-source benchmark and reproducibility workflow for evaluating whether self-hosted agents preserve those boundaries under indirect prompt injection, tool poisoning, and approval-bound workflow pressure. The current public surface includes a stable `34`-fixture control suite, a harder `7`-fixture frontier pack, deterministic policy controls, explicit tool-decision coverage analysis, run manifests, public contribution/security guidance, BoundaryBench Commons for reuse, and local, Mac mini, hosted, and TPU-backed model and defense sweeps.

The most useful current result is not just that we have more rows. It is that the benchmark now separates **safety**, **utility**, and **completeness** on the same fixed frontier pack. The frontier controls show why state matters: `deny-high-risk-payment-state` passes only `1/7`, while `deny-high-risk-stateful` passes `7/7`. The TPU matrix then shows that different open model families need different defense mixes to close the same pack. `Qwen 7B` mainly needed a structured checklist prompt to move from `4/7` to `7/7`; `Mistral 7B` improved from `2/7` to `5/7` with the same checklist but still needed a runtime risk floor to reach `7/7`; `Qwen 14B` was the strongest weak-prompt row at `5/7`, but surfaced unsafe approvals until the runtime layer was restored. Together, these rows make a stronger public-good contribution than a simple score leaderboard: they show how boundary-layer failures change shape across model families, prompting regimes, and runtime defenses.

## Public Deliverables

- A permissively licensed benchmark repository.
- A stable `34`-fixture control suite plus a separate `7`-fixture frontier pack.
- Deterministic scorer, trace format, coverage analysis, sweep-index format, and run-manifest format.
- Public contribution, security, issue-template, citation, CI, and Commons surfaces.
- Baseline and defended results across deterministic policies plus local, Mac mini, hosted, and TPU-backed model surfaces.
- Reproducible TPU provisioning, serving, artifact copy-back, and shutdown documentation.
- A higher-layer synthesis that explains the benchmark's safety, utility, and completeness thesis.

## Why Now

MCP and similar tool protocols are moving quickly into developer workflows. The practical security problem is no longer only whether a model can identify malicious text. It is whether the surrounding runtime keeps untrusted content from causing privileged tool calls, stale approval reuse, provenance drift, and incomplete decision-making under pressure. This benchmark targets that practical control layer.

## Fit

- Safety evaluation and robustness: measures whether agents preserve security boundaries under adversarial tool content.
- Privacy-preserving safety methods: focuses on preventing cross-context and cross-repository leakage.
- Agentic oversight: creates inspectable traces and deterministic scoring for agent action review.
- Open-source public goods: all fixtures, scoring, and runbooks are publishable.

## Near-Term Milestones

1. Keep the `34`-fixture control row and `7`-fixture frontier pack stable long enough to support reuse and external comparison.
2. Add new frontier fixtures only when they introduce a genuinely new failure thesis, not just more difficulty.
3. Expand public-safe contributor and grant surfaces around the frontier synthesis, fixed-pack sweep, and Commons artifacts.
4. Use the remaining TPU window only for sharp unanswered questions, not general model collection.
5. Publish one tighter outward-facing package that makes the benchmark's safety/utility/completeness thesis easy to cite and reuse.
