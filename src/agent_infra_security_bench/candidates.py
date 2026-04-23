from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any

from agent_infra_security_bench.fixtures import AgentFixture

SCHEMA_VERSION = "agent-infra-security-bench/candidate-fixture/v1"

PUBLIC_SAFETY_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"AIza[0-9A-Za-z_-]{20,}"),
    re.compile(r"ghp_[0-9A-Za-z]{20,}"),
    re.compile(r"xox[baprs]-[0-9A-Za-z-]+"),
    re.compile(r"BEGIN (RSA|OPENSSH|EC) PRIVATE KEY"),
    re.compile("OPENAI" + r"_API_KEY"),
    re.compile(r"C:[/\\]Users[/\\]andre", re.IGNORECASE),
    re.compile(r"ig_session\.json", re.IGNORECASE),
    re.compile(r"config\.py", re.IGNORECASE),
)


@dataclass(frozen=True)
class CandidateFixture:
    path: Path
    id: str
    source: dict[str, Any]
    review: dict[str, Any]
    fixture_data: dict[str, Any]
    fixture: AgentFixture

    @property
    def review_status(self) -> str:
        status = self.review.get("status")
        return status if isinstance(status, str) else ""


@dataclass(frozen=True)
class CandidateValidationSummary:
    candidate_count: int
    valid_count: int
    accepted_count: int
    invalid_candidates: list[dict[str, str]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_count": self.candidate_count,
            "valid_count": self.valid_count,
            "accepted_count": self.accepted_count,
            "invalid_candidates": self.invalid_candidates,
        }


def load_candidate(path: str | Path) -> CandidateFixture:
    candidate_path = Path(path)
    with candidate_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("Candidate root must be a JSON object")
    _check_public_safety(data)

    schema_version = data.get("schema_version")
    if schema_version != SCHEMA_VERSION:
        raise ValueError(f"Unsupported candidate schema_version: {schema_version}")

    source = data.get("source")
    if not isinstance(source, dict) or not source:
        raise ValueError("Candidate source must be a non-empty object")
    review = data.get("review")
    if not isinstance(review, dict) or not review:
        raise ValueError("Candidate review must be a non-empty object")
    fixture_data = data.get("fixture")
    if not isinstance(fixture_data, dict):
        raise ValueError("Candidate fixture must be a JSON object")

    return CandidateFixture(
        path=candidate_path,
        id=_required_str(data, "id"),
        source=source,
        review=review,
        fixture_data=fixture_data,
        fixture=AgentFixture.from_dict(fixture_data),
    )


def validate_candidate_dir(candidate_dir: str | Path) -> CandidateValidationSummary:
    paths = sorted(Path(candidate_dir).rglob("*.json"))
    valid_count = 0
    accepted_count = 0
    invalid_candidates: list[dict[str, str]] = []
    for path in paths:
        try:
            candidate = load_candidate(path)
        except ValueError as exc:
            invalid_candidates.append({"path": str(path), "error": str(exc)})
            continue
        valid_count += 1
        if candidate.review_status == "accepted":
            accepted_count += 1

    return CandidateValidationSummary(
        candidate_count=len(paths),
        valid_count=valid_count,
        accepted_count=accepted_count,
        invalid_candidates=invalid_candidates,
    )


def promote_candidate(
    candidate_path: str | Path,
    scenario_dir: str | Path,
    *,
    overwrite: bool = False,
) -> Path:
    candidate = load_candidate(candidate_path)
    if candidate.review_status != "accepted":
        raise ValueError("Candidate must be accepted before promotion")

    output_dir = Path(scenario_dir)
    output = output_dir / f"{_fixture_filename(candidate.fixture.id)}.json"
    if output.exists() and not overwrite:
        raise ValueError(f"Promoted fixture already exists: {output}")

    output_dir.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(candidate.fixture_data, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )
    return output


def _check_public_safety(data: dict[str, Any]) -> None:
    text = json.dumps(data, sort_keys=True)
    for pattern in PUBLIC_SAFETY_PATTERNS:
        if pattern.search(text):
            raise ValueError(f"Candidate public-safety check failed: {pattern.pattern}")


def _fixture_filename(fixture_id: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", fixture_id).strip("_").lower()


def _required_str(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"Required string field missing or empty: {key}")
    return value
