# Stateful Payment Baseline - April 2026

## Summary

This report evaluates a third transparent deterministic policy agent against Agent Infrastructure Security Bench: `deny-high-risk-payment-state`.

The goal is to turn the first baseline failure into a concrete mitigation test. The earlier `deny-high-risk` baseline blocked obvious risky tool categories but allowed the `x402.replay_payment.basic` fixture because the unsafe tool was labeled `payment`, not `exfiltration`, `secret_exposure`, or `code_execution`.

The new baseline keeps the same high-risk denylist and adds a narrow state-aware payment check for replay evidence:

- reused or stale payment nonce state
- payment proof seen earlier in the same trace render
- payment proof bound to a different request than the current settlement attempt

These results are not model results. They are deterministic control baselines that make the benchmark's expected defense behavior explicit before LLM-agent or TPU-backed sweeps.

## Run Metadata

- Benchmark commit: `aaecefe`
- Scenario count: `20`
- Model or agent: deterministic policy agent
- Trace adapter: `policy-agent`
- Hardware: local CPU
- Date: April 22, 2026

## Policies

- `naive-allow`: allows every expected tool action.
- `deny-high-risk`: blocks tools whose fixture risk label is one of `code_execution`, `credential_theft`, `exfiltration`, `financial_loss`, `network_exfiltration`, `privilege_escalation`, `secret_exposure`, or `supply_chain_execution`; allows all other labeled risks.
- `deny-high-risk-payment-state`: applies `deny-high-risk`, then blocks payment tools when fixture metadata shows a reused/stale nonce, replayed proof, or proof bound to a different approved request.

## Result Summary

| Policy | Manifest Run ID | Passed | Total | Pass Rate | Average Score |
| --- | --- | ---: | ---: | ---: | ---: |
| `naive-allow` | `run-3de17f339fa9` | 0 | 20 | 0.000 | 0.517 |
| `deny-high-risk` | `run-ca7683fad180` | 19 | 20 | 0.950 | 0.975 |
| `deny-high-risk-payment-state` | `run-7e92db46affd` | 20 | 20 | 1.000 | 1.000 |

## Key Finding

Static risk labels catch broad dangerous-tool categories, but they do not express protocol state.

The `x402.replay_payment.basic` fixture is a small example: the tool category remains `payment`, while the unsafe condition is that settlement material is stale and bound to a previous request. A policy that only asks "is this tool in a high-risk category?" lets it through. A policy that also asks "is this proof fresh and bound to the current request?" blocks it.

This is the next useful public claim for the repo: payment-agent safety needs stateful protocol validation, not only tool-category denylisting.

## Payment Domain Comparison

| Policy | Payments Passed | Payments Total | Payment Pass Rate | Payment Average Score |
| --- | ---: | ---: | ---: | ---: |
| `deny-high-risk` | 1 | 2 | 0.500 | 0.750 |
| `deny-high-risk-payment-state` | 2 | 2 | 1.000 | 1.000 |

## Reproduction

```powershell
python -m pip install -e .[dev]
python -m pytest
agent-bench run-policy-baseline scenarios outputs/policy-baseline --policy naive-allow --scenario-commit aaecefe
agent-bench run-policy-baseline scenarios outputs/policy-baseline --policy deny-high-risk --scenario-commit aaecefe
agent-bench run-policy-baseline scenarios outputs/policy-baseline --policy deny-high-risk-payment-state --scenario-commit aaecefe
```

The commands write per-policy traces, `results.md`, `results.csv`, and `manifest.json` under `outputs/policy-baseline/<policy>/`.

## Claims Boundary

- This report does not evaluate any LLM, cloud model, or TPU-backed model.
- The fixtures are synthetic and public-safe.
- `deny-high-risk-payment-state` is a transparent baseline, not a production x402 verifier.
- Passing this suite does not prove broad payment-agent safety.
- The result should be read as a control baseline showing that replay-style payment failures need state-aware validation in addition to static tool risk labels.
