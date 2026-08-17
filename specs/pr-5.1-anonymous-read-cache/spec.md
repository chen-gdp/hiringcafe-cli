# PR 5.1 — Anonymous read cache

## API dependencies

| Cached response | Request | Verified cache behavior |
|---|---|---|
| Search/count envelope | `GET /?searchState=<urlencoded JSON>&page=<n>` | Usable contract, but `cache-control: private, no-store`. An explicit local TTL is allowed; HTTP/shared caching is not. |
| Job description | `GET /api/job-description?id=<objectID>` | Usable contract; observed `cache-control: public` plus ETag/age without a usable lifetime. An explicit local TTL is allowed. |

Verification result: both cached endpoints are usable, but neither advertises a trustworthy response lifetime. CLI-managed TTLs are required.

Never cache:

- Firebase token exchange or any response containing refresh/ID tokens.
- Firestore reads and writes.
- `/api/tracker/searchIndex`.
- Marketplace mutation endpoints.

## Scope

- Add a versioned, owner-only local TTL cache.
- Cache normalized output, not 1 MB SSR HTML.
- Key search/count by base URL, canonical `searchState`, and page.
- Key job detail by base URL and object ID.
- Add `--no-cache` to bypass reads and writes.
- Add `--cache-ttl <seconds>` for the current command.
- Add `hiringcafe cache purge`.
- Replace entries atomically.
- Report cache hit/miss on stderr only.

## Defaults

| Command family | TTL |
|---|---:|
| Search and count | 15 minutes |
| Job detail | 24 hours |

## Non-goals

- No conditional HTTP revalidation.
- No daemon or background refresh.
- No authenticated response cache.
- No cross-machine cache sharing.

## Acceptance criteria

- A repeated identical anonymous request can complete without HiringCafe HTTP traffic.
- Expired entries are refreshed and replaced.
- `--no-cache` bypasses both cache read and write.
- `cache purge` removes cache data and succeeds when already empty.
- Cache keys distinguish base URL, search state, page, and object ID.
- Corrupt cache data is an error, never fabricated output.
- No token, cookie, UID, email, or authenticated response is written.

## Traceability

Source: `roadmap.md`, Phase 5, PR 5.1.
