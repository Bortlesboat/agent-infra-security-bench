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
    request = Request(f"{base_url}?{query}")
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


def write_boundarypay_demo(output_dir: Path, *, mode: str = "fixture") -> dict[str, Any]:
    if mode not in {"fixture", "live"}:
        raise ValueError("mode must be 'fixture' or 'live'")

    output_dir.mkdir(parents=True, exist_ok=True)
    price_snapshot = (
        fetch_jupiter_price_snapshot(api_key=os.environ.get("JUPITER_API_KEY"))
        if mode == "live"
        else _fixture_price_snapshot()
    )
    intents = _demo_intents(price_snapshot)
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
        "source": {
            "platform": "jupiter",
            "price_endpoint": JUPITER_PRICE_V3_URL,
            "price_snapshot": price_snapshot,
        },
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
    (output_dir / "README.md").write_text(_readme_text(mode, allowed, blocked), encoding="utf-8")
    (output_dir / "DX-REPORT.md").write_text(_dx_report_text(mode), encoding="utf-8")
    return {
        "project": "BoundaryPay Guard",
        "mode": mode,
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


def _demo_intents(price_snapshot: dict[str, Any]) -> list[dict[str, Any]]:
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


def _readme_text(mode: str, allowed: int, blocked: int) -> str:
    return f"""# BoundaryPay Guard Demo

This artifact demonstrates a Jupiter-style payment intent guard for AI agents.

Mode: `{mode}`

Result summary:

- Allowed: {allowed}
- Blocked: {blocked}

The demo is public-safe and non-custodial. It does not sign transactions, place orders,
hold wallet keys, or execute swaps. It shows how replay, stale authorization, amount
drift, route drift, and platform/token binding issues can be blocked before execution.
"""


def _dx_report_text(mode: str) -> str:
    return f"""# BoundaryPay Guard DX Report

## Current Run

This generated report was created in `{mode}` mode. In fixture mode, the demo uses a
deterministic Jupiter price snapshot so reviewers can run it without an API key or
wallet. Before final Superteam/Jupiter submission, rerun with `--mode live` after the
Jupiter Developer Platform account and API key are ready.

## Jupiter Developer Platform Notes

- The Jupiter Developer Platform is a strong fit for agents because the docs present
  REST APIs, clean JSON responses, and AI-specific surfaces such as llms.txt, skills,
  MCP, and CLI tooling.
- For an agentic payment safety demo, the most useful review surfaces are the Price,
  Tokens, and Swap API families plus the AI tooling docs.
- The most important DX artifact for this submission is a reproducible trace showing
  what the agent proposed and why the guard allowed or blocked it.

## What Needs Live Follow-Up

- Time from API-key creation to first successful request.
- Whether the Price/Swap docs make route and amount binding easy to preserve.
- Whether error responses are structured enough for an agent to recover safely.
- Whether API logs expose enough metadata to audit agent-triggered requests.
"""
