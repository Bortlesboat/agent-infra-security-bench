from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "agent-infra-security-bench/compute-commons/v1"

REQUIRED_ARTIFACT_FIELDS = (
    "id",
    "kind",
    "title",
    "summary",
    "status",
    "primary_path",
    "reusable_by_without_accelerator",
)

PATH_FIELDS = (
    "primary_path",
    "report_path",
    "example_path",
    "runbook_path",
)


@dataclass(frozen=True)
class CommonsArtifact:
    id: str
    kind: str
    title: str
    summary: str
    status: str
    primary_path: str
    reusable_by_without_accelerator: str
    source_commit: str | None = None
    report_path: str | None = None
    example_path: str | None = None
    runbook_path: str | None = None
    notes: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CommonsArtifact":
        for field in REQUIRED_ARTIFACT_FIELDS:
            if not isinstance(data.get(field), str) or not data[field].strip():
                raise ValueError(f"Commons artifact is missing string field: {field}")
        optional_strings = {
            key: value for key, value in data.items() if key not in REQUIRED_ARTIFACT_FIELDS
        }
        for field, value in optional_strings.items():
            if value is not None and not isinstance(value, str):
                raise ValueError(f"Commons artifact optional field must be a string: {field}")
        return cls(
            id=data["id"],
            kind=data["kind"],
            title=data["title"],
            summary=data["summary"],
            status=data["status"],
            primary_path=data["primary_path"],
            reusable_by_without_accelerator=data["reusable_by_without_accelerator"],
            source_commit=data.get("source_commit"),
            report_path=data.get("report_path"),
            example_path=data.get("example_path"),
            runbook_path=data.get("runbook_path"),
            notes=data.get("notes"),
        )

    def existing_paths(self) -> dict[str, str]:
        paths: dict[str, str] = {}
        for field in PATH_FIELDS:
            value = getattr(self, field)
            if value:
                paths[field] = value
        return paths


@dataclass(frozen=True)
class CommonsIndex:
    schema_version: str
    name: str
    updated_at: str
    mission: str
    artifacts: tuple[CommonsArtifact, ...]
    missing_paths: list[str]

    def to_summary_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "name": self.name,
            "updated_at": self.updated_at,
            "artifact_count": len(self.artifacts),
            "missing_paths": list(self.missing_paths),
            "artifacts": [
                {
                    "id": artifact.id,
                    "kind": artifact.kind,
                    "status": artifact.status,
                    "primary_path": artifact.primary_path,
                }
                for artifact in self.artifacts
            ],
        }


def load_commons_index(path: str | Path, *, root: str | Path | None = None) -> CommonsIndex:
    index_path = Path(path)
    data = json.loads(index_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Commons index root must be a JSON object")
    return _parse_commons_index(data, root=Path(root) if root else index_path.parent.parent)


def _parse_commons_index(data: dict[str, Any], *, root: Path) -> CommonsIndex:
    if data.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"Unsupported commons schema_version: {data.get('schema_version')}")
    for field in ("name", "updated_at", "mission"):
        if not isinstance(data.get(field), str) or not data[field].strip():
            raise ValueError(f"Commons index is missing string field: {field}")
    raw_artifacts = data.get("artifacts")
    if not isinstance(raw_artifacts, list) or not raw_artifacts:
        raise ValueError("Commons index must contain at least one artifact")

    artifacts: list[CommonsArtifact] = []
    for raw_artifact in raw_artifacts:
        if not isinstance(raw_artifact, dict):
            raise ValueError("Every commons artifact must be a JSON object")
        artifacts.append(CommonsArtifact.from_dict(raw_artifact))

    return CommonsIndex(
        schema_version=data["schema_version"],
        name=data["name"],
        updated_at=data["updated_at"],
        mission=data["mission"],
        artifacts=tuple(artifacts),
        missing_paths=_missing_paths(root, artifacts),
    )


def _missing_paths(root: Path, artifacts: list[CommonsArtifact]) -> list[str]:
    missing: list[str] = []
    for artifact in artifacts:
        for field, value in artifact.existing_paths().items():
            path = root / value
            if not path.exists():
                missing.append(f"{artifact.id}:{field}:{value}")
    return missing
