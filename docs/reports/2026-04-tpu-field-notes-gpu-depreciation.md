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
| 4 | `europe-west4-a` | spot `v6e-8` | queue-driven strike path created the host and reached live SSH, but the first Windows `gcloud ... scp` path failed on `~/...` remote uploads; the host was then reclaimed before a corrected rerun completed |
| 5 | `europe-west4-b` | spot `v5litepod-8` | live serving quota exhausted (`TPUV5sPreemptibleLitepodServingPerProjectPerZoneForTPUAPI`) |
| 6 | `us-central1-a` | spot `v5litepod-8` | live serving quota exhausted (`TPUV5sPreemptibleLitepodServingPerProjectPerZoneForTPUAPI`) |
| 7 | `europe-west4-a` | spot `v6e-8` | corrected queue run created a `READY` host again, but the Windows PuTTY-backed `gcloud ... ssh/scp` path still hung on a cached host-key mismatch prompt even after adding `--strict-host-key-checking=no`; the TPU had to be cleaned up manually |
| 8 | `europe-west4-a` | spot `v6e-8` | the same live host was then reached cleanly through native Windows OpenSSH using a temp-copy of `~/.ssh/google_compute_engine` with locked-down ACLs and an isolated `known_hosts` file; `python3 --version` and a real file upload both succeeded, so the strike path was rewritten to use `gcloud` only for create/describe/delete and OpenSSH for transport |

After the failed/preempted attempts, all touched zones were checked and showed zero TPU VMs left running.

This is already an investor-relevant data point. TPU substitution pressure depends on more than chip architecture. It also depends on usable supply, quota shape, reservation rules, and preemption reliability.

The follow-up automation result matters too. Once the queue-driven strike path existed, the live `v6e` lane stopped failing on "we were too slow to type commands" and started failing on concrete platform details: spot reclaim timing, the Windows TPU `scp` path shape, and host-key cache behavior on short-lived TPU names. That is exactly the kind of operator-friction evidence that broad TPU commentary usually misses.

Just as important, the transport workaround is now real evidence too. On this Windows machine, the stable answer was not "use `gcloud ... ssh` more carefully." It was "let `gcloud` create and describe the TPU, but let native OpenSSH carry the session." That is a better operational story than a generic "TPUs are hard" complaint because it points to a fix other builders can actually reuse.

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

## Cost And GPU Comparison

Pricing checked on 2026-04-27 from the public Google Cloud pages for [Cloud TPU pricing](https://cloud.google.com/tpu/pricing), [Compute GPU pricing](https://cloud.google.com/compute/gpus-pricing), [Compute Engine VM pricing](https://cloud.google.com/compute/all-pricing), and [Spot VM pricing](https://cloud.google.com/spot-vms/pricing). The public TPU page prices TPUs per chip-hour and says TPU charges accrue while the TPU node is in `READY`. The public GPU page says A3, A2, and G2 accelerator-optimized machine types include the attached GPU cost in the machine-type price, so GPU comparisons should use whole-machine hours rather than GPU-only component prices.

The current hourly meter snapshot:

| Lane | Current public price signal | Full-node hourly meter used for comparison | Notes |
| --- | ---: | ---: | --- |
| Cloud TPU `v6e-8`, `europe-west4` | `$2.97` per Trillium chip-hour on demand | `$23.76/hr` | Closest on-demand meter for the completed `europe-west4-a` TPU rows. |
| Cloud TPU `v6e-8`, US Trillium regions | `$2.70` per Trillium chip-hour on demand | `$21.60/hr` | Useful if a US `v6e-8` lane has capacity. |
| Cloud TPU `v5litepod-8`, `europe-west4` | `$1.56` per v5e chip-hour on demand | `$12.48/hr` | Cheaper fallback, but the April 26 attempts hit serving-quota limits before a run. |
| Cloud TPU `v5litepod-8`, US v5e regions | `$1.20` per v5e chip-hour on demand | `$9.60/hr` | Cheaper fallback if quota permits. |
| Cloud TPU `v6e-8`, current Spot table | `$0.6365` per Trillium chip-hour | `$5.09/hr` | Spot prices are dynamic; record the exact zone/table snapshot at launch. |
| Cloud TPU `v5litepod-8`, current Spot table | `$0.244926` per v5e chip-hour | `$1.96/hr` | Attractive meter, but quota/capacity has to be proven first. |
| G2 `g2-standard-4`, 1x L4 | `$0.706832276/hr` on demand | `$0.71/hr` | Best cheap GPU control for Qwen 7B if memory/context is sufficient. |
| A2 `a2-highgpu-1g`, 1x A100 40GB | `$3.673385/hr` on demand | `$3.67/hr` | Stronger single-GPU control for 7B/14B rows. |
| A3 High `a3-highgpu-1g`, 1x H100 80GB | `$11.061250015/hr` on demand | `$11.06/hr` | Comparable when the question is H100 single-node latency/headroom. |
| A3 High `a3-highgpu-8g`, 8x H100 80GB | `$88.490000119/hr` on demand | `$88.49/hr` | Not the right first control for small 7B rows unless measuring batched throughput or multi-GPU serving. |

The immediate answer is therefore split:

- Against an `8xH100` A3 High node, a `v6e-8` TPU is much cheaper per wall-clock hour: `$23.76/hr` on-demand in `europe-west4` versus `$88.49/hr` for `a3-highgpu-8g` in the current `us-central1` public table. TPU can be as much as `3.7x` slower than that 8xH100 node and still tie on meter cost.
- Against single-GPU controls, TPU is not automatically cheaper for this small BoundaryBench-style workload. `g2-standard-4` is about `$0.71/hr`, `a2-highgpu-1g` is about `$3.67/hr`, and `a3-highgpu-1g` is about `$11.06/hr`. A `v6e-8` on-demand row only wins those comparisons if it is materially faster, more available, or replacing a workload that genuinely needs an 8-chip/large-node shape.
- Against current Spot examples, the meter can flip again: current Spot lists Trillium at about `$5.09/hr` for `v6e-8`, while an approximate `a3-highgpu-8g` Spot component build-up is about `$23.45/hr` before any workload-specific idle/friction accounting. But the April 26 field attempt showed why Spot has to include setup and preemption friction rather than only the quoted meter.

The `$23.45/hr` A3 Spot estimate is a component build-up from the current Spot table: `8` H100 (A3-HIGH) GPUs, `208` A3-HIGH vCPUs, `1,872` GiB memory, and `6,000` GiB local SSD. The exact launch-time value should still be captured from the calculator or billing table beside the run manifest.

The cost framework for the paired run should be:

```text
billable_hours =
  (setup_seconds + benchmark_seconds + copyback_seconds + idle_seconds) / 3600

run_cost_usd =
  billable_hours * full_node_hourly_meter_usd

cost_per_fixture =
  run_cost_usd / fixture_count

cost_per_passed_fixture =
  run_cost_usd / passed_fixture_count

cost_per_covered_tool_decision =
  run_cost_usd / decided_tool_count

cost_per_fully_covered_tool_decision =
  run_cost_usd / total_tool_count
  only when decided_tool_count == total_tool_count
```

Setup and preemption friction should stay separate from model quality:

```text
friction_cost_usd =
  failed_allocation_billable_hours * attempted_node_meter
  + preempted_bootstrap_billable_hours * attempted_node_meter
  + operator_minutes * chosen_operator_rate_per_minute

economic_run_cost_usd =
  successful_run_cost_usd + allocated_friction_cost_usd
```

What we can already quantify from the completed TPU rows is the denominator quality: each v1 frontier row has `7` fixtures and `47` possible tool decisions, with pass count and coverage recorded. For example, Qwen 7B `checklist + none` on TPU passed `7/7` with `47/47` coverage. At `H` successful billable hours on `europe-west4` on-demand `v6e-8`, that row would cost `23.76 * H`, or `3.39 * H` per passed fixture and `0.506 * H` per fully covered tool decision. At the current Trillium Spot meter, the same successful billable window would be about `5.09 * H`, or `0.727 * H` per passed fixture and `0.108 * H` per fully covered tool decision.

What we cannot honestly compute yet is actual cost per run, because the existing TPU manifests and artifacts do not carry wall-clock timing. The manifests record fields such as `created_at`, `model`, `policy`, `hardware`, `scenario_count`, `results_path`, and `coverage_path`; `coverage.json` records fixture/tool coverage; `results.csv` records pass, unsafe, and missed counts. None of those artifacts record `create_requested_at`, `ready_at`, `serve_ready_at`, `benchmark_started_at`, `benchmark_finished_at`, `copyback_finished_at`, or `delete_verified_at`.

The next paired TPU-vs-GPU run needs a pricing/timing block in every manifest:

- `pricing_snapshot`: provider, zone, accelerator or machine type, provisioning model, accelerator count, full-node hourly meter, pricing source URL, and checked date
- `timing`: create requested, host ready, bootstrap start/end, server ready, benchmark start/end, copy-back finish, delete requested, delete verified
- `reliability`: allocation failures, preemption count, whether preemption occurred before benchmark start, and whether teardown was verified
- `derived_costs`: billable seconds, successful run cost, friction cost, cost per fixture, cost per passed fixture, cost per covered tool decision, and cost per fully covered tool decision when coverage is complete

The cleanest next measurement is a paired `scenarios-frontier-v2` sweep with the same repo commit, same model weights, same `max_model_len=4096`, same prompt/runtime settings, and same OpenAI-compatible benchmark path:

| Pair | Hardware | Why |
| --- | --- | --- |
| Qwen 7B `baseline + none` | TPU `v6e-8` vs G2 L4 or A2 A100 | Cheapest first answer to whether TPU beats the practical single-GPU control. |
| Qwen 7B `checklist + none` | TPU `v6e-8` vs the same GPU lane | Measures the strongest prior TPU behavior with timing and cost instrumentation. |
| Qwen 14B `checklist + risk-floor` | TPU `v6e-8` vs A2 A100 or A3 H100 | Checks whether the larger row needs the more expensive GPU class. |

No new TPU or GPU resources should be created for this report update. The next live run should start only after preflight is clean, pricing is snapshotted, and final teardown verification is part of the run plan.

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
