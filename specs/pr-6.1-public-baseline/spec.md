# PR 6.1 — Public repository baseline

## Scope

- Change repository-facing documentation from private draft status to a public, unofficial CLI README.
- Add the MIT license and project metadata required for distribution.
- Add a security policy and changelog.
- Keep the existing endpoint contracts, commands, output, and exit codes unchanged.

## Public documentation requirements

- State clearly that the project is unofficial and not affiliated with Hiring Cafe.
- Show installation from Git with `uv tool install`.
- Document installation, authentication, search/count/job commands, saved-job commands, cache controls, retries, and exit codes.
- Warn that upstream APIs may change and that users must use their own accounts responsibly.
- Document credential storage and cache locations.

## Package metadata

- Add an SPDX license expression and MIT classifier.
- Add project homepage, repository, issues, and changelog URLs.
- Keep runtime dependencies empty.

## Security policy

- Publish responsible-disclosure instructions.
- Define credential handling expectations.
- Explicitly exclude committed refresh tokens, ID tokens, cookies, passwords, real UIDs, emails, and private saved-job data from valid reports.

## Acceptance criteria

- README no longer describes the project as private or as a draft PR stack.
- Public users can install and run the CLI using documented commands.
- License, security, and changelog files exist.
- Package metadata resolves without adding runtime dependencies.
- Existing tests pass unchanged.

## Traceability

Source: `roadmap.md`, Phase 6, PR 6.1.
