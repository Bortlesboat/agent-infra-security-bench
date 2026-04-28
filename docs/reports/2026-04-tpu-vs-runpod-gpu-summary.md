# TPU vs RunPod GPU: First Paired Cost Result

Date: 2026-04-28

## Short Version

The first paired GPU control is now measured.

For the same `scenarios-frontier-v2` Qwen 7B BoundaryBench workload, a RunPod credit-backed A100 row was cheaper than the completed Cloud TPU `v6e-8` Spot rows.

That is not a universal "GPU beats TPU" claim. It is narrower and more useful:

> for this small open-model agent-eval workload, available single-GPU supply was the better economic home than a fresh short-lived TPU strike.

The TPU thesis still matters. TPUs remain a credible substitution pressure on GPU useful life, especially when workloads are portable and the alternative GPU comparison is H100-class or multi-GPU. But the first measured single-GPU control says the cheap-GPU baseline cannot be waved away.

## What We Ran

The fixed workload was `scenarios-frontier-v2`:

- `9` public-safe boundary fixtures
- `60` expected tool decisions
- same model family: `Qwen/Qwen2.5-7B-Instruct`
- same OpenAI-compatible benchmark path
- same prompt/runtime ladder:
  - `baseline + none`
  - `checklist + none`
  - `checklist + risk-floor`

The TPU side used completed Cloud TPU `v6e-8` Spot rows. The GPU side used RunPod credits on a secure `NVIDIA A100 80GB PCIe` pod with the launch-time pod meter captured in the run metadata.

## Result

| Row | TPU `v6e-8` Spot | RunPod A100 |
| --- | ---: | ---: |
| Qwen 7B `baseline + none` | `5/9`, `$1.286313` | `5/9`, `$0.012585` benchmark-only |
| Qwen 7B `checklist + none` | `8/9`, `$1.158181` | `7/9`, `$0.011436` benchmark-only |
| Qwen 7B `checklist + risk-floor` | `9/9`, `$1.336235` | `9/9`, `$0.010725` benchmark-only |

The clean paired row is the defended row:

- TPU: `9/9`, `60/60` coverage, `$1.336235`
- RunPod A100: `9/9`, `60/60` coverage, `$0.010725` benchmark-only

The RunPod rows were warm-server benchmark costs. The setup envelope still matters: cheaper 4090/A5000 lanes failed allocation or readiness before the A100 succeeded, and the A100 serving stack needed pinned `vllm` and `transformers` versions before it was benchmark-ready. Even allocating the whole successful A100 session plus failed cheaper-GPU friction across the three completed rows, the RunPod session remained below the three matched TPU Spot rows.

## What Changed

Before this run, the report could only say:

- TPU Spot was cheaper than same-time H100-class Google controls.
- TPU was not automatically cheaper than cheap single-GPU controls.
- The actual GPU wall-clock row was missing.

After this run, the answer is sharper:

- A real RunPod A100 control exists.
- It matched the TPU defended result at `9/9`.
- It was materially cheaper for this small Qwen 7B workload.
- GPU-side setup friction is real and should be recorded separately from model quality.

## Claim Boundary

This does not prove:

- GPUs are generally cheaper than TPUs.
- TPUs are economically irrelevant.
- A100 is the right long-term control for every row.
- Larger models, batched throughput, or warm TPU sessions will show the same ratio.

It does prove:

- BoundaryBench can now compare TPU and GPU rows with the same benchmark artifact shape.
- The first paired Qwen 7B cost result favors the RunPod A100 lane.
- The next useful GPU question is cheaper 24GB-class viability or Qwen 14B economics, not another A100 Qwen 7B baseline.

## Artifacts

- Detailed field notes: `docs/reports/2026-04-tpu-field-notes-gpu-depreciation.md`
- TPU costed sweep: `docs/reports/2026-04-frontier-v2-costed-tpu-sweep.md`
- RunPod GPU sweep: `docs/reports/2026-04-frontier-v2-runpod-gpu-sweep.md`
- Plain-English frontier-v2 synthesis: `docs/reports/2026-04-frontier-v2-what-we-learned.md`
- Runbook for next paired run: `docs/runbooks/frontier-v2-costed-tpu-gpu-pair.md`
