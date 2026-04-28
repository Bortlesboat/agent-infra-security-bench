# TPU v6e Serving Pressure Probe

Date: 2026-04-28

This is the first TPU-native serving probe after the `frontier-v2` costed model sweep.

The earlier sweep measured agent/model behavior on a TPU host. This probe measures the serving layer itself: cold start, TPU-specific runtime setup, concurrency scaling, latency, failures, and token throughput for a frontier-shaped prompt.

## Safety And Scope

This was a short Cloud TPU VM run in an approved TPU Research Cloud zone and shape:

- accelerator: Spot `v6e-8`
- serving stack: `vllm-tpu`
- model: `Qwen/Qwen2.5-7B-Instruct`
- context window: `4096`
- tensor parallel size: `1`
- benchmark endpoint: OpenAI-compatible `/v1/chat/completions`
- probe client location: same TPU VM, against `http://127.0.0.1:8000/v1`

No GPU, Compute Engine VM, disk, address, or storage-bucket resource was intentionally created for this probe.

Billing was linked only long enough to let Cloud TPU API calls run, then unlinked after the TPU VM was deleted. Final provider checks showed the touched TPU zones empty, Compute instances empty, Compute disks empty, and project billing disabled again.

One first Spot attempt in another approved `v6e-8` zone reached `READY` but was reclaimed before SSH/bootstrap. It produced no serving data and was deleted before the successful attempt.

## Cold Start Observations

The successful TPU VM reached a live vLLM model endpoint after the serving process started.

Observed log milestones:

| Event | Observation |
| --- | --- |
| TPU backend | `v6e-8`, `8` chips, `1` core per chip |
| Attention path | default RPA kernel |
| KV cache | FP8 KV cache selected automatically for TPU v6e |
| Model weight download | `54.95s` |
| Model weight load | `24.45s` |
| HBM after model init | `14.19 GiB` used of `31.25 GiB` HBM limit |
| Reported max concurrency at `4096` tokens/request | `63.69x` |
| Engine profile / KV cache / warmup | `87.84s` |
| vLLM process start to server-ready log | about `3m35s` |

That cold-start tax is part of the TPU story. It should be measured separately from warm serving throughput.

## Short Frontier Prompt

Prompt size: `945` characters
Max generation: `96` tokens

Initial concurrency ladder:

| Concurrency | Requests | OK | Failed | Req/s | P50 Latency | P95 Latency | Completion Tok/s |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 12 | 12 | 0 | 0.788 | 1.265 | 1.288 | 75.684 |
| 2 | 12 | 12 | 0 | 1.557 | 1.284 | 1.288 | 149.450 |
| 4 | 12 | 12 | 0 | 3.081 | 1.298 | 1.302 | 295.754 |
| 8 | 12 | 12 | 0 | 4.569 | 1.326 | 1.328 | 438.624 |

Higher concurrency ladder:

| Concurrency | Requests | OK | Failed | Req/s | P50 Latency | P95 Latency | Completion Tok/s |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 8 | 64 | 64 | 0 | 6.089 | 1.312 | 1.317 | 584.518 |
| 16 | 64 | 64 | 0 | 11.599 | 1.372 | 1.396 | 1113.467 |
| 32 | 64 | 64 | 0 | 21.388 | 1.472 | 1.503 | 2053.242 |
| 64 | 64 | 64 | 0 | 36.430 | 1.694 | 1.727 | 3497.284 |

Saturation ladder:

| Concurrency | Requests | OK | Failed | Req/s | P50 Latency | P95 Latency | Completion Tok/s |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 64 | 256 | 256 | 0 | 38.026 | 1.656 | 1.833 | 3650.544 |
| 128 | 256 | 256 | 0 | 52.417 | 2.350 | 2.891 | 5031.996 |
| 256 | 256 | 256 | 0 | 62.254 | 3.829 | 4.014 | 5976.384 |
| 512 | 512 | 512 | 0 | 64.428 | 6.205 | 7.752 | 6185.124 |

The useful bend appears between `128` and `256` concurrent requests. Throughput continues to rise to about `64 req/s`, but p95 latency starts climbing much faster after `128`.

## Repeated Long-Prompt Pressure

Prompt size: `7617` characters
Max generation: `64` tokens

This long-prompt run used a repeated frontier-shaped prompt. Because the repeated prompt is identical across requests, vLLM prefix caching likely helps. Treat this as repeated-context pressure, not as a mixed long-context benchmark.

| Concurrency | Requests | OK | Failed | Req/s | P50 Latency | P95 Latency | Completion Tok/s |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 128 | 128 | 0 | 1.173 | 0.852 | 0.855 | 75.093 |
| 8 | 128 | 128 | 0 | 8.597 | 0.930 | 0.934 | 550.212 |
| 64 | 128 | 128 | 0 | 44.995 | 1.397 | 1.434 | 2879.708 |
| 256 | 128 | 128 | 0 | 63.974 | 1.930 | 1.962 | 4094.331 |

The long repeated-prompt row remained stable through `256` concurrent requests with `0` failures.

## What This Tells Us

This is meaningfully different from the earlier model-behavior sweep.

The earlier sweep answered:

> Which model/prompt/runtime combinations make safer boundary decisions?

This probe answers:

> How much serving pressure can the TPU-backed endpoint absorb, and where does latency bend?

The answer for this setup:

- `Qwen/Qwen2.5-7B-Instruct` on Spot `v6e-8` served the frontier-shaped prompt with `0` failures through `512` concurrent short-prompt requests.
- Throughput scaled sharply through `128` concurrent requests.
- The practical latency bend showed up after `128`: p95 latency rose from `2.891s` at `128` to `4.014s` at `256`, then `7.752s` at `512`.
- The best high-throughput operating point for short prompts is probably around `128-256` concurrency, depending on whether latency or maximum throughput matters more.
- Cold start and XLA/JAX compilation are real and should be amortized across batches; one-off tiny runs understate the TPU lane.

## Claim Boundary

This is not a TPU-versus-GPU benchmark yet. It is a TPU serving field measurement.

The next fair comparison is the same probe on a credit-backed GPU endpoint with the same model, prompt, max tokens, request counts, and cost/timing fields.

Until that paired row exists, the honest public claim is:

> TPU v6e can turn this benchmark from a few model-eval rows into a serving-throughput measurement surface, and the first Qwen 7B v6e probe shows stable high-concurrency behavior with an observable latency bend rather than early failures.
