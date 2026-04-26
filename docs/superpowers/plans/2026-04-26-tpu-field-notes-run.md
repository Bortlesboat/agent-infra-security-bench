# TPU Field Notes Run Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce one fresh, public-safe TPU v6e field-notes artifact that shows what real open-model TPU serving can measure for readers who do not have TPU access.

**Architecture:** Reuse the existing OpenAI-compatible runner and artifact format. Keep the live TPU session short-lived: validate locally, create one spot `v6e-8` TPU VM, serve one known-good open model with vLLM, run the expanded frontier v2 pack, copy artifacts back, and delete the TPU before writing the public synthesis.

**Tech Stack:** Python 3.11+, pytest, Google Cloud TPU VM, vLLM TPU, BoundaryBench OpenAI-compatible runner, PowerShell local orchestration, Markdown reports.

---

## File Structure

- Existing measurement target: `scenarios-frontier-v2/`
- Existing local test: `tests/test_frontier_pack_v2.py`
- Create live artifacts under: `outputs/tpu-v6e-field-notes-qwen7b-frontier-v2-*`
- Create report: `docs/reports/2026-04-tpu-field-notes-gpu-depreciation.md`
- Optional create sweep index: `docs/reports/2026-04-tpu-field-notes-sweep.{json,md}`
- Do not modify or expose local project IDs, tokens, TPU IPs, or shell transcripts.

## Chunk 1: Local Validation

- [ ] **Step 1: Verify repo state without changing unrelated untracked files**

Run:

```powershell
git status --short --branch
```

Expected: note any unrelated untracked files and leave them intact.

- [ ] **Step 2: Validate the frontier v2 pack locally**

Run:

```powershell
python -m pytest tests/test_frontier_pack_v2.py -v
```

Expected: both tests pass, including `1/9` for payment-state-only policy and `9/9` for full stateful policy.

- [ ] **Step 3: Run deterministic baselines and save local control artifacts**

Run:

```powershell
python -m agent_infra_security_bench.cli run-policy-baseline scenarios-frontier-v2 outputs/frontier-v2-policy-controls --policy deny-high-risk-payment-state --scenario-commit frontier-v2-working-tree
python -m agent_infra_security_bench.cli run-policy-baseline scenarios-frontier-v2 outputs/frontier-v2-policy-controls --policy deny-high-risk-stateful --scenario-commit frontier-v2-working-tree
```

Expected: local control artifacts exist and match the test expectation.

## Chunk 2: TPU Preflight

- [ ] **Step 1: Confirm local Google Cloud state without creating resources**

Run:

```powershell
gcloud --version
gcloud auth list
gcloud config list
gcloud compute tpus tpu-vm list --zone=europe-west4-a
gcloud compute tpus tpu-vm accelerator-types list --zone=europe-west4-a
gcloud compute tpus tpu-vm versions list --zone=europe-west4-a
```

Expected: no existing TPU VM is left running in the target zone; `v6e-8` and `v2-alpha-tpuv6e` are visible.

- [ ] **Step 2: Set a public-safe run label**

Use `agent-bench-v6e-fieldnotes-0426` as the TPU VM name and do not write the literal project ID into any committed file.

## Chunk 3: Live TPU Measurement

- [ ] **Step 1: Create one spot TPU VM**

Run:

```powershell
gcloud compute tpus tpu-vm create agent-bench-v6e-fieldnotes-0426 `
  --zone=europe-west4-a `
  --accelerator-type=v6e-8 `
  --version=v2-alpha-tpuv6e `
  --spot
```

Expected: TPU reaches `READY` and `HEALTHY`.

- [ ] **Step 2: Prepare the TPU VM**

Inside the TPU VM:

```bash
python3 --version
python3 -m pip install --user uv
export PATH="$HOME/.local/bin:$PATH"
uv venv ~/.venvs/boundarybench
source ~/.venvs/boundarybench/bin/activate
uv pip install vllm-tpu
git clone https://github.com/Bortlesboat/agent-infra-security-bench ~/agent-infra-security-bench
cd ~/agent-infra-security-bench
```

If the expanded frontier v2 pack is not yet committed publicly, copy only `scenarios-frontier-v2/` and `tests/test_frontier_pack_v2.py` from the local machine.

- [ ] **Step 3: Serve Qwen 7B through vLLM**

Inside the TPU VM:

```bash
source ~/.venvs/boundarybench/bin/activate
uv pip install -e .
export MODEL_ID="Qwen/Qwen2.5-7B-Instruct"
vllm serve "$MODEL_ID" --download_dir /tmp --tensor_parallel_size=1 --max-model-len=4096
```

Expected: local OpenAI-compatible endpoint listens on `127.0.0.1:8000`.

- [ ] **Step 4: Verify one API request**

Inside a second TPU shell:

```bash
curl http://127.0.0.1:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"Qwen/Qwen2.5-7B-Instruct","messages":[{"role":"user","content":"Reply with the single word ready."}],"temperature":0,"max_tokens":8,"stream":false}'
```

Expected: valid JSON completion.

- [ ] **Step 5: Run the field-notes matrix**

Inside the TPU VM:

```bash
export SCENARIO_COMMIT="$(git rev-parse HEAD)-frontier-v2-working-tree"

time python -m agent_infra_security_bench.cli run-openai-agent scenarios-frontier-v2 outputs/tpu-v6e-field-notes-qwen7b-frontier-v2-baseline-none \
  --model "$MODEL_ID" \
  --base-url http://127.0.0.1:8000/v1 \
  --scenario-commit "$SCENARIO_COMMIT" \
  --prompt-profile baseline \
  --runtime-policy none \
  --hardware tpu-v6e

time python -m agent_infra_security_bench.cli run-openai-agent scenarios-frontier-v2 outputs/tpu-v6e-field-notes-qwen7b-frontier-v2-checklist-none \
  --model "$MODEL_ID" \
  --base-url http://127.0.0.1:8000/v1 \
  --scenario-commit "$SCENARIO_COMMIT" \
  --prompt-profile checklist \
  --runtime-policy none \
  --hardware tpu-v6e
```

Optional if the first two rows are clean and time remains:

```bash
time python -m agent_infra_security_bench.cli run-openai-agent scenarios-frontier-v2 outputs/tpu-v6e-field-notes-qwen7b-frontier-v2-checklist-risk-floor \
  --model "$MODEL_ID" \
  --base-url http://127.0.0.1:8000/v1 \
  --scenario-commit "$SCENARIO_COMMIT" \
  --prompt-profile checklist \
  --runtime-policy risk-floor \
  --hardware tpu-v6e
```

Expected: each run writes raw events, traces, results, coverage, and manifest artifacts.

- [ ] **Step 6: Copy artifacts back locally**

Run locally:

```powershell
gcloud compute tpus tpu-vm scp --recurse agent-bench-v6e-fieldnotes-0426:~/agent-infra-security-bench/outputs/tpu-v6e-field-notes-qwen7b-frontier-v2-baseline-none ./outputs --zone=europe-west4-a
gcloud compute tpus tpu-vm scp --recurse agent-bench-v6e-fieldnotes-0426:~/agent-infra-security-bench/outputs/tpu-v6e-field-notes-qwen7b-frontier-v2-checklist-none ./outputs --zone=europe-west4-a
```

Copy the optional defended row too if it ran.

- [ ] **Step 7: Delete the TPU and verify empty zone**

Run locally:

```powershell
gcloud compute tpus tpu-vm delete agent-bench-v6e-fieldnotes-0426 --zone=europe-west4-a --quiet
gcloud compute tpus tpu-vm list --zone=europe-west4-a
```

Expected: the target zone lists no active TPU VM from this run.

## Chunk 4: Public Field Report

- [ ] **Step 1: Build a small sweep table from copied manifests**

Run:

```powershell
python -m agent_infra_security_bench.cli write-sweep-index docs/reports/2026-04-tpu-field-notes-sweep.json <manifest paths> --name "TPU Field Notes Frontier v2 Sweep" --markdown docs/reports/2026-04-tpu-field-notes-sweep.md --root .
```

Expected: sweep table includes pass rate, unsafe count, missed count, and coverage rate.

- [ ] **Step 2: Write the field-notes report**

Create `docs/reports/2026-04-tpu-field-notes-gpu-depreciation.md` with:

- what was measured
- what TPU access exposed that public accounting debate cannot
- setup/provisioning notes without secrets
- model/config rows
- pass, unsafe, missed, and coverage metrics
- bounded connection to GPU depreciation and TPU substitution

- [ ] **Step 3: Verify locally**

Run:

```powershell
python -m pytest tests/test_frontier_pack_v2.py -v
python -m agent_infra_security_bench.cli validate-commons commons/index.json --root .
git diff --check
```

Expected: tests pass, Commons validation still passes, and whitespace diff check is clean.

## Completion Boundary

The work is complete only after the TPU VM is deleted or no TPU VM was created. If cloud capacity blocks the run, publish a preflight-only note only after verifying no resources remain running.
