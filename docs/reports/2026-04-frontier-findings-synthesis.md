# Frontier Findings Synthesis - April 2026

## Thesis

The frontier pack shows that boundary-layer agent reliability is not one problem.

On the same fixed `7`-fixture pack:

- some models mainly fail by omission and incomplete tool coverage
- some recover with prompt structure alone
- some still need a runtime defense layer after completeness is repaired
- larger checkpoints can improve utility while introducing sharper safety failures

That is the main value of this TPU sprint. It did not just produce a few better scores. It separated **safety**, **utility**, and **completeness** into visibly different failure modes on the same benchmark surface.

## What The Frontier Pack Was Designed To Test

The published `34`-fixture suite had become a clean control row. It was useful, but too solved to justify scarce TPU time by itself.

So the frontier pack added `7` harder fixtures with three roles:

- long-menu controls that pressure tool-decision completeness
- stateful continuation controls where one bad decision poisons the workflow
- hybrid cases where long menus and state drift interact

The point was not to make everything maximally hard. The point was to make omission, state tracking, and approval-bound continuation matter enough that different model and defense layers would fail differently.

The deterministic controls prove the pack is shaped correctly:

| Control | Passed | Unsafe | Coverage |
| --- | ---: | ---: | ---: |
| `deny-high-risk-payment-state` | 1/7 | 15 | 47/47 |
| `deny-high-risk-stateful` | 7/7 | 0 | 47/47 |

That is the first key result. A generic high-risk denylist is not enough here; state tracking is the controlling variable.

## The Frontier Matrix

This is the current fixed-pack TPU comparison surface:

| Model + configuration | Passed | Unsafe | Missed | Coverage |
| --- | ---: | ---: | ---: | ---: |
| `Qwen 7B baseline + none` | 4/7 | 0 | 4 | 46/47 |
| `Qwen 7B checklist + none` | 7/7 | 0 | 0 | 47/47 |
| `Qwen 7B checklist + risk-floor` | 7/7 | 0 | 0 | 47/47 |
| `Mistral 7B baseline + none` | 2/7 | 0 | 7 | 44/47 |
| `Mistral 7B checklist + none` | 5/7 | 0 | 2 | 47/47 |
| `Mistral 7B checklist + risk-floor` | 7/7 | 0 | 0 | 47/47 |
| `Qwen 14B baseline + none` | 5/7 | 1 | 1 | 47/47 |
| `Qwen 14B checklist + none` | 6/7 | 2 | 0 | 47/47 |
| `Qwen 14B checklist + risk-floor` | 7/7 | 0 | 0 | 47/47 |

The matching sweep index is in `docs/reports/2026-04-frontier-pack-tpu-sweep.md`.

## Main Findings

### 1. Completeness is a first-class failure mode

The weak rows are not all failing for the same reason.

`Qwen 7B baseline + none` falls to `4/7`, but stays conservative and only drops one tool decision.

`Mistral 7B baseline + none` falls harder to `2/7`, with `44/47` coverage and an omission cluster concentrated in the CI continuation case.

So "model missed the task" is too coarse. One model is mostly struggling to finish safe work. The other is sometimes failing to answer for every tool at all.

### 2. The checklist prompt is a real completeness intervention

The checklist prompt is not cosmetic prompt dressing.

It repairs coverage for both families:

- `Qwen 7B`: `46/47` to `47/47`
- `Mistral 7B`: `44/47` to `47/47`

And it sharply improves pass rate:

- `Qwen 7B`: `4/7` to `7/7`
- `Mistral 7B`: `2/7` to `5/7`

That means the benchmark is sensitive to structured output discipline in exactly the way we wanted. It can tell the difference between "model is unsafe" and "model is incomplete under pressure."

### 3. Runtime policy matters differently by model family

This is the most important higher-layer finding.

For `Qwen 7B`, the runtime floor did not matter once the checklist prompt was in place:

- `checklist + none`: `7/7`
- `checklist + risk-floor`: `7/7`

For `Mistral 7B`, the runtime floor still mattered after completeness was repaired:

- `checklist + none`: `5/7`
- `checklist + risk-floor`: `7/7`

So the runtime layer is not just a generic crutch. It closes the last real gap for some families and does almost nothing for others.

That is exactly the sort of distinction a useful benchmark should expose.

### 4. Scale helps, but not monotonically

`Qwen 14B` is the strongest open weak-prompt row we tested:

- `baseline + none`: `5/7`, full coverage

That is better than `Qwen 7B baseline + none` and much better than `Mistral 7B baseline + none`.

But the larger checkpoint also introduced explicit unsafe approvals:

- `baseline + none`: `1` unsafe
- `checklist + none`: `2` unsafe

So scale improved utility and completeness, but it did not simply dominate the frontier story. In this pack, bigger was more capable and also more willing to approve the wrong thing until the runtime floor was restored.

### 5. The defended rows are not interchangeable

Three defended configurations now close the pack cleanly:

- `Qwen 7B checklist + none`
- `Mistral 7B checklist + risk-floor`
- `Qwen 14B checklist + risk-floor`

But they get there for different reasons:

- `Qwen 7B` mainly needed prompt structure
- `Mistral 7B` needed prompt structure plus runtime support
- `Qwen 14B` needed runtime support mainly to remove safety failures, not completeness failures

That is the cleanest evidence we have so far that "a defended row" is not a single thing. Different models need different defense mixes.

## Why This Matters

The useful public claim is not "TPUs made the benchmark fast."

It is:

> scarce accelerator access let us publish reusable evidence about how safety, utility, and completeness separate under boundary pressure, and how different open model families need different defense layers to close the same frontier pack

That is more valuable to other builders than another leaderboard-style score dump.

It tells them:

- what kind of failures to look for
- when prompting is enough
- when runtime policy still matters
- why full tool-decision coverage should be treated as a benchmark output, not hidden implementation detail

## What This Suggests For The Project

The repo is moving in the right direction.

The frontier pack validates the stated agenda in `docs/roadmap/frontier-research-agenda.md`:

- keep the control row stable
- make frontier pressure explicit
- preserve the three-axis lens all the way up the stack
- publish artifacts other people can reuse without the same hardware

The next high-value work should keep that shape:

1. write and publish this higher-layer synthesis
2. keep the frontier pack fixed long enough to support public comparison and reuse
3. only add new frontier fixtures when they introduce a genuinely new failure thesis
4. use remaining TPU time for comparisons that answer a sharp question, not just because capacity exists

## Open Questions

The current matrix leaves several good next questions:

- Is there another ungated family whose weak-prompt row is stronger than Mistral but safer than Qwen 14B?
- Do larger frontier packs preserve the same defense-layer split, or does one layer start to dominate again?
- Can a small audited runtime layer recover the remaining weak rows without hiding the underlying completeness failure from the report surface?
- Which fixture families are most likely to generalize into a `20+` scenario frontier pack without turning into noise?

## Claims Boundary

- This synthesis is grounded in a small fixed frontier pack, not a broad model leaderboard.
- The defended rows do not prove universal safety; they show how these specific models behave on a deliberately harder boundary-layer pack.
- The main claim is about failure shape and defense-layer interaction, not about declaring one family universally best.
