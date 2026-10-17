# PR 11.3 — Respect cache freshness overrides

## Dependencies

Local normalized anonymous cache only; no new endpoints. Search/count share MCP search data; job details use MCP detail data. Auth responses remain excluded.

## Scope

- Record writtenAt and expiresAt in a new cache schema so age is verifiable. Treat old/invalid schema as a miss, not a fresh entry.
- A read is valid only before its stored expiry and while its age is below the current requested TTL. A longer override never extends an existing entry's original expiry.
- Zero TTL always misses and avoids writing a reusable entry; negative TTL fails with CLI exit 2 before cache/network access on search/count/job show.
- Preserve --no-cache/HIRINGCAFE_NO_CACHE bypass, atomic owner-only writes, shared search/count entries, and purge behavior.
- Test shorter/longer/zero TTL, schema migration, clock rollback or malformed timestamps, CLI validation, and search/count/job integration.

## Acceptance

Existing fresh entries no longer ignore a shorter requested TTL; zero forces a fresh read. Offline tests, format/lint, pre-commit and CI pass. Update docs and skill when the fix lands.
