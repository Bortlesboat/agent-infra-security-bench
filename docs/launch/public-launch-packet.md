# Public Launch Packet

## Launch Thesis

Agent Infrastructure Security Bench should now be presented as a benchmark for **boundary-layer agent failures under decision pressure**, not as a one-off payment-replay demo and not as a generic model-safety leaderboard.

The strongest current public claim is:

> the repo separates **safety**, **utility**, and **completeness** on the same fixed frontier pack, and shows that different open model families need different defense mixes to close the same boundary-pressure benchmark

That is the story worth launching.

## What Is Ready To Share

- the stable `34`-fixture control suite in `scenarios/`
- the harder `7`-fixture frontier pack in `scenarios-frontier/`
- deterministic policy controls that prove the frontier pack is shaped correctly
- local, Mac mini, hosted, and TPU-backed comparison rows
- a fixed-pack TPU sweep across `Qwen 7B`, `Mistral 7B`, and `Qwen 14B`
- a higher-layer synthesis that explains what the matrix means
- BoundaryBench Commons so other builders can reuse the evidence without the same hardware

## Canonical Proof Points

These are the numbers to lead with right now:

1. **The frontier pack is real, not decorative**
   - `deny-high-risk-payment-state`: `1/7`
   - `deny-high-risk-stateful`: `7/7`

2. **Completeness is a measurable failure mode**
   - `Qwen 7B baseline + none`: `4/7`, `46/47` coverage
   - `Mistral 7B baseline + none`: `2/7`, `44/47` coverage

3. **Checklist prompting is a real intervention, not copy polish**
   - `Qwen 7B checklist + none`: `7/7`, `47/47` coverage
   - `Mistral 7B checklist + none`: `5/7`, `47/47` coverage

4. **Runtime policy matters differently by family**
   - `Qwen 7B checklist + none`: `7/7`
   - `Qwen 7B checklist + risk-floor`: `7/7`
   - `Mistral 7B checklist + none`: `5/7`
   - `Mistral 7B checklist + risk-floor`: `7/7`

5. **Scale helps, but not monotonically**
   - `Qwen 14B baseline + none`: `5/7`, `1` unsafe
   - `Qwen 14B checklist + none`: `6/7`, `2` unsafe
   - `Qwen 14B checklist + risk-floor`: `7/7`, `0` unsafe

## Canonical Links

Use these as the main public evidence spine:

- Repo: `https://github.com/Bortlesboat/agent-infra-security-bench`
- Frontier synthesis: `https://github.com/Bortlesboat/agent-infra-security-bench/blob/main/docs/reports/2026-04-frontier-findings-synthesis.md`
- Frontier sweep index: `https://github.com/Bortlesboat/agent-infra-security-bench/blob/main/docs/reports/2026-04-frontier-pack-tpu-sweep.md`
- Frontier pack overview: `https://github.com/Bortlesboat/agent-infra-security-bench/blob/main/scenarios-frontier/README.md`
- BoundaryBench Commons: `https://github.com/Bortlesboat/agent-infra-security-bench/blob/main/docs/commons/README.md`
- Grant-ready summary: `https://github.com/Bortlesboat/agent-infra-security-bench/blob/main/docs/grants/one-page-proposal.md`

## Story Ladder

Keep the public story in this order:

1. **Why this exists**
   - many practical agent failures happen at the boundary between untrusted text and privileged tools

2. **Why the existing control row was not enough**
   - the `34`-fixture suite became a solved control and stopped being a worthy scarce-compute target

3. **What the frontier pack changes**
   - omission pressure, stateful continuation, and hybrid workflow drift become visible

4. **What the benchmark now shows**
   - models do not fail the same way
   - prompt structure can repair completeness
   - runtime defense still matters for some families
   - larger checkpoints can improve utility while sharpening safety failures

5. **Why TPU access mattered**
   - not because "we used a TPU"
   - because scarce compute let us publish reusable evidence other builders can study without the same hardware

## Channel Priority

### Owned Channels

- `README.md`
- `docs/reports/2026-04-frontier-findings-synthesis.md`
- `docs/reports/2026-04-frontier-pack-tpu-sweep.md`
- `docs/launch/frontier-launch-copy.md`
- `docs/grants/one-page-proposal.md`

### Rented Channels

- X thread for agent, MCP, eval, and infrastructure builders
- LinkedIn post for infrastructure, security, grant, and research audiences
- Hacker News only after the synthesis and sweep links are the obvious first stops

### Borrowed Channels

- benchmark maintainers
- agent-runtime and MCP builders
- grant reviewers
- conference CFPs for agent engineering, security, evals, and infra

## Launch Sequence

1. Merge the frontier-era launch docs so `main` reflects the current thesis.
2. Publish one GitHub-friendly summary that links the repo, synthesis, and frontier sweep.
3. Reuse the same thesis in X and LinkedIn copy.
4. Use the one-paragraph grant summary in applications and outreach notes.
5. Reserve Hacker News for the version where the claims boundary and fixed-pack sweep are already easy to inspect.

## Messaging Guardrails

- Do not lead with TPU credits or quota.
- Do not collapse pass rate into a generic "model safety" claim.
- Do not hide unsafe counts when a stronger model improves pass rate.
- Do not describe omissions as a cosmetic formatting issue; treat coverage as part of the result.
- Do not imply the defended rows generalize outside this benchmark surface.

## Recommended Primary Message

If we only get one sentence, use this one:

> Agent Infrastructure Security Bench is an open benchmark for boundary-layer agent failures that shows how safety, utility, and completeness separate under decision pressure, and how different open model families need different defense layers to close the same frontier pack.

## Claims Boundary

- This is a small fixed benchmark surface, not a broad leaderboard.
- Synthetic and deterministic controls are controls, not model rows.
- Defended rows do not prove universal safety.
- The current claim is about failure shape and defense-layer interaction on a public-safe boundary benchmark.
