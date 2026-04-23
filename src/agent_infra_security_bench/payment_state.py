from __future__ import annotations

from typing import Any

INVALID_NONCE_STATUSES = {"expired", "reused", "stale"}
APPROVAL_BOUND_FIELDS = (
    "request_id",
    "amount",
    "amount_usd",
    "asset",
    "chain_id",
    "facilitator",
    "facilitator_url",
    "recipient",
    "resource",
    "route",
)


class PaymentStateValidator:
    def __init__(self) -> None:
        self._seen_proofs: set[str] = set()

    def allows(self, state: Any) -> bool:
        if not isinstance(state, dict):
            return True

        nonce_status = state.get("nonce_status")
        if isinstance(nonce_status, str) and nonce_status.lower() in INVALID_NONCE_STATUSES:
            return False

        if _has_approval_binding_mismatch(state):
            return False

        proof_id = state.get("proof_id")
        if isinstance(proof_id, str) and proof_id:
            if proof_id in self._seen_proofs:
                return False
            self._seen_proofs.add(proof_id)

        return True


def payment_state_allows_once(state: Any) -> bool:
    return PaymentStateValidator().allows(state)


def _has_approval_binding_mismatch(state: dict[str, Any]) -> bool:
    for field in APPROVAL_BOUND_FIELDS:
        approved_field = f"approved_{field}"
        value = state.get(field)
        approved_value = state.get(approved_field)
        if _both_present(value, approved_value) and value != approved_value:
            return True
    return False


def _both_present(left: Any, right: Any) -> bool:
    return left is not None and right is not None
