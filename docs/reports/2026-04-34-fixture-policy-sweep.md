# 34-Fixture Policy Sweep

Date: 2026-04-23

Scenario commit: `e93f579`

This is the first sweep-index artifact for the 34-fixture suite. It turns individual run manifests and results CSVs into one comparable table, so deterministic policies, local model runs, Mac mini runs, and future TPU runs can be reviewed through the same evidence shape.

This first index uses the deterministic policy ladder. It is not an LLM result. It is the baseline table future model and defense sweeps should compare against.

## Sweep Table

- Runs: 4
- Generated: 2026-04-23T06:16:55Z

| Run | Model | Policy | Prompt | Runtime | Hardware | Commit | Passed | Pass Rate | Avg Score | Unsafe | Missed |
| --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| run-6d1dec8ccd11 | deterministic-policy-agent | deny-high-risk | n/a | n/a | local | e93f579 | 24/34 | 0.706 | 0.853 | 10 | 0 |
| run-55554f8df4c6 | deterministic-policy-agent | deny-high-risk-payment-state | n/a | n/a | local | e93f579 | 30/34 | 0.882 | 0.941 | 4 | 0 |
| run-75649c64e745 | deterministic-policy-agent | deny-high-risk-stateful | n/a | n/a | local | e93f579 | 34/34 | 1.000 | 1.000 | 0 | 0 |
| run-89799d3317e9 | deterministic-policy-agent | naive-allow | n/a | n/a | local | e93f579 | 1/34 | 0.029 | 0.525 | 33 | 0 |

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

The sweep index gives the project a stable scoreboard format. A model run is no longer just a standalone writeup. It can be added to a manifest list, summarized with the same totals, and compared against policy baselines by scenario commit, model, policy, prompt profile, runtime policy, hardware, and trace adapter.

The immediate next use is to rerun the local Windows and Mac mini model/defense baselines against the 34-fixture suite and add those manifests to the same sweep shape.
