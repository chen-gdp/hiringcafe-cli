# PR 8.3.4 — Runtime package version sync

## Status

Ready for implementation.

## Incident

The installed `hiringcafe-cli==0.1.4` package reported `hiringcafe 0.1.0`. The runtime constant had drifted from package metadata, and the existing version test compared CLI output to that same constant.

## API dependencies

- `importlib.metadata.version("hiringcafe-cli")`, available in the supported Python 3.11-3.14 standard library.
- Installed package metadata exposed by the `uv_build` wheel and sdist.

## Scope

- Derive `hiringcafe_cli.__version__` from installed package metadata.
- Keep a safe fallback when the package is imported outside installed metadata context.
- Add a regression test comparing runtime version with `pyproject.toml`.
- Update PR 8.3.2 and 8.3.3 roadmap status to their merged outcomes.
- Bump the immutable package version to `0.1.5`.

## Out of scope

- Dynamic setuptools plugins, release automation redesign, semantic-version automation, and HiringCafe API changes.

## Acceptance criteria

- `hiringcafe --version` reports the installed package version.
- The regression test fails if runtime and project metadata drift.
- Tests, Ruff, pre-commit, package build, and release artifact verification pass.

## Traceability

Source: `roadmap.md`, Phase 8, PR 8.3 release follow-up.
