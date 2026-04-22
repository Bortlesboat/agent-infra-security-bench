# Policy Agent Baseline Example

This example reproduces the first deterministic policy-agent baseline.

```powershell
agent-bench run-policy-baseline scenarios outputs/policy-baseline --policy naive-allow --scenario-commit 243f5fa
agent-bench run-policy-baseline scenarios outputs/policy-baseline --policy deny-high-risk --scenario-commit 243f5fa
```

Expected summary:

| Policy | Passed | Total | Pass Rate |
| --- | ---: | ---: | ---: |
| `naive-allow` | 0 | 20 | 0.000 |
| `deny-high-risk` | 19 | 20 | 0.950 |

The failed `deny-high-risk` fixture is `x402.replay_payment.basic`, showing that payment replay needs stateful validation beyond static risk-label blocking.

These are deterministic policy baselines, not LLM or TPU-backed model results.
