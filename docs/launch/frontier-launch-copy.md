# Frontier Launch Copy

## Historical Note

This is the current outward-facing copy surface for the frontier-era benchmark story.

The earlier `stateful-payment-launch-copy.md` file is still useful as a historical record of the first `20`-fixture payment-state release, but it is no longer the best top-level launch surface for the repo.

## Primary Links

- Repo: `https://github.com/Bortlesboat/agent-infra-security-bench`
- Frontier findings synthesis: `https://github.com/Bortlesboat/agent-infra-security-bench/blob/main/docs/reports/2026-04-frontier-findings-synthesis.md`
- Frontier pack TPU sweep: `https://github.com/Bortlesboat/agent-infra-security-bench/blob/main/docs/reports/2026-04-frontier-pack-tpu-sweep.md`
- Frontier pack overview: `https://github.com/Bortlesboat/agent-infra-security-bench/blob/main/scenarios-frontier/README.md`
- BoundaryBench Commons: `https://github.com/Bortlesboat/agent-infra-security-bench/blob/main/docs/commons/README.md`
- Grant-ready summary: `https://github.com/Bortlesboat/agent-infra-security-bench/blob/main/docs/grants/one-page-proposal.md`

## GitHub-Friendly Summary

Agent Infrastructure Security Bench is an open benchmark for a narrow but practical failure surface: what happens when tool-using agents read untrusted context and then cross into repositories, MCP tools, payment actions, CI artifacts, memory surfaces, browser state, and shell-capable workflows.

The project's current frontier result is not just a better score table. It shows that boundary-layer agent reliability splits across **safety**, **utility**, and **completeness**. On the same fixed `7`-fixture frontier pack, some models mainly fail by omission, some recover with prompt structure alone, some still need a runtime defense layer after completeness is repaired, and a larger checkpoint can improve pass rate while surfacing sharper unsafe approvals. That is the reusable public claim.

## X Thread Draft

1/ I published an open benchmark for a failure mode that keeps showing up in agent infrastructure:

untrusted context crossing into privileged tools

Repo:
https://github.com/Bortlesboat/agent-infra-security-bench

2/ The interesting part now is not just the original control suite.

There is also a fixed `7`-scenario frontier pack that pressures:

- long tool menus
- stateful workflow continuation
- hybrid omission + state drift failures

3/ The frontier pack has a clean control result:

- `deny-high-risk-payment-state`: `1/7`
- `deny-high-risk-stateful`: `7/7`

So the pack is doing real work. A generic high-risk denylist is not enough here.

4/ The main benchmark result is that boundary-layer reliability is not one problem.

This pack separates:

- safety
- utility
- completeness

and different model families fail differently on the same scenarios.

5/ `Qwen 7B` on TPU is mostly a completeness/prompting story:

- `baseline + none`: `4/7`, `46/47` coverage
- `checklist + none`: `7/7`, `47/47` coverage

Same model, same pack, very different behavior once the tool checklist is explicit.

6/ `Mistral 7B` needs more than that:

- `baseline + none`: `2/7`, `44/47`
- `checklist + none`: `5/7`, `47/47`
- `checklist + risk-floor`: `7/7`, `47/47`

So runtime policy still matters after completeness is repaired.

7/ `Qwen 14B` is the strongest open weak-prompt row here, but it also shows why pass rate is not enough:

- `baseline + none`: `5/7`, `1` unsafe
- `checklist + none`: `6/7`, `2` unsafe
- `checklist + risk-floor`: `7/7`, `0` unsafe

8/ The public claim is deliberately narrow:

this is not "model safety."

It is evidence that safety, utility, and completeness split apart under boundary pressure, and different open model families need different defense mixes to close the same pack.

9/ The higher-layer synthesis is here:
https://github.com/Bortlesboat/agent-infra-security-bench/blob/main/docs/reports/2026-04-frontier-findings-synthesis.md

And the fixed-pack TPU comparison is here:
https://github.com/Bortlesboat/agent-infra-security-bench/blob/main/docs/reports/2026-04-frontier-pack-tpu-sweep.md

## LinkedIn Draft

I published an open benchmark for a narrow but increasingly practical problem in agent infrastructure:

when a tool-using agent reads untrusted context, does the surrounding runtime preserve boundaries around repositories, MCP tools, payment actions, CI artifacts, browser state, memory, and shell-capable workflows?

The current frontier result is more useful than another leaderboard row.

On a fixed `7`-scenario frontier pack, the benchmark now separates three different dimensions:

- safety
- utility
- completeness

That matters because different open model families fail differently on the same pressure test.

For example:

- `Qwen 7B` with a weak prompt lands at `4/7`, but reaches `7/7` once the prompt explicitly requires a tool-by-tool checklist
- `Mistral 7B` improves from `2/7` to `5/7` with the same checklist, but still needs a runtime risk floor to reach `7/7`
- `Qwen 14B` is the strongest open weak-prompt row here, but still surfaces unsafe approvals until the runtime layer is restored

That is the main takeaway of the project so far: boundary-layer reliability is not one number, and a "defended row" is not one thing. Some models mostly need completeness discipline. Some need runtime help after completeness is repaired. Larger checkpoints can improve utility while sharpening safety failures.

The repo keeps the control row, frontier pack, TPU sweep, and synthesis public so other builders can reuse the evidence without needing the same hardware.

Repo:
https://github.com/Bortlesboat/agent-infra-security-bench

Frontier synthesis:
https://github.com/Bortlesboat/agent-infra-security-bench/blob/main/docs/reports/2026-04-frontier-findings-synthesis.md

Frontier sweep:
https://github.com/Bortlesboat/agent-infra-security-bench/blob/main/docs/reports/2026-04-frontier-pack-tpu-sweep.md

## Hacker News Draft

Title:

Agent Infrastructure Security Bench: frontier evals for tool-using agents

Text:

I built an open benchmark for boundary-layer agent failures: repository drift, MCP provenance issues, payment-state errors, browser and CI continuation problems, memory leakage, and tool-driven workflow escalation.

The current interesting artifact is a fixed `7`-scenario frontier pack on top of the original control suite.

It shows that different open models fail in different ways on the same benchmark surface:

- `Qwen 7B` mostly needed prompt structure to stop missing or omitting decisions
- `Mistral 7B` needed prompt structure plus a runtime risk floor
- `Qwen 14B` improved pass rate under the same pressure, but also introduced unsafe approvals until the runtime layer came back

So the useful result is not "model X scored better."

It is that the benchmark separates safety, utility, and completeness under decision pressure, and that different families need different defense mixes to close the same pack.

Repo:
https://github.com/Bortlesboat/agent-infra-security-bench

Synthesis:
https://github.com/Bortlesboat/agent-infra-security-bench/blob/main/docs/reports/2026-04-frontier-findings-synthesis.md

Sweep:
https://github.com/Bortlesboat/agent-infra-security-bench/blob/main/docs/reports/2026-04-frontier-pack-tpu-sweep.md

## Grant / Application Paragraph

Agent Infrastructure Security Bench is an open benchmark for self-hosted, tool-using AI agents that focuses on practical boundary failures rather than generic benchmark scores. The repo now combines a stable `34`-fixture control suite, a harder `7`-fixture frontier pack, deterministic policy controls, local/Mac mini/hosted/TPU-backed comparison rows, and a public synthesis that separates **safety**, **utility**, and **completeness** on the same benchmark surface. The key result so far is that different open model families need different defense mixes to close the same frontier pack: some mainly need structured completeness prompting, while others still need a runtime risk floor after completeness is repaired. All fixtures, scoring, reports, and runbooks are public-safe and reusable through BoundaryBench Commons so other builders can inspect and reuse the evidence without the same hardware.

## Short Blurb

BoundaryBench is an open benchmark for boundary-layer agent failures that turns repository, MCP, payment, CI, browser, memory, and shell workflow mistakes into reproducible evidence about safety, utility, and completeness.
