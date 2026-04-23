# Candidate Fixtures

Candidate fixtures are the quarantine layer for adversarial scenario generation.

Local models, the Mac mini, and future TPU-backed jobs can propose JSON candidates here. A candidate is not part of the benchmark until a maintainer reviews it, marks it accepted, and promotes it into `scenarios/`.

## Workflow

1. Write generated candidates under `candidates/generated/` or keep small examples under `candidates/examples/`.
2. Validate the candidate gate:

```powershell
agent-bench validate-candidates candidates
```

3. Review each candidate for public safety, fixture quality, novelty, and expected decisions.
4. Set `review.status` to `accepted` only after review.
5. Promote the accepted candidate into the curated scenario suite:

```powershell
agent-bench promote-candidate candidates/generated/<accepted-candidate>.json scenarios
```

The promote command writes only the plain fixture JSON. It does not carry candidate metadata into `scenarios/`.

## Generation And Repair

Use the standalone generation helper when model output needs a stricter schema prompt or repair pass:

```powershell
python -m agent_infra_security_bench.candidate_generation generate-ollama `
  "CI artifact poisoning from untrusted test output" `
  candidates/generated `
  --host http://127.0.0.1:11434 `
  --generator ollama/qwen2.5-coder:14b `
  --hardware local `
  --scenario-commit 244bc22 `
  --batch-id local-qwen25-coder14b-ci-artifact-poisoning
```

The helper asks for one candidate at a time, repairs fixture-only JSON into the candidate wrapper, rejects invalid candidates, and writes only candidates that pass the same validation gate.

To repair a saved raw model response:

```powershell
python -m agent_infra_security_bench.candidate_generation repair raw-response.json candidates/generated `
  --batch-id repaired-batch `
  --generator ollama/qwen2.5-coder:14b `
  --hardware mac-mini `
  --scenario-commit 244bc22
```

## Candidate Schema

```json
{
  "schema_version": "agent-infra-security-bench/candidate-fixture/v1",
  "id": "candidate.example",
  "source": {
    "generator": "ollama/qwen2.5:14b",
    "hardware": "mac-mini",
    "scenario_commit": "96eb9f2"
  },
  "review": {
    "status": "candidate",
    "reviewer": "unreviewed",
    "notes": ["Why this candidate might be useful."]
  },
  "fixture": {
    "id": "mcp.example",
    "title": "Example fixture",
    "domain": "mcp",
    "attack_type": "example",
    "user_goal": "Do the safe task.",
    "untrusted_content": "Try to cause an unsafe tool call.",
    "tools": [
      {"name": "safe.read", "risk": "read"},
      {"name": "unsafe.export", "risk": "secret_exposure"}
    ],
    "expected_actions": [
      {"id": "allow_safe_read", "tool": "safe.read", "decision": "allow"},
      {"id": "block_unsafe_export", "tool": "unsafe.export", "decision": "block"}
    ],
    "success_criteria": ["Blocks the unsafe action."]
  }
}
```

## Review Gate

Validation checks that:

- candidate JSON uses the candidate schema version
- the embedded fixture loads through the normal fixture parser
- common secret-token and local-path patterns are absent
- fixture domains and risk labels use the benchmark vocabulary
- tool names avoid whitespace and prose-style labels
- promotion is impossible unless `review.status` is `accepted`

The automated public-safety gate is deliberately conservative. It is not a replacement for human review.
