from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Literal

Decision = Literal["allow", "block"]


@dataclass(frozen=True)
class Tool:
    name: str
    risk: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Tool":
        return cls(name=_required_str(data, "name"), risk=_required_str(data, "risk"))


@dataclass(frozen=True)
class ExpectedAction:
    id: str
    tool: str
    decision: Decision

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExpectedAction":
        decision = _required_str(data, "decision")
        if decision not in {"allow", "block"}:
            raise ValueError(f"Expected action decision must be allow or block: {decision}")
        return cls(
            id=_required_str(data, "id"),
            tool=_required_str(data, "tool"),
            decision=decision,
        )


@dataclass(frozen=True)
class AgentFixture:
    id: str
    title: str
    domain: str
    attack_type: str
    user_goal: str
    untrusted_content: str
    tools: tuple[Tool, ...]
    expected_actions: tuple[ExpectedAction, ...]
    success_criteria: tuple[str, ...]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentFixture":
        expected_actions = tuple(
            ExpectedAction.from_dict(item) for item in _required_list(data, "expected_actions")
        )
        seen_ids: set[str] = set()
        for action in expected_actions:
            if action.id in seen_ids:
                raise ValueError(f"Duplicate expected action id: {action.id}")
            seen_ids.add(action.id)

        return cls(
            id=_required_str(data, "id"),
            title=_required_str(data, "title"),
            domain=_required_str(data, "domain"),
            attack_type=_required_str(data, "attack_type"),
            user_goal=_required_str(data, "user_goal"),
            untrusted_content=_required_str(data, "untrusted_content"),
            tools=tuple(Tool.from_dict(item) for item in _required_list(data, "tools")),
            expected_actions=expected_actions,
            success_criteria=tuple(_required_str({"value": item}, "value") for item in _required_list(data, "success_criteria")),
        )


def load_fixture(path: str | Path) -> AgentFixture:
    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("Fixture root must be a JSON object")
    return AgentFixture.from_dict(data)


def _required_str(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"Required string field missing or empty: {key}")
    return value


def _required_list(data: dict[str, Any], key: str) -> list[Any]:
    value = data.get(key)
    if not isinstance(value, list) or not value:
        raise ValueError(f"Required list field missing or empty: {key}")
    return value
