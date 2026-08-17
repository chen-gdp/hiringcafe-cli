# PR 1.1 — HTTP and SSR client

## API dependency

| Purpose | Request |
|---|---|
| Search | `GET https://hiringcafe.com/?searchState=<urlencoded JSON>&page=<n>` |

This is the current SSR web route, not `/api/search-jobs`.

Verification result: usable and implemented as the anonymous search transport. The live response sends `cache-control: private, no-store`, so this PR performs no caching; explicit TTL caching is deferred to PR 5.1.

## Scope

- Own every HiringCafe web URL in one client module.
- Default base URL to `https://hiringcafe.com`; allow an environment override for tests.
- Send browser-like headers.
- Apply a bounded timeout.
- URL-encode `searchState` and `page`.
- Parse the `__NEXT_DATA__` script as JSON.
- Return `props.pageProps`.
- Validate required SSR properties.
- Throw typed errors carrying endpoint name and HTTP status.

## Required response properties

- `ssrHits`
- `ssrPage`
- `ssrTotalCount`
- `ssrPageSize`
- `ssrIsLastPage`

Optional but preserved when present:

- `ssrError`
- `ssrCompanyCount`
- `ssrTimings`
- `initialSearchState`

## Non-goals

- No cookie jar.
- No retry.
- No auth headers.
- No result normalization.

## Acceptance criteria

- A request for page 1 returns parsed page properties.
- Malformed or missing `__NEXT_DATA__` produces a parse error, never an empty successful result.
- Transport, HTTP, and parse failures are distinguishable.
- No command module constructs a HiringCafe URL.
- One offline test covers successful parsing and malformed HTML.

## Traceability

Source: `roadmap.md`, Phase 1, PR 1.1.
