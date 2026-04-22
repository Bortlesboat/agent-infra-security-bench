# Agent Infrastructure Security Bench Baseline Report Template

## Summary

This report evaluates one agent, model, or defense policy against Agent Infrastructure Security Bench.

## Run Metadata

- Benchmark commit:
- Run manifest:
- Scenario count:
- Model or agent:
- Policy or defense:
- Trace adapter:
- Hardware:
- Date:

## Result Summary

- Total fixtures:
- Passed:
- Pass rate:
- Average score:

## Domain Breakdown

Paste the `agent-bench run --markdown` domain table here.

## Failed Fixtures

For each failed fixture:

- Fixture ID:
- Domain:
- Attack type:
- Unsafe actions:
- Missed required actions:
- Notes:

## Synthetic Controls

Synthetic control traces are included only to prove the scoring and reporting pipeline.

- Synthetic pass run:
- Synthetic fail run:

## Limitations

- This benchmark measures tool-boundary behavior, not general model safety.
- Scenario coverage is intentionally narrow.
- Public fixtures are synthetic and may not capture all production runtime details.
- A passing run should be treated as evidence for a specific policy/configuration, not a universal safety claim.

## Reproduction

```powershell
python -m pip install -e .[dev]
agent-bench run scenarios <trace-dir> --markdown outputs/results.md --csv outputs/results.csv
agent-bench write-manifest outputs/run-manifest.json --model <model> --policy <policy> --trace-adapter <adapter> --hardware <hardware> --scenario-commit <commit> --results outputs/results.csv
```
