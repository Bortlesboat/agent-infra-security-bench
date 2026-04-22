from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_generic_events(path: str | Path) -> list[dict[str, Any]]:
    source = Path(path)
    text = source.read_text(encoding="utf-8").strip()
    if not text:
        return []
    if text.startswith("["):
        payload = json.loads(text)
        if not isinstance(payload, list):
            raise ValueError("Generic event JSON root must be an array")
        return [_require_event(item) for item in payload]
    events: list[dict[str, Any]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        item = json.loads(line)
        if not isinstance(item, dict):
            raise ValueError(f"JSONL event must be an object on line {line_number}")
        events.append(item)
    return events


def convert_generic_events(events: list[dict[str, Any]]) -> list[dict[str, str]]:
    actions: list[dict[str, str]] = []
    for event in events:
        action = _convert_event(event)
        if action is not None:
            actions.append(action)
    return actions


def write_trace(path: str | Path, actions: list[dict[str, str]]) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(actions, indent=2) + "\n", encoding="utf-8")
    return output


def _convert_event(event: dict[str, Any]) -> dict[str, str] | None:
    tool = _tool_name(event)
    decision = _decision(event)
    if tool is None or decision is None:
        return None
    return {"tool": tool, "decision": decision}


def _tool_name(event: dict[str, Any]) -> str | None:
    for key in ("tool", "name", "tool_name"):
        value = event.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def _decision(event: dict[str, Any]) -> str | None:
    decision = event.get("decision")
    if decision in {"allow", "block"}:
        return decision
    allowed = event.get("allowed")
    if isinstance(allowed, bool):
        return "allow" if allowed else "block"
    status = event.get("status")
    if status in {"allowed", "allow", "completed", "success"}:
        return "allow"
    if status in {"blocked", "block", "denied", "rejected"}:
        return "block"
    return None


def _require_event(item: Any) -> dict[str, Any]:
    if not isinstance(item, dict):
        raise ValueError("Generic event must be a JSON object")
    return item
