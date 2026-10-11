# PR 0.2 — Endpoint regression probe

## API dependencies

Only anonymous endpoints already verified by the roadmap:

| Purpose | Request |
|---|---|
| Search pages 0 and 1 | `GET https://hiringcafe.com/?searchState=<urlencoded JSON>&page=<n>` |
| Job description | `GET https://hiringcafe.com/api/job-description?id=<objectID>` |

The job-description request must use an `objectID` returned by the page-0 search response.

Historical verification result: both endpoints worked when this PR shipped. On 2026-10-11, the CLI host received Cloudflare challenge responses for both routes. PR 9.1 replaces the live probe's read path with HiringCafe's documented MCP connector; this historical spec remains the original acceptance record.

## Scope

- Add one offline parser test using a minimized `__NEXT_DATA__` fixture.
- Add one opt-in live probe enabled only by `LIVE=1`.
- Probe search pages 0 and 1.
- Probe one job description using the first page-0 hit.
- Print only status, required-key presence, and one object ID.
- Update the roadmap if live behavior differs.

## Non-goals

- No authenticated requests.
- No rate-limit stress testing.
- No fixture recording of full live responses.
- No retry implementation.

## Acceptance criteria

- Offline test runs in the normal test command.
- Live probe is skipped unless explicitly enabled.
- Missing or malformed `__NEXT_DATA__`, `ssrHits`, `ssrTotalCount`, `ssrPage`, or `ssrIsLastPage` fails the probe.
- Page 1 retains the page-0 query in its response metadata or the probe fails.
- Job-description response contains a `job` object.
- No tokens, cookies, user IDs, emails, or personal data are printed or committed.

## Traceability

Source: `roadmap.md`, Phase 0, PR 0.2.
