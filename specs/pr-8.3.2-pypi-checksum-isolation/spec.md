# PR 8.3.2 — PyPI checksum isolation

## Status

Ready for implementation.

## Incident

The `v0.1.2` release built and checksum-verified correctly, but publication rejected `dist/hiringcafe-cli.sha256` as an unknown distribution format. PyPI did not receive the package.

## API dependencies

- GitHub Actions artifact download and upload behavior.
- PyPI publication action behavior: its upload directory may contain only valid Python distributions.

## Scope

- Keep the checksum manifest in the GitHub artifact for release attachment.
- Before PyPI publication, move it outside the directory passed to the publisher.
- Verify the unchanged checksums after moving the manifest.
- Bump the immutable package version to `0.1.3`.

## Out of scope

- Reusing or deleting failed tags `v0.1.0`–`v0.1.2`.
- Separate GitHub and PyPI artifact downloads.
- TestPyPI rehearsal.

## Acceptance criteria

- The publisher upload directory contains exactly the sdist and wheel.
- The checksum manifest still verifies and remains attached to the GitHub release.
- Local workflow lint, tests, release artifact checks, and CI pass.

## Traceability

Source: `roadmap.md`, Phase 8, PR 8.3 release follow-up.
