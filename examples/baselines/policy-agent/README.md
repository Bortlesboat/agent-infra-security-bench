# Policy Agent Baseline Example

This example reproduces the deterministic policy-agent baselines.

```powershell
agent-bench run-policy-baseline scenarios outputs/policy-baseline --policy naive-allow --scenario-commit aaecefe
agent-bench run-policy-baseline scenarios outputs/policy-baseline --policy deny-high-risk --scenario-commit aaecefe
agent-bench run-policy-baseline scenarios outputs/policy-baseline --policy deny-high-risk-payment-state --scenario-commit aaecefe
```

Expected summary:

| Policy | Passed | Total | Pass Rate |
| --- | ---: | ---: | ---: |
| `naive-allow` | 0 | 20 | 0.000 |
| `deny-high-risk` | 19 | 20 | 0.950 |
| `deny-high-risk-payment-state` | 20 | 20 | 1.000 |

The failed `deny-high-risk` fixture is `x402.replay_payment.basic`, showing that payment replay needs stateful validation beyond static risk-label blocking. The `deny-high-risk-payment-state` baseline adds a narrow replay/binding check and passes that fixture.

These are deterministic policy baselines, not LLM or TPU-backed model results.
