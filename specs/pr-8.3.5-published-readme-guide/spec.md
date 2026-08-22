# PR 8.3.5 — Published-package README guide

## Status

Ready for implementation.

## Context

The package is now published on PyPI, but the README still begins with direct CLI usage and does not provide a table of contents. New humans and agents need installation and orientation before usage details.

## API dependencies

- None. This is a documentation-only follow-up to PR 8.3.
- PyPI metadata is available at `https://pypi.org/project/hiringcafe-cli/`.

## Scope

- Add PyPI, Python, CI, and license badges.
- Add a README table of contents.
- Lead with persistent and one-shot PyPI installation.
- Consolidate the current command surface into a command reference.
- Preserve the agent JSON contract and refresh-token import path.
- Document authentication, saved-job, cache, local-data, exit-code, and development contracts accurately.
- Keep JSON/JSONL and password-input examples aligned with the implementation.
- Update PR 8.3.4 status and add this release-documentation follow-up to the roadmap.

## Out of scope

- CLI behavior changes, new endpoints, screenshots, marketing claims, and release workflow changes.

## Acceptance criteria

- All README commands match `hiringcafe --help` and subcommand help.
- The installation path works from PyPI rather than a local checkout.
- The table of contents links to every major README section.
- The unofficial-client warning and implementation limitations remain clear.
- Markdown/pre-commit checks pass.

## Traceability

Source: `roadmap.md`, Phase 8, PR 8.3 release follow-up.
