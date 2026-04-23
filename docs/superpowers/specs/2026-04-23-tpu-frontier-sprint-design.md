# TPU Frontier Sprint Design

Date: 2026-04-23

## Stated Goal

Use the newly granted 30-day Cloud TPU window for project `gmail-claude-485913` to publish the first strong TPU-backed BoundaryBench evidence, then use the remaining window to push the benchmark into a more frontier-style omission and state-pressure regime.

This sprint should produce public, reusable documentation and benchmark artifacts on GitHub, not just a private compute experiment.

## Why This Sprint Exists

BoundaryBench already has useful local, Mac mini, and hosted evidence:

- deterministic policy baselines
- local Windows and Mac mini open-model sweeps
- hosted NVIDIA NIM baselines
- explicit safety, utility, and completeness reporting

What it does not have yet is a real TPU-backed comparison row or a TPU-shaped frontier pack that makes scarcity of compute matter scientifically.

The TPU grant changes the project from "TPU-ready" to "time-boxed frontier opportunity." The right response is to use the TPU immediately while the benchmark is being deepened in parallel.

## External Constraints

### TPU Window

The grant email received on 2026-04-23 gives 30 days of free TPU quota in specific zones. Treat the useful window as ending around 2026-05-23 unless updated by Google.

### Billing Discipline

The TPU portion is free only for newly created TPUs in the approved zones from the grant email. Other Google Cloud services can still incur charges.

Operational rules for this sprint:

- create TPUs only in grant-approved zones
- prefer single-host spot TPU VMs
- avoid GKE, Vertex, and other extra platform layers for the first run
- keep cloud-side state minimal
- after each run, explicitly stop or delete the TPU and verify the final state with `gcloud compute tpus tpu-vm list`

### Supported Inference Direction

As verified against current official docs on 2026-04-23:

- Cloud TPU inference is supported on TPU `v5e` and newer
- `vllm-tpu` supports `v5e` and `v6e`

That makes `spot v6e-8` the preferred first serving lane.

## Sprint Strategy

Run two tracks in parallel.

### Track A: Use TPU Now

Start using the TPU immediately to avoid wasting the 30-day window.

Track A outcomes:

1. bring up one TPU VM safely
2. serve one model through a local OpenAI-compatible endpoint
3. run a tiny smoke subset
4. run the current 34-fixture checklist + risk-floor baseline
5. publish the first TPU comparison row

### Track B: Build The TPU Frontier Pack

While Track A is generating the first evidence row, deepen the benchmark so the TPU can be used on something harder than the current suite.

Track B outcomes:

1. define a small frontier pack that stresses omission and state pressure
2. keep the pack public-safe and benchmark-readable
3. run local/Mac/hosted controls where useful
4. rerun the TPU lane against the new pack

The project should never pause TPU usage waiting for a perfect frontier pack design.

## First TPU Run Design

### Preferred TPU Shape

- project: `gmail-claude-485913`
- primary zone: `us-east1-d`
- primary accelerator: `spot v6e-8`
- fallback accelerator: `spot v5e-8`
- fallback zone: `us-central1-a`

Do not start with `v4` for serving. Even though quota exists, `v5e/v6e` is the correct inference lane for this benchmark.

### Serving Architecture

BoundaryBench should not gain a TPU-only runner. The repo should add a generic OpenAI-compatible model client so the TPU path shares the same trace, scoring, manifest, coverage, and sweep machinery already used by hosted inference.

Recommended repo addition:

- `OpenAICompatibleModelClient`
- CLI entry point like `agent-bench run-openai-agent`

Required arguments:

- `--base-url`
- `--model`
- `--api-key-env` or equivalent env-driven auth hook
- `--prompt-profile`
- `--runtime-policy`
- `--hardware`

This keeps TPU serving, hosted serving, and future backends on one runner shape.

### First TPU Model

Use the easiest reliable instruct model that serves cleanly on `vllm-tpu`.

Default starting candidate:

- `meta-llama/Llama-3.1-8B-Instruct`

If model access or compatibility becomes annoying, switch quickly to another supported instruct model. The first objective is a clean TPU row, not model-selection perfection.

### First TPU Run Phases

1. local preflight
2. TPU VM create
3. server installation and single completion verification
4. benchmark smoke subset
5. full 34-fixture checklist baseline
6. artifact copy-back
7. TPU stop or delete
8. explicit post-run state verification

### First TPU Success Criteria

A successful first TPU run produces:

- raw events
- adapted traces
- results CSV
- results Markdown
- coverage JSON
- coverage Markdown
- manifest
- one directly comparable sweep row

## TPU Frontier Pack Design

The next fixture pack should be TPU-oriented but not uniformly maximalist. The pack should have a clear research shape rather than becoming "everything harder."

### Pack Size

Start with `6-8` fixtures.

This is small enough to design carefully and large enough to create a meaningful second-wave benchmark slice.

### Pack Structure

- `2` long-menu controls
- `2` stateful controls
- `3-4` marquee hybrid fixtures

Optional eighth fixture:

- one "boss fight" hybrid case with the longest tool menu and the clearest safety/utility/completeness split

### What The Pack Is Trying To Prove

The TPU Frontier Pack should make one point clearly:

Under stronger decision pressure, omitted tool decisions are not just a formatting error. They become a safety and utility failure mode.

### Long-Menu Controls

Purpose:

- isolate omission pressure
- use many tools and near-duplicate names
- mix safe and unsafe actions in one decision surface

These should answer:

- does the model respond to every tool?
- does it preserve safe work while blocking unsafe branches?

### Stateful Controls

Purpose:

- isolate workflow-state reasoning
- keep menus smaller
- make one skipped or wrong decision poison the next step

These should answer:

- does the model preserve approval-bound state?
- does it notice when a workflow crosses a trust boundary?

### Marquee Hybrid Fixtures

Purpose:

- combine long tool menus with stateful pressure
- make omission materially consequential

Candidate themes:

- cross-tool payment or proof reuse hidden among many same-family settlement tools
- provenance drift hidden among near-duplicate MCP tools
- repository scope drift inside a mostly-safe workflow continuation
- CI artifact continuation where one skipped decision changes the trust boundary
- memory retrieval/write split where omission causes privilege drift
- multi-destination communication where only one branch is approval-safe

## Documentation And Public Surface

This sprint should publish more than benchmark rows.

Required public GitHub surfaces:

- TPU setup runbook updated to the grant-safe first path
- the first TPU comparison report
- the frontier-pack design and rationale
- clear notes on safety, utility, and completeness
- exact reproduction commands where practical

The tone should stay evidence-first, not hype-first.

## Research Questions

The sprint should aim to answer:

1. Does TPU-backed serving materially change performance on the current 34-fixture checklist baseline?
2. On harder omission/state fixtures, which failures are judgment failures versus completeness failures?
3. Which prompt-layer interventions help completeness without hiding missing-tool behavior behind runtime policy?
4. Does the same model family behave differently when the benchmark moves from compact cases to pressure-heavy cases?

## What Success Looks Like

By the end of the sprint, BoundaryBench should have:

- one safe, verified TPU serving path
- one public TPU baseline row
- one small TPU Frontier Pack
- one public comparison story across local, Mac mini, hosted, and TPU lanes
- stronger GitHub documentation that makes the project look like a real research artifact instead of a private experiment

## Out Of Scope

This sprint does not need to:

- train a custom model
- create a hosted eval platform
- pivot to broad outreach before the evidence is stronger
- make every fixture maximally hybrid

The near-term job is to create frontier-grade public evidence while the TPU window is live.

## Immediate Next Step

After this spec is reviewed, write the implementation plan and execute in this order:

1. generic OpenAI-compatible runner
2. updated TPU runbook
3. first `v6e-8` smoke and 34-fixture TPU row
4. frontier-pack fixture implementation
5. second-wave TPU comparison and public report
