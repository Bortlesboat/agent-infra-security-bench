# Public Launch Packet

## Launch Thesis

Agent Infrastructure Security Bench is a small open benchmark for evaluating whether tool-using AI agents preserve repository, payment, identity, browser, and shell boundaries under indirect prompt injection and tool poisoning.

The launch should emphasize reproducibility and restraint: this is not a claim that any model is safe. It is a public test harness for finding where agent runtimes need better boundaries.

## Launch Sequence

1. Publish the GitHub repository after a final public-safety scan.
2. Publish deterministic baseline reports that separate synthetic controls, transparent policy baselines, and future model results.
3. Announce the stateful payment baseline on X and LinkedIn with a short thread linking to the repo and report.
4. Send targeted notes to MCP, agent security, and eval builders who are already discussing tool-boundary failures.
5. Reuse the same artifact as appendix material for safety, information-security, and open-source grant applications.
6. Hold Hacker News until the first real-agent trace report is ready.

## Owned Channels

- GitHub README and reports
- Project docs under `docs/reports/`
- Grant appendix under `docs/grants/`

## Rented Channels

- X thread for agent security and MCP builders
- LinkedIn post for security, infrastructure, and grant audiences
- Hacker News only after the real-agent baseline is in place

## Borrowed Channels

- Conference CFPs around MCP, agent engineering, security, and evals
- Grant reviewers and open-source funders
- Maintainers of adjacent benchmark or agent-runtime projects

## Short Social Copy

I am publishing a small open benchmark for a failure mode I keep seeing in agent infrastructure: untrusted text crosses into privileged tools.

The first suite covers MCP tool poisoning, cross-repository leakage, payment replay, CI token exposure, browser deception, and shell/tool-return injection.

The first concrete finding: static tool-risk labels catch obvious dangerous actions, but miss x402 payment replay. A stateful payment baseline closes that fixture by validating proof freshness and request binding.

Current deterministic results:

- `naive-allow`: 0/20
- `deny-high-risk`: 19/20
- `deny-high-risk-payment-state`: 20/20

Next step: real-agent traces, then TPU-backed model/defense sweeps after access is confirmed.

Repo: <link>

Report: <link>

## Claims Boundary

- Synthetic traces are controls, not model results.
- Benchmark pass rate is not a proof of general model safety.
- Results should include commit, manifest, model/policy, trace adapter, hardware, and limitations.
