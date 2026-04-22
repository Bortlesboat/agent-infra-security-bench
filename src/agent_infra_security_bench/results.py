from __future__ import annotations

from dataclasses import dataclass
import csv
import io
import json
from pathlib import Path
from typing import Any

from agent_infra_security_bench.fixtures import AgentFixture, load_fixture
from agent_infra_security_bench.scoring import ScoreResult, score_trace


@dataclass(frozen=True)
class GroupSummary:
    total: int
    passed: int
    average_score: float

    @property
    def pass_rate(self) -> float:
        return self.passed / self.total if self.total else 0.0

    def to_dict(self) -> dict[str, float | int]:
        return {
            "total": self.total,
            "passed": self.passed,
            "pass_rate": self.pass_rate,
            "average_score": self.average_score,
        }


@dataclass(frozen=True)
class ResultRow:
    fixture: AgentFixture
    score: ScoreResult

    def to_dict(self) -> dict[str, Any]:
        return {
            "fixture_id": self.fixture.id,
            "domain": self.fixture.domain,
            "attack_type": self.fixture.attack_type,
            "passed": self.score.passed,
            "score": self.score.score,
            "unsafe_count": len(self.score.unsafe),
            "missed_count": len(self.score.missed),
        }


@dataclass(frozen=True)
class BenchmarkSummary:
    rows: tuple[ResultRow, ...]
    by_domain: dict[str, GroupSummary]
    by_attack_type: dict[str, GroupSummary]

    @property
    def total(self) -> int:
        return len(self.rows)

    @property
    def passed(self) -> int:
        return sum(1 for row in self.rows if row.score.passed)

    @property
    def pass_rate(self) -> float:
        return self.passed / self.total if self.total else 0.0

    @property
    def average_score(self) -> float:
        return _average([row.score.score for row in self.rows])

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "passed": self.passed,
            "pass_rate": self.pass_rate,
            "average_score": self.average_score,
            "by_domain": {key: value.to_dict() for key, value in self.by_domain.items()},
            "by_attack_type": {
                key: value.to_dict() for key, value in self.by_attack_type.items()
            },
            "rows": [row.to_dict() for row in self.rows],
        }


def score_suite(scenario_dir: str | Path, trace_dir: str | Path) -> BenchmarkSummary:
    scenarios = sorted(Path(scenario_dir).glob("*.json"))
    rows: list[ResultRow] = []
    for scenario_path in scenarios:
        fixture = load_fixture(scenario_path)
        trace_path = Path(trace_dir) / f"{fixture.id}.json"
        trace = _load_trace(trace_path)
        rows.append(ResultRow(fixture=fixture, score=score_trace(fixture, trace)))
    return summarize_rows(rows)


def summarize_rows(rows: list[ResultRow]) -> BenchmarkSummary:
    sorted_rows = tuple(sorted(rows, key=lambda row: row.fixture.id))
    return BenchmarkSummary(
        rows=sorted_rows,
        by_domain=_group(sorted_rows, lambda row: row.fixture.domain),
        by_attack_type=_group(sorted_rows, lambda row: row.fixture.attack_type),
    )


def render_markdown(summary: BenchmarkSummary) -> str:
    lines = [
        "# Agent Infrastructure Security Bench Results",
        "",
        f"- Total fixtures: {summary.total}",
        f"- Passed: {summary.passed}",
        f"- Pass rate: {summary.pass_rate:.3f}",
        f"- Average score: {summary.average_score:.3f}",
        "",
        "## By Domain",
        "",
        "| Domain | Total | Passed | Pass Rate | Average Score |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for key, group in sorted(summary.by_domain.items()):
        lines.append(
            f"| {key} | {group.total} | {group.passed} | {group.pass_rate:.3f} | {group.average_score:.3f} |"
        )
    lines.extend(
        [
            "",
            "## By Attack Type",
            "",
            "| Attack Type | Total | Passed | Pass Rate | Average Score |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for key, group in sorted(summary.by_attack_type.items()):
        lines.append(
            f"| {key} | {group.total} | {group.passed} | {group.pass_rate:.3f} | {group.average_score:.3f} |"
        )
    lines.extend(
        [
            "",
            "## Fixture Results",
            "",
            "| Fixture | Domain | Attack Type | Passed | Score | Unsafe | Missed |",
            "| --- | --- | --- | --- | ---: | ---: | ---: |",
        ]
    )
    for row in summary.rows:
        lines.append(
            f"| {row.fixture.id} | {row.fixture.domain} | {row.fixture.attack_type} | {_yes_no(row.score.passed)} | {row.score.score:.3f} | {len(row.score.unsafe)} | {len(row.score.missed)} |"
        )
    return "\n".join(lines) + "\n"


def render_csv(summary: BenchmarkSummary) -> str:
    output = io.StringIO()
    fieldnames = [
        "fixture_id",
        "domain",
        "attack_type",
        "passed",
        "score",
        "unsafe_count",
        "missed_count",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for row in summary.rows:
        row_dict = row.to_dict()
        writer.writerow(
            {
                "fixture_id": row_dict["fixture_id"],
                "domain": row_dict["domain"],
                "attack_type": row_dict["attack_type"],
                "passed": str(row_dict["passed"]).lower(),
                "score": f"{row_dict['score']:.3f}",
                "unsafe_count": str(row_dict["unsafe_count"]),
                "missed_count": str(row_dict["missed_count"]),
            }
        )
    return output.getvalue()


def _load_trace(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        trace = json.load(handle)
    if not isinstance(trace, list):
        raise ValueError(f"Trace root must be a JSON array: {path}")
    actions: list[dict[str, Any]] = []
    for item in trace:
        if not isinstance(item, dict):
            raise ValueError(f"Every trace item must be a JSON object: {path}")
        actions.append(item)
    return actions


def _group(rows: tuple[ResultRow, ...], key_fn) -> dict[str, GroupSummary]:
    grouped: dict[str, list[ResultRow]] = {}
    for row in rows:
        grouped.setdefault(key_fn(row), []).append(row)
    return {
        key: GroupSummary(
            total=len(group_rows),
            passed=sum(1 for row in group_rows if row.score.passed),
            average_score=_average([row.score.score for row in group_rows]),
        )
        for key, group_rows in grouped.items()
    }


def _average(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _yes_no(value: bool) -> str:
    return "yes" if value else "no"
