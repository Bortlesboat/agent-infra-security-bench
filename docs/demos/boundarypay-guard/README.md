# BoundaryPay Guard

BoundaryPay Guard is a public-safe demo for testing agent-initiated payment intent boundaries before execution.

The first version was Jupiter/Solana-oriented because the near-term submission targets reward shipped artifacts:

- Colosseum Solana Frontier Hackathon
- Superteam/Jupiter Frontier bounty
- Solana Foundation developer tooling grants
- Base builder rewards after a Base-specific proof

## Run The Demo

```powershell
agent-bench boundarypay-demo outputs/boundarypay-guard --mode fixture
```

Fixture mode writes a deterministic artifact folder:

- `boundarypay-report.json` - guard decisions, reasons, and source metadata
- `boundarypay-trace.json` - compact agent-tool decision trace
- `README.md` - reviewer-facing result summary
- `DX-REPORT.md` - Jupiter Developer Platform feedback scaffold

A checked-in fixture example is available under `sample-output/` for reviewers who want to inspect the artifact before running the command.

To write the Base/x402 proof lane for Base funding submissions:

```powershell
agent-bench boundarypay-demo outputs/boundarypay-guard-base --mode fixture --surface base
```

That writes the same artifact set, but with Base/x402-oriented request state and reviewer copy. The Base lane is intentionally fixture-first: it proves request binding, network binding, facilitator binding, resource binding, stale proof rejection, and replay resistance without pretending we already have a live Base settlement flow.

A checked-in Base fixture example is available under `base-output/`.

Live mode can be used keyless against Jupiter Lite Price V3 for a current public-price snapshot:

```powershell
agent-bench boundarypay-demo outputs/boundarypay-guard-live --mode live
```

For authenticated Developer Platform analytics or higher rate limits, set `JUPITER_API_KEY` before running live mode.

A checked-in live example is available under `live-output/`.

## What It Checks

The demo allows a fresh, approval-bound payment intent and blocks unsafe variants:

- reused or stale proof state
- amount drift
- route or resource drift
- facilitator/platform/token binding mismatches
- Base network binding mismatches
- proof replay across intents

## Claims Boundary

This demo does not sign transactions, place orders, hold wallet keys, execute swaps, or automate trading. It is developer infrastructure for reviewing and testing payment-agent safety checks.

## Submission Path

Use the generated folder as the review artifact for Superteam/Jupiter, Colosseum, and the Base grant nomination packet. Before final Jupiter submission, rerun the Jupiter lane in live mode and update `DX-REPORT.md` with any portal API-key onboarding notes, first authenticated API call timing, and docs/API friction observed during the build. For Base, keep the current artifact honest: fixture-first proof now, then a narrow Base Sepolia follow-up once spend-capped credentials and social/demo links are ready.
