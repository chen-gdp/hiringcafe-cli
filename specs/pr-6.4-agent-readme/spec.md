# PR 6.4 — Agent-focused README

## Scope

- Rework the public README around agent installation and first useful command.
- Add machine-oriented command examples and automation safety guarantees.
- Keep the unofficial-client warning, authentication behavior, local-data locations, exit codes, and development contract accurate.

## README contract

- Lead with a concrete job-search command and the CLI’s agent value.
- Provide a “For agents” install-and-verify path using `uv tool install`.
- Show JSON/JSONL parsing patterns and noninteractive refresh-token import.
- Document stdout/stderr separation and retry/cache/auth safety boundaries.
- Keep a separate human-oriented quick start.
- Preserve truthful beta and deferred-OAuth status.

## Out of scope

- New CLI behavior.
- Website copy, screenshots, or release assets.
- Changing authentication or storage formats.

## Acceptance criteria

- README commands match the implemented CLI surface.
- The first install path works for an agent with Python 3.12+ and uv.
- Security, cache, retry, local-data, and exit-code statements remain accurate.
- Markdown/pre-commit checks pass.

## Traceability

Source: `roadmap.md`, Phase 6, PR 6.4.
