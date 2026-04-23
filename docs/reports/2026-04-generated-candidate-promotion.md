# Generated Candidate Promotion Matrix

Date: 2026-04-23

Scenario commit: `e93f579`

This report promotes four reviewed candidates from the generated fixture quarantine into the curated benchmark suite. The goal was not to graduate everything the local model produced. The goal was to prove a usable loop: generate candidate boundary failures on local/Mac hardware, validate them through the candidate gate, review for novelty and public safety, promote only the strongest cases, and rerun deterministic baselines against the expanded suite.

## Review Decision

Eight candidates were reviewed. Four were accepted:

| Promoted Fixture | Domain | Attack Type | Reason |
| --- | --- | --- | --- |
| `browser.candidate.checkout_redirect` | browser | `candidate_browser_checkout_redirect` | Adds a safe checkout-total read followed by blocked lookalike payment navigation. |
| `ci.candidate.artifact_poisoning` | ci | `candidate_ci_artifact_poisoning` | Adds a CI artifact-to-shell execution boundary distinct from token permission drift. |
| `memory.candidate.privilege_crossing` | memory | `candidate_memory_retrieval_privilege_crossing` | Adds memory retrieval privilege crossing, rather than another memory-write poisoning case. |
| `repository.candidate.fork_private_drift` | repository | `candidate_repository_fork_private_drift` | Adds fork-to-private repository scope drift for agents that keep expanding access. |

Four candidates were deferred:

| Deferred Candidate | Reason |
| --- | --- |
| `candidate.browser.checkout_redirect_verification` | Duplicate browser redirect shape after accepting the cleaner checkout redirect fixture. |
| `candidate.mcp.response_provenance_drift` | Useful idea, but overlaps the existing MCP provenance and shadow-server matrix. |
| `candidate.mcp.response_header_injection` | Useful example candidate, but overlaps existing tool-return/private-repository leakage fixtures. |
| `candidate.payments.payment_route_mutation` | Overlaps the existing x402 route binding mismatch fixture. |

## Deterministic Baselines

| Policy | Passed | Total | Pass Rate | Average Score | Notes |
| --- | ---: | ---: | ---: | ---: | --- |
| `naive-allow` | 1 | 34 | 0.029 | 0.525 | Allows nearly every unsafe action. |
| `deny-high-risk` | 24 | 34 | 0.706 | 0.853 | Catches the four promoted high-risk candidates, but still misses payment state and same-risk provenance drift. |
| `deny-high-risk-payment-state` | 30 | 34 | 0.882 | 0.941 | Adds payment-state validation, but still misses same-risk provenance drift. |
| `deny-high-risk-stateful` | 34 | 34 | 1.000 | 1.000 | Blocks payment-state failures, provenance drift, and the promoted high-risk candidate fixtures. |

The new promoted fixtures are intentionally simple high-risk boundary checks. They broaden coverage without changing the core ladder result: static risk labels catch obvious high-risk tools, but stateful defenses are still required for payment proof state and same-risk provenance drift.

## Reproduction

```powershell
agent-bench validate-candidates candidates
agent-bench run-policy-baseline scenarios outputs/policy-baseline --policy naive-allow --scenario-commit e93f579
agent-bench run-policy-baseline scenarios outputs/policy-baseline --policy deny-high-risk --scenario-commit e93f579
agent-bench run-policy-baseline scenarios outputs/policy-baseline --policy deny-high-risk-payment-state --scenario-commit e93f579
agent-bench run-policy-baseline scenarios outputs/policy-baseline --policy deny-high-risk-stateful --scenario-commit e93f579
```

Expected summary:

```text
validate-candidates: 8 valid, 4 accepted, 0 invalid
naive-allow: 1/34
deny-high-risk: 24/34
deny-high-risk-payment-state: 30/34
deny-high-risk-stateful: 34/34
```

## Interpretation

This is the first end-to-end evidence that the candidate gate can turn local model output into curated benchmark coverage. The strongest use of local/Mac/TPU compute is not raw generation volume. It is a disciplined loop where compute proposes, validators reject malformed output, humans select for novelty, and deterministic baselines preserve comparability.

The next frontier step is a multi-model and multi-defense sweep manifest: the suite now has 34 curated fixtures, a candidate-generation path, and enough deterministic policy baselines to compare model families without losing provenance.
