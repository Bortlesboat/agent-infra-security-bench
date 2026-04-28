# TPU Field Notes For The GPU Depreciation Debate

Date: 2026-04-26
Updated: 2026-04-28

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

## Fresh Access Attempts

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

On 2026-04-27, the costed Qwen 7B baseline retry finally produced the missing frontier-v2 TPU cost row:

- Launch pricing was refreshed before the run; the current Trillium Spot snapshot used for `v6e-8` is `$0.748824` per chip-hour, or `$5.990592/hr` for the 8-chip node.
- Several retries were still useful failures: they exposed stale-resource cleanup, TPU SSH metadata priming, Windows line-ending behavior in uploaded shell scripts, pid-file polling versus self-matching `pgrep`, and a TPU image defaulting to Python `3.10` while the repo requires `3.11`.
- After those fixes, a `europe-west4-a` Spot `v6e-8` allocation completed bootstrap, served `Qwen/Qwen2.5-7B-Instruct`, ran the `9`-fixture `scenarios-frontier-v2` baseline/no-runtime row, copied artifacts back, annotated the manifest with timing and cost, and deleted the TPU.
- The completed row passed `5/9` fixtures with `0` unsafe approvals, `5` missed expected actions, and `59/60` tool decisions covered.
- Billable elapsed time from create request through delete verification was `773` seconds (`0.214722` hours), giving a TPU Spot run cost of `$1.286313`.
- Final teardown verification after the retry session showed zero TPU VMs in the touched zones.

That first successful row opened the lane for a broader costed TPU sweep. By the end of the April 27 retry session, the repo had `9` cost-annotated frontier-v2 TPU rows: all three Qwen 7B prompt/runtime rows, all three Mistral 7B prompt/runtime rows, and all three Qwen 14B prompt/runtime rows. The generated sweep table is `docs/reports/2026-04-frontier-v2-costed-tpu-sweep.md`.

The new rows changed the useful denominator from "one TPU cost point" to "small costed TPU frontier surface." Qwen 7B, Mistral 7B, and Qwen 14B all reach `9/9` on `checklist + risk-floor`. Qwen 14B is the sharpest scale nuance: `baseline + none` reaches `7/9` with `1` unsafe approval and `1` missed action, `checklist + none` reaches `8/9` but concentrates the remaining miss into `2` unsafe approvals, and `checklist + risk-floor` closes cleanly at `9/9`. Every completed costed row was copied back, annotated with pricing/timing/reliability, and followed by provider-side TPU deletion verification.

The first GPU-control attempt on 2026-04-27 did not reach a benchmark row. Local preflight, regional L4 quota, and teardown checks were clean, but the actual `g2-standard-4` create failed on the global Compute Engine GPU quota: `GPUS_ALL_REGIONS` was `0`. That is a useful negative datapoint rather than a model result. Google documents that GPU projects need both the regional GPU-family quota and the additional global `GPUs (all regions)` quota, so any future GPU control would need both checks before allocation. It would also need a verified no-cost or explicitly approved billing boundary; the live workspace should not create paid GPU/GCE resources for this comparison. The same live session also exposed stale TPU strike processes from earlier retries; those were stopped, the created TPU VMs were deleted, and final provider checks showed no GCE instances or TPU VMs left running in the touched zones.

On 2026-04-28, the RunPod credit lane produced the missing GPU control rows without re-linking Google Cloud billing. Preflight found no running RunPod pods, a known pre-existing storage baseline from one exited pod, and a positive credit balance. The cheap GPU lane still had friction: an A5000 allocation disappeared before launch, a secure 4090 vLLM pod never became API/SSH-ready, a secure 4090 PyTorch pod also failed readiness/port exposure, and community 4090 allocation attempts failed before a usable pod existed. The first successful lane was a secure `NVIDIA A100 80GB PCIe` pod at a launch-time meter of `$1.39/hr`. The base PyTorch image had a working CUDA stack, but the first vLLM install pulled an incompatible newer torch wheel; pinning `vllm==0.10.2` and `transformers==4.56.2` fixed the serving stack. The live endpoint then returned an OpenAI-compatible smoke response and ran all three Qwen 7B frontier-v2 rows. A later secure `NVIDIA A100-SXM4-80GB` pod at `$1.49/hr` ran the Qwen 14B `checklist + risk-floor` row; that session also exposed setup friction until the Python venv was moved off the network-mounted workspace and into `/root`. After copy-back, the benchmark pods were deleted, RunPod showed no running pods, and current spend returned to the pre-run storage baseline.

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

RunPod was checked on 2026-04-28 as the practical no-cash GPU lane because this workspace has RunPod credits and Google Cloud billing is intentionally unlinked. The relevant public RunPod docs are [billing overview](https://docs.runpod.io/accounts-billing/billing), [Pods pricing](https://docs.runpod.io/pods/pricing), [Pods API list response](https://docs.runpod.io/api-reference/pods/GET/pods), and [CLI GPU list](https://docs.runpod.io/runpodctl/reference/runpodctl-gpu). The important pricing behavior is different from Google: RunPod consumes prepaid credits for active pods, serverless endpoints, and storage; current GPU prices are refreshed during pod deployment; the pod record exposes `costPerHr` and `adjustedCostPerHr`; stopped pods can still accrue storage charges; and Spot pods are interruptible. So a RunPod GPU row must capture the actual pod hourly meter from launch, not rely only on a static public table.

The current hourly meter snapshot:

| Lane | Current public price signal | Full-node hourly meter used for comparison | Notes |
| --- | ---: | ---: | --- |
| Cloud TPU `v6e-8`, `europe-west4` | `$2.97` per Trillium chip-hour on demand | `$23.76/hr` | Closest on-demand meter for the completed `europe-west4-a` TPU rows. |
| Cloud TPU `v6e-8`, US Trillium regions | `$2.70` per Trillium chip-hour on demand | `$21.60/hr` | Useful if a US `v6e-8` lane has capacity. |
| Cloud TPU `v5litepod-8`, `europe-west4` | `$1.56` per v5e chip-hour on demand | `$12.48/hr` | Cheaper fallback, but the April 26 attempts hit serving-quota limits before a run. |
| Cloud TPU `v5litepod-8`, US v5e regions | `$1.20` per v5e chip-hour on demand | `$9.60/hr` | Cheaper fallback if quota permits. |
| Cloud TPU `v6e-8`, current Spot table | `$0.748824` per Trillium chip-hour | `$5.99/hr` | Spot prices are dynamic; record the exact zone/table snapshot at launch. |
| Cloud TPU `v5litepod-8`, current Spot table | `$0.244926` per v5e chip-hour | `$1.96/hr` | Attractive meter, but quota/capacity has to be proven first. |
| G2 `g2-standard-4`, 1x L4 | `$0.706832276/hr` on demand | `$0.71/hr` | Best cheap GPU control for Qwen 7B if memory/context is sufficient. |
| A2 `a2-highgpu-1g`, 1x A100 40GB | `$3.673385/hr` on demand | `$3.67/hr` | Stronger single-GPU control for 7B/14B rows. |
| A3 High `a3-highgpu-1g`, 1x H100 80GB | `$11.061250015/hr` on demand | `$11.06/hr` | Comparable when the question is H100 single-node latency/headroom. |
| A3 High `a3-highgpu-8g`, 8x H100 80GB | `$88.490000119/hr` on demand | `$88.49/hr` | Not the right first control for small 7B rows unless measuring batched throughput or multi-GPU serving. |
| RunPod Secure Pod, 1x A100 80GB PCIe | Launch-time pod meter | `$1.39/hr` | Actual 2026-04-28 GPU control meter, paid from credits. |
| RunPod Secure Pod, 1x A100 SXM 80GB | Launch-time pod meter | `$1.49/hr` | Actual 2026-04-28 Qwen 14B GPU control meter, paid from credits. |
| RunPod Secure Pod, 1x RTX 4090 | Launch-time pod meter | `$0.69/hr` | Attempted cheaper lane; readiness/allocation friction blocked a benchmark row. |

The costed TPU sweep now gives actual workload denominators:

| Row | Result | Unsafe | Missed | Coverage | Billable elapsed | Run cost | Cost/fixture | Cost/pass | Cost/covered tool |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Qwen 7B `baseline + none` | `5/9` | `0` | `5` | `59/60` | `773s` | `$1.286313` | `$0.142924` | `$0.257263` | `$0.021802` |
| Qwen 7B `checklist + none` | `8/9` | `1` | `0` | `60/60` | `696s` | `$1.158181` | `$0.128687` | `$0.144773` | `$0.019303` |
| Qwen 7B `checklist + risk-floor` | `9/9` | `0` | `0` | `60/60` | `803s` | `$1.336235` | `$0.148471` | `$0.148471` | `$0.022271` |
| Mistral 7B `baseline + none` | `2/9` | `0` | `9` | `56/60` | `828s` | `$1.377836` | `$0.153093` | `$0.688918` | `$0.024604` |
| Mistral 7B `checklist + none` | `7/9` | `0` | `2` | `60/60` | `869s` | `$1.446062` | `$0.160674` | `$0.206580` | `$0.024101` |
| Mistral 7B `checklist + risk-floor` | `9/9` | `0` | `0` | `60/60` | `772s` | `$1.284649` | `$0.142739` | `$0.142739` | `$0.021411` |
| Qwen 14B `baseline + none` | `7/9` | `1` | `1` | `60/60` | `770s` | `$1.281321` | `$0.142369` | `$0.183046` | `$0.021355` |
| Qwen 14B `checklist + none` | `8/9` | `2` | `0` | `60/60` | `887s` | `$1.476015` | `$0.164002` | `$0.184502` | `$0.024600` |
| Qwen 14B `checklist + risk-floor` | `9/9` | `0` | `0` | `60/60` | `815s` | `$1.356203` | `$0.150689` | `$0.150689` | `$0.022603` |

The completed TPU rows are tightly clustered on elapsed allocation time: roughly `696-887s` and `$1.16-$1.48` per successful Spot row at the launch-time `v6e-8` meter. Prompt/runtime structure matters more to cost per useful result than the small timing differences: Mistral baseline is the most expensive per passed fixture because it only passes `2/9`, while Mistral `checklist + risk-floor` is the cheapest perfect row at `$0.142739` per passed fixture. Qwen 14B `checklist + risk-floor` adds a second scale row that is clean on quality and still only `$0.150689` per passed fixture.

The 2026-04-28 RunPod A100 controls give measured GPU denominators for the same Qwen frontier-v2 workload. The generated GPU sweep is `docs/reports/2026-04-frontier-v2-runpod-gpu-sweep.md`. The row-level GPU costs below are benchmark-only warm-server costs from the annotated manifests; RunPod allocation, image readiness, package install, model download, server warmup, and failed lower-cost GPU attempts are handled as setup friction rather than hidden in model quality.

| Row | TPU `v6e-8` Spot row | RunPod A100 row | Read |
| --- | --- | --- | --- |
| Qwen 7B `baseline + none` | `5/9`, `773s`, `$1.286313`, `$0.257263/pass`, `59/60` coverage | `5/9`, `32.595s`, `$0.012585`, `$0.002517/pass`, `60/60` coverage | Same pass count; the GPU row covered every tool decision. |
| Qwen 7B `checklist + none` | `8/9`, `696s`, `$1.158181`, `$0.144773/pass`, `60/60` coverage | `7/9`, `29.619s`, `$0.011436`, `$0.001634/pass`, `60/60` coverage | GPU was far cheaper but one fixture worse on quality. |
| Qwen 7B `checklist + risk-floor` | `9/9`, `803s`, `$1.336235`, `$0.148471/pass`, `60/60` coverage | `9/9`, `27.778s`, `$0.010725`, `$0.001192/pass`, `60/60` coverage | Clean paired row; A100 wins this small workload on measured marginal cost. |
| Qwen 14B `checklist + risk-floor` | `9/9`, `815s`, `$1.356203`, `$0.150689/pass`, `60/60` coverage | `9/9`, `47.167s`, `$0.019522`, `$0.002169/pass`, `60/60` coverage | Clean paired scale row; A100 SXM wins on benchmark-only marginal cost. |

The setup envelope matters. The two failed 4090 pods consumed about `883s` at `$0.69/hr`, or roughly `$0.169` of billable friction. The successful Qwen 7B A100 pod was live for about `3,160s` at `$1.39/hr`, or roughly `$1.220`, and produced all three Qwen 7B rows. Allocating that whole RunPod session envelope across the three completed rows gives about `$0.463/row`, still below the three matched TPU Spot rows' combined `$3.780729` (`$1.260/row`). The first Qwen 14B A100 SXM single-row session was the cautionary counterpart: the benchmark-only row cost was only `$0.019522`, but the one-off setup session was roughly a tie/slightly worse than the matched TPU row until amortized.

The later amortized Qwen 14B session closes that specific caveat. The same Qwen 14B triplet was rerun once on TPU and once on RunPod A100 SXM: both sessions produced identical quality (`7/9`, `8/9`, `9/9`) and full `180/180` aggregate tool coverage. The setup-inclusive TPU `v6e-8` Spot session took `983s` and cost `$1.635764`; the setup-inclusive RunPod A100 SXM session took `1877.104s` and cost `$0.776912`, including the RunPod readiness-parser miss and a CRLF retry. On this matched triplet, RunPod A100 SXM was `47.5%` of the TPU session cost, or about `2.11x` cheaper. That is a stronger answer than the earlier theoretical comparison, but it is still not a universal hardware claim.

At the Qwen 7B baseline's `0.214722h` TPU wall-clock time, the current Google GPU meters would imply about `$0.152` on `g2-standard-4` L4, `$0.789` on `a2-highgpu-1g` A100, `$2.375` on `a3-highgpu-1g` H100, and `$18.999` on `a3-highgpu-8g`. The measured RunPod A100 rows now show that an available credit-backed single-GPU lane can be materially cheaper for warm-server BoundaryBench-style rows. The open question moves from "can any GPU row beat TPU?" to "how much of that advantage survives on cheaper 24GB GPUs, batched throughput, and equally amortized warm-session runs?"

The immediate answer is therefore split:

- Against an `8xH100` A3 High node, a `v6e-8` TPU is much cheaper per wall-clock hour: `$23.76/hr` on-demand in `europe-west4` versus `$88.49/hr` for `a3-highgpu-8g` in the current `us-central1` public table. TPU can be as much as `3.7x` slower than that 8xH100 node and still tie on meter cost.
- Against single-GPU controls, TPU is not automatically cheaper for this small BoundaryBench-style workload. `g2-standard-4` is about `$0.71/hr`, `a2-highgpu-1g` is about `$3.67/hr`, and `a3-highgpu-1g` is about `$11.06/hr`. A `v6e-8` on-demand row only wins those comparisons if it is materially faster, more available, or replacing a workload that genuinely needs an 8-chip/large-node shape.
- Against current Spot examples, the meter can flip again: current Spot lists Trillium at about `$5.99/hr` for `v6e-8`, while an approximate `a3-highgpu-8g` Spot component build-up is about `$23.45/hr` before any workload-specific idle/friction accounting. But the April 26 field attempt showed why Spot has to include setup and preemption friction rather than only the quoted meter.

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

What we can now quantify is a `9`-row frontier-v2 TPU Spot surface, a `4`-row RunPod A100 benchmark-only GPU surface, and one setup-inclusive Qwen 14B matched session. The TPU surface has `9` fixtures per row, `60` possible tool decisions per row, per-row allocation windows of roughly `11.6-14.8` minutes, and per-row Spot costs of roughly `$1.16-$1.48`. The RunPod A100 controls have the same `9` fixtures and `60` possible tool decisions, benchmark-only durations of roughly `28-47s`, and row costs of roughly `$0.011-$0.020` before allocating shared setup friction. The Qwen 14B amortized session then shows the setup-inclusive answer for a larger-model triplet: `$1.635764` on TPU versus `$0.776912` on RunPod A100 SXM for identical aggregate quality.

What the 2026-04-27 Google GPU attempt adds is a quota-friction measurement, not a GPU quality or cost row. The attempted G2/L4 control was blocked before VM startup by `GPUS_ALL_REGIONS=0`, even though the regional L4 quota surface showed one available L4. Under the current no-spend operating rule, retrying G2, A2, or A3 on Google Cloud should remain planning-only.

The RunPod lane is no longer theoretical. The 2026-04-28 controls proved the credit-backed path, but also proved that "available GPU" is not the same as "usable benchmark pod": allocation disappearance, no-port readiness, serving-stack version drift, slow resolver behavior, and network-volume stale-file-handle behavior all showed up before the A100 rows succeeded. The public repo should still avoid RunPod account IDs, account emails, pod IDs, public IPs, exact balances, or API-key material.

What we still cannot honestly compute is actual cost per run for the older completed TPU v1 rows, because those historical manifests and artifacts do not carry wall-clock timing. They record fields such as `created_at`, `model`, `policy`, `hardware`, `scenario_count`, `results_path`, and `coverage_path`; `coverage.json` records fixture/tool coverage; `results.csv` records pass, unsafe, and missed counts. They do not record `create_requested_at`, `ready_at`, `bootstrap_started_at`, `benchmark_started_at`, `benchmark_finished_at`, `copyback_finished_at`, or `delete_verified_at`.

The repo now has the instrumentation needed for the next paired TPU-vs-GPU run. Every completed costed run should write or annotate these manifest blocks:

- `pricing_snapshot`: provider, zone, accelerator or machine type, provisioning model, accelerator count, full-node hourly meter, pricing source URL, and checked date
- `timing`: create requested, host ready, bootstrap start/end, benchmark start/end, copy-back finish, delete requested, delete verified; add an explicit server-ready timestamp in the next refinement if we need to split model-load time from fixture execution
- `reliability`: allocation failures, preemption count, whether preemption occurred before benchmark start, and whether teardown was verified
- `derived_costs`: billable seconds, successful run cost, friction cost, cost per fixture, cost per passed fixture, cost per covered tool decision, and cost per fully covered tool decision when coverage is complete

Scientifically, the cleanest missing Qwen 7B GPU measurement, the first Qwen 14B defended GPU measurement, and the first setup-inclusive Qwen 14B TPU-vs-RunPod session have now been collected on RunPod A100-class pods and Cloud TPU `v6e-8`. The next missing measurement is narrower: a cheaper 24GB-class RunPod GPU if allocation/readiness stabilizes.

| Pair | Hardware | Why |
| --- | --- | --- |
| Qwen 7B prompt/runtime triplet | Completed TPU `v6e-8` rows vs completed RunPod A100 rows | First paired answer: A100 credits beat TPU Spot on this small measured workload, with setup friction tracked separately. |
| Qwen 14B prompt/runtime triplet | Completed setup-inclusive TPU `v6e-8` session vs completed setup-inclusive RunPod A100 SXM session | First scale amortization answer: same quality on both sides, RunPod A100 SXM cost `47.5%` of TPU session cost. |
| Qwen 7B `baseline + none` on a cheaper RunPod 24GB-class GPU | L4 if available, otherwise A5000 / RTX 4090 / RTX 3090 | Checks whether A100 was overkill and whether the cheap-GPU lane can actually provision cleanly. |

No additional TPU or GPU resources should be created from this report alone. The next live run should start only after preflight is clean, pricing is snapshotted, the no-cost or approved-billing boundary is explicit, and final teardown verification is part of the run plan.

For the next RunPod GPU control specifically, preflight now means: verify no stale TPU strike processes are still running, verify no TPU/GCE resources remain from prior attempts, verify RunPod credits and account spend controls, verify current spend is zero or explicitly baselined, verify target GPU availability, create exactly one pod, capture `costPerHr` and `adjustedCostPerHr`, run the planned rows while the server is warm, copy artifacts back, delete/terminate the pod, and verify the RunPod spend rate returned to the pre-run baseline.

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
- **Operational friction:** real; the April 26/27 TPU attempts hit capacity inconsistency, spot preemption, serving-quota limits, TPU VM SSH-key metadata friction, Windows script transport issues, Python-version drift, stale retry processes, and global Google GPU quota gating. The April 28 RunPod attempts added GPU-side friction: disappearing lower-cost allocations, pods that never exposed usable ports, serving-stack version drift, slow package install behavior, and a network-mounted venv stale-file-handle failure.
- **Economic implication:** TPU substitution is not a binary replacement story. It is a pressure function. The measured TPU Spot rows are already cheaper than same-time H100-class Google controls, but the real RunPod A100 controls beat TPU Spot on warm-server benchmark-only marginal cost for Qwen 7B and Qwen 14B. The amortized Qwen 14B triplet also beats TPU on setup-inclusive session cost in this run. That narrows the claim: TPU pressure is real, but available single-GPU supply can still be the better economic home for small open-model agent-eval rows when setup is amortized.

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

The first GPU side of the Qwen 7B frontier-v2 ladder, the Qwen 14B defended row, and the Qwen 14B setup-inclusive amortized session are now complete on RunPod A100-class pods, and they should not be repeated on this workspace as paid Google Cloud controls. The next useful step is not "another A100 baseline." It is testing whether the same result survives a cheaper GPU class.

To make that window count, the repo now carries a queue-driven strike path at `scripts/tpu-strike.ps1` plus cost-aware queue manifests under `docs/runbooks/`. The strike path snapshots timing, primes TPU SSH metadata, uses native OpenSSH for transport, copies artifacts back, deletes the TPU, verifies teardown, and annotates the manifest with cost metadata. The GPU control should mirror those fields instead of becoming a one-off stopwatch note.

Candidate next rows if a no-cost/approved-billing lane exists:

| Row | Why |
| --- | --- |
| Qwen 7B `baseline + none` on RunPod L4 if available, otherwise RTX A5000 / RTX 3090 / RTX 4090 | tests whether the A100 result was overkill and whether a cheap GPU can provision cleanly |
| Same-session warm TPU-vs-GPU rerun only if regression is suspected | separates accelerator economics from create/bootstrap/delete overhead on both sides, but the Qwen 14B amortized session already answers the main caveat |

The public value is the same: show people without TPU access what TPU-backed workload substitution looks like at the level where accounting debate becomes operational reality.

## Claim Boundary

- This report is not a broad TPU-versus-GPU benchmark.
- The fresh 2026-04-27 retries completed nine costed TPU frontier-v2 model runs. The 2026-04-28 RunPod sessions completed three matched Qwen 7B A100 GPU rows, one Qwen 14B defended A100 GPU row, and one setup-inclusive Qwen 14B amortized TPU-vs-RunPod session. Those rows showed that this A100 credit lane was cheaper on warm-server benchmark-only marginal cost, and that the Qwen 14B triplet stayed cheaper on RunPod even with setup friction included. That does not prove GPUs are generally cheaper, TPUs are generally worse, or batched workloads behave the same way.
- The model-behavior table is from earlier completed Cloud TPU v6e runs in this repo.
- The investment claim is about substitution pressure and economic useful life, not a declaration that TPUs universally dominate GPUs.
