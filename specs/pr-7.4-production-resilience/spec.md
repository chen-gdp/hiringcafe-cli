# PR 7.4 — Production resilience follow-ups

## Scope

- Treat a corrupt local anonymous cache entry as a miss, delete it, and continue without fabricating data.
- Reject a saved-job document with a missing or unsupported `stage` before attempting marketplace deletion.
- Bound response reads from HiringCafe, Firebase, and Firestore at 8 MiB so malformed peers cannot exhaust memory.
- Convert anonymous HiringCafe transport failures into the documented exit-1 diagnostic path.
- Reject legacy saved-job documents without a usable old stage before stage mutations.
- Restrict configured HiringCafe base URLs to HTTPS so tokens cannot be redirected to arbitrary schemes.
- Pin CI actions to immutable commit SHAs and add least-privilege workflow permissions and a bounded job timeout.
- Correct the PR 7.1 roadmap status now that its implementing PR has merged.

## Out of scope

- Streamed parsers or spooled response files.
- Authenticated caching.
- Additional static-analysis jobs such as mypy, CodeQL, or Dependabot.

## Acceptance criteria

- A corrupt or wrong-schema cache entry is removed and the next read is a miss.
- A legacy saved-job document without a usable stage exits 6 and performs no mutation.
- A response larger than 8 MiB is rejected without an unbounded read.
- Offline anonymous HTTP calls exit 1 with a diagnostic rather than an uncaught traceback.
- Legacy stage documents exit 6 before marketplace or Firestore stage writes.
- Non-HTTPS configured base URLs are rejected with exit 1.
- CI uses SHA-pinned actions, `contents: read`, and a 10-minute job timeout.
- Tests, lint, formatting, pre-commit, and package build pass.

## Traceability

Source: `roadmap.md`, Phase 7, PR 7.4.
