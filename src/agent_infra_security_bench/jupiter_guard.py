from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


DEFAULT_SOL_MINT = "So11111111111111111111111111111111111111112"
DEFAULT_USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
JUPITER_PRICE_V3_URL = "https://lite-api.jup.ag/price/v3"
DEFAULT_BASE_CHAIN_ID = "84532"
DEFAULT_BASE_NETWORK = "base-sepolia"
DEFAULT_BASE_ASSET = "USDC"
DEFAULT_BASE_FACILITATOR = "https://x402.org"
DEFAULT_BASE_FACILITATOR_URL = "https://x402.org/facilitator/base-sepolia"
DEFAULT_BASE_RESOURCE = "https://api.bitcoinsapi.com/v1/premium/fees?confirm_target=2"
DEFAULT_BASE_RECIPIENT = "base:0x0000000000000000000000000000000000004020"
PUBLIC_DEMO_USER_AGENT = (
    "agent-infra-security-bench/0.1 "
    "(+https://github.com/Bortlesboat/agent-infra-security-bench)"
)
INVALID_NONCE_STATUSES = {"expired", "reused", "stale"}
BOUND_FIELDS = (
    "platform",
    "request_id",
    "amount",
    "amount_usd",
    "asset",
    "chain_id",
    "facilitator",
    "facilitator_url",
    "input_mint",
    "output_mint",
    "recipient",
    "resource",
    "route",
    "slippage_bps",
    "swap_mode",
)


class JupiterPriceFetchError(RuntimeError):
    pass


def evaluate_payment_intent(
    intent: dict[str, Any],
    *,
    seen_proofs: set[str] | None = None,
) -> dict[str, Any]:
    reasons: list[str] = []
    nonce_status = intent.get("nonce_status")
    if isinstance(nonce_status, str) and nonce_status.lower() in INVALID_NONCE_STATUSES:
        reasons.append(f"nonce_status:{nonce_status.lower()}")

    for field in BOUND_FIELDS:
        proposed = intent.get(field)
        approved = intent.get(f"approved_{field}")
        if proposed is not None and approved is not None and proposed != approved:
            reasons.append(f"binding_mismatch:{field}")

    proof_id = intent.get("proof_id")
    if isinstance(proof_id, str) and proof_id:
        if seen_proofs is not None and proof_id in seen_proofs:
            reasons.append(f"proof_replay:{proof_id}")
        elif seen_proofs is not None:
            seen_proofs.add(proof_id)

    return {
        "intent_id": str(intent.get("intent_id", "unknown")),
        "decision": "block" if reasons else "allow",
        "reasons": reasons,
    }


def fetch_jupiter_price_snapshot(
    *,
    token_mint: str = DEFAULT_SOL_MINT,
    api_key: str | None = None,
    base_url: str = JUPITER_PRICE_V3_URL,
) -> dict[str, Any]:
    query = urlencode({"ids": token_mint})
    request = Request(
        f"{base_url}?{query}",
        headers={"User-Agent": PUBLIC_DEMO_USER_AGENT},
    )
    if api_key:
        request.add_header("x-api-key", api_key)
    try:
        with urlopen(request, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise JupiterPriceFetchError(
            f"Jupiter Price V3 returned HTTP {exc.code}; set JUPITER_API_KEY or rerun with --mode fixture"
        ) from exc
    except (OSError, URLError) as exc:
        raise JupiterPriceFetchError(
            f"Jupiter Price V3 request failed; set JUPITER_API_KEY, check network access, or rerun with --mode fixture: {exc}"
        ) from exc
    price = _extract_price(payload, token_mint)
    return {
        "source": "live",
        "platform": "jupiter",
        "endpoint": base_url,
        "token_mint": token_mint,
        "usd_price": price,
        "raw": payload,
    }


def write_boundarypay_demo(
    output_dir: Path,
    *,
    mode: str = "fixture",
    surface: str = "jupiter",
) -> dict[str, Any]:
    if mode not in {"fixture", "live"}:
        raise ValueError("mode must be 'fixture' or 'live'")
    if surface not in {"jupiter", "base"}:
        raise ValueError("surface must be 'jupiter' or 'base'")

    output_dir.mkdir(parents=True, exist_ok=True)
    source_metadata = _load_source_metadata(mode=mode, surface=surface)
    intents = _demo_intents(source_metadata, surface=surface)
    seen_proofs: set[str] = set()
    checks = [
        evaluate_payment_intent(intent, seen_proofs=seen_proofs) | {"intent": intent}
        for intent in intents
    ]
    allowed = sum(1 for check in checks if check["decision"] == "allow")
    blocked = sum(1 for check in checks if check["decision"] == "block")
    report = {
        "project": "BoundaryPay Guard",
        "mode": mode,
        "surface": surface,
        "source": source_metadata,
        "summary": {"allowed": allowed, "blocked": blocked, "total": len(checks)},
        "checks": checks,
    }
    (output_dir / "boundarypay-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (output_dir / "boundarypay-trace.json").write_text(
        json.dumps(
            [
                {"tool": f"jupiter.intent.{check['intent_id']}", "decision": check["decision"]}
                for check in checks
            ],
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    (output_dir / "README.md").write_text(
        _readme_text(mode, allowed, blocked, surface=surface),
        encoding="utf-8",
    )
    (output_dir / "DX-REPORT.md").write_text(
        _dx_report_text(mode, surface=surface),
        encoding="utf-8",
    )
    return {
        "project": "BoundaryPay Guard",
        "mode": mode,
        "surface": surface,
        "allowed": allowed,
        "blocked": blocked,
        "output_dir": str(output_dir),
        "report": str(output_dir / "boundarypay-report.json"),
        "dx_report": str(output_dir / "DX-REPORT.md"),
    }


def _extract_price(payload: dict[str, Any], token_mint: str) -> Any:
    data = payload.get("data", payload)
    if isinstance(data, dict):
        item = data.get(token_mint)
        if isinstance(item, dict):
            return item.get("usdPrice", item.get("price"))
        if isinstance(item, (int, float, str)):
            return item
    return None


def _fixture_price_snapshot() -> dict[str, Any]:
    return {
        "source": "fixture",
        "platform": "jupiter",
        "endpoint": JUPITER_PRICE_V3_URL,
        "token_mint": DEFAULT_SOL_MINT,
        "usd_price": "175.00",
        "note": "Deterministic fixture value for public-safe demo runs.",
    }


def _load_source_metadata(*, mode: str, surface: str) -> dict[str, Any]:
    if surface == "jupiter":
        return (
            fetch_jupiter_price_snapshot(api_key=os.environ.get("JUPITER_API_KEY"))
            if mode == "live"
            else _fixture_price_snapshot()
        )
    return _base_fixture_source()


def _demo_intents(source_metadata: dict[str, Any], *, surface: str) -> list[dict[str, Any]]:
    if surface == "base":
        return _base_demo_intents(source_metadata)
    return _jupiter_demo_intents(source_metadata)


def _jupiter_demo_intents(price_snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    base = {
        "platform": "jupiter",
        "approved_platform": "jupiter",
        "nonce_status": "fresh",
        "amount_usd": "10.00",
        "approved_amount_usd": "10.00",
        "route": "jupiter:swap-v2:sol-usdc",
        "approved_route": "jupiter:swap-v2:sol-usdc",
        "facilitator": "https://developers.jup.ag",
        "approved_facilitator": "https://developers.jup.ag",
        "input_mint": DEFAULT_SOL_MINT,
        "approved_input_mint": DEFAULT_SOL_MINT,
        "output_mint": DEFAULT_USDC_MINT,
        "approved_output_mint": DEFAULT_USDC_MINT,
        "price_source": price_snapshot.get("source"),
    }
    return [
        base
        | {
            "intent_id": "fresh-sol-usdc",
            "proof_id": "proof-fresh-001",
            "request_id": "swap-demo-001",
            "approved_request_id": "swap-demo-001",
        },
        base
        | {
            "intent_id": "reused-proof",
            "proof_id": "proof-old-001",
            "request_id": "swap-demo-002",
            "approved_request_id": "swap-demo-002",
            "nonce_status": "reused",
        },
        base
        | {
            "intent_id": "amount-drift",
            "proof_id": "proof-amount-001",
            "request_id": "swap-demo-003",
            "approved_request_id": "swap-demo-003",
            "amount_usd": "100.00",
        },
        base
        | {
            "intent_id": "route-drift",
            "proof_id": "proof-route-001",
            "request_id": "swap-demo-004",
            "approved_request_id": "swap-demo-004",
            "route": "jupiter:swap-v2:sol-jup",
        },
    ]


def _base_fixture_source() -> dict[str, Any]:
    return {
        "mode": "fixture",
        "platform": "x402",
        "network": DEFAULT_BASE_NETWORK,
        "chain_id": DEFAULT_BASE_CHAIN_ID,
        "asset": DEFAULT_BASE_ASSET,
        "facilitator": DEFAULT_BASE_FACILITATOR,
        "facilitator_url": DEFAULT_BASE_FACILITATOR_URL,
        "resource": DEFAULT_BASE_RESOURCE,
        "note": "Deterministic Base/x402 fixture for public-safe grant review runs.",
    }


def _base_demo_intents(source_metadata: dict[str, Any]) -> list[dict[str, Any]]:
    base = {
        "platform": "x402",
        "approved_platform": "x402",
        "nonce_status": "fresh",
        "amount_usd": "2.50",
        "approved_amount_usd": "2.50",
        "asset": DEFAULT_BASE_ASSET,
        "approved_asset": DEFAULT_BASE_ASSET,
        "chain_id": DEFAULT_BASE_CHAIN_ID,
        "approved_chain_id": DEFAULT_BASE_CHAIN_ID,
        "facilitator": DEFAULT_BASE_FACILITATOR,
        "approved_facilitator": DEFAULT_BASE_FACILITATOR,
        "facilitator_url": DEFAULT_BASE_FACILITATOR_URL,
        "approved_facilitator_url": DEFAULT_BASE_FACILITATOR_URL,
        "recipient": DEFAULT_BASE_RECIPIENT,
        "approved_recipient": DEFAULT_BASE_RECIPIENT,
        "resource": DEFAULT_BASE_RESOURCE,
        "approved_resource": DEFAULT_BASE_RESOURCE,
        "route": "x402:GET:/v1/premium/fees",
        "approved_route": "x402:GET:/v1/premium/fees",
        "source_mode": source_metadata.get("mode"),
        "source_network": source_metadata.get("network"),
    }
    return [
        base
        | {
            "intent_id": "base-x402-fresh",
            "proof_id": "base-proof-fresh-001",
            "request_id": "base-charge-001",
            "approved_request_id": "base-charge-001",
        },
        base
        | {
            "intent_id": "base-x402-stale",
            "proof_id": "base-proof-stale-001",
            "request_id": "base-charge-002",
            "approved_request_id": "base-charge-002",
            "nonce_status": "stale",
        },
        base
        | {
            "intent_id": "base-x402-chain-drift",
            "proof_id": "base-proof-chain-001",
            "request_id": "base-charge-003",
            "approved_request_id": "base-charge-003",
            "chain_id": "8453",
        },
        base
        | {
            "intent_id": "base-x402-resource-drift",
            "proof_id": "base-proof-resource-001",
            "request_id": "base-charge-004",
            "approved_request_id": "base-charge-004",
            "resource": "https://api.bitcoinsapi.com/v1/premium/fees?confirm_target=6",
        },
        base
        | {
            "intent_id": "base-x402-facilitator-drift",
            "proof_id": "base-proof-facilitator-001",
            "request_id": "base-charge-005",
            "approved_request_id": "base-charge-005",
            "facilitator_url": "https://shadow.example/x402/base-sepolia",
        },
        base
        | {
            "intent_id": "base-x402-proof-replay",
            "proof_id": "base-proof-fresh-001",
            "request_id": "base-charge-006",
            "approved_request_id": "base-charge-006",
        },
    ]


def _readme_text(mode: str, allowed: int, blocked: int, *, surface: str) -> str:
    if surface == "base":
        intro = "This artifact demonstrates a Base/x402 request-boundary guard for AI agents."
        claims = (
            "It is fixture-first and public-safe. It does not sign transactions, move funds, "
            "or claim a production Base settlement flow."
        )
    else:
        intro = "This artifact demonstrates a Jupiter-style payment intent guard for AI agents."
        claims = (
            "The demo is public-safe and non-custodial. It does not sign transactions, place orders, "
            "hold wallet keys, or execute swaps."
        )

    return f"""# BoundaryPay Guard Demo

{intro}

Mode: `{mode}`
Surface: `{surface}`

Result summary:

- Allowed: {allowed}
- Blocked: {blocked}

{claims} It shows how replay, stale authorization, amount drift, route drift, resource
drift, and facilitator/network binding issues can be blocked before execution.
"""


def _dx_report_text(mode: str, *, surface: str) -> str:
    if surface == "base":
        return """# BoundaryPay Guard DX Report

## Current Run

This generated report was created for the `base` surface in `fixture` mode. The lane is
intentionally fixture-first so grant reviewers can inspect approval-bound Base/x402 request
state without requiring wallet funding, signing, or live facilitator access.

## Base Builder Funding Fit

- Base Builder Rewards and Base Builder Grants favor shipped public work with clear technical proof.
- The most useful review artifact here is a reproducible trace that shows a fresh Base/x402
  request allowed while stale, replayed, cross-network, or facilitator-drifted requests are blocked.
- This lane is positioned as agent payment safety infrastructure, not a wallet or merchant processor.

## What Needs Live Follow-Up

- Optional Base Sepolia or facilitator-backed trace once a low-risk test wallet and spend limits exist.
- Public project social links and a one-minute hosted walkthrough for the Base nomination form.
- A short build update that explains why the guard blocks network/resource/facilitator drift.

## Claims Boundary

- This lane does not sign transactions, move funds, or call a live facilitator.
- It exists to prove the safety boundary logic that a Base-native x402 integration should preserve.
- The honest next step after this proof is a narrowly scoped Sepolia validation, not a mainnet demo.
"""

    if mode == "live":
        current_run = """This generated report was created in `live` mode. Jupiter Price V3 returned a live snapshot for the public SOL mint, and the guard evaluated the same deterministic payment-boundary cases against that live source metadata."""
    else:
        current_run = """This generated report was created in `fixture` mode. The demo uses a
deterministic Jupiter price snapshot so reviewers can run it without an API key or
wallet. Rerun with `--mode live` to capture current Price V3 metadata."""

    return f"""# BoundaryPay Guard DX Report

## Current Run

{current_run}

## Jupiter Developer Platform Notes

- The Jupiter Developer Platform is a strong fit for agents because the docs present
  REST APIs, clean JSON responses, and AI-specific surfaces such as llms.txt, skills,
  MCP, and CLI tooling.
- For an agentic payment safety demo, the most useful review surfaces are the Price,
  Tokens, and Swap API families plus the AI tooling docs.
- The most important DX artifact for this submission is a reproducible trace showing
  what the agent proposed and why the guard allowed or blocked it.

## What Needs Live Follow-Up

- Time from portal API-key creation to first authenticated request, if the bounty review wants Developer Platform analytics in addition to the keyless live Lite API run.
- Whether the Price/Swap docs make route and amount binding easy to preserve.
- Whether error responses are structured enough for an agent to recover safely.
- Whether API logs expose enough metadata to audit agent-triggered requests.
"""
