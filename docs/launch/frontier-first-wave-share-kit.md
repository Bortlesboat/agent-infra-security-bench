# Frontier First-Wave Share Kit

## Purpose

This is the tactical companion to `public-launch-packet.md` and `frontier-launch-copy.md`.

Those documents explain the thesis. This one answers the more practical question:

> if we want to start turning the frontier benchmark into reputation, what should we actually say first?

## Recommended First Wave

Use the first outward-facing push in this order:

1. GitHub-friendly summary post
2. X thread
3. LinkedIn post
4. Targeted direct note to benchmark, agent-runtime, or grant audiences
5. Hacker News only after the first four surfaces are live

That order fits the current state of the project: the repo, fixed-pack sweep, and synthesis are ready; the benchmark has a sharp claim; and we are still better served by precise technical visibility than by a broad front-page gamble.

## The One-Sentence Thesis

Use this whenever space is tight:

> Agent Infrastructure Security Bench is an open benchmark for boundary-layer agent failures that shows how safety, utility, and completeness separate under decision pressure, and how different open model families need different defense layers to close the same frontier pack.

## Recommended First Public Post

If we only publish one short post first, use this shape:

I published an open benchmark for boundary-layer agent failures in tool-using AI systems.

The useful result is not just a score table. On the same fixed frontier pack, the benchmark separates **safety**, **utility**, and **completeness**, and shows that different open model families need different defense mixes to close the same boundary-pressure scenarios.

That means the project can distinguish:

- models that mostly fail by omission
- models that recover with prompt structure
- models that still need runtime defense after completeness is repaired
- stronger checkpoints that improve pass rate while still surfacing unsafe approvals

Repo: `https://github.com/Bortlesboat/agent-infra-security-bench`

Synthesis: `https://github.com/Bortlesboat/agent-infra-security-bench/blob/main/docs/reports/2026-04-frontier-findings-synthesis.md`

Sweep: `https://github.com/Bortlesboat/agent-infra-security-bench/blob/main/docs/reports/2026-04-frontier-pack-tpu-sweep.md`

## X Post Variant

I published an open benchmark for boundary-layer agent failures in tool-using AI systems.

The interesting part is not just a score table. On the same fixed frontier pack, it separates **safety**, **utility**, and **completeness**, and shows that different open model families need different defense mixes to close the same scenarios.

Repo:
`https://github.com/Bortlesboat/agent-infra-security-bench`

Synthesis:
`https://github.com/Bortlesboat/agent-infra-security-bench/blob/main/docs/reports/2026-04-frontier-findings-synthesis.md`

## LinkedIn Post Variant

I published an open benchmark for a narrow but increasingly practical problem in agent infrastructure:

when a tool-using agent reads untrusted context, does the surrounding runtime preserve boundaries around repositories, MCP tools, payment actions, CI artifacts, browser state, memory, and shell-capable workflows?

The project now has a fixed frontier pack that does something more useful than another leaderboard row. It separates **safety**, **utility**, and **completeness** on the same benchmark surface and shows that different open model families need different defense mixes to close the same boundary-pressure cases.

The highest-level lesson so far is simple: a defended row is not one thing. Some models mainly need completeness structure. Some still need runtime help after completeness is repaired. Larger checkpoints can improve utility while still surfacing sharper safety failures.

Repo:
`https://github.com/Bortlesboat/agent-infra-security-bench`

Synthesis:
`https://github.com/Bortlesboat/agent-infra-security-bench/blob/main/docs/reports/2026-04-frontier-findings-synthesis.md`

Sweep:
`https://github.com/Bortlesboat/agent-infra-security-bench/blob/main/docs/reports/2026-04-frontier-pack-tpu-sweep.md`

## Direct Note Variant

Subject: Open benchmark for boundary-layer agent failures

I published an open benchmark for tool-using AI agents that focuses on practical boundary failures: repositories, MCP tools, payment actions, CI artifacts, browser state, memory surfaces, and shell-capable workflows.

The current frontier result is useful because it does more than rank models. On the same fixed frontier pack, it separates **safety**, **utility**, and **completeness**, and shows that different open model families need different defense mixes to close the same benchmark surface.

Repo:
`https://github.com/Bortlesboat/agent-infra-security-bench`

Frontier synthesis:
`https://github.com/Bortlesboat/agent-infra-security-bench/blob/main/docs/reports/2026-04-frontier-findings-synthesis.md`

Frontier sweep:
`https://github.com/Bortlesboat/agent-infra-security-bench/blob/main/docs/reports/2026-04-frontier-pack-tpu-sweep.md`

If this is relevant to what you're building, I would especially value reactions on fixture shape, completeness measurement, and where runtime policy should remain visible instead of being hidden by a final pass rate.

## Grant Paragraph

Agent Infrastructure Security Bench is an open benchmark for self-hosted, tool-using AI agents that focuses on practical boundary failures rather than generic benchmark scores. The repo now combines a stable `34`-fixture control suite, a harder fixed frontier pack, deterministic policy controls, local/Mac mini/hosted/TPU-backed comparison rows, and a public synthesis that separates **safety**, **utility**, and **completeness** on the same benchmark surface. The key result so far is that different open model families need different defense mixes to close the same boundary-pressure cases: some mainly need structured completeness prompting, while others still need a runtime risk floor after completeness is repaired. All fixtures, scoring, reports, and runbooks are public-safe and reusable so other builders can inspect and reuse the evidence without the same hardware.

## Where To Point People

Default link order:

1. Repo
2. Frontier synthesis
3. Frontier sweep

Use the sweep when the audience wants numbers.

Use the synthesis when the audience wants the thesis.

Use the repo when the audience wants to inspect methodology, fixtures, and reproducibility.

## First-Wave CTA

Prefer this CTA over a generic "thoughts?":

> I would especially value reactions on fixture shape, completeness measurement, and where runtime policy should remain visible instead of being hidden by a final pass rate.

It attracts the right kind of technical response and keeps the conversation on the benchmark's real contribution.

## What Not To Lead With

- TPU credits
- raw quota numbers
- generic "AI safety" language
- pass rate without unsafe counts or coverage context
- claims that a defended row proves broad safety

## Launch Goal

The goal of the first wave is not mass attention.

It is to establish one credible public identity for the project:

this is a benchmark that makes boundary-layer agent failures legible, reproducible, and comparable across safety, utility, and completeness.
