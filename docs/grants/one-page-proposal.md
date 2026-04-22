# One-Page Proposal Draft

## Title

Agent Infrastructure Security Bench: reproducible evals for self-hosted tool-using AI agents

## Summary

Tool-using AI agents increasingly operate across local files, source repositories, MCP servers, payment APIs, browser automation, and shell commands. Existing benchmarks cover important prompt-injection and cyber tasks, but many practical failures happen at the infrastructure boundary: overly broad tokens, cross-repository data leakage, tool shadowing, replayed payment proofs, and untrusted tool outputs that trigger privileged actions.

This project builds an open-source benchmark and reproducibility workflow for evaluating whether self-hosted agents preserve tool, identity, payment, and repository boundaries under indirect prompt injection and tool poisoning. The first release includes public-safe fixtures, deterministic scoring, synthetic control traces, run manifests, public contribution/security guidance, TPU-backed model/defense sweeps, and a short technical report.

## Public Deliverables

- A permissively licensed benchmark repository.
- At least 20 public-safe fixtures across repository, payment, shell, filesystem, and browser domains.
- Deterministic scorer, trace format, and run-manifest format.
- Public contribution, security, issue-template, citation, and CI surfaces.
- Baseline results across at least two agent policies or open models.
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
2. Week 2: 20 fixtures, synthetic controls, run manifests, CI, and public trust layer. In progress.
3. Week 3: one real-agent baseline, TPU-backed model/defense sweeps, and results table.
4. Week 4: public technical report and grant appendix.
