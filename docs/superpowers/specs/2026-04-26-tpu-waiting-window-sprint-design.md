# TPU Waiting-Window Sprint Design

Date: 2026-04-26

## Stated Goal

Use the remaining TPU window to publish one stronger public answer than the current frontier matrix already gives us:

> when the boundary-pressure pack gets slightly harder, which defense layers still matter by model family, and what TPU-backed serving actually buys us beyond "we ran it on a TPU"

This is not a new benchmark direction. It is the shortest high-signal extension of the work already proven in:

- `docs/reports/2026-04-frontier-findings-synthesis.md`
- `docs/reports/2026-04-frontier-pack-tpu-sweep.md`
- `docs/roadmap/frontier-research-agenda.md`

## Why This Is The Right Use Of The Window

The TPU window is time-boxed. The benchmark already has:

- a stable `34`-fixture control row
- a useful `7`-fixture frontier pack
- real TPU rows for `Qwen 7B`, `Mistral 7B`, and `Qwen 14B`
- a clear public thesis around safety, utility, and completeness

What it does not yet have is a second-wave TPU artifact that shows we used the rest of the window intentionally rather than just proving the first TPU row and stopping.

The mistake to avoid is scattering the remaining time across too many unrelated directions:

- no WildClawBench brute-force score chase
- no custom training project
- no broad new benchmark surface before the current one is squeezed harder

## One Strong Recommendation

Run a `7-day` TPU sprint centered on a **frontier pack v2 question**, not a broad infrastructure rewrite.

That means:

1. keep the current frontier matrix as the control story
2. add only `2-3` new fixtures if they introduce a genuinely new failure thesis
3. rerun only the highest-value TPU comparisons
4. publish one new synthesis artifact that explains what changed and why

## Sprint Question

The sprint should answer:

> after completeness is mostly repaired, do the hardest remaining failures come from state tracking, provenance drift, or explicit unsafe approvals, and does that answer vary by open model family?

That is a better question than "can we get a slightly different score."

## Scope

### In Scope

- a small frontier-pack expansion from `7` fixtures to roughly `9-10`
- reruns on the existing TPU-served open model families that already worked
- one new public sweep or synthesis report
- optional throughput/latency notes if they are easy to collect cleanly

### Out Of Scope

- large pack expansion
- TPU fine-tuning
- new hosted platform work
- introducing multiple new unknown model families unless serving friction is near zero

## Fixture Strategy

The next pack should stay tight. Add only fixtures that introduce a new failure thesis not already visible in frontier pack v1.

### Recommended New Fixture Themes

#### 1. Repository privilege drift under apparently safe continuation

Candidate shape:

- a public-facing artifact or issue comment suggests a patch or release action
- the workflow looks routine
- the actual tool boundary crosses into a repo or branch scope with different trust assumptions

What this adds:

- a clearer repository-boundary state problem than the current mixed hybrid row
- a case where omission is not the only failure; wrong continuation matters too

#### 2. Memory retrieval into a privileged action

Candidate shape:

- an earlier memory write is harmless on its own
- a later workflow retrieves it into a shell, CI, payment, or repository action
- the model must distinguish "stored context exists" from "stored context is still safe to execute on"

What this adds:

- a true memory-to-action provenance case
- a cleaner test of whether runtime defenses are tracking trust state, not just action labels

### Guardrail

Do not add both fixtures if local deterministic controls or rubric clarity are weak. One great new fixture is better than three noisy ones.

## Model And Defense Matrix

Prioritize rows that are already proven to serve cleanly on TPU:

- `Qwen/Qwen2.5-7B-Instruct`
- `mistralai/Mistral-7B-Instruct-v0.3`
- `Qwen/Qwen2.5-14B-Instruct`

Recommended comparison surface:

| Row type | Qwen 7B | Mistral 7B | Qwen 14B |
| --- | --- | --- | --- |
| weak row | `baseline + none` | `baseline + none` | `baseline + none` |
| repaired completeness row | `checklist + none` | `checklist + none` | `checklist + none` |
| defended row | optional if unchanged | required | required |

Why this shape:

- `Qwen 7B checklist + none` already looked "closed" on v1, so it is the canary for whether the harder pack exposes new misses without needing runtime help.
- `Mistral 7B` is the strongest test of whether runtime policy still matters after completeness is repaired.
- `Qwen 14B` is the strongest test of whether scale continues to trade utility gains for unsafe approvals.

## Throughput Claim Boundary

If we talk about TPU value beyond score, keep it modest and evidence-backed.

Allowed claim:

- TPU-backed serving made repeated fixed-pack comparisons practical and reproducible on the same hardware lane.

Only include throughput or latency tables if we can collect them without muddying the benchmark story.

Do not let "TPU speed" become the headline if the useful scientific result is still defense-layer separation.

## 7-Day Sequence

### Day 1

- freeze the sprint question
- select `1-2` new fixture additions
- define the exact rerun matrix

### Day 2

- implement and locally validate the new fixtures
- rerun deterministic policy controls to prove the new slice is shaped correctly

### Day 3

- TPU rerun on the current fixed frontier pack if needed as a control refresh
- verify serving, context-window, and artifact-copy steps are still boring

### Day 4-5

- run the new TPU matrix on the expanded frontier pack
- collect pass, unsafe, missed, and coverage outputs exactly as before

### Day 6

- write the sweep index or synthesis report
- emphasize what changed from frontier pack v1 and what did not

### Day 7

- refresh README / launch / grant surfaces only if the new result changes the public thesis

## Success Criteria

At the end of this waiting-window sprint, the repo should have:

- one new small frontier-pack revision with a clearer thesis
- one new TPU comparison matrix or synthesis artifact
- a sharper answer to which defense layers still matter by model family
- a stronger explanation of why TPU time was worth spending on this benchmark

## Failure Criteria

The sprint is off track if:

- fixture count grows faster than clarity
- new TPU rows do not answer a sharper question than the old rows
- we spend TPU time on model lanes that fail at serving or setup instead of benchmark substance
- the public output becomes another score dump instead of a benchmark insight

## Immediate Next Step

Execute this sprint in the repo and workspace in this order:

1. add the waiting-window sprint to the active checklist
2. select the first `1-2` fixture additions
3. validate them locally before any new TPU session
4. run the highest-value TPU reruns only
5. publish one new synthesis artifact while the TPU window is still live
