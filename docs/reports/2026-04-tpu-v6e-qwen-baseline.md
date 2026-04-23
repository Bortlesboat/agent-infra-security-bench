# Cloud TPU v6e Baseline - April 2026

## Summary

This report adds the first real Cloud TPU-backed BoundaryBench row.

The run used the new generic OpenAI-compatible backend, served `Qwen/Qwen2.5-7B-Instruct` through `vllm-tpu`, and scored the same 34 public-safe fixtures already used by the Windows, Mac mini, and hosted baselines.

The important result is not "TPUs are better." The important result is that the TPU path is now real, reproducible, and directly comparable. The benchmark can now use scarce TPU time on harder omission and state-pressure fixtures instead of spending that time on setup uncertainty.

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
| Benchmark/runner commit | `1ab0b14` |

The public repo does not include the literal Google Cloud project ID, SSH transcript, or any private credentials.

## Provisioning Notes

The first live TPU path did not succeed in the originally preferred zone:

| Attempt | Result |
| --- | --- |
| `us-east1-d` `spot v6e-8` | failed on spot capacity |
| `us-central1-a` TPU `v5e` fallback (`v5litepod-8`) | failed on serving quota exhaustion |
| `europe-west4-a` `spot v6e-8` | succeeded |

That matters operationally. The right lesson is to treat grant-approved TPU zones as a portfolio, not a single lane.

## Three-Fixture Smoke

The smoke used:

- `mcp.tool_shadowing.wallet_export`
- `x402.payment_proof.fresh_control`
- `x402.replay_payment.basic`

| Prompt Profile | Runtime Policy | Run ID | Passed | Pass Rate | Unsafe | Missed |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| `checklist` | `risk-floor` | `run-0b5e84373327` | 3/3 | 1.000 | 0 | 0 |

The smoke artifact lives under `outputs/tpu-v6e-qwen-smoke/`.

## 34-Fixture TPU Baseline

| Prompt Profile | Runtime Policy | Run ID | Passed | Pass Rate | Average Score | Unsafe | Missed | Coverage | Omitted | Duplicates |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `checklist` | `risk-floor` | `run-ae5a59012e0a` | 34/34 | 1.000 | 1.000 | 0 | 0 | 70/70 | 0 | 0 |

The full TPU artifact lives under `outputs/tpu-v6e-qwen-baseline-34/`.

## Interpretation

This is a strong first TPU row for three reasons.

First, it proves the new backend shape. BoundaryBench can now evaluate any local or remote OpenAI-compatible endpoint with the same raw-event, trace, manifest, scoring, and coverage machinery. TPU serving is not a snowflake path anymore.

Second, it proves the runbook. The project now has a tested grant-safe flow from zone preflight to VM create, TPU-side setup, model serving, smoke run, full suite run, artifact copy-back, and explicit deletion.

Third, it gives the benchmark a clean TPU control row before the frontier-pack expansion. Local and Mac mini defended rows had already shown that this suite can be solved. The TPU result matters because it removes environment uncertainty before the benchmark gets harder.

What this does **not** prove:

- that TPU serving makes a model inherently safer
- that `Qwen/Qwen2.5-7B-Instruct` is generally safe outside this fixture set
- that every TPU zone or quota lane will be equally available

## Reproduction

Once a Cloud TPU VM is up and a compatible model is being served through a local OpenAI-style endpoint:

```powershell
python -m agent_infra_security_bench.cli run-openai-agent scenarios outputs/tpu-v6e-qwen-baseline-34 `
  --model Qwen/Qwen2.5-7B-Instruct `
  --base-url http://127.0.0.1:8000/v1 `
  --scenario-commit 1ab0b14 `
  --prompt-profile checklist `
  --runtime-policy risk-floor `
  --hardware tpu-v6e
```

For the exact infrastructure sequence, use `docs/runbooks/cloud-tpu-first-run.md`.

## Claims Boundary

- This is a TPU-backed inference run, not local CPU/GPU inference.
- The benchmark suite is still 34 public-safe fixtures, not a broad model evaluation.
- The row is directly comparable to the rest of the repo because it uses the same generic JSONL trace path, scorer, manifest, and coverage analysis.
- The TPU VM was explicitly deleted after artifact copy-back and the final zone check returned empty.
