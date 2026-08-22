# PR 8.3.1 — Release test stability

## Status

Ready for implementation.

## Motivation

The first post-release `main` run exposed a flaky cache failure test. The test relied on real elapsed time with a one-second TTL, so CI scheduling could expire the entry before asserting that a failed atomic replace preserves the previous cache value.

## API dependencies

None. This PR changes test timing only.

## Scope

- Freeze the cache clock in the failed-replace test.
- Use a non-expiring TTL within that frozen timeline.
- Preserve assertions that the old entry survives and no temporary file remains.

## Out of scope

- Cache behavior, schema, TTL defaults, production code, and release workflow changes.

## Acceptance criteria

- `uv run pytest` passes consistently regardless of runner scheduling.
- Formatting, linting, pre-commit, and package build remain unchanged and passing.

## Traceability

Source: `roadmap.md`, Phase 8, PR 8.3 release follow-up.
