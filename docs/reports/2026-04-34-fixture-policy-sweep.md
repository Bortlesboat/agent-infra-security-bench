# 34-Fixture Policy Sweep

Date: 2026-04-23

Scenario commit: `e93f579`

This is the deterministic policy baseline for the 34-fixture suite. It keeps the same sweep-index shape used by model runs, but now also carries tool-decision coverage so future local, hosted, and TPU-backed rows can be compared on safety, utility, and completeness instead of pass rate alone.

This table is still not an LLM result. It is the reference ladder the model rows should be judged against.

## Sweep Table

- Runs: 4
- Generated: 2026-04-23T13:57:28Z

| Run | Model | Policy | Prompt | Runtime | Hardware | Commit | Passed | Pass Rate | Avg Score | Unsafe | Missed | Coverage | Omitted | Duplicates |
| --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| run-6d1dec8ccd11 | deterministic-policy-agent | deny-high-risk | n/a | n/a | local | e93f579 | 24/34 | 0.706 | 0.853 | 10 | 0 | 1.000 | 0 | 0 |
| run-55554f8df4c6 | deterministic-policy-agent | deny-high-risk-payment-state | n/a | n/a | local | e93f579 | 30/34 | 0.882 | 0.941 | 4 | 0 | 1.000 | 0 | 0 |
| run-75649c64e745 | deterministic-policy-agent | deny-high-risk-stateful | n/a | n/a | local | e93f579 | 34/34 | 1.000 | 1.000 | 0 | 0 | 1.000 | 0 | 0 |
| run-89799d3317e9 | deterministic-policy-agent | naive-allow | n/a | n/a | local | e93f579 | 1/34 | 0.029 | 0.525 | 33 | 0 | 1.000 | 0 | 0 |

Machine-readable JSON: `docs/reports/2026-04-34-fixture-policy-sweep.json`

## Reproduction

```powershell
agent-bench run-policy-baseline scenarios outputs/policy-baseline --policy naive-allow --scenario-commit e93f579
agent-bench run-policy-baseline scenarios outputs/policy-baseline --policy deny-high-risk --scenario-commit e93f579
agent-bench run-policy-baseline scenarios outputs/policy-baseline --policy deny-high-risk-payment-state --scenario-commit e93f579
agent-bench run-policy-baseline scenarios outputs/policy-baseline --policy deny-high-risk-stateful --scenario-commit e93f579
agent-bench write-sweep-index docs/reports/2026-04-34-fixture-policy-sweep.json `
  outputs/policy-baseline/naive-allow/manifest.json `
  outputs/policy-baseline/deny-high-risk/manifest.json `
  outputs/policy-baseline/deny-high-risk-payment-state/manifest.json `
  outputs/policy-baseline/deny-high-risk-stateful/manifest.json `
  --name "34-Fixture Policy Sweep" `
  --markdown docs/reports/2026-04-34-fixture-policy-sweep.md `
  --root .
```

## Interpretation

The policy ladder now establishes the benchmark's floor on all three axes:

- safety: naive allow stays obviously unsafe
- utility: stateful payment and provenance checks recover expected-safe actions without reopening unsafe ones
- completeness: every deterministic policy row already has full `70/70` tool coverage

That last point matters for the next layer up. When a model row underperforms this table, we can now tell whether it failed because it made the wrong judgment or because it did not answer for every listed tool.
