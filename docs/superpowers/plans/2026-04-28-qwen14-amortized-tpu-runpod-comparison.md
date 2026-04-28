# Qwen 14B Amortized TPU/RunPod Comparison Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Measure Qwen 14B `scenarios-frontier-v2` TPU-vs-RunPod economics with setup time amortized across multiple matched rows in each live session.

**Architecture:** Run the same three Qwen 14B rows (`baseline + none`, `checklist + none`, `checklist + risk-floor`) once on a single Cloud TPU `v6e-8` Spot session and once on a single RunPod A100-class session. Preserve per-row benchmark results and session-level timing/cost separately so the public report can compare benchmark-only and setup-inclusive economics without double-counting setup.

**Tech Stack:** PowerShell, `gcloud`, `runpodctl`, `vllm`, `agent-bench run-openai-agent`, existing `scripts/tpu-strike.ps1`, BoundaryBench reports/Commons.

---

### Task 1: Preflight And Guardrails

**Files:**
- Modify local workspace todo after the run
- Read: `docs/runbooks/frontier-v2-costed-tpu-gpu-pair.md`

- [ ] Run local validation: `py -m pytest tests/test_frontier_pack_v2.py tests/test_tpu_runbooks.py -q`
- [ ] Check repo cleanliness with `git status --short` and `git diff --check`
- [ ] Confirm no active RunPod benchmark pods with `runpodctl pod list --all -o json`
- [ ] Confirm Google billing starts disabled and no TPU/Compute leftovers exist before any create
- [ ] Start a hidden TPU cleanup watchdog before linking billing for the TPU window

### Task 2: TPU Session

**Files:**
- Read: `docs/runbooks/tpu-frontier-v2-qwen14-first-wave.json`
- Create local-only/private queue if output paths need to avoid overwriting prior rows
- Use: `scripts/tpu-strike.ps1`

- [ ] Link billing only for the approved TPU window
- [ ] Run Qwen 14B first-wave queue on an approved `v6e-8` Spot lane
- [ ] Copy back all three row artifacts
- [ ] Verify the TPU VM is deleted and touched TPU zones are empty
- [ ] Unlink billing immediately after teardown

### Task 3: RunPod Session

**Files:**
- Create local-only session timing/pricing JSON under `outputs/gpu-frontier-v2-qwen14-amortized-session/`

- [ ] Create one secure RunPod A100-class pod with no persistent network volume
- [ ] Install the known-good serving stack in `/root`, not `/workspace`
- [ ] Serve `Qwen/Qwen2.5-14B-Instruct` through vLLM
- [ ] Run the same three `scenarios-frontier-v2` rows through `agent-bench run-openai-agent`
- [ ] Copy results back, stop/delete the pod, and verify `runpodctl pod list` is empty

### Task 4: Publish The Result

**Files:**
- Create: `docs/reports/2026-04-frontier-v2-qwen14-amortized-tpu-runpod-session.md`
- Create: `docs/reports/2026-04-frontier-v2-qwen14-amortized-tpu-runpod-session.json`
- Modify: `README.md`
- Modify: `commons/index.json`
- Modify local memory/todo files after commit

- [ ] Build a session-level comparison table: wall-clock time, benchmark time, hourly meter, total session cost, cost per row, cost per fixture, cost per passed fixture, cost per covered tool decision
- [ ] Keep setup/preemption/allocation friction separate from benchmark-only cost
- [ ] Run tests, Commons validation, whitespace check, public leak scan, RunPod pod verification, and Google billing verification
- [ ] Commit and push the public report
