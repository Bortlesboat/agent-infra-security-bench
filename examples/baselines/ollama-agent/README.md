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
