# PR 6.2 — CI, Ruff, and pre-commit

## Scope

- Add Ruff as a development dependency.
- Configure formatting and lint rules compatible with the project’s 120-column PEP 8 contract.
- Add `.pre-commit-config.yaml` using Ruff hooks.
- Add GitHub Actions CI.

## Ruff configuration

- Format with 120-character lines.
- Lint with `E`, `F`, `I`, `B`, `UP`, and `S` rule families.
- Ignore noisy, non-actionable rules that conflict with the existing test contract.
- Exclude generated caches and build artifacts.

## Pre-commit contract

Run locally with:

```bash
uv run pre-commit run --all-files
```

Hooks:

- `ruff` lint/autofix
- `ruff-format`
- standard hygiene checks

## CI contract

GitHub Actions must run on pull requests and pushes to `main`:

```bash
uv sync --locked
uv run ruff format --check .
uv run ruff check .
uv run pytest -q
uv build
```

CI uses Python 3.12 and does not access live services or account credentials.

## Acceptance criteria

- `.pre-commit-config.yaml` exists and runs Ruff locally.
- CI workflow validates lock, formatting, linting, tests, and package build.
- Existing source passes Ruff after mechanical fixes only.
- Existing tests continue to pass.
- No runtime dependency is added.

## Traceability

Source: `roadmap.md`, Phase 6, PR 6.2.
