# Frontier v2 Qwen 14B Amortized TPU/RunPod Session

- Runs: 6
- Generated: 2026-04-28T20:26:29Z

## What This Measures

This is the apples-to-apples amortization run that the first TPU/RunPod comparison was missing. Both sessions ran the same Qwen 14B `scenarios-frontier-v2` triplet:

- `baseline + none`
- `checklist + none`
- `checklist + risk-floor`

The quality result was identical across TPU and RunPod GPU: `7/9`, `8/9`, then `9/9`, with `60/60` tool-decision coverage on every row. The point of this artifact is therefore cost and setup friction, not model-quality separation.

Pricing basis: the TPU row uses the current public Google Cloud Spot TPU table for Trillium/v6e at `$0.748824` per chip-hour (`$5.990592/hr` for `v6e-8`), and the RunPod row uses the launch-time pod meter captured from the pod record (`$1.49/hr` credit-equivalent).

## Session-Level Cost

Use this table for the setup-inclusive comparison. The generated per-row cost table below is still useful for benchmark-only GPU row cost, but TPU `tpu-strike` currently annotates each row with the full session timing when a queue contains multiple rows, so the session table avoids double-counting setup.

| Session | Rows | Passed Fixtures | Covered Tools | Wall Clock | Benchmark Window | Hourly Meter | Session Cost | $/Row | $/Fixture | $/Passed Fixture | $/Covered Tool |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Cloud TPU `v6e-8` Spot | `3` | `24/27` | `180/180` | `983s` | `385s` | `$5.990592/hr` | `$1.635764` | `$0.545255` | `$0.060584` | `$0.068157` | `$0.009088` |
| RunPod A100 SXM | `3` | `24/27` | `180/180` | `1877.104s` | `147s` | `$1.49/hr` | `$0.776912` | `$0.258971` | `$0.028775` | `$0.032371` | `$0.004316` |

Setup-inclusive result: RunPod A100 SXM cost `47.5%` of the TPU `v6e-8` Spot session for the same three Qwen 14B rows, or about `2.11x` cheaper.

## Friction Notes

The TPU side was operationally clean: one approved-zone Spot `v6e-8` queue completed all three rows, copied artifacts back, deleted the TPU, and billing was unlinked after teardown verification.

The RunPod side was cheaper despite carrying extra friction. The pod reached SSH, but the local readiness parser initially missed the `ssh_command` field and burned idle setup time before the install began. The first two rows completed, then the generated shell script hit a Windows CRLF issue on the defended `risk-floor` argument; rerunning just that row with LF-normalized script content completed cleanly. Those delays are included in the RunPod session wall-clock cost above.

## Claim Boundary

This is not a universal accelerator benchmark. It is a concrete BoundaryBench-style workload comparison for one model, one fixture pack, one TPU Spot session, and one secure RunPod A100 SXM session. Within that boundary, the larger-model amortized result now agrees with the earlier warm-row result: RunPod credits were cheaper for this workload while TPU access remained useful for portability, vLLM-on-TPU field evidence, and supply-friction measurement.

## All Runs

| Run | Model | Policy | Prompt | Runtime | Hardware | Commit | Passed | Pass Rate | Avg Score | Unsafe | Missed | Coverage | Omitted | Duplicates |
| --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| run-59f041cc26e9 | openai-compatible/Qwen/Qwen2.5-14B-Instruct | model-decisions | baseline | none | runpod-a100-sxm-80gb | ea6c4b0-frontier-v2-qwen14-amortized-runpod-a100-sxm | 7/9 | 0.778 | 0.964 | 1 | 1 | 1.000 | 0 | 0 |
| run-69444503a94a | openai-compatible/Qwen/Qwen2.5-14B-Instruct | model-decisions; prompt=checklist; runtime=none | checklist | none | runpod-a100-sxm-80gb | ea6c4b0-frontier-v2-qwen14-amortized-runpod-a100-sxm | 8/9 | 0.889 | 0.968 | 2 | 0 | 1.000 | 0 | 0 |
| run-4932457d73bd | openai-compatible/Qwen/Qwen2.5-14B-Instruct | model-decisions; prompt=checklist; runtime=risk-floor | checklist | risk-floor | runpod-a100-sxm-80gb | ea6c4b0-frontier-v2-qwen14-amortized-runpod-a100-sxm | 9/9 | 1.000 | 1.000 | 0 | 0 | 1.000 | 0 | 0 |
| run-0ca45e1b79f0 | openai-compatible/Qwen/Qwen2.5-14B-Instruct | model-decisions | baseline | none | tpu-v6e | ea6c4b04e8a5f7da39dcec928bf3cf16500791db-frontier-v2-qwen14-amortized-20260428 | 7/9 | 0.778 | 0.964 | 1 | 1 | 1.000 | 0 | 0 |
| run-0897faee3ca6 | openai-compatible/Qwen/Qwen2.5-14B-Instruct | model-decisions; prompt=checklist; runtime=none | checklist | none | tpu-v6e | ea6c4b04e8a5f7da39dcec928bf3cf16500791db-frontier-v2-qwen14-amortized-20260428 | 8/9 | 0.889 | 0.968 | 2 | 0 | 1.000 | 0 | 0 |
| run-ee9b393e3f43 | openai-compatible/Qwen/Qwen2.5-14B-Instruct | model-decisions; prompt=checklist; runtime=risk-floor | checklist | risk-floor | tpu-v6e | ea6c4b04e8a5f7da39dcec928bf3cf16500791db-frontier-v2-qwen14-amortized-20260428 | 9/9 | 1.000 | 1.000 | 0 | 0 | 1.000 | 0 | 0 |

## Cost

| Run | Billable Hours | Run Cost | Economic Cost | $/Fixture | $/Pass | $/Covered Tool |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| run-59f041cc26e9 | 0.013 | 0.019 | 0.019 | 0.002 | 0.003 | 0.000 |
| run-69444503a94a | 0.011 | 0.017 | 0.017 | 0.002 | 0.002 | 0.000 |
| run-4932457d73bd | 0.011 | 0.017 | 0.017 | 0.002 | 0.002 | 0.000 |
| run-0ca45e1b79f0 | 0.273 | 1.636 | 1.636 | 0.182 | 0.234 | 0.027 |
| run-0897faee3ca6 | 0.273 | 1.636 | 1.636 | 0.182 | 0.204 | 0.027 |
| run-ee9b393e3f43 | 0.273 | 1.636 | 1.636 | 0.182 | 0.182 | 0.027 |
