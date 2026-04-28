# Frontier v2: What We Learned From 9 Costed TPU Rows

This is the plain-English readout of the `frontier-v2` TPU sweep.

Companion artifacts:

- costed sweep table: `docs/reports/2026-04-frontier-v2-costed-tpu-sweep.md`
- machine-readable sweep: `docs/reports/2026-04-frontier-v2-costed-tpu-sweep.json`
- RunPod GPU control sweep: `docs/reports/2026-04-frontier-v2-runpod-gpu-sweep.md`
- TPU/GPU field notes and claim boundary: `docs/reports/2026-04-tpu-field-notes-gpu-depreciation.md`

No GPU/GCE resources are needed to use this report. Google Cloud GPU controls should stay blocked unless an explicit no-cost or approved-billing boundary is restored. The first paired GPU control now exists through RunPod credits: Qwen 7B on a secure A100 pod produced `5/9`, `7/9`, and `9/9` rows across the same baseline/checklist/risk-floor ladder, then the benchmark pod was deleted and spend returned to the pre-existing storage baseline.

## What this benchmark is actually testing

`frontier-v2` is a boundary-pressure benchmark for tool-using agents.

It is not mainly asking, "Is the model generally smart?"

It is asking:

- does the agent block the dangerous tool action?
- does it still allow the safe action it is supposed to complete?
- does it make a decision for every tool, or does it silently skip some?

Those are three different things:

- `safety`: block the bad action
- `utility`: still complete the good action
- `completeness`: make a decision for every tool

The frontier-v2 pack has `9` fixtures and `60` expected tool decisions. It is deliberately harder than the earlier frontier-v1 pack because it mixes long menus, stateful workflows, repository ownership drift, and memory-to-publish transitions.

## The short version

Three open-model families were run on the same TPU-backed `frontier-v2` pack:

| Model | Baseline + None | Checklist + None | Checklist + Risk-Floor |
| --- | ---: | ---: | ---: |
| `Qwen 7B` | `5/9` | `8/9` | `9/9` |
| `Mistral 7B` | `2/9` | `7/9` | `9/9` |
| `Qwen 14B` | `7/9` | `8/9` | `9/9` |

That means:

1. prompt structure repairs many omission-heavy failures
2. runtime defense still matters after prompting
3. larger models can be more capable without being fully safer

## The most important findings

### 1. The benchmark is separating real failure modes

This is the core success.

The rows do not all fail in the same way:

- `Qwen 7B baseline` mostly had a usefulness/completeness problem: `5/9`, `59/60`, `0` unsafe, `5` missed
- `Mistral 7B baseline` was much weaker: `2/9`, `56/60`, `0` unsafe, `9` missed
- `Qwen 14B baseline` was stronger on utility/completeness, but not clean on safety: `7/9`, `60/60`, `1` unsafe, `1` missed

So the benchmark is not just producing one generic "bad score." It is showing different *shapes* of failure.

### 2. Checklist prompting mostly repairs omission pressure

The `checklist` prompt helps omission-heavy rows:

- `Qwen 7B`: `5/9` to `8/9`
- `Mistral 7B`: `2/9` to `7/9`
- both reach full `60/60` coverage after checklist

That tells us the benchmark is catching a real model weakness: some failures are not bad approvals; they are incomplete tool reasoning under pressure.

### 3. Runtime policy is still what closes the last dangerous gap

All three families reached `9/9` only with `checklist + risk-floor`.

That matters because it means the runtime layer is not redundant on the harder pack.

The cleanest example is `Qwen 14B`:

- `baseline + none`: `7/9`, `1` unsafe
- `checklist + none`: `8/9`, but still `2` unsafe
- `checklist + risk-floor`: `9/9`, `0` unsafe

So prompt structure alone did **not** make the strongest open checkpoint safe enough.

### 4. Scale helped, but it changed the failure shape instead of removing failure

`Qwen 14B baseline` was clearly stronger than `Mistral 7B baseline` and `Qwen 7B baseline`.

But the important nuance is that its checklist-only row did **not** fail by omission. It failed by a concentrated unsafe decision on one MCP provenance case:

- failing fixture: `mcp.frontier_long_menu.owner_reply`
- `2` unsafe approvals
- `0` missed actions

That is a more dangerous kind of near-success than a row that simply forgets tools.

In other words:

> scale improved usefulness and completeness, but the remaining weakness became more sharply safety-relevant

## What changed from frontier v1

The earlier frontier-v1 pack already showed that prompt and runtime layers mattered. But `frontier-v2` tells a stronger story:

- the pack is harder
- the pack contains more state pressure
- the pack keeps all three axes visible
- the larger-model row is no longer a clean "bigger solves it" story

That last part is important. `frontier-v2` shows that a stronger open model can look much better overall and still need runtime defense to remove the last unsafe behavior.

## What TPU access was actually good for

The TPU did not invent the benchmark idea.

What it gave us was the ability to build a costed comparison surface across several open checkpoints on the same fixed harder pack:

- `Qwen 7B`
- `Mistral 7B`
- `Qwen 14B`

And to do it with real per-run cost/time evidence instead of vague claims. The completed TPU rows are not a broad TPU-versus-GPU benchmark. They are a reusable evidence surface for this workload.

That is why the TPU work is useful here:

- same benchmark
- same hardware class
- multiple families
- multiple defense stacks
- explicit cost per run

## The real thesis now

The current best statement of the project is:

> under boundary pressure, agent failures split across completeness, utility, and safety; prompting repairs many omission failures, but runtime defense is still what reliably closes the last unsafe gap across model families and scales

## GPU control addendum

The later RunPod A100 control did not change the safety thesis, but it did change the cost thesis. Qwen 7B on RunPod A100 matched the TPU baseline pass count, reached the same clean `9/9` result under `checklist + risk-floor`, and ran the benchmark rows in roughly `28-33s` of warm-server time at about `$0.011-$0.013` per row before setup allocation. The full RunPod session still had real friction, including failed cheaper 4090/A5000 paths and a vLLM/torch compatibility fix, so the honest comparison is benchmark cost plus a separate setup envelope, not a naked hourly quote.

## What we should do next

Do not spend more TPU time on random extra rows.

The next best moves are:

1. publish this frontier-v2 interpretation alongside the costed sweep
2. test whether the Qwen 7B A100 result survives a cheaper 24GB-class RunPod GPU
3. if we spend more TPU/GPU time, use it only on one contrast run that tests the thesis, not on blind volume

Right now, the benchmark has already taught us something real:

> "better model" does not mean "no runtime guard needed."
