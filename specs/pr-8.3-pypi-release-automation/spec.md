# PR 8.3 — PyPI release automation

## Status

Implemented and merged. The `pypi` GitHub environment and registered trusted publisher are configured; publishing begins when the first matching immutable `v*` tag is pushed.

## Release channel decision

Publish `hiringcafe-cli` to PyPI with GitHub Actions using PyPI Trusted Publishing. Do not store a PyPI token in GitHub secrets.

## API dependencies

No HiringCafe API dependency. Release behavior depends only on:

- GitHub tag events matching `v*`.
- PyPI Trusted Publishing for the repository and workflow.
- The existing `uv build` backend.

## Scope

- Add a release workflow triggered only by `v*` tags.
- Build the sdist and wheel with `uv build`.
- Verify package metadata and that both artifacts contain no credentials or local files.
- Publish to `https://upload.pypi.org/legacy/` through Trusted Publishing.
- Attach the same immutable artifacts and checksums to the matching GitHub release.
- Pin every workflow action to an immutable commit SHA.
- Grant only the permissions required for publication, including OIDC publication.
- Document the repository owner's one-time setup:
  - create a protected GitHub environment for PyPI publication,
  - configure the PyPI trusted publisher for this repository and workflow.
- Add a manual release runbook covering version bump, changelog, tag, verification, and rollback/notation if publication partially fails.
- Update README installation to prefer `uv tool install hiringcafe-cli` / `pipx install hiringcafe-cli`, with Git installation retained for development.

## Out of scope

- Publishing to TestPyPI unless the first production publication fails and a rehearsal becomes necessary.
- Auto-generated release notes.
- Semantic-version automation or enforced release cadence.
- macOS or Windows platform-specific wheels.
- HiringCafe feature changes.

## Acceptance criteria

- Pushing a non-release commit never publishes.
- A tag build produces the same sdist and wheel locally and in CI.
- The workflow publishes exactly once per immutable tag.
- PyPI installation works on Python 3.11–3.14 with no runtime dependencies.
- The GitHub release and PyPI project point to the same source tag.
- The workflow contains no PyPI token, uses least-privilege permissions, and pins actions by SHA.
- The changelog and README accurately document the released install path.
- Normal tests, lint, formatting, pre-commit, and package checks pass.

## Traceability

Source: `roadmap.md`, Phase 8, PR 8.3.
