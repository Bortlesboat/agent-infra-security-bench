# TPU Field Notes For The GPU Depreciation Debate

Date: 2026-04-26

## Thesis

The useful contribution to the current GPU depreciation debate is not another opinion about whether TPUs are "better" than GPUs.

The useful contribution is field evidence:

> what can a non-Google operator with real Cloud TPU access actually measure, and what does that imply about GPU economic life when workloads become portable to non-NVIDIA accelerators?

Michael Burry's depreciation frame asks whether hyperscalers are stretching GPU useful lives too far. TPU field work adds a missing variable: useful life is not just physical life or accounting policy. It is also substitution pressure.

If a growing share of inference, agent serving, and fixed-stack benchmark work can run on TPUs, older GPU fleets do not need to become useless to become economically impaired. They only need to become the less attractive tier for enough workloads.

## What We Can Measure With TPU Access

Most public commentary sees TPUs through announcements, capex numbers, and customer quotes. Direct access lets us measure lower-level things:

- which TPU types are visible in the live control plane
- which zones have capacity at the moment of use
- whether spot TPUs stay alive long enough to run real workloads
- which open models serve cleanly through vLLM on TPU
- what context-window settings are needed for comparable benchmark runs
- pass rate, unsafe approvals, missed expected actions, and tool-decision coverage on the same workload

That last point matters. A usable accelerator thesis is not only "can it produce tokens?" It is "can it run a repeatable workload with enough fidelity that the result can replace a GPU-backed row?"

## Fresh Access Attempt

On 2026-04-26, the local v2 measurement target was validated before any TPU create attempt.

The expanded frontier pack has:

- `9` fixtures
- `60` tools
- deterministic payment-state-only baseline: `1/9`
- deterministic full-stateful baseline: `9/9`

That gives the live TPU session a sharper target than the already-published `7`-fixture v1 pack.

The live TPU access attempt produced the following field data:

| Attempt | Zone | Type | Result |
| --- | --- | --- | --- |
| 1 | `europe-west4-a` | spot `v6e-8` | create succeeded, but the host was reclaimed before setup completed |
| 2 | `europe-west4-a` | spot `v6e-8` | create succeeded again and answered `python3 --version`, then the host was preempted during bootstrap |
| 3 | `us-east1-d` | spot `v6e-8` | no capacity |

After the failed/preempted attempts, all touched zones were checked and showed zero TPU VMs left running.

This is already an investor-relevant data point. TPU substitution pressure depends on more than chip architecture. It also depends on usable supply, quota shape, reservation rules, and preemption reliability.

## Prior Completed TPU v6e Benchmark Rows

Earlier completed Cloud TPU `v6e-8` runs provide the model-behavior side of the field evidence. These rows used the same BoundaryBench artifact path: raw events, adapted traces, results, coverage, and manifests.

On the fixed `7`-fixture frontier pack:

| Model + configuration | Hardware | Passed | Unsafe | Missed | Coverage |
| --- | --- | ---: | ---: | ---: | ---: |
| Qwen 7B `baseline + none` | TPU v6e | 4/7 | 0 | 4 | 46/47 |
| Qwen 7B `checklist + none` | TPU v6e | 7/7 | 0 | 0 | 47/47 |
| Qwen 7B `checklist + risk-floor` | TPU v6e | 7/7 | 0 | 0 | 47/47 |
| Mistral 7B `baseline + none` | TPU v6e | 2/7 | 0 | 7 | 44/47 |
| Mistral 7B `checklist + none` | TPU v6e | 5/7 | 0 | 2 | 47/47 |
| Mistral 7B `checklist + risk-floor` | TPU v6e | 7/7 | 0 | 0 | 47/47 |
| Qwen 14B `baseline + none` | TPU v6e | 5/7 | 1 | 1 | 47/47 |
| Qwen 14B `checklist + none` | TPU v6e | 6/7 | 2 | 0 | 47/47 |
| Qwen 14B `checklist + risk-floor` | TPU v6e | 7/7 | 0 | 0 | 47/47 |

The important point is not that every row was perfect. The important point is that TPU-backed serving was good enough to expose differentiated failure modes across open model families:

- Qwen 7B mostly needed prompt structure.
- Mistral 7B needed prompt structure plus runtime support.
- Qwen 14B improved weak-prompt utility but introduced sharper unsafe approvals until the runtime floor was restored.

Those are not marketing claims. They are measured workload outcomes on a non-GPU accelerator path.

## What This Adds To The NVIDIA/GPU Useful-Life Debate

The accounting debate asks: how many years should a GPU be depreciated over?

The workload debate asks a better question:

> how long can each GPU generation remain the best economic home for the workloads it was bought to serve?

TPU access turns that into a measurable question:

1. Can the workload move?
2. How much work is needed to make it move?
3. Is the result comparable once it moves?
4. Is TPU supply reliable enough to matter at scale?

For BoundaryBench-style agent evaluation, the answer so far is mixed but meaningful:

- **Workload portability:** yes; vLLM plus an OpenAI-compatible runner made open-model TPU rows comparable with local and hosted rows.
- **Measurement fidelity:** yes; the same pass, unsafe, missed, and coverage metrics survive the hardware move.
- **Operational friction:** real; today's v6e field attempt hit capacity inconsistency and spot preemption before SSH.
- **Economic implication:** TPU substitution is not a binary replacement story. It is a pressure function. The more workloads become portable, the less safe it is to assume long, smooth GPU economic lives.

## Substitution-Adjusted Useful Life

A simple way to frame this for investors:

```text
GPU economic life =
accounting useful life
x workload utilization durability
x software lock-in durability
x perf/$ durability versus new alternatives
x available non-GPU supply
x hyperscaler incentive to substitute
```

TPUs pressure the middle of that equation. They do not need to replace all GPUs. They only need to make enough high-volume workloads portable that the residual value and utilization curve of older GPU fleets steepens.

## What We Should Measure Next

The next live TPU attempt should run the already-validated frontier v2 pack as soon as `v6e-8` capacity is available long enough to complete SSH and serving setup.

To make that window count, the repo now carries a queue-driven strike path at `scripts/tpu-strike.ps1` plus first-wave queue manifests under `docs/runbooks/`. The goal is to spend the next stable allocation on model rows, not on reassembling the same shell sequence by hand.

Target rows:

| Row | Why |
| --- | --- |
| Qwen 7B `baseline + none` | measures weak-row portability on the harder v2 pack |
| Qwen 7B `checklist + none` | tests whether prompt structure still closes the expanded pack |
| Qwen 7B `checklist + risk-floor` | optional defended row if the first two rows expose unsafe or missed actions |

The public value is the same: show people without TPU access what TPU-backed workload substitution looks like at the level where accounting debate becomes operational reality.

## Claim Boundary

- This report is not a broad TPU-versus-GPU benchmark.
- The fresh 2026-04-26 live attempt did not complete a new model run because spot capacity/preemption blocked execution.
- The model-behavior table is from earlier completed Cloud TPU v6e runs in this repo.
- The investment claim is about substitution pressure and economic useful life, not a declaration that TPUs universally dominate GPUs.
