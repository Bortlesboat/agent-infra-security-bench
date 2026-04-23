# TPU Frontier Pack v1

This directory is the first harder benchmark slice beyond the published 34-fixture control suite in `scenarios/`.

It is intentionally small and sharp:

- `2` long-menu controls that stress omission pressure with many near-duplicate tools
- `2` stateful controls that isolate workflow continuation and provenance drift
- `3` hybrid fixtures that combine long menus with stateful continuation pressure

The current fixtures are:

- `mcp.frontier_long_menu.owner_reply`
- `payments.frontier_long_menu.approved_settlement`
- `ci.frontier_stateful.public_artifact_comment`
- `memory.frontier_stateful.workspace_handoff`
- `browser.frontier_hybrid.checkout_proof_origin`
- `repository.frontier_hybrid.artifact_release_notes`
- `agent_runtime.frontier_hybrid.incident_webhook`

This pack is meant to answer a different question than the 34-fixture control row. The control row shows whether a model or defense stack can solve the current public-safe benchmark cleanly. The frontier pack asks whether that same stack stays safe, useful, and complete when:

- the tool menu gets longer
- same-family tools become harder to distinguish
- low-risk tools become unsafe only after provenance drift
- payment tools stay syntactically valid while approval-bound state changes
- one skipped decision can break the rest of the workflow

Quick local validation:

```powershell
python -m pytest tests/test_frontier_pack.py
agent-bench run-policy-baseline scenarios-frontier outputs/frontier-policy --policy deny-high-risk-stateful
```

The frontier pack is kept separate so the published 34-fixture reports, sweep rows, and Commons index remain a clean control surface while harder TPU-targeted experiments are still evolving.
