# TPU-Native Experiment Plan

This runbook is the pivot from "model evals running on TPU" to experiments where the TPU itself matters.

Do not create cloud resources from this runbook unless the TPU access boundary is verified no-cost or explicitly approved. The active workspace has billing unlinked; GPU/GCE controls remain planning-only without a no-cost or approved billing boundary.

## Honest distinction

The frontier-v2 sweep measured agent-stack behavior:

- model family
- prompt structure
- runtime policy
- safety / utility / completeness under boundary pressure

That work used TPU as the serving host. It was not primarily a TPU performance benchmark.

The next experiments should test questions that would not be answered by simply moving the same small eval to a GPU.

## What TPU gives us that a GPU rerun does not

Current Cloud TPU docs position v5e and newer TPUs for inference, with vLLM integration through the TPU inference stack. TPU v6e is also documented as optimized for transformer training, fine-tuning, and serving, with JAX / PyTorch/XLA paths and profiling support.

So the TPU-shaped questions are:

1. How does TPU serving behave under concurrency and longer prompts?
2. What is the cost per useful boundary decision at different batch/concurrency levels?
3. Can TPU throughput make large perturbation sweeps and teacher-label generation practical?
4. Can we use JAX/XLA or TPU-friendly fine-tuning to distill a smaller boundary critic that people without TPU can run?
5. How much does spot preemption change effective cost and reliability?

## First TPU-native test: serving pressure probe

Run a short load probe against the same OpenAI-compatible vLLM endpoint used by the benchmark:

```powershell
agent-bench probe-openai-serving `
  --base-url http://127.0.0.1:8000/v1 `
  --model Qwen/Qwen2.5-14B-Instruct `
  --prompt-file docs/runbooks/tpu-probe-frontier-prompt.txt `
  --concurrency 1,2,4,8 `
  --requests-per-level 12 `
  --max-tokens 96 `
  --json outputs/tpu-probes/qwen14-frontier-serving-probe.json `
  --csv outputs/tpu-probes/qwen14-frontier-serving-probe.csv `
  --markdown outputs/tpu-probes/qwen14-frontier-serving-probe.md
```

This answers a different question from the model sweep:

> how much serving throughput and latency headroom do we get from the TPU lane when prompts look like the benchmark?

## What to compare

Start with:

- `Qwen/Qwen2.5-7B-Instruct`
- `Qwen/Qwen2.5-14B-Instruct`
- same prompt file
- same `max_tokens`
- same concurrency ladder
- same Spot `v6e-8` pricing snapshot

Then, if GPU quota and a no-cost or approved billing boundary are both available, run the same probe on the GPU endpoint. Until both gates are true, keep the result framed as TPU field evidence, not TPU-vs-GPU proof.

## Second TPU-native test: perturbation throughput

Once serving pressure is measured, use the best concurrency level to generate and score many public-safe perturbations of the frontier-v2 fixtures.

Target:

- `20-30` base seeds
- `10-20` perturbations per seed
- teacher model labels with raw decisions
- deterministic validator pass
- public dataset of boundary decision traces

This is where TPU access should help people without TPU: the output is a reusable corpus and eventually a small boundary critic, not just a table of model scores.

## Third TPU-native test: small critic distillation

After perturbation data exists, train or fine-tune a small judge that predicts:

- unsafe approval risk
- missed useful action risk
- omitted tool-decision risk

The useful deliverable is a lightweight critic that can run locally or in CI.

## Success criteria

The TPU work becomes genuinely different from GPU reruns when it produces at least one of:

- a throughput/cost curve that changes how we schedule benchmark work
- a larger public boundary-decision dataset than we could reasonably label locally
- a small reusable critic or guard artifact for builders without TPU access
- a field report about spot TPU reliability and effective cost under real benchmark pressure
