# TPU vs RunPod GPU: First Paired Cost Result

Date: 2026-04-28

## Short Version

The first paired GPU controls are now measured.

For the same `scenarios-frontier-v2` Qwen 7B BoundaryBench workload, a RunPod credit-backed A100 row was cheaper than the completed Cloud TPU `v6e-8` Spot rows.

That is not a universal "GPU beats TPU" claim. It is narrower and more useful:

> for this small open-model agent-eval workload, available single-GPU supply was the better economic home than a fresh short-lived TPU strike.

The follow-up amortized Qwen 14B session closes that caveat. Running the Qwen 14B triplet once on TPU and once on RunPod A100 SXM produced identical quality (`7/9`, `8/9`, `9/9`) while the setup-inclusive RunPod session cost `47.5%` of the TPU session.

The TPU thesis still matters. TPUs remain a credible substitution pressure on GPU useful life, especially when workloads are portable and the alternative GPU comparison is H100-class or multi-GPU. But the first measured single-GPU control says the cheap-GPU baseline cannot be waved away.

## What We Ran

The fixed workload was `scenarios-frontier-v2`:

- `9` public-safe boundary fixtures
- `60` expected tool decisions
- same OpenAI-compatible benchmark path
- Qwen 7B prompt/runtime ladder:
  - `baseline + none`
  - `checklist + none`
  - `checklist + risk-floor`
- Qwen 14B prompt/runtime ladder:
  - `baseline + none`
  - `checklist + none`
  - `checklist + risk-floor`

The TPU side used completed Cloud TPU `v6e-8` Spot rows. The GPU side used RunPod credits on secure A100 pods with the launch-time pod meters captured in the run metadata.

## Result

| Row | TPU `v6e-8` Spot | RunPod A100 |
| --- | ---: | ---: |
| Qwen 7B `baseline + none` | `5/9`, `$1.286313` | `5/9`, `$0.012585` benchmark-only |
| Qwen 7B `checklist + none` | `8/9`, `$1.158181` | `7/9`, `$0.011436` benchmark-only |
| Qwen 7B `checklist + risk-floor` | `9/9`, `$1.336235` | `9/9`, `$0.010725` benchmark-only |
| Qwen 14B `checklist + risk-floor` | `9/9`, `$1.356203` | `9/9`, `$0.019522` benchmark-only |

The clean paired row is the defended row:

- TPU: `9/9`, `60/60` coverage, `$1.336235`
- RunPod A100: `9/9`, `60/60` coverage, `$0.010725` benchmark-only

For Qwen 14B, the clean paired row is also defended:

- TPU: `9/9`, `60/60` coverage, `$1.356203`
- RunPod A100 SXM: `9/9`, `60/60` coverage, `$0.019522` benchmark-only

The fresh amortized Qwen 14B session gives the setup-inclusive answer:

| Session | Quality | Wall Clock | Session Cost | Cost/Row | Cost/Passed Fixture | Cost/Covered Tool |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| TPU `v6e-8` Spot | `7/9`, `8/9`, `9/9` | `983s` | `$1.635764` | `$0.545255` | `$0.068157` | `$0.009088` |
| RunPod A100 SXM | `7/9`, `8/9`, `9/9` | `1877.104s` | `$0.776912` | `$0.258971` | `$0.032371` | `$0.004316` |

The RunPod rows were faster on the benchmark window (`147s` for the three successful rows, versus the TPU queue's `385s`) but slower in wall-clock setup because this session included a readiness-parser miss plus a CRLF retry on the defended row. Even with that friction included, the RunPod A100 SXM session was about `2.11x` cheaper for the matched Qwen 14B triplet.

## What Changed

Before this run, the report could only say:

- TPU Spot was cheaper than same-time H100-class Google controls.
- TPU was not automatically cheaper than cheap single-GPU controls.
- The actual GPU wall-clock row was missing.

After this run, the answer is sharper:

- A real RunPod A100 control exists.
- It matched the TPU defended result at `9/9`.
- It was materially cheaper for this small Qwen 7B workload.
- A real Qwen 14B A100 amortized control now exists too, and it shows setup-inclusive economics instead of only warm-server marginal cost.
- GPU-side setup friction is real and should be recorded separately from model quality.

## Claim Boundary

This does not prove:

- GPUs are generally cheaper than TPUs.
- TPUs are economically irrelevant.
- A100 is the right long-term control for every row.
- Batched throughput or warm TPU sessions will show the same ratio.

It does prove:

- BoundaryBench can now compare TPU and GPU rows with the same benchmark artifact shape.
- The first paired Qwen 7B cost result favors the RunPod A100 lane.
- The first paired Qwen 14B amortized session favors RunPod A100 SXM even after setup friction.
- The next useful GPU question is cheaper 24GB-class viability, not another A100 rerun.

## Artifacts

- Detailed field notes: `docs/reports/2026-04-tpu-field-notes-gpu-depreciation.md`
- TPU costed sweep: `docs/reports/2026-04-frontier-v2-costed-tpu-sweep.md`
- RunPod GPU sweep: `docs/reports/2026-04-frontier-v2-runpod-gpu-sweep.md`
- Qwen 14B amortized session: `docs/reports/2026-04-frontier-v2-qwen14-amortized-tpu-runpod-session.md`
- Plain-English frontier-v2 synthesis: `docs/reports/2026-04-frontier-v2-what-we-learned.md`
- Runbook for next paired run: `docs/runbooks/frontier-v2-costed-tpu-gpu-pair.md`
