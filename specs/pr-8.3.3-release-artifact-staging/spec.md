# PR 8.3.3 — Release artifact staging

## Status

Ready for implementation.

## Incident

`v0.1.3` still failed before upload because checksum verification looked for distributions beside the moved manifest, while they remained under `dist/`. The publisher itself was no longer receiving the checksum file.

## API dependencies

- GitHub Actions artifact downloads preserve all uploaded release files.
- PyPI publication accepts a dedicated upload directory containing one sdist and one wheel.

## Scope

- Download the complete GitHub artifact into `release/`.
- Verify all checksums in that complete directory.
- Copy only the `.tar.gz` and `.whl` into a clean `dist/` for PyPI.
- Upload the GitHub release from the complete `release/` directory.
- Bump the immutable package version to `0.1.4`.

## Out of scope

- Reusing failed immutable tags, publishing TestPyPI, or changing package contents.

## Acceptance criteria

- Checksum verification sees the manifest and both distributions in one directory.
- PyPI sees exactly two valid distributions.
- GitHub receives the same two distributions plus the checksum manifest.
- Tests, lint, pre-commit, workflow structure checks, and package verification pass.

## Traceability

Source: `roadmap.md`, Phase 8, PR 8.3 release follow-up.
