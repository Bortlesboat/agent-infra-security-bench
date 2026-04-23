# Cloud TPU First Runbook

This runbook is for the first controlled TPU-backed BoundaryBench baseline. Keep it narrow: one single-host spot TPU VM, one local vLLM server, one smoke subset, one full checklist baseline, then explicit shutdown verification.

Keep literal project IDs, API keys, Hugging Face tokens, external IPs, and SSH transcripts out of the repo. Use local shell variables or private env files only.

This runbook was refreshed against the official Cloud TPU and vLLM TPU docs on 2026-04-23:

- [Cloud TPU inference](https://docs.cloud.google.com/tpu/docs/tpu-inference)
- [Manage TPU Spot VMs](https://docs.cloud.google.com/tpu/docs/spot)
- [Manage TPU resources](https://docs.cloud.google.com/tpu/docs/managing-tpus-tpu-vm)
- [TPU software versions](https://docs.cloud.google.com/tpu/docs/runtimes)
- [TPU v6e](https://docs.cloud.google.com/tpu/docs/v6e)
- [vLLM TPU quickstart](https://docs.vllm.ai/projects/tpu/en/latest/getting_started/quickstart/)

## What This Run Must Produce

A successful first TPU run should emit:

- raw events
- adapted traces
- results CSV and Markdown
- coverage JSON and Markdown
- a run manifest
- one directly comparable TPU sweep row

## No-Surprises Rules

- Create TPUs only in grant-approved zones.
- Primary lane: `spot v6e-8` in `us-east1-d`.
- Fallback lane: TPU `v5e` in `us-central1-a` using the current `gcloud` accelerator name `v5litepod-8`.
- Use a direct TPU VM for the first run. Do not add GKE, Vertex, or other platform layers yet.
- Keep one TPU VM alive at a time.
- Cloud TPU charges can accrue while a node is `READY`; do not leave an idle TPU running.
- Other Google Cloud services can still bill even during the free TPU window.
- For this sprint, prefer `delete` at the end of each spot session. The TPU Spot VM docs say Spot VMs cannot be restarted after preemption, so delete is the safest session-ending habit.
- Do not commit `.env` files, project identifiers, tokens, TPU addresses, or copied cloud shell history.

## Local Preflight (Non-Billed)

Run these locally before any TPU create:

```powershell
$env:PROJECT_ID = "<your-grant-approved-project-id>"
$env:PRIMARY_ZONE = "us-east1-d"
$env:FALLBACK_ZONE = "us-central1-a"

gcloud --version
gcloud auth list
gcloud config set project $env:PROJECT_ID
gcloud services enable cloudresourcemanager.googleapis.com serviceusage.googleapis.com iam.googleapis.com compute.googleapis.com tpu.googleapis.com --project $env:PROJECT_ID --quiet
gcloud alpha services identity create --service=tpu.googleapis.com --project $env:PROJECT_ID --quiet

gcloud compute tpus tpu-vm versions list --zone=$env:PRIMARY_ZONE
gcloud compute tpus tpu-vm accelerator-types list --zone=$env:PRIMARY_ZONE
gcloud compute tpus tpu-vm versions list --zone=$env:FALLBACK_ZONE
gcloud compute tpus tpu-vm accelerator-types list --zone=$env:FALLBACK_ZONE
```

As of the 2026-04-23 doc check, the common PyTorch/JAX runtime versions are:

- `v2-alpha-tpuv6e` for `v6e`
- `v2-alpha-tpuv5-lite` for `v5e`

Still verify the live runtime list immediately before create.

## Primary TPU Create

Use this first:

```powershell
$env:TPU_NAME = "agent-bench-v6e-smoke"
$env:ZONE = "us-east1-d"
$env:ACCELERATOR_TYPE = "v6e-8"
$env:RUNTIME_VERSION = "v2-alpha-tpuv6e"

gcloud compute tpus tpu-vm create $env:TPU_NAME `
  --project=$env:PROJECT_ID `
  --zone=$env:ZONE `
  --accelerator-type=$env:ACCELERATOR_TYPE `
  --version=$env:RUNTIME_VERSION `
  --spot

gcloud compute tpus tpu-vm describe $env:TPU_NAME `
  --project=$env:PROJECT_ID `
  --zone=$env:ZONE
```

Confirm the describe output includes `spot: true`.

## Fallback TPU Create

Use this only if the primary lane cannot get capacity:

```powershell
$env:TPU_NAME = "agent-bench-v5e-smoke"
$env:ZONE = "us-central1-a"
$env:ACCELERATOR_TYPE = "v5litepod-8"
$env:RUNTIME_VERSION = "v2-alpha-tpuv5-lite"

gcloud compute tpus tpu-vm create $env:TPU_NAME `
  --project=$env:PROJECT_ID `
  --zone=$env:ZONE `
  --accelerator-type=$env:ACCELERATOR_TYPE `
  --version=$env:RUNTIME_VERSION `
  --spot

gcloud compute tpus tpu-vm describe $env:TPU_NAME `
  --project=$env:PROJECT_ID `
  --zone=$env:ZONE
```

## Connect To The TPU VM

```powershell
gcloud compute tpus tpu-vm ssh $env:TPU_NAME `
  --project=$env:PROJECT_ID `
  --zone=$env:ZONE
```

## Prepare The TPU VM

Inside the TPU VM:

```bash
python3 --version
python3 -m pip install --user uv
export PATH="$HOME/.local/bin:$PATH"

uv venv ~/.venvs/boundarybench
source ~/.venvs/boundarybench/bin/activate
uv pip install vllm-tpu

python -c '
import jax
import vllm
import importlib.metadata
from vllm.platforms import current_platform
print(f"vllm version: {vllm.__version__}")
print(f"tpu_inference version: {importlib.metadata.version(\"tpu_inference\")}")
print(f"vllm platform: {current_platform.get_device_name()}")
print(f"jax devices: {jax.devices()}")
'
```

## Get The Repo Onto The TPU VM

Use one of these paths:

1. Preferred after push: clone the repo and check out the exact commit you want to benchmark.
2. Temporary local-only path: copy the working tree with `gcloud compute tpus tpu-vm scp --recurse`.

Example clone flow inside the TPU VM:

```bash
git clone <repo-url> ~/agent-infra-security-bench
cd ~/agent-infra-security-bench
git checkout <commit-or-branch>
source ~/.venvs/boundarybench/bin/activate
uv pip install -e .
export SCENARIO_COMMIT="$(git rev-parse HEAD)"
```

## Serve One Model With vLLM

Start with the easiest instruct model that serves cleanly. If a gated model slows the sprint down, switch to another supported instruct model instead of blocking the first TPU row.

Example:

```bash
export MODEL_ID="meta-llama/Llama-3.1-8B-Instruct"

source ~/.venvs/boundarybench/bin/activate
vllm serve "$MODEL_ID" \
  --download_dir /tmp \
  --tensor_parallel_size=1 \
  --max-model-len=2048
```

## Verify One OpenAI-Compatible Request

Open a second TPU VM shell and verify the exact API surface the benchmark uses:

```bash
curl http://127.0.0.1:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "meta-llama/Llama-3.1-8B-Instruct",
    "messages": [{"role": "user", "content": "Reply with the single word ready."}],
    "temperature": 0,
    "max_tokens": 8,
    "stream": false
  }'
```

Do not move to the benchmark until this returns valid JSON.

## Create A 3-Fixture Smoke Subset

Inside the repo on the TPU VM:

```bash
mkdir -p scenarios-smoke
cp scenarios/mcp_tool_shadowing_wallet_export.json scenarios-smoke/
cp scenarios/x402_fresh_payment_control.json scenarios-smoke/
cp scenarios/x402_replay_payment.json scenarios-smoke/
```

## Run The Smoke Subset

Run the new generic OpenAI-compatible runner against the local vLLM endpoint:

```bash
source ~/.venvs/boundarybench/bin/activate

python -m agent_infra_security_bench.cli run-openai-agent \
  scenarios-smoke \
  outputs/tpu-v6e-smoke \
  --model "$MODEL_ID" \
  --base-url http://127.0.0.1:8000/v1 \
  --scenario-commit "$SCENARIO_COMMIT" \
  --prompt-profile checklist \
  --runtime-policy risk-floor \
  --hardware tpu-v6e
```

The local TPU loopback server does not need an API key, so omit `--api-key` and `--api-key-env` unless you explicitly add auth to the serving layer.

## Run The Full 34-Fixture Baseline

```bash
source ~/.venvs/boundarybench/bin/activate

python -m agent_infra_security_bench.cli run-openai-agent \
  scenarios \
  outputs/tpu-v6e-baseline-34 \
  --model "$MODEL_ID" \
  --base-url http://127.0.0.1:8000/v1 \
  --scenario-commit "$SCENARIO_COMMIT" \
  --prompt-profile checklist \
  --runtime-policy risk-floor \
  --hardware tpu-v6e
```

## Copy Artifacts Back Locally

From the local machine:

```powershell
gcloud compute tpus tpu-vm scp --recurse `
  $env:TPU_NAME`:~/agent-infra-security-bench/outputs/tpu-v6e-smoke `
  ./outputs `
  --zone=$env:ZONE

gcloud compute tpus tpu-vm scp --recurse `
  $env:TPU_NAME`:~/agent-infra-security-bench/outputs/tpu-v6e-baseline-34 `
  ./outputs `
  --zone=$env:ZONE
```

After copy-back, validate the imported artifacts locally before writing any public report.

## Shutdown And Verify

Delete the TPU at the end of the session:

```powershell
gcloud compute tpus tpu-vm delete $env:TPU_NAME `
  --project=$env:PROJECT_ID `
  --zone=$env:ZONE `
  --quiet

gcloud compute tpus tpu-vm list `
  --project=$env:PROJECT_ID `
  --zone=$env:ZONE
```

The safest end state for this sprint is: no TPU VM listed in the zone after the session completes.
