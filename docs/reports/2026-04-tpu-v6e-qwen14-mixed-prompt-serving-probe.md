# TPU v6e Qwen 14B Mixed-Prompt Serving Probe

Date: 2026-04-28

This probe is the follow-up to the overnight TPU serving run. The overnight long-prompt row reused an identical prompt, which means prefix caching likely helped. This run rotates three public-safe boundary prompts so the serving layer sees more prompt variety while preserving the same OpenAI-compatible measurement surface.

The result: Qwen 14B on one Spot TPU `v6e-8` lane completed `1,280` mixed-prompt chat requests with `0` failed requests, including a `512`-concurrency row.

## Safety And Scope

This was a guarded TPU Research Cloud run:

- accelerator: Spot Cloud TPU `v6e-8`
- serving stack: `vllm-tpu`
- model: `Qwen/Qwen2.5-14B-Instruct`
- tensor parallel: `4`
- max model length: `4096`
- endpoint: OpenAI-compatible `/v1/chat/completions`
- client location: same TPU VM, against loopback
- run id: `20260428-120138`
- local artifact bundle: `outputs/tpu-mixed-prompts/20260428-120138/tpu-mixed-prompt-20260428-120138.tgz`

No billing account identifiers, project identifiers, SSH keys, workstation paths, or cloud account details are included in this public report.

Billing was linked only for the approved TPU run window, then unlinked after teardown. Cleanup checks before unlink showed the touched TPU zones empty, Compute instances empty, and Compute disks empty. After unlink, project billing reported disabled again.

This report is a field note from an approved free TPU lane, not a guarantee that an independent rerun will be free in another project.

## Prompt Shape

The probe rotated these public-safe prompt files per request:

- `docs/runbooks/tpu-probe-mixed-prompts/ci-memory-boundary.txt`
- `docs/runbooks/tpu-probe-mixed-prompts/payment-repository-boundary.txt`
- `docs/runbooks/tpu-probe-mixed-prompts/mcp-browser-boundary.txt`

Prompt size range: `1,387-1,479` characters

Max generation: `96` tokens

This reduces the identical-prefix effect from the previous repeated-prompt row, but it does not eliminate caching entirely because the same three variants repeat across requests. A stronger future run should rotate dozens of unique prompt variants.

## Timeline

| Event | UTC Time |
| --- | --- |
| Bootstrap start | `2026-04-28T16:07:45Z` |
| Bootstrap done | `2026-04-28T16:08:40Z` |
| Qwen 14B server start | `2026-04-28T16:08:40Z` |
| Qwen 14B server ready | `2026-04-28T16:14:15Z` |
| Artifact tarball written | `2026-04-28T16:14:45Z` |

Server-ready time after model start: about `5m35s`.

## Mixed-Prompt Results

| Concurrency | Requests | OK | Failed | Req/s | P50 Latency | P95 Latency | Completion Tok/s |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 16 | 192 | 192 | 0 | 21.504 | 0.739 | 0.804 | 2064.404 |
| 64 | 192 | 192 | 0 | 53.130 | 1.192 | 1.228 | 5100.450 |
| 128 | 192 | 192 | 0 | 63.596 | 1.827 | 1.885 | 6105.227 |
| 256 | 192 | 192 | 0 | 74.649 | 2.507 | 2.515 | 7166.334 |
| 512 | 512 | 512 | 0 | 81.843 | 4.701 | 6.089 | 7856.939 |

The `512`-concurrency row is the important top-line result: no failed requests, p95 below `6.1s`, and nearly `7.9k` completion tokens per second for Qwen 14B on `TP=4`.

## What Changed From The Overnight Probe

The overnight report showed Qwen 14B on `TP=4` was stable through `512` concurrent short-prompt requests:

- overnight short prompt, 512 concurrency: `64.680 req/s`, p95 `7.731s`, `6209.248` completion tok/s
- mixed-prompt follow-up, 512 concurrency: `81.843 req/s`, p95 `6.089s`, `7856.939` completion tok/s

This does not prove mixed prompts are inherently faster. The run was short, warm, and still repeated three prompt variants. The safer conclusion is:

> the Qwen 14B TPU serving lane remained stable when we moved from one repeated prompt to three rotated boundary prompts, and the measured `512`-concurrency row improved rather than degrading.

## Why This Matters

This is now more clearly TPU-native work. It is not just a model score table running on a TPU host. It measures:

- cold-start/server-ready time
- mixed-prompt serving stability
- high-concurrency latency
- completion-token throughput
- whether the endpoint fails under pressure

For people without TPU access, the reusable value is the curve: Qwen 14B can be served through `vllm-tpu` on a Spot `v6e-8` lane and absorb hundreds of concurrent OpenAI-compatible chat requests without immediate failure in this boundary-prompt shape.

## Claim Boundary

This is not a TPU-versus-GPU benchmark.

It is also not a final long-context benchmark:

- only three prompt variants were rotated
- the variants repeated, so prefix caching may still help
- the client ran on the same TPU VM over loopback
- the row measures serving pressure, not answer quality
- Qwen 14B used `TP=4`, so it should not be compared naively against `TP=1` rows

The honest public claim is:

> On one approved Spot TPU `v6e-8` serving lane, `Qwen/Qwen2.5-14B-Instruct` with `TP=4` completed `1,280` mixed-prompt OpenAI-compatible chat requests with `0` failed requests, including a `512`-concurrency row at `81.843 req/s` and p95 `6.089s`.

## Next Experiments

The next stronger serving probes are:

1. Rotate `32-64` unique prompt variants to reduce repeated-prefix effects further.
2. Run the same mixed-prompt probe on Qwen 7B and Mistral 7B for model-family comparison.
3. Add a paired GPU row with the same prompt files, concurrency levels, and max-token settings.
4. Use the best stable concurrency point to generate a larger public boundary-decision trace corpus.
