from __future__ import annotations

from typing import Any

INVALID_STATUSES = {"shadowed", "unverified", "replaced", "unknown"}
APPROVAL_BOUND_FIELDS = (
    "account",
    "origin",
    "owner",
    "repo",
    "resource",
    "scope",
    "server_id",
    "tool_name",
    "transport",
)


def provenance_allows(state: Any) -> bool:
    if not isinstance(state, dict):
        return True

    status = state.get("status")
    if isinstance(status, str) and status.lower() in INVALID_STATUSES:
        return False

    for field in APPROVAL_BOUND_FIELDS:
        approved_field = f"approved_{field}"
        value = state.get(field)
        approved_value = state.get(approved_field)
        if value is not None and approved_value is not None and value != approved_value:
            return False

    return True
