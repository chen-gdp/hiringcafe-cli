# PR 7.3 — Python 3.11-3.14 support

## Scope

- Require Python `>=3.11`.
- Keep runtime dependencies empty.
- Replace Python-3.12-only standard-library use with Python-3.11-compatible equivalents.
- Add Python 3.11, 3.13, and 3.14 to CI beside 3.12.
- Update package metadata, linter target, documentation, and agent rules to the supported range.

## Out of scope

- Interpreter-specific distribution wheels.
- Compatibility dependencies.
- Python 3.10 or earlier.

## Acceptance criteria

- CI runs and passes on Python 3.11, 3.12, 3.13, and 3.14.
- `requires-python`, Ruff target-version, documentation, and source agree.
- Full tests, pre-commit checks, and package build pass.

## Traceability

Source: `roadmap.md`, Phase 7, PR 7.3.
