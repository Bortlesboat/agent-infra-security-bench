# TPU Agent Security Landscape - 2026-04-22

## Recommendation

Build a narrow benchmark for self-hosted agent infrastructure security, then use TPU access to run public model and defense sweeps.

The repo should not compete head-on with broad benchmarks. Its value is specificity: MCP tool boundaries, x402/payment flows, GitHub-like repository access, and developer-agent shell boundaries.

## Current TPU Facts

- Google TPU Research Cloud positions free Cloud TPU access as a research accelerator and expects public outputs such as open-source code, blog posts, publications, or similar artifacts.
- Google Cloud TPU setup now centers on Cloud TPU VMs for v5e/v5p/v6e, with PyTorch and JAX quickstarts.
- The current single-host starter path in official docs uses `v5litepod-8` with runtime `v2-alpha-tpuv5-lite`.
- v6e/Trillium examples use `v6e-8` with runtime `v2-alpha-tpuv6e`.
- Ironwood / TPU7x requires GKE, so it should not be the first-run path.
- Official docs call out PyTorch/XLA and JAX support, and TPU inference support for v5e and newer versions.

Sources:

- Google TRC: https://sites.research.google/trc/about/
- TPU setup: https://docs.cloud.google.com/tpu/docs/setup-gcp-account
- PyTorch quickstart: https://docs.cloud.google.com/tpu/docs/run-calculation-pytorch
- JAX quickstart: https://docs.cloud.google.com/tpu/docs/run-calculation-jax
- TPU software versions: https://docs.cloud.google.com/tpu/docs/runtimes
- TPU inference: https://docs.cloud.google.com/tpu/docs/tpu-inference

## Existing Benchmark Landscape

- AgentDojo provides a dynamic environment for prompt-injection attacks and defenses against LLM agents.
- Inspect Evals includes many agent and cybersecurity evals, including The Agent Company, CVEBench, Cybench, CyberGym, and related suites.
- MCP-SafetyBench focuses on MCP ecosystems and lists 245 tasks across 5 domains and 20 attack types.
- Recent research argues that current prompt-injection benchmarks can have weak attacks, flawed metrics, or implementation bugs, so stronger targeted benchmark design matters.
- Docker's public writeup on the GitHub MCP data-heist pattern is a useful example of the exact infrastructure boundary this repo should model: public untrusted issue text plus overly broad repository access.

Sources:

- AgentDojo: https://github.com/ethz-spylab/agentdojo
- Inspect Evals: https://github.com/UKGovernmentBEIS/inspect_evals
- MCP-SafetyBench: https://xjzzzzzzzz.github.io/mcpsafety.github.io/
- Benchmark critique paper: https://arxiv.org/abs/2510.05244
- Docker MCP/GitHub prompt-injection writeup: https://www.docker.com/blog/mcp-horror-stories-github-prompt-injection/

## Grant Fit

The strongest grant framing is:

> Open-source benchmark and reproducibility workflow for evaluating whether self-hosted AI agents preserve tool, identity, payment, and repository boundaries under indirect prompt injection and tool poisoning.

Best near-term targets:

- OpenAI Safety Fellowship - safety evaluation, robustness, privacy-preserving safety methods, agentic oversight.
- Amazon AI for Information Security CFP - trustworthy agentic AI for security operations and reliable security tooling.
- NLnet - public-goods open-source tooling, open standards, and digital commons.

Sources:

- OpenAI Safety Fellowship: https://openai.com/index/introducing-openai-safety-fellowship/
- Amazon AI for Information Security CFP: https://www.amazon.science/research-awards/call-for-proposals/ai-for-information-security-call-for-proposals-spring-2026
- NLnet proposal page: https://nlnet.nl/propose/

## First 14-Day Build

1. Finish the fixture schema and deterministic scorer.
2. Add 20 public-safe fixtures across repository, payment, shell, browser, and filesystem domains.
3. Add trace adapters for one local agent loop and one synthetic trace generator.
4. Run a local baseline.
5. Run a TPU smoke test with a small open model or embedding/ranking model.
6. Publish a results table and short writeup.
7. Convert the writeup into grant proposal appendix language.
