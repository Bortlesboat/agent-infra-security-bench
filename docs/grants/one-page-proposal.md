# One-Page Proposal Draft

## Title

Agent Infrastructure Security Bench: reproducible evals for self-hosted tool-using AI agents

## Summary

Tool-using AI agents increasingly operate across local files, source repositories, MCP servers, payment APIs, browser automation, and shell commands. Existing benchmarks cover important prompt-injection and cyber tasks, but many practical failures happen at the infrastructure boundary: overly broad tokens, cross-repository data leakage, tool shadowing, replayed payment proofs, and untrusted tool outputs that trigger privileged actions.

This project builds an open-source benchmark and reproducibility workflow for evaluating whether self-hosted agents preserve tool, identity, payment, and repository boundaries under indirect prompt injection and tool poisoning. The first release includes public-safe fixtures, deterministic scoring, synthetic control traces, run manifests, public contribution/security guidance, TPU-backed model/defense sweeps, and a short technical report.

The current public baseline already shows one concrete control gap: a static high-risk tool denylist passes 19 of 20 fixtures but misses `x402.replay_payment.basic`. A follow-up deterministic baseline, `deny-high-risk-payment-state`, adds narrow payment-state validation and passes 20 of 20 fixtures. The first local model-backed run adds a second signal: `ollama/qwen2.5:7b` passed 14 of 20 fixtures, with zero unsafe approvals but six over-blocked expected-safe actions. A prompt/runtime defense sweep then recovers the full suite two ways: setup-aware prompting reaches 20 of 20, and a deterministic runtime risk-floor policy also reaches 20 of 20, both with zero unsafe approvals. A second local baseline runner on a Mac mini adds cross-model evidence: `qwen2.5:14b` passes 20 of 20 with the baseline prompt, while `qwen2.5-coder:14b` moves from 19 of 20 to 20 of 20 with setup-aware prompting. Together, these results show both sides of practical agent controls: protocol-state validation, safety/utility tradeoffs, and reproducible cross-machine model comparison.

## Public Deliverables

- A permissively licensed benchmark repository.
- At least 20 public-safe fixtures across repository, payment, shell, filesystem, and browser domains.
- Deterministic scorer, trace format, and run-manifest format.
- Public contribution, security, issue-template, citation, and CI surfaces.
- Baseline results across at least three deterministic policies, local prompt/runtime defense configurations, and two local model-runner surfaces.
- Reproducible TPU smoke-run documentation.
- Technical writeup with limitations and next steps.

## Why Now

MCP and similar tool protocols are moving quickly into developer workflows. The security problem is no longer only whether a model can identify malicious text. It is whether the surrounding agent runtime keeps untrusted content from causing privileged tool calls. This benchmark targets that practical control layer.

## Fit

- Safety evaluation and robustness: measures whether agents preserve security boundaries under adversarial tool content.
- Privacy-preserving safety methods: focuses on preventing cross-context and cross-repository leakage.
- Agentic oversight: creates inspectable traces and deterministic scoring for agent action review.
- Open-source public goods: all fixtures, scoring, and runbooks are publishable.

## Near-Term Milestones

1. Week 1: schema, scorer, first four fixtures, TPU setup runbook. Done.
2. Week 2: 20 fixtures, synthetic controls, run manifests, CI, public trust layer, deterministic policy baselines, and stateful payment validation baseline. Done.
3. Week 3: prompt/runtime defense comparison and local cross-model baseline. Done.
4. Week 4: public technical report, conference proposal, and grant appendix.
5. Week 5: external fixture contribution path, expanded x402 replay variants, and TPU smoke manifest after access confirmation.
