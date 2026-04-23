# Opportunity Stack

## Primary Angle

Open-source benchmark and reproducibility workflow for evaluating whether self-hosted AI agents preserve tool, identity, payment, and repository boundaries under indirect prompt injection and tool poisoning.

## Priority Targets

### OpenAI Safety Fellowship

- Deadline: May 3, 2026
- Fit: safety evaluation, robustness, agentic oversight, privacy/security of agent tooling
- Packet: research agenda, benchmark repo, baseline report, public-deliverables plan, references
- Source: https://openai.com/index/introducing-openai-safety-fellowship/

### Amazon AI for Information Security CFP

- Deadline: May 6, 2026
- Fit: trustworthy agentic AI for security operations, confused-deputy prevention, access governance, reliable security tooling
- Packet: 3-page proposal, evaluation method, milestones, public-release plan, budget, and April 2026 stateful payment baseline report
- Source: https://www.amazon.science/research-awards/call-for-proposals/ai-for-information-security-call-for-proposals-spring-2026

### NLnet Open Call

- Deadline: June 1, 2026 at 12:00 CEST
- Fit: open-source public-goods tooling, open standards, reproducible security evaluation, digital commons
- Packet: compact work packages, deliverables, license plan, budget, maintenance plan, stateful payment validation baseline
- Source: https://nlnet.nl/propose/

### AGNTCon and MCPCon North America CFP

- Deadline: June 7, 2026 at 11:59 PM PDT / June 8, 2026 at 2:59 AM EDT
- Fit: MCP security, agent engineering, benchmarks/evals, traceability, identity, sandboxing, runtime controls
- Packet: talk proposal, demo outline, deterministic policy baseline, stateful payment baseline, lessons from first real-agent traces
- Source: https://events.linuxfoundation.org/agntcon-mcpcon-north-america/program/cfp/

### AGNTCon and MCPCon Europe CFP

- Deadline: June 8, 2026 at 23:59 CEST / June 8, 2026 at 5:59 PM EDT
- Fit: same agent protocol and runtime-security audience as North America, with a stronger Europe/open-commons overlap for NLnet-adjacent framing
- Packet: adapt the North America talk proposal with one slide on open-source reproducibility and one slide on payment-state validation
- Source: https://sessionize.com/agntcon-mcpcon-europe-2026/

## Reusable Proof Assets

- Public repo with trust and contribution files
- Scenario suite and deterministic scorer
- Run manifest JSON for every published result
- Baseline report with synthetic controls separated from model results
- Stateful payment baseline showing `deny-high-risk` at `19/20` and `deny-high-risk-payment-state` at `20/20`
- Public roadmap issues for real-agent traces, x402 replay fixture expansion, TPU smoke manifests, and fixture contributions
- TPU smoke-run runbook once TRC quota is confirmed

## Next Packet To Assemble

Use the stateful payment baseline as the evidence spine for NLnet, Amazon PI follow-ups, and AGNTCon/MCPCon. The next technical proof to add is a first real-agent trace, because deterministic baselines are now strong enough to anchor the comparison.
