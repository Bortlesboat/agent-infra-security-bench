# Cloud TPU v6e Frontier Ablation - April 2026

## Summary

This report removes one layer of help from the first TPU frontier-pack result.

The earlier defended TPU row used:

- model: `Qwen/Qwen2.5-7B-Instruct`
- prompt profile: `checklist`
- runtime policy: `risk-floor`
- suite: `scenarios-frontier/`

This ablation reran the same TPU lane with the same model and prompt profile, but with `runtime-policy none`.

Result: nothing changed on this frontier pack. The `3`-fixture smoke still passed `3/3`, and the full `7`-fixture frontier pack still passed `7/7` with full `47/47` tool-decision coverage.

That makes this a useful negative result. On this specific model and frontier slice, the runtime floor was not the thing carrying the benchmark pass.

## Hardware And Serving Path

| Layer | Value |
| --- | --- |
| Provisioned host | Cloud TPU VM |
| Zone | `europe-west4-a` |
| Accelerator | `spot v6e-8` |
| Runtime | `v2-alpha-tpuv6e` |
| Serving stack | `vllm-tpu` |
| Model | `Qwen/Qwen2.5-7B-Instruct` |
| Endpoint shape | local OpenAI-compatible API at `http://127.0.0.1:8000/v1` |
| Benchmark checkout | `96c6ec1` |
| Frontier fixture commit | `76eea57` |
| Serving context limit | `4096` |

This reused the same grant-safe TPU pattern as the earlier frontier report: short-lived TPU VM, local `vllm-tpu`, artifact copy-back, explicit delete, final empty-zone check.

## Three-Fixture Smoke

| Prompt Profile | Runtime Policy | Run ID | Passed | Pass Rate | Coverage | Omitted | Duplicates |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| `checklist` | `none` | `run-3a419f8a6aae` | 3/3 | 1.000 | 22/22 | 0 | 0 |

The smoke artifact lives under `outputs/tpu-v6e-qwen-frontier-smoke-no-runtime/`.

## Full Frontier Pack Ablation

| Prompt Profile | Runtime Policy | Run ID | Passed | Pass Rate | Average Score | Unsafe | Missed | Coverage | Omitted | Duplicates |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `checklist` | `none` | `run-cc8b5df98f1c` | 7/7 | 1.000 | 1.000 | 0 | 0 | 47/47 | 0 | 0 |

The full artifact lives under `outputs/tpu-v6e-qwen-frontier-pack-v1-no-runtime/`.

## Direct Comparison

| Configuration | Run ID | Passed | Unsafe | Missed | Coverage |
| --- | --- | ---: | ---: | ---: | ---: |
| `checklist + risk-floor` | `run-d65aa98e528b` | 7/7 | 0 | 0 | 47/47 |
| `checklist + none` | `run-cc8b5df98f1c` | 7/7 | 0 | 0 | 47/47 |

The local deterministic controls still matter:

| Local control | Passed |
| --- | ---: |
| `deny-high-risk-payment-state` | 1/7 |
| `deny-high-risk-stateful` | 7/7 |

So the pack is still doing real benchmark work. It just is not currently separating these two Qwen TPU configurations.

## Interpretation

This result changes the next question.

Before the ablation, the natural suspicion was that the runtime floor might be doing most of the safety work on the frontier pack. After the ablation, that is no longer the leading explanation for this model.

What this suggests instead:

- the `checklist` prompt profile may be doing more than the runtime layer here
- `Qwen/Qwen2.5-7B-Instruct` may already be robust on this `7`-fixture slice
- the current frontier pack is stronger than the 34-fixture control row, but not yet hard enough to split this model between `runtime=none` and `runtime=risk-floor`

That means the next informative comparison is not another repeat of this exact row. The next informative move is one of:

- remove the `checklist` prompt and keep `runtime=none`
- keep the frontier pack fixed and swap in a weaker or different model family
- expand the frontier pack with another small slice that targets the exact places this Qwen row still solves cleanly

## Reproduction

Once the TPU host is serving the model with a `4096` context window:

```powershell
python -m agent_infra_security_bench.cli run-openai-agent scenarios-frontier outputs/tpu-v6e-qwen-frontier-pack-v1-no-runtime `
  --model Qwen/Qwen2.5-7B-Instruct `
  --base-url http://127.0.0.1:8000/v1 `
  --scenario-commit 76eea57 `
  --prompt-profile checklist `
  --runtime-policy none `
  --hardware tpu-v6e
```

## Claims Boundary

- This is still a TPU-backed inference run on a small frontier suite, not a broad model evaluation.
- The result only shows that `risk-floor` made no measurable difference for this one model, prompt, and frontier-pack version.
- The TPU VM was explicitly deleted after artifact copy-back, and the final zone check returned empty.
