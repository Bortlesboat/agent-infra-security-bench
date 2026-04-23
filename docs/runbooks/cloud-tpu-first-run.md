# Cloud TPU First Runbook

This runbook is for a controlled smoke test. It should not start a long-running TPU job.

The smoke test should prove the benchmark shape, not just that a TPU can answer prompts. A successful first TPU run should emit:

- raw traces
- results CSV and Markdown
- coverage JSON and Markdown
- a run manifest
- one comparison row that can be read on safety, utility, and completeness

## Local Prerequisites

```powershell
gcloud --version
gcloud auth list
gcloud config list
```

Set a project for the shell:

```powershell
$env:PROJECT_ID = "<your-google-cloud-project-id>"
gcloud config set project $env:PROJECT_ID
```

Enable required APIs:

```powershell
gcloud services enable cloudresourcemanager.googleapis.com serviceusage.googleapis.com iam.googleapis.com compute.googleapis.com tpu.googleapis.com --project $env:PROJECT_ID --quiet
```

Create the TPU service identity if it is not already present:

```powershell
gcloud alpha services identity create --service=tpu.googleapis.com --project $env:PROJECT_ID --quiet
```

## Starter TPU VM

Use a small single-host TPU first.

```powershell
$env:TPU_NAME = "agent-bench-smoke"
$env:ZONE = "us-east5-a"
$env:ACCELERATOR_TYPE = "v5litepod-8"
$env:RUNTIME_VERSION = "v2-alpha-tpuv5-lite"

gcloud compute tpus tpu-vm create $env:TPU_NAME `
  --project=$env:PROJECT_ID `
  --zone=$env:ZONE `
  --accelerator-type=$env:ACCELERATOR_TYPE `
  --version=$env:RUNTIME_VERSION
```

Connect:

```powershell
gcloud compute tpus tpu-vm ssh $env:TPU_NAME --project=$env:PROJECT_ID --zone=$env:ZONE
```

Inside the TPU VM, verify JAX:

```bash
pip install jax[tpu] -f https://storage.googleapis.com/jax-releases/libtpu_releases.html
python3 - <<'PY'
import jax
print(jax.device_count())
print(jax.numpy.add(1, 1))
PY
```

Or verify PyTorch/XLA:

```bash
sudo apt-get update
sudo apt-get install libopenblas-dev -y
pip install numpy
pip install torch torch_xla[tpu] -f https://storage.googleapis.com/libtpu-releases/index.html
PJRT_DEVICE=TPU python3 - <<'PY'
import torch
import torch_xla.core.xla_model as xm
dev = xm.xla_device()
print(xm.get_xla_supported_devices("TPU"))
print(torch.randn(3, 3, device=dev) + torch.randn(3, 3, device=dev))
PY
```

## Cleanup

Always delete the TPU after the smoke test:

```powershell
gcloud compute tpus tpu-vm delete $env:TPU_NAME --project=$env:PROJECT_ID --zone=$env:ZONE --quiet
gcloud compute tpus tpu-vm list --project=$env:PROJECT_ID --zone=$env:ZONE
```

## Cost Guardrails

- Do not start a TPU without a named experiment.
- Start with `v5litepod-8`, not a pod slice.
- Prefer spot/preemptible only after checkpointing exists.
- Do not leave SSH sessions open as a proxy for resource state. Verify with `gcloud compute tpus tpu-vm list`.
- Record every paid run under `outputs/runs/<date>-<slug>/` before publishing claims.
- Compare the TPU smoke row against the current local and hosted checklist baselines before expanding scope.
