# PR 0.1 — Minimal CLI package

## API dependency

None. This PR must not make a network request and must not depend on a HiringCafe or Firebase endpoint.

Verification result: not applicable by design; no endpoint may be used.

## Scope

- Create the smallest installable Python 3.12+ package exposing `hiringcafe`.
- Add `pyproject.toml` with an executable entry point and no runtime dependencies.
- Implement `hiringcafe --help`.
- Implement `hiringcafe --version` using the package semantic version.
- Add one runnable smoke check.
- Document local installation and command execution in `README.md`.
- Document the roadmap exit-code contract in help.

## Non-goals

- No HTTP client.
- No auth.
- No search.
- No command framework, no third-party runtime dependency.

## Acceptance criteria

- A local package install/link can execute `hiringcafe --help` with exit code 0.
- `hiringcafe --version` prints exactly the package version.
- The smoke check executes without external services.
- No runtime dependency is added.
- No endpoint behavior is claimed in README.

## Traceability

Source: `roadmap.md`, Phase 0, PR 0.1.
