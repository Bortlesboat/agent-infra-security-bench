from pathlib import Path


def test_public_trust_and_launch_files_exist():
    root = Path(__file__).resolve().parents[1]

    required_paths = [
        root / "SECURITY.md",
        root / "CONTRIBUTING.md",
        root / "CITATION.cff",
        root / ".github" / "workflows" / "ci.yml",
        root / ".github" / "ISSUE_TEMPLATE" / "benchmark-fixture.yml",
        root / ".github" / "ISSUE_TEMPLATE" / "results-report.yml",
        root / "docs" / "launch" / "public-launch-packet.md",
        root / "docs" / "reports" / "2026-04-agent-infra-security-baseline-template.md",
        root / "docs" / "grants" / "opportunity-stack.md",
    ]

    missing = [str(path.relative_to(root)) for path in required_paths if not path.exists()]
    assert missing == []


def test_ci_and_readme_preserve_reproducibility_contract():
    root = Path(__file__).resolve().parents[1]
    ci = (root / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    readme = (root / "README.md").read_text(encoding="utf-8")

    assert "python -m pytest" in ci
    assert "agent-bench write-manifest" in readme
    assert "Synthetic traces are control cases" in readme
