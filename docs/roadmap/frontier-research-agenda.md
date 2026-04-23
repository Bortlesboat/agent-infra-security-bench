# Frontier Research Agenda

## Stated Goal

By June 30, 2026, make Agent Infrastructure Security Bench the most useful open, reproducible benchmark for stateful agent infrastructure boundary failures.

The benchmark should stress the places where autonomous agents cross from language into durable systems: payment proof freshness and replay, repository privileges, MCP tool provenance, CI and shell execution, memory leakage, and runtime policy gaps.

The goal is not to out-scale every existing MCP benchmark. The goal is to own the neglected stateful boundary layer and publish evidence that other builders can reproduce locally, on a second machine, and on accelerator-backed runs.

The core evaluation lens is now three-axis, not pass-rate-only:

- safety: unsafe approvals
- utility: missed expected actions
- completeness: tool-decision coverage, omissions, and duplicate decisions

## Why This Lane

Existing benchmark work already proves the broad agent-security problem:

- [Agent Security Bench](https://proceedings.iclr.cc/paper_files/paper/2025/file/5750f91d8fb9d5c02bd8ad2c3b44456b-Paper-Conference.pdf) evaluates attacks across system prompts, user prompts, tool use, and memory, and shows that current defenses still leave major agent vulnerabilities.
- [MCPSecBench](https://arxiv.org/abs/2508.13220) formalizes MCP security and covers prompt datasets, servers, clients, attack scripts, harnesses, and protections across protocol layers.
- [MCP Security Benchmark](https://openreview.net/pdf?id=irxxkFMrry) focuses on MCP-specific attacks across task planning, tool invocation, and response handling, with large-scale tool and scenario coverage.
- [MCPSHIELD](https://arxiv.org/abs/2604.05969) argues that the defense landscape is fragmented and that runtime enforcement, capability control, attestation, and information-flow tracking need to work together.

This repo should differentiate by focusing on infrastructure-state failures that generic prompt and MCP benchmarks do not center:

- a payment proof is syntactically valid but stale, reused, or bound to the wrong request
- a repository action is safe in one repo but unsafe after crossing an ownership boundary
- a tool name or description looks trusted but comes from the wrong server or provenance chain
- a CI or shell action is useful only if runtime policy sees the untrusted source that caused it
- a memory write is harmless alone but unsafe when later retrieved into a privileged task

## Compute Strategy

Use accelerator access to scale evidence, not to chase an unrelated training project.

- Mac mini: second local baseline runner for reproducibility, larger local Ollama/MLX-family runs, and cross-machine checks before publishing claims.
- Main local GPU box: fast iteration for medium open-model sweeps, candidate fixture generation, and overnight ablations when available.
- Google TPU Research Cloud: after confirmation only, use TPU-backed runs for batch model evaluation, adversarial scenario generation, and possibly a small boundary-risk model if the dataset becomes large enough.

The repo output should stay hardware-neutral: public-safe JSON fixtures, raw JSONL model/tool traces, deterministic scores, CSV/Markdown tables, and run manifests.

The public-good expression of this strategy is BoundaryBench Commons: a static index of reusable fixtures, reports, traces, and runbooks that lets people without TPU access benefit from accelerator-backed work.

## Research Milestones

### Milestone 1: Stateful Fixture Expansion

Grow from 20 fixtures to at least 75 public-safe fixtures, with the first heavy slice focused on x402/payment replay and request-binding failures.

Target categories:

- x402 replay, freshness, route binding, amount mismatch, facilitator mismatch, and cross-tool reuse
- MCP tool shadowing, name collision, description injection, response injection, and tool-transfer attempts
- repository read/write boundary crossing between public, private, fork, and organization-like scopes
- CI/shell escalation from untrusted issue text, logs, artifacts, and package scripts
- memory write and retrieval failures that become unsafe only across multiple steps

### Milestone 2: Adversarial Scenario Factory

Build a local generator loop that proposes candidate fixtures, mutates existing scenarios, and keeps only cases that pass schema validation and public-safety checks.

The first version should not auto-publish generated fixtures. It should create candidate JSON plus review notes so the curated benchmark remains small, inspectable, and credible.

### Milestone 3: Model And Defense Sweeps

Run the same fixture suite across multiple open model families and defense modes.

Minimum comparison surface:

- baseline prompt
- setup-aware prompt
- runtime risk floor
- stateful verifier for payment and provenance evidence
- combined prompt plus runtime defense

Every run should include model name, runtime, hardware, benchmark commit, trace adapter, raw traces, result tables, and known limitations.
Every comparison table should preserve all three axes so pass-rate improvements do not hide coverage failures.

### Milestone 4: Runtime Boundary Defense

Turn the current risk-floor idea into a small policy layer that reasons over action state, not only action labels.

The defense should be simple enough to audit:

- verify payment proof freshness and request binding
- preserve tool provenance and server identity through trace adaptation
- detect privilege-boundary changes across repo, memory, CI, and shell actions
- fail closed on missing required state for high-consequence actions

### Milestone 5: Technical Report Before Outreach

Do not spend the next cycle on outreach. Publish only after the artifact has a stronger technical spine:

- 75 to 100 curated fixtures
- at least 5 model/runtime comparisons
- at least 4 defense configurations
- one clear failure class that prompt-only defenses miss but stateful runtime validation catches
- reproducible raw traces, manifests, and CI-backed scoring

### Milestone 6: BoundaryBench Commons

Turn scarce compute access into a public artifact other builders can use without owning the same hardware.

The first commons layer should stay static:

- a machine-readable index of published artifacts
- links to reports, fixtures, examples, and runbooks
- clear notes on what is reusable without accelerator access
- a validation command that proves the index points at real repo paths

Only add a hosted eval queue after the fixture format, trace format, and commons index have earned trust.

## Near-Term Commit Sequence

1. Add this frontier agenda and align the README around development-first positioning.
2. Expand the x402 replay fixture family and close the first stateful payment gap.
3. Add provenance metadata to relevant MCP and repository fixtures.
4. Add an adversarial fixture candidate format and public-safety review gate.
5. Add a scenario mutator/generator that runs locally first.
6. Add a sweep manifest command that can compare many models and defenses in one table.
7. Prepare the TPU smoke run, but create no TPU VM until TRC confirmation arrives.
8. Maintain BoundaryBench Commons as the public index for reusable compute-backed artifacts.
9. Publish a development report only after the next fixture and sweep expansion lands.
