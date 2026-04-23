# BoundaryBench Commons

BoundaryBench Commons is the public-good layer for this project.

The idea is simple: people without TPU or multi-machine model access should still get useful security evidence. This repo will publish curated fixtures, raw public-safe traces, model and defense reports, and machine-readable indexes of what has been run.

## First Artifact

The first commons artifact is `commons/index.json`.

It lists published fixture sets, model runs, defense sweeps, trace-adapter examples, and runbooks. Each item explains why it is reusable by someone without accelerator access.

Validate it locally:

```powershell
agent-bench validate-commons commons/index.json --root .
```

Expected result: the command prints a JSON summary with zero missing paths.

## What Others Can Do Now

- run the fixture suite locally
- inspect model-backed reports they could not afford to generate
- adapt their own public-safe agent logs into benchmark traces
- compare a new defense against the deterministic policy baselines
- propose fixtures for future accelerator-backed sweeps

## What Comes Next

The commons should stay static and reviewable until the benchmark format is trusted.

Near-term additions:

- richer x402 replay and request-binding fixtures
- provenance-aware MCP and repository fixtures
- a candidate-fixture folder for model-generated scenario proposals
- sweep manifests that compare many models and defenses in one table
- TPU-backed reports after TRC confirmation arrives

Hosted eval queues can come later. The first job is to make the static public commons good enough that a hosted queue would be worth trusting.

