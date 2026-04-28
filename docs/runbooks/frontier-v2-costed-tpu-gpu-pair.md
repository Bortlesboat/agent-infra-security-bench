# Frontier v2 Costed TPU/GPU Pair

Use this when the next objective is cost per comparable BoundaryBench row, not just another pass-rate row.

Do not create TPU or GPU resources until the local preflight passes, pricing is refreshed, teardown verification is part of the run, and the billing boundary is explicitly approved. In this workspace, GPU controls are planning targets only unless a no-cost credit path or other approved billing guardrail is verified first.

## Local preflight

```powershell
python -m pytest tests/test_frontier_pack_v2.py tests/test_tpu_runbooks.py
git diff --check
```

Confirm `scenarios-frontier-v2/` still loads as `9` fixtures and `60` tools before spending cloud time.

## Cloud preflight

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

## TPU path

The TPU side is now costed for nine `scenarios-frontier-v2` rows: Qwen 7B `baseline + none`, Qwen 7B `checklist + none`, Qwen 7B `checklist + risk-floor`, Mistral 7B `baseline + none`, Mistral 7B `checklist + none`, Mistral 7B `checklist + risk-floor`, Qwen 14B `baseline + none`, Qwen 14B `checklist + none`, and Qwen 14B `checklist + risk-floor`. The generated public sweep is `docs/reports/2026-04-frontier-v2-costed-tpu-sweep.md`.

The paired GPU side is still missing. On 2026-04-27 the first G2/L4 attempt failed before VM startup because project-level `GPUS_ALL_REGIONS` was `0`. Even after quota is raised, treat the GPU control as a no-cost/approved-billing-only target; otherwise keep the comparison as a pricing framework plus completed TPU evidence.

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

If a no-cost or approved-billing GPU lane exists, start with Qwen 7B `baseline + none` against the cheapest GPU control that can honestly serve the same model/context. Without that billing boundary, keep this section as a planning template only. The first preferred controls are:

| Row | First GPU control | Fallback |
| --- | --- | --- |
| Qwen 7B `baseline + none` | G2 / L4 | A2 / A100 |
| Qwen 7B `checklist + none` | G2 / L4 | A2 / A100 |
| Qwen 14B `checklist + risk-floor` | A2 / A100 | A3 / H100 |

Serve the model through an OpenAI-compatible endpoint, then run the same benchmark command shape:

The first live GPU-control attempt on 2026-04-27 was intentionally stopped at allocation failure. It attempted the G2/L4 row after local tests and empty-resource checks, but Compute Engine rejected the VM create with `Quota 'GPUS_ALL_REGIONS' exceeded. Limit: 0.0 globally.` Treat that as a preflight blocker, not as a benchmark row.

```powershell
agent-bench run-openai-agent scenarios-frontier-v2 outputs/gpu-frontier-v2-qwen7b-baseline-none `
  --model Qwen/Qwen2.5-7B-Instruct `
  --base-url http://127.0.0.1:8000/v1 `
  --scenario-commit <repo-commit>-frontier-v2 `
  --prompt-profile baseline `
  --runtime-policy none `
  --hardware g2-l4
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

Every live run ends with provider-side verification that the named TPU or GPU resource is gone. Keep project IDs, account emails, public IPs, and secrets out of committed files.
