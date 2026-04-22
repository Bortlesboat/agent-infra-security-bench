# Security Policy

## Scope

This repository contains public-safe benchmark fixtures, scoring code, and reproducibility docs for evaluating agent infrastructure boundaries. It should not contain secrets, private logs, exploit weaponization, private repository contents, wallet keys, project identifiers, or live payment credentials.

## Reporting Issues

Please open a private security advisory or contact the maintainer privately before publishing details if you find:

- a fixture that leaks real private data
- scoring behavior that rewards unsafe tool use
- instructions that could enable credential theft or unauthorized access
- a dependency or packaging issue that compromises users of the benchmark

Public issues are welcome for fixture ideas, docs bugs, scoring disagreements, and reproducibility gaps that do not expose sensitive details.

## Fixture Safety Rules

- Use synthetic names, repositories, wallets, payment proofs, and tokens.
- Preserve the shape of the failure without copying real secrets or production traces.
- Describe attacks at the control-boundary level; do not include copy-paste exploit chains against live systems.
- Keep model results separate from synthetic controls.

## Supported Versions

This project is pre-1.0. Security fixes apply to the current `main` branch unless a release branch is explicitly created later.
