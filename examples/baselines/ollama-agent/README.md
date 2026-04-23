# Ollama Agent Baseline Example

This example reproduces the first model-backed local Ollama baseline.

```powershell
ollama pull qwen2.5:7b
agent-bench run-ollama-agent scenarios outputs/llm-agent-baseline --model qwen2.5:7b --scenario-commit 4814bbf
```

Expected summary from the April 23, 2026 run:

| Agent | Passed | Total | Pass Rate | Average Score |
| --- | ---: | ---: | ---: | ---: |
| `ollama/qwen2.5:7b` | 14 | 20 | 0.700 | 0.867 |

The observed failures were over-blocks of expected-safe actions. The model did not allow any expected-blocked action in this run.

This is a local Ollama model result, not an OpenAI, cloud, or TPU-backed result.

## Defense Sweep

The follow-up defense sweep compares the baseline prompt against a setup-aware prompt and a runtime risk-floor policy:

```powershell
agent-bench run-ollama-agent scenarios outputs/llm-defense-sweep --model qwen2.5:7b --scenario-commit 9f2b415 --prompt-profile baseline --runtime-policy none
agent-bench run-ollama-agent scenarios outputs/llm-defense-sweep --model qwen2.5:7b --scenario-commit 9f2b415 --prompt-profile setup-aware --runtime-policy none
agent-bench run-ollama-agent scenarios outputs/llm-defense-sweep --model qwen2.5:7b --scenario-commit 9f2b415 --prompt-profile baseline --runtime-policy risk-floor
agent-bench run-ollama-agent scenarios outputs/llm-defense-sweep --model qwen2.5:7b --scenario-commit 9f2b415 --prompt-profile setup-aware --runtime-policy risk-floor
```

Expected summary from the April 23, 2026 sweep:

| Prompt Profile | Runtime Policy | Passed | Total | Pass Rate | Unsafe Allows | Missed Allows |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `baseline` | `none` | 14 | 20 | 0.700 | 0 | 6 |
| `setup-aware` | `none` | 20 | 20 | 1.000 | 0 | 0 |
| `baseline` | `risk-floor` | 20 | 20 | 1.000 | 0 | 0 |
| `setup-aware` | `risk-floor` | 20 | 20 | 1.000 | 0 | 0 |

The report is in `docs/reports/2026-04-ollama-defense-sweep.md`.
