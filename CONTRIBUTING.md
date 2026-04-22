# Contributing

Thanks for helping make agent infrastructure safer and easier to evaluate.

## Good First Contributions

- add a public-safe benchmark fixture
- improve fixture wording or success criteria
- add a trace adapter for a local agent runner
- improve result reporting or reproducibility metadata
- tighten docs around limitations and public claims

## Fixture Requirements

Every scenario must be synthetic and safe to publish. A fixture should include:

- a realistic user goal
- untrusted content that creates the boundary pressure
- tools with clear risk labels
- expected actions with explicit `allow` or `block` decisions
- success criteria that a reviewer can understand without running code

Before proposing a fixture, run:

```powershell
python -m pytest
```

## Result Claims

Do not claim a model, agent, policy, or defense is safe based only on synthetic traces. Any public result should include:

- benchmark commit
- run manifest
- model or agent version
- policy/defense configuration
- trace adapter
- scenario count
- hardware and runtime notes
- known limitations

## Development

```powershell
python -m pip install -e .[dev]
python -m pytest
```

Keep changes small, test behavior first when touching Python code, and avoid unrelated refactors.
