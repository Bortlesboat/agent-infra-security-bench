# BoundaryPay Guard

BoundaryPay Guard is a public-safe demo for testing agent-initiated payment intent boundaries before execution.

The first version is Jupiter/Solana-oriented because the near-term submission targets reward shipped artifacts:

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

Live mode can be used after a Jupiter Developer Platform API key is available:

```powershell
$env:JUPITER_API_KEY = "<developer-platform-key>"
agent-bench boundarypay-demo outputs/boundarypay-guard-live --mode live
```

## What It Checks

The demo allows a fresh, approval-bound Jupiter-style payment/swap intent and blocks unsafe variants:

- reused or stale proof state
- amount drift
- route drift
- facilitator/platform/token binding mismatches
- proof replay across intents

## Claims Boundary

This demo does not sign transactions, place orders, hold wallet keys, execute swaps, or automate trading. It is developer infrastructure for reviewing and testing payment-agent safety checks.

## Submission Path

Use the generated folder as the review artifact for Superteam/Jupiter and Colosseum. Before final submission, rerun in live mode and update `DX-REPORT.md` with real API-key onboarding notes, first successful API call timing, and any docs/API friction observed during the build.
