import json

from agent_infra_security_bench.jupiter_guard import (
    DEFAULT_SOL_MINT,
    DEFAULT_USDC_MINT,
    evaluate_payment_intent,
    write_boundarypay_demo,
)


def _fresh_intent():
    return {
        "intent_id": "boundarypay-demo-001",
        "platform": "jupiter",
        "approved_platform": "jupiter",
        "proof_id": "proof-fresh-001",
        "nonce_status": "fresh",
        "request_id": "swap-demo-001",
        "approved_request_id": "swap-demo-001",
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
    }


def test_jupiter_guard_allows_fresh_bound_intent_and_blocks_unsafe_variants():
    fresh = _fresh_intent()

    assert evaluate_payment_intent(fresh) == {
        "intent_id": "boundarypay-demo-001",
        "decision": "allow",
        "reasons": [],
    }

    reused = fresh | {"intent_id": "reused", "proof_id": "proof-old-001", "nonce_status": "reused"}
    assert evaluate_payment_intent(reused) == {
        "intent_id": "reused",
        "decision": "block",
        "reasons": ["nonce_status:reused"],
    }

    amount_changed = fresh | {"intent_id": "amount-changed", "amount_usd": "100.00"}
    assert evaluate_payment_intent(amount_changed) == {
        "intent_id": "amount-changed",
        "decision": "block",
        "reasons": ["binding_mismatch:amount_usd"],
    }

    route_changed = fresh | {"intent_id": "route-changed", "route": "jupiter:swap-v2:sol-jup"}
    assert evaluate_payment_intent(route_changed) == {
        "intent_id": "route-changed",
        "decision": "block",
        "reasons": ["binding_mismatch:route"],
    }


def test_jupiter_guard_blocks_replayed_proof_across_intents():
    first = _fresh_intent()
    second = _fresh_intent() | {"intent_id": "second-request", "request_id": "swap-demo-002", "approved_request_id": "swap-demo-002"}
    seen: set[str] = set()

    assert evaluate_payment_intent(first, seen_proofs=seen)["decision"] == "allow"
    assert evaluate_payment_intent(second, seen_proofs=seen) == {
        "intent_id": "second-request",
        "decision": "block",
        "reasons": ["proof_replay:proof-fresh-001"],
    }


def test_boundarypay_demo_writes_submission_artifacts(tmp_path):
    output_dir = tmp_path / "boundarypay"

    summary = write_boundarypay_demo(output_dir, mode="fixture")

    assert summary["project"] == "BoundaryPay Guard"
    assert summary["mode"] == "fixture"
    assert summary["allowed"] == 1
    assert summary["blocked"] >= 3
    assert (output_dir / "boundarypay-report.json").exists()
    assert (output_dir / "boundarypay-trace.json").exists()
    assert (output_dir / "README.md").exists()
    assert (output_dir / "DX-REPORT.md").exists()

    report = json.loads((output_dir / "boundarypay-report.json").read_text(encoding="utf-8"))
    assert report["source"]["platform"] == "jupiter"
    assert report["checks"][0]["decision"] == "allow"
    assert {reason for check in report["checks"] for reason in check["reasons"]} >= {
        "nonce_status:reused",
        "binding_mismatch:amount_usd",
        "binding_mismatch:route",
    }

    dx_report = (output_dir / "DX-REPORT.md").read_text(encoding="utf-8")
    assert "Jupiter Developer Platform" in dx_report
    assert "fixture mode" in dx_report
