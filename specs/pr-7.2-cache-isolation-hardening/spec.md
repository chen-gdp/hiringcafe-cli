# PR 7.2 — Cache isolation and hardening

## Scope

- Key anonymous search and job-description caches by the active `WebClient.base_url`.
- Write cache entries through a private unpredictable temporary file.
- Force temporary-file mode `0600` before writing cache data.
- Flush and sync the file, atomically replace the destination, and remove the temporary file on failure.
- Preserve cache versioning, TTL behavior, corruption handling, and owner-only directories.

## Out of scope

- Conditional HTTP revalidation.
- Authenticated response caching.
- Background refresh or a daemon.
- A new on-disk cache format.

## Acceptance criteria

- Identical requests against different configured base URLs never share cache entries.
- No interval exists where a newly written cache file is group/world readable.
- Failed writes leave no temporary files and do not replace valid entries.
- Existing cache read, write, expiry, purge, and corruption tests pass.

## Traceability

Source: `roadmap.md`, Phase 7, PR 7.2.
