# TPU v6e Overnight Serving Pressure Probe

Date: 2026-04-28

This overnight probe extends the first single-model TPU serving run into a multi-model serving field measurement.

The goal was not to score agent behavior. The goal was to use the TPU access for a TPU-native question:

> Can one Cloud TPU `v6e-8` serving lane keep several open-weight instruction models stable under high concurrent OpenAI-compatible request pressure?

Short answer: yes for the tested shapes. Across three sequential model servers and `4,992` total chat-completion requests, every tested row reported `0` failed requests.

## Safety And Scope

This was a guarded TPU Research Cloud run:

- accelerator: Spot Cloud TPU `v6e-8`
- serving stack: `vllm-tpu`
- endpoint: OpenAI-compatible `/v1/chat/completions`
- client location: same TPU VM, against loopback
- run window: overnight April 28, 2026 UTC
- artifact bundle: `outputs/tpu-overnight/20260428-040459/tpu-overnight-20260428-040459.tgz`

No billing account identifiers, project identifiers, SSH keys, workstation paths, or cloud account details are included in this public report.

Billing was linked only for the approved TPU run window, then unlinked after teardown. Cleanup checks before unlink showed the touched TPU zones empty, Compute instances empty, and Compute disks empty. After unlink, project billing reported disabled again.

This report is a field note from an approved free TPU lane, not a guarantee that an independent rerun will be free in another project.

## Runnable Harness

The guarded runner lives at `scripts/tpu-overnight-serving-probe.ps1`, with a delayed cleanup fallback at `scripts/tpu-cleanup-watchdog.ps1`.

The scripts intentionally require account/project inputs at runtime. They should be run only in an approved TPU zone and only after confirming the billing and cleanup boundary for the project being used.

## Run Shape

Models were served sequentially on the same TPU shape:

| Label | Model | Tensor Parallel | Max Model Len | Notes |
| --- | --- | ---: | ---: | --- |
| `qwen14b-v6e8` | `Qwen/Qwen2.5-14B-Instruct` | 4 | 4096 | Larger Qwen row using 4 TPU chips |
| `mistral7b-v6e8` | `mistralai/Mistral-7B-Instruct-v0.3` | 1 | 4096 | 7B comparison row |
| `qwen7b-v6e8-repeat` | `Qwen/Qwen2.5-7B-Instruct` | 1 | 4096 | Repeat of the earlier Qwen 7B serving lane |

Prompt shapes:

| Shape | Prompt Size | Max Generation | What It Tests |
| --- | ---: | ---: | --- |
| Short frontier prompt | 945 characters | 96 tokens | Standard high-concurrency chat serving pressure |
| Short prompt at 512 concurrency | 945 characters | 96 tokens | Saturation and failure behavior at the top tested concurrency |
| Repeated long prompt | 7,617 characters | 64 tokens | Repeated-context pressure; prefix caching likely helps |

The repeated long-prompt rows reuse the same prompt across requests. Treat them as repeated-context pressure, not as a mixed long-context benchmark.

## Timeline

| Event | UTC Time |
| --- | --- |
| Bootstrap start | `2026-04-28T08:11:22Z` |
| Bootstrap done | `2026-04-28T08:12:06Z` |
| Qwen 14B server start | `2026-04-28T08:12:06Z` |
| Qwen 14B server ready | `2026-04-28T08:17:42Z` |
| Qwen 14B rows finished | `2026-04-28T08:20:47Z` |
| Mistral 7B server start | `2026-04-28T08:20:47Z` |
| Mistral 7B server ready | `2026-04-28T08:25:42Z` |
| Mistral 7B rows finished | `2026-04-28T08:31:27Z` |
| Qwen 7B repeat server start | `2026-04-28T08:31:27Z` |
| Qwen 7B repeat server ready | `2026-04-28T08:35:03Z` |
| Qwen 7B repeat rows finished | `2026-04-28T08:40:35Z` |

Server-ready time after each model start:

| Model Row | Ready Time |
| --- | ---: |
| Qwen 14B, TP=4 | 5m36s |
| Mistral 7B, TP=1 | 4m55s |
| Qwen 7B repeat, TP=1 | 3m36s |

## Short Prompt Results

Prompt size: `945` characters
Max generation: `96` tokens

| Model Row | TP | Concurrency | Requests | Failed | Req/s | P50 Latency | P95 Latency | Completion Tok/s |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Qwen 14B | 4 | 1 | 128 | 0 | 1.530 | 0.653 | 0.654 | 146.854 |
| Qwen 14B | 4 | 8 | 128 | 0 | 11.099 | 0.721 | 0.723 | 1065.486 |
| Qwen 14B | 4 | 64 | 128 | 0 | 45.225 | 1.390 | 1.607 | 4341.609 |
| Qwen 14B | 4 | 128 | 128 | 0 | 55.737 | 2.211 | 2.252 | 5350.766 |
| Qwen 14B | 4 | 256 | 128 | 0 | 55.670 | 2.214 | 2.255 | 5344.283 |
| Mistral 7B | 1 | 1 | 128 | 0 | 0.787 | 1.270 | 1.273 | 75.538 |
| Mistral 7B | 1 | 8 | 128 | 0 | 6.044 | 1.322 | 1.325 | 580.192 |
| Mistral 7B | 1 | 64 | 128 | 0 | 32.169 | 1.885 | 2.003 | 3088.253 |
| Mistral 7B | 1 | 128 | 128 | 0 | 42.267 | 2.982 | 2.988 | 4057.613 |
| Mistral 7B | 1 | 256 | 128 | 0 | 42.193 | 2.985 | 2.992 | 4050.559 |
| Qwen 7B repeat | 1 | 1 | 128 | 0 | 0.796 | 1.257 | 1.262 | 76.375 |
| Qwen 7B repeat | 1 | 8 | 128 | 0 | 6.060 | 1.320 | 1.323 | 581.757 |
| Qwen 7B repeat | 1 | 64 | 128 | 0 | 37.857 | 1.720 | 1.844 | 3634.265 |
| Qwen 7B repeat | 1 | 128 | 128 | 0 | 51.192 | 2.440 | 2.446 | 4914.472 |
| Qwen 7B repeat | 1 | 256 | 128 | 0 | 50.940 | 2.451 | 2.458 | 4890.264 |

## 512-Concurrency Rows

These were the highest-concurrency short-prompt rows in the overnight run.

| Model Row | TP | Requests | Failed | Req/s | P50 Latency | P95 Latency | Completion Tok/s |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Qwen 14B | 4 | 512 | 0 | 64.680 | 6.303 | 7.731 | 6209.248 |
| Mistral 7B | 1 | 512 | 0 | 50.883 | 7.372 | 9.907 | 4884.815 |
| Qwen 7B repeat | 1 | 512 | 0 | 64.303 | 6.209 | 7.764 | 6173.086 |

Qwen 14B on `TP=4` matched the Qwen 7B repeat row at the highest tested concurrency. That is the most TPU-specific result here, but it is not an apples-to-apples model-size comparison because the 14B row used four TPU chips while the 7B row used one.

## Repeated Long-Prompt Results

Prompt size: `7,617` characters
Max generation: `64` tokens

| Model Row | TP | Concurrency | Requests | Failed | Req/s | P50 Latency | P95 Latency | Completion Tok/s |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Qwen 14B | 4 | 1 | 128 | 0 | 2.244 | 0.444 | 0.446 | 143.639 |
| Qwen 14B | 4 | 8 | 128 | 0 | 15.428 | 0.518 | 0.521 | 987.404 |
| Qwen 14B | 4 | 64 | 128 | 0 | 65.312 | 0.969 | 1.008 | 4179.985 |
| Qwen 14B | 4 | 256 | 128 | 0 | 85.424 | 1.429 | 1.459 | 5467.147 |
| Mistral 7B | 1 | 1 | 128 | 0 | 1.151 | 0.867 | 0.870 | 73.676 |
| Mistral 7B | 1 | 8 | 128 | 0 | 7.736 | 1.033 | 1.050 | 495.084 |
| Mistral 7B | 1 | 64 | 128 | 0 | 29.957 | 2.094 | 2.299 | 1917.259 |
| Mistral 7B | 1 | 256 | 128 | 0 | 36.570 | 3.408 | 3.460 | 2340.496 |
| Qwen 7B repeat | 1 | 1 | 128 | 0 | 1.181 | 0.846 | 0.849 | 75.591 |
| Qwen 7B repeat | 1 | 8 | 128 | 0 | 8.633 | 0.925 | 0.929 | 552.522 |
| Qwen 7B repeat | 1 | 64 | 128 | 0 | 45.434 | 1.366 | 1.415 | 2907.773 |
| Qwen 7B repeat | 1 | 256 | 128 | 0 | 65.853 | 1.897 | 1.900 | 4214.609 |

The repeated long-prompt rows are useful for service-pressure behavior, but they should not be oversold. Identical prompts can benefit from prefix caching, so completion-token throughput is the more honest comparison surface than total-token throughput.

## What This Tells Us

This result is meaningfully different from a normal model benchmark.

The model-behavior sweep answers:

> Which model and defense combination makes better boundary decisions?

This serving probe answers:

> How much stable serving pressure can a TPU-backed OpenAI-compatible endpoint absorb, and how does model/runtime choice change that curve?

The strongest observations:

- The tested `v6e-8` lane handled all `512`-concurrency short-prompt rows with `0` failed requests.
- Qwen 14B on `TP=4` reached Qwen 7B-like high-concurrency throughput, showing why TPU chip topology matters for serving experiments.
- Mistral 7B was stable but slower and had higher p95 latency at the top row.
- Runtime compatibility matters. The Qwen rows used the TPU-focused Qwen path, while Mistral showed different serving behavior under the same harness.
- The TPU advantage here is not just raw model speed. It is the ability to run repeatable high-concurrency, multi-model serving probes during a short access window and publish the operational curve for people who cannot get TPU quota.

## Claim Boundary

This is not a final TPU-versus-GPU benchmark.

It is also not a pure model-quality comparison:

- Qwen 14B used `TP=4`; the 7B rows used `TP=1`.
- The long prompts were repeated and likely benefited from prefix caching.
- The client ran on the same TPU VM over loopback, so this excludes internet latency and load-balancer effects.
- These rows measure serving stability, throughput, latency, and failure behavior, not benchmark answer quality.

The honest public claim is:

> On one approved Spot TPU `v6e-8` serving lane, three sequential open-weight instruction-model servers completed `4,992` OpenAI-compatible chat requests with `0` failed requests, including `512`-concurrency short-prompt rows for Qwen 14B, Mistral 7B, and a repeat Qwen 7B row.

## Next Experiments

The next best TPU-native moves are:

1. Run a mixed long-context prompt set that reduces identical-prefix caching.
2. Add a paired GPU serving row with the same prompt shapes, request counts, and measurement fields.
3. Compare TPU tensor-parallel settings where memory permits, especially whether the 14B result is topology-driven or implementation-driven.
4. Publish a simple "TPU serving pressure harness" path so other people can reproduce the measurement surface without needing our cloud account details.
