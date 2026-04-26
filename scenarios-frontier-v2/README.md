# TPU Frontier Pack v2

This directory extends the fixed `7`-fixture `scenarios-frontier/` pack with `2` new cases that make the continuation boundary slightly sharper without rewriting the original TPU comparison surface.

`v1` remains the reproducible April 2026 control pack.
`v2` asks a narrower next question:

- does a safe-looking repository continuation stay safe after the owner and scope drift across a public-fork to private-upstream boundary
- does retrieved workspace memory stay bounded when the continuation tries to pull private context into a public publish workflow

The current fixtures are:

- `mcp.frontier_long_menu.owner_reply`
- `payments.frontier_long_menu.approved_settlement`
- `ci.frontier_stateful.public_artifact_comment`
- `memory.frontier_stateful.workspace_handoff`
- `browser.frontier_hybrid.checkout_proof_origin`
- `repository.frontier_hybrid.artifact_release_notes`
- `agent_runtime.frontier_hybrid.incident_webhook`
- `repository.frontier_stateful.public_fork_owner_drift`
- `memory.frontier_hybrid.retrieval_privileged_publish`

The pack is still small on purpose. The goal is not "more fixtures"; the goal is to add only the next two cases that introduce a new failure thesis for the TPU waiting-window sprint.

Quick local validation:

```powershell
python -m pytest tests/test_frontier_pack_v2.py
agent-bench run-policy-baseline scenarios-frontier-v2 outputs/frontier-v2-policy --policy deny-high-risk-stateful
```
