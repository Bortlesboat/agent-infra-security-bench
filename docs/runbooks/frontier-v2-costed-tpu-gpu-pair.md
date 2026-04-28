# Frontier v2 Costed TPU/GPU Pair

Use this when the next objective is cost per comparable BoundaryBench row, not just another pass-rate row.

Do not create TPU or GPU resources until the local preflight passes, pricing is refreshed, teardown verification is part of the run, and the billing boundary is explicitly approved. In this workspace, Google Cloud GPU controls are planning targets only; the practical GPU lane is RunPod credits. The RunPod A100 Qwen 7B triplet and the first Qwen 14B defended row have completed, so use this runbook for cheaper follow-up GPUs or a same-session amortized TPU/GPU comparison.

## Local preflight

```powershell
python -m pytest tests/test_frontier_pack_v2.py tests/test_tpu_runbooks.py
git diff --check
```

Confirm `scenarios-frontier-v2/` still loads as `9` fixtures and `60` tools before spending cloud time.

## Google Cloud preflight

Use this only if Google Cloud GPU controls are reconsidered later. The active no-cash direction is RunPod, not G2/A2/A3 on this Google Cloud project.

Before any GPU control, check the global GPU quota in addition to regional GPU-family quota. Regional L4 quota can look available while the project is still blocked by `GPUS_ALL_REGIONS=0`.

```powershell
$projectQuota = gcloud compute project-info describe --format=json | ConvertFrom-Json
$projectQuota.quotas |
  Where-Object { $_.metric -eq "GPUS_ALL_REGIONS" } |
  Select-Object metric,limit,usage

$region = "us-central1"
$regionQuota = gcloud compute regions describe $region --format=json | ConvertFrom-Json
$regionQuota.quotas |
  Where-Object { $_.metric -match "NVIDIA_L4|GPU_FAMILY:NVIDIA_L4|NVIDIA_A100|GPU_FAMILY:NVIDIA_H100|NVIDIA_H100" } |
  Select-Object metric,limit,usage
```

Do not start a G2, A2, or A3 VM unless `GPUS_ALL_REGIONS` has enough unused headroom for the requested GPU count and the billing boundary is explicitly no-cost or approved. On 2026-04-27, the first G2/L4 control attempt failed before benchmark startup because regional L4 quota showed one available GPU but `GPUS_ALL_REGIONS` was `0`.

Also check for stale strike processes before new live resources:

```powershell
Get-CimInstance Win32_Process |
  Where-Object { $_.CommandLine -match "tpu-strike|frontier-v2-qwen7b|tpu-vm create|gpu-qwen7b-l4" } |
  Select-Object ProcessId,ParentProcessId,Name,CommandLine
```

If a stale strike process is still creating retry-shaped TPU names, stop that process and delete the named TPU VM before attempting the GPU control. End the preflight with empty provider lists for all touched TPU zones and Compute Engine instances.

## RunPod credit preflight

RunPod credits are the preferred GPU control lane because they produced the first paired GPU rows without re-linking Google Cloud billing. Do not launch another pod until all of these checks pass:

- `runpodctl` is installed and authenticated.
- The RunPod account has enough credits for at least one hour of the selected pod shape.
- Auto-pay is disabled in the RunPod console, or Andy explicitly accepts the card-reload risk. As of 2026-04-28, `runpodctl user` does not expose an auto-pay field.
- `currentSpendPerHr` is zero, or any existing storage burn is identified and explicitly accepted as unrelated baseline spend before the run.
- `runpodctl pod list --all` shows no unexpected running pods.
- The target GPU is available from `runpodctl gpu list --include-unavailable`.
- The chosen pod shape uses one GPU, minimal disk, no persistent network volume unless intentionally needed, and a hard stop timer.

Safe read-only checks:

```powershell
runpodctl user -o json
runpodctl pod list --all -o json
runpodctl network-volume list -o json
runpodctl gpu list --include-unavailable -o json
runpodctl template search vllm -o json
```

The local 2026-04-28 run showed configured RunPod access, positive credits, no benchmark pods left running after teardown, one pre-existing exited pod with retained volume storage, and a non-zero current-spend baseline from that storage. The completed A100 control deleted the benchmark pod and temporary template, then verified spend returned to that baseline.

Do not record RunPod account IDs, account emails, public pod IPs, pod IDs, API keys, or exact credit balance in public files.

## Pricing snapshot

Refresh the launch-time public price before every run. Spot prices are dynamic, so the queue snapshots are starting defaults, not a substitute for a fresh check.

Minimum `pricing.json` shape:

```json
{
  "provider": "google-cloud",
  "zone": "europe-west4-a",
  "pricing_checked_at": "2026-04-27",
  "pricing_source_url": "https://cloud.google.com/spot-vms/pricing",
  "pricing_basis": "Current public Spot TPU table; refresh at launch.",
  "provisioning_model": "spot",
  "accelerator_type": "v6e-8",
  "accelerator_count": 8,
  "accelerator_hourly_meter_usd": 0.748824,
  "full_node_hourly_meter_usd": 5.990592,
  "currency": "USD",
  "requires_launch_time_refresh": true
}
```

For accelerator-optimized GPU controls, use the whole-machine hourly meter from the public Compute Engine table, not just the GPU component price.

For RunPod controls, the public docs say Pods are billed by the second for compute and storage, current GPU prices are visible in the console during deployment, and the Pods API returns `costPerHr` plus `adjustedCostPerHr`. Capture both the pre-launch price shown in console/CLI and the post-create `adjustedCostPerHr` from the pod record.

## TPU path

The TPU side is now costed for nine `scenarios-frontier-v2` rows: Qwen 7B `baseline + none`, Qwen 7B `checklist + none`, Qwen 7B `checklist + risk-floor`, Mistral 7B `baseline + none`, Mistral 7B `checklist + none`, Mistral 7B `checklist + risk-floor`, Qwen 14B `baseline + none`, Qwen 14B `checklist + none`, and Qwen 14B `checklist + risk-floor`. The generated public sweep is `docs/reports/2026-04-frontier-v2-costed-tpu-sweep.md`.

The first paired GPU side now exists for Qwen 7B on RunPod A100, and the defended Qwen 14B GPU control now exists on RunPod A100 SXM. On 2026-04-27 the first Google G2/L4 attempt failed before VM startup because project-level `GPUS_ALL_REGIONS` was `0`. Even after quota is raised, treat Google GPU controls as no-cost/approved-billing-only targets; otherwise keep Google GPU as planning-only and use RunPod credits for live rows.

For future TPU rows, use the cost-aware strike queues. The strike script records timing around create, ready, SSH, bootstrap, benchmark, copy-back, and delete; primes TPU VM SSH metadata with `gcloud` before native OpenSSH transport; normalizes generated shell scripts to LF; uses pid-file remote polling; creates a Python 3.11 venv; then annotates copied manifests after teardown verification.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/tpu-strike.ps1 `
  -QueueFile docs/runbooks/tpu-frontier-v2-qwen7b-baseline-v6e-retry.json
```

Expected per-run output after a completed lane:

- `manifest.json` with `pricing_snapshot`, `timing`, `reliability`, and `derived_costs`
- `cost-metadata/pricing.json`
- `cost-metadata/timing.json`
- `cost-metadata/reliability.json`

The script does not make a failed pre-benchmark allocation look like a benchmark row. If a lane preempts before copy-back, preserve the console log as friction evidence and run the next lane.

## GPU control path

Use RunPod credits first. The Qwen 7B A100 triplet is complete, and the Qwen 14B defended A100 row is complete. The next live GPU control should try a cheaper one-GPU shape that can honestly serve the same model and `4096` context, or run a same-session amortized comparison. The Google G2/A2/A3 rows remain fallback planning targets, not the active lane.

| Row | First GPU control | Fallback |
| --- | --- | --- |
| Qwen 7B prompt/runtime triplet | Completed on RunPod A100 80GB | Repeat only for same-session amortization or regression checks |
| Qwen 7B `baseline + none` cheaper rerun | RunPod L4 if available | RunPod RTX A5000, RTX 3090, or RTX 4090 |
| Qwen 14B `checklist + risk-floor` | Completed on RunPod A100 SXM 80GB | Repeat only for same-session amortization, H100 throughput, or quantized cheaper-GPU fit tests |

Serve the model through an OpenAI-compatible endpoint, then run the same benchmark command shape:

The first live GPU-control attempt on 2026-04-27 was intentionally stopped at allocation failure. It attempted the G2/L4 row after local tests and empty-resource checks, but Compute Engine rejected the VM create with `Quota 'GPUS_ALL_REGIONS' exceeded. Limit: 0.0 globally.` Treat that as a preflight blocker, not as a benchmark row.

The first 2026-04-28 RunPod control completed three Qwen 7B A100 rows: `baseline + none` at `5/9`, `checklist + none` at `7/9`, and `checklist + risk-floor` at `9/9`. The cheaper GPU path had real setup friction before that success: A5000 allocation disappeared, 4090 pods failed allocation/readiness, and the first A100 serving stack needed vLLM/Transformers pinning. A later Qwen 14B A100 SXM row completed `checklist + risk-floor` at `9/9` with benchmark-only cost `$0.019522`, but the one-off session hit setup friction from a network-mounted venv and only became stable after moving the venv to `/root`. Preserve those failures as friction evidence, not benchmark rows.

```powershell
agent-bench run-openai-agent scenarios-frontier-v2 outputs/gpu-frontier-v2-qwen7b-baseline-none `
  --model Qwen/Qwen2.5-7B-Instruct `
  --base-url http://127.0.0.1:8000/v1 `
  --scenario-commit <repo-commit>-frontier-v2 `
  --prompt-profile baseline `
  --runtime-policy none `
  --hardware runpod-rtx4090
```

Example RunPod launch shape, to be refreshed before use:

```powershell
runpodctl pod create `
  --name frontier-v2-qwen7b-gpu-control `
  --template-id <refreshed-vllm-or-pytorch-template-id> `
  --gpu-id "NVIDIA GeForce RTX 4090" `
  --gpu-count 1 `
  --cloud-type SECURE `
  --container-disk-in-gb 20 `
  --volume-in-gb 40 `
  --ports "8000/http,22/tcp" `
  -o json
```

Immediately after create, save a private copy of the pod JSON, extract only non-sensitive cost fields into `pricing.json`, and start a local teardown timer. If the pod never reaches SSH or serving readiness, terminate it and preserve the allocation failure as friction evidence rather than calling it a benchmark row.

Minimum RunPod `pricing.json` shape:

```json
{
  "provider": "runpod",
  "pricing_checked_at": "2026-04-28",
  "pricing_source_url": "https://docs.runpod.io/pods/pricing",
  "pricing_basis": "RunPod credits per hour from launch console and pod adjustedCostPerHr; refresh at launch.",
  "cloud_type": "SECURE",
  "gpu_id": "NVIDIA GeForce RTX 4090",
  "gpu_count": 1,
  "credits_per_hour": 0.0,
  "adjusted_credits_per_hour": 0.0,
  "full_node_hourly_meter_usd": 0.0,
  "currency": "USD-credit-equivalent",
  "requires_launch_time_refresh": true
}
```

Create `pricing.json`, `timing.json`, and `reliability.json` beside the copied run output, then annotate the manifest:

```powershell
agent-bench annotate-run-cost <path-to-manifest.json> `
  --pricing-json <path-to-pricing.json> `
  --timing-json <path-to-timing.json> `
  --reliability-json <path-to-reliability.json> `
  --root .
```

Minimum `timing.json` shape:

```json
{
  "create_requested_at": "2026-04-27T12:00:00Z",
  "ready_at": "2026-04-27T12:04:00Z",
  "serve_ready_at": "2026-04-27T12:11:00Z",
  "benchmark_started_at": "2026-04-27T12:12:00Z",
  "benchmark_finished_at": "2026-04-27T12:20:00Z",
  "copyback_finished_at": "2026-04-27T12:21:00Z",
  "delete_requested_at": "2026-04-27T12:22:00Z",
  "delete_verified_at": "2026-04-27T12:23:00Z"
}
```

Minimum `reliability.json` shape:

```json
{
  "preemption_count": 0,
  "teardown_verified": true,
  "operator_minutes": 0,
  "operator_rate_usd_per_minute": 0
}
```

## Costed comparison

After both manifests are annotated, build the sweep:

```powershell
agent-bench write-sweep-index docs/reports/2026-04-frontier-v2-costed-tpu-gpu-sweep.json `
  <tpu-manifest.json> `
  <gpu-manifest.json> `
  --name "Frontier v2 Costed TPU/GPU Sweep" `
  --markdown docs/reports/2026-04-frontier-v2-costed-tpu-gpu-sweep.md `
  --root .
```

The Markdown includes a cost table only when at least one manifest has `derived_costs`.

## Stop condition

Every live run ends with provider-side verification that the named TPU or GPU resource is gone. On RunPod, stopping is not enough when no data retention is needed; delete/terminate the pod after copy-back and verify no running pod remains. If preflight started with `currentSpendPerHr = 0`, the final RunPod user check must return to zero. If there was accepted pre-existing storage burn, final spend must return to the recorded pre-run baseline. Keep project IDs, account emails, public IPs, pod IDs, exact balances, and secrets out of committed files.
