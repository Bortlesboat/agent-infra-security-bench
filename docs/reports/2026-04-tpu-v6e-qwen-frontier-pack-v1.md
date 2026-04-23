# Cloud TPU v6e Frontier Pack v1 - April 2026

## Summary

This report publishes the first TPU-backed run on the harder `scenarios-frontier/` suite.

The same model and defense stack used for the solved 34-fixture TPU control row were rerun on the new frontier pack:

- model: `Qwen/Qwen2.5-7B-Instruct`
- serving stack: `vllm-tpu`
- hardware: temporary `spot v6e-8` Cloud TPU VM
- prompt/runtime: `checklist` plus `risk-floor`

The smoke passed `3/3`. The full frontier pack then passed `7/7` with full `47/47` tool-decision coverage.

The key operational finding is also worth recording: the original `2048` serving context cap that was fine for the 34-fixture control row was too small for the longer frontier prompts. The first smoke attempt returned an HTTP `400` context-length error. Restarting `vllm serve` with `--max-model-len 4096` resolved it cleanly.

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
| Benchmark runner | `agent-bench run-openai-agent` |
| Frontier fixture commit | `76eea57` |
| Final serving context limit | `4096` |

The public repo still omits the literal cloud project identifier, SSH transcript, and private credential material.

## Three-Fixture Frontier Smoke

The smoke subset covered one long-menu MCP case, one long-menu payment case, and one hybrid browser case.

| Prompt Profile | Runtime Policy | Run ID | Passed | Pass Rate | Coverage | Omitted | Duplicates |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| `checklist` | `risk-floor` | `run-15ee9c6f1259` | 3/3 | 1.000 | 22/22 | 0 | 0 |

The smoke artifact lives under `outputs/tpu-v6e-qwen-frontier-smoke/`.

## Full Frontier Pack Result

| Prompt Profile | Runtime Policy | Run ID | Passed | Pass Rate | Average Score | Unsafe | Missed | Coverage | Omitted | Duplicates |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `checklist` | `risk-floor` | `run-d65aa98e528b` | 7/7 | 1.000 | 1.000 | 0 | 0 | 47/47 | 0 | 0 |

The full artifact lives under `outputs/tpu-v6e-qwen-frontier-pack-v1/`.

## Local Control Comparison

The frontier pack was intentionally shaped so weaker state handling would stay visible.

Before the TPU model run:

| Local control | Passed | Pass Rate |
| --- | ---: | ---: |
| `deny-high-risk-payment-state` | 1/7 | 0.143 |
| `deny-high-risk-stateful` | 7/7 | 1.000 |

That matters because it means the pack is not just longer for the sake of being longer. It still separates partial state handling from full provenance-plus-payment handling.

## Interpretation

This is a good result, but not yet the final frontier story.

What it proves:

- the TPU lane remains stable on a harder benchmark slice
- the new frontier fixtures survive real model execution, not just deterministic policy scoring
- the `checklist + risk-floor` stack still gives full completeness under a longer mixed-menu workload

What it does **not** prove:

- that the frontier pack is now hard enough to differentiate this defended stack
- that TPU serving itself is the reason the run passed
- that the same model without the runtime policy would also pass

The important strategic update is simple: we now have a solved TPU control row on `34` fixtures and a solved TPU defended row on a harder `7`-fixture frontier pack. The next meaningful comparison is no longer "can TPU run the benchmark?" It is "which layer breaks first when we remove defense help or swap model families on the frontier pack?"

## Reproduction

Once a Cloud TPU VM is up and the model is being served through a local OpenAI-compatible endpoint:

```powershell
python -m agent_infra_security_bench.cli run-openai-agent scenarios-frontier outputs/tpu-v6e-qwen-frontier-pack-v1 `
  --model Qwen/Qwen2.5-7B-Instruct `
  --base-url http://127.0.0.1:8000/v1 `
  --scenario-commit 76eea57 `
  --prompt-profile checklist `
  --runtime-policy risk-floor `
  --hardware tpu-v6e
```

For this frontier pack, the serving process should use a larger context window than the original 34-fixture control row:

```bash
vllm serve Qwen/Qwen2.5-7B-Instruct \
  --host 0.0.0.0 \
  --port 8000 \
  --download_dir /tmp \
  --tensor_parallel_size 1 \
  --max-model-len 4096
```

## Claims Boundary

- This is a TPU-backed inference run, not local CPU or GPU inference.
- The frontier pack is still small: `7` curated fixtures, not a broad benchmark replacement.
- The row is directly comparable to the rest of the repo because it uses the same generic JSONL trace path, scorer, manifest format, and coverage analysis.
- The TPU VM was explicitly deleted after artifact copy-back, and the final zone check returned empty.
