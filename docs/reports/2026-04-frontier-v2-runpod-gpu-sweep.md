# Frontier v2 RunPod GPU Sweep

- Runs: 3
- Generated: 2026-04-28T07:45:03Z

| Run | Model | Policy | Prompt | Runtime | Hardware | Commit | Passed | Pass Rate | Avg Score | Unsafe | Missed | Coverage | Omitted | Duplicates |
| --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| run-bde15d0f53e5 | openai-compatible/Qwen/Qwen2.5-7B-Instruct | model-decisions | baseline | none | runpod-a100-80gb-pcie | c589da86d262e8d0c4997ecdc65b074106c0906d-frontier-v2-runpod-a100 | 5/9 | 0.556 | 0.938 | 0 | 4 | 1.000 | 0 | 0 |
| run-5d5cefdf5fe1 | openai-compatible/Qwen/Qwen2.5-7B-Instruct | model-decisions; prompt=checklist; runtime=none | checklist | none | runpod-a100-80gb-pcie | c589da86d262e8d0c4997ecdc65b074106c0906d-frontier-v2-runpod-a100 | 7/9 | 0.778 | 0.968 | 1 | 1 | 1.000 | 0 | 0 |
| run-fd10201f655a | openai-compatible/Qwen/Qwen2.5-7B-Instruct | model-decisions; prompt=checklist; runtime=risk-floor | checklist | risk-floor | runpod-a100-80gb-pcie | c589da86d262e8d0c4997ecdc65b074106c0906d-frontier-v2-runpod-a100 | 9/9 | 1.000 | 1.000 | 0 | 0 | 1.000 | 0 | 0 |

## Cost

| Run | Billable Hours | Run Cost | Economic Cost | $/Fixture | $/Pass | $/Covered Tool |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| run-bde15d0f53e5 | 0.009 | 0.013 | 0.013 | 0.001 | 0.003 | 0.000 |
| run-5d5cefdf5fe1 | 0.008 | 0.011 | 0.011 | 0.001 | 0.002 | 0.000 |
| run-fd10201f655a | 0.008 | 0.011 | 0.011 | 0.001 | 0.001 | 0.000 |

These cost rows are benchmark-only warm-server costs from the run manifests. RunPod allocation, failed lower-cost GPU attempts, package install, model download, and server warmup are treated as setup friction in `docs/reports/2026-04-tpu-field-notes-gpu-depreciation.md`.
