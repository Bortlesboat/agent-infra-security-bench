# BoundaryPay Guard Demo Video Script

Target length: 2 to 4 minutes.

## 1. Problem

AI agents are starting to touch onchain APIs and payment flows. The failure mode is not only "the model said something wrong." It is that a stale quote, reused proof, route change, or untrusted tool result crosses into a privileged payment action.

## 2. What BoundaryPay Guard Does

BoundaryPay Guard is a small open-source guard and demo harness. It checks a Jupiter-style payment or swap intent before execution and verifies that the proposed action still matches the approved request: amount, route, token mints, facilitator, platform, nonce state, and proof replay state.

## 3. Run The Demo

Show:

```powershell
agent-bench boundarypay-demo outputs/boundarypay-guard --mode fixture
```

Open `outputs/boundarypay-guard/boundarypay-report.json`.

Point out:

- one fresh intent is allowed
- reused proof is blocked
- amount drift is blocked
- route drift is blocked

## 4. Why It Fits Jupiter / Solana

Jupiter gives builders agent-friendly REST APIs and clean JSON surfaces. BoundaryPay Guard adds a safety layer around the moment an agent moves from quote or intent into execution. The goal is to help Solana builders ship agentic payment flows without losing traceability or binding.

## 5. What Is Next

The next slice is a live Jupiter Developer Platform run, then Base/EVM variants and more public fixtures for agent payment boundaries.

## Closing Line

BoundaryPay Guard is not a trading bot. It is a seatbelt for agents before they touch payment execution.
