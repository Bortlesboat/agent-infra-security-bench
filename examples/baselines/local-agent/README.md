# Local Agent Baseline Example

This example reproduces the first local agent trace baseline.

```powershell
agent-bench run-local-agent scenarios outputs/local-agent-baseline --scenario-commit f706176
```

Expected summary:

| Agent | Passed | Total | Pass Rate |
| --- | ---: | ---: | ---: |
| `boundary-heuristic-v1` | 20 | 20 | 1.000 |

The runner writes raw generic JSONL events first, adapts them into benchmark trace JSON, then scores those traces through the same suite runner used by other baselines.

This is a local heuristic agent baseline, not an LLM or TPU-backed model result.
