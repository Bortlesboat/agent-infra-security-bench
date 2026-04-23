from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from agent_infra_security_bench.fixtures import AgentFixture, load_fixture


@dataclass(frozen=True)
class CoverageDetail:
    fixture_id: str
    total_tools: int
    decided_tools: int
    omitted_tools: tuple[str, ...]
    duplicate_tools: tuple[str, ...]

    @property
    def coverage_rate(self) -> float:
        return self.decided_tools / self.total_tools if self.total_tools else 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "fixture_id": self.fixture_id,
            "total_tools": self.total_tools,
            "decided_tools": self.decided_tools,
            "coverage_rate": self.coverage_rate,
            "omitted_tools": list(self.omitted_tools),
            "duplicate_tools": list(self.duplicate_tools),
        }


@dataclass(frozen=True)
class CoverageAnalysisSummary:
    details: tuple[CoverageDetail, ...]

    @property
    def total_fixtures(self) -> int:
        return len(self.details)

    @property
    def total_tools(self) -> int:
        return sum(detail.total_tools for detail in self.details)

    @property
    def decided_tools(self) -> int:
        return sum(detail.decided_tools for detail in self.details)

    @property
    def omitted_tools(self) -> int:
        return sum(len(detail.omitted_tools) for detail in self.details)

    @property
    def duplicate_decision_tools(self) -> int:
        return sum(len(detail.duplicate_tools) for detail in self.details)

    @property
    def coverage_rate(self) -> float:
        return self.decided_tools / self.total_tools if self.total_tools else 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_fixtures": self.total_fixtures,
            "total_tools": self.total_tools,
            "decided_tools": self.decided_tools,
            "omitted_tools": self.omitted_tools,
            "duplicate_decision_tools": self.duplicate_decision_tools,
            "coverage_rate": self.coverage_rate,
            "details": [detail.to_dict() for detail in self.details],
        }


@dataclass(frozen=True)
class CoverageArtifacts:
    summary: CoverageAnalysisSummary
    json_path: Path
    markdown_path: Path


def analyze_suite_coverage(scenario_dir: str | Path, trace_dir: str | Path) -> CoverageAnalysisSummary:
    details: list[CoverageDetail] = []
    for scenario_path in sorted(Path(scenario_dir).glob("*.json")):
        fixture = load_fixture(scenario_path)
        trace = _load_trace(Path(trace_dir) / f"{fixture.id}.json")
        details.append(analyze_trace_coverage(fixture, trace))
    return CoverageAnalysisSummary(tuple(sorted(details, key=lambda detail: detail.fixture_id)))


def analyze_trace_coverage(fixture: AgentFixture, trace: list[dict[str, Any]]) -> CoverageDetail:
    counts: dict[str, int] = {tool.name: 0 for tool in fixture.tools}
    for action in trace:
        tool = action.get("tool")
        decision = action.get("decision")
        if not isinstance(tool, str) or decision not in {"allow", "block"}:
            continue
        if tool in counts:
            counts[tool] += 1

    omitted_tools = tuple(tool for tool, count in counts.items() if count == 0)
    duplicate_tools = tuple(tool for tool, count in counts.items() if count > 1)
    decided_tools = sum(1 for count in counts.values() if count > 0)
    return CoverageDetail(
        fixture_id=fixture.id,
        total_tools=len(fixture.tools),
        decided_tools=decided_tools,
        omitted_tools=omitted_tools,
        duplicate_tools=duplicate_tools,
    )


def render_coverage_markdown(summary: CoverageAnalysisSummary) -> str:
    lines = [
        "# BoundaryBench Tool Decision Coverage",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Total fixtures | {summary.total_fixtures} |",
        f"| Total tools | {summary.total_tools} |",
        f"| Decided tools | {summary.decided_tools} |",
        f"| Omitted tools | {summary.omitted_tools} |",
        f"| Duplicate-decision tools | {summary.duplicate_decision_tools} |",
        f"| Coverage rate | {summary.coverage_rate:.3f} |",
        "",
        "## Fixture Coverage",
        "",
        "| Fixture | Total Tools | Decided Tools | Coverage | Omitted Tools | Duplicate Tools |",
        "| --- | ---: | ---: | ---: | --- | --- |",
    ]
    for detail in summary.details:
        omitted = ", ".join(detail.omitted_tools) if detail.omitted_tools else "none"
        duplicate = ", ".join(detail.duplicate_tools) if detail.duplicate_tools else "none"
        lines.append(
            f"| {detail.fixture_id} | {detail.total_tools} | {detail.decided_tools} | "
            f"{detail.coverage_rate:.3f} | {omitted} | {duplicate} |"
        )
    return "\n".join(lines) + "\n"


def write_coverage_analysis_json(path: str | Path, summary: CoverageAnalysisSummary) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary.to_dict(), indent=2) + "\n", encoding="utf-8")
    return output


def write_coverage_analysis_markdown(path: str | Path, summary: CoverageAnalysisSummary) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_coverage_markdown(summary), encoding="utf-8")
    return output


def write_coverage_artifacts(
    run_dir: str | Path,
    *,
    scenario_dir: str | Path,
    trace_dir: str | Path,
    stem: str = "coverage",
) -> CoverageArtifacts:
    output_dir = Path(run_dir)
    summary = analyze_suite_coverage(scenario_dir, trace_dir)
    json_path = write_coverage_analysis_json(output_dir / f"{stem}.json", summary)
    markdown_path = write_coverage_analysis_markdown(output_dir / f"{stem}.md", summary)
    return CoverageArtifacts(summary=summary, json_path=json_path, markdown_path=markdown_path)


def _load_trace(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        trace = json.load(handle)
    if not isinstance(trace, list):
        raise ValueError(f"Trace root must be a JSON array: {path}")
    return [item for item in trace if isinstance(item, dict)]
