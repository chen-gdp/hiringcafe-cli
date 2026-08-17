# PR 4.1 — Multi-page search

## API dependency

| Purpose | Request |
|---|---|
| Each page | `GET https://hiringcafe.com/?searchState=<urlencoded JSON>&page=<n>` |

No parallel endpoint or total-count endpoint is allowed.

Verification result: usable. Pages 0–2 were verified while preserving the same search state; stop conditions use `ssrIsLastPage`.

## Scope

- Add `--pages <count>` to search.
- Fetch pages sequentially.
- Add `--jsonl` output.
- Stop at requested count or `ssrIsLastPage`.
- Preserve `ssrHits` source order.

## Non-goals

- No concurrent requests.
- No resume state.
- No result deduplication unless object IDs duplicate within returned pages; duplicates must then be reported, not silently changed.

## Acceptance criteria

- No page beyond the requested count is fetched.
- `ssrIsLastPage` stops iteration early.
- Each JSONL line is independently valid JSON.
- Ordering is deterministic.
- Rate-limit response exits 3.
- Any page failure emits no partial final JSON document in non-JSONL mode.

## Traceability

Source: `roadmap.md`, Phase 4, PR 4.1.
