from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from agent_infra_security_bench.fixtures import load_fixture
from agent_infra_security_bench.scoring import score_trace


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="agent-bench",
        description="Score agent security traces against benchmark fixtures.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    score_parser = subparsers.add_parser("score", help="Score one fixture and trace JSON file")
    score_parser.add_argument("fixture", type=Path)
    score_parser.add_argument("trace", type=Path)

    args = parser.parse_args(argv)
    if args.command == "score":
        fixture = load_fixture(args.fixture)
        with args.trace.open("r", encoding="utf-8") as handle:
            trace = json.load(handle)
        if not isinstance(trace, list):
            raise ValueError("Trace root must be a JSON array")
        result = score_trace(fixture, _trace_actions(trace))
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
        return 0 if result.passed else 2

    return 1


def _trace_actions(trace: list[Any]) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    for item in trace:
        if not isinstance(item, dict):
            raise ValueError("Every trace item must be a JSON object")
        actions.append(item)
    return actions


if __name__ == "__main__":
    raise SystemExit(main())
