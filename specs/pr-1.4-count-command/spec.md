# PR 1.4 — `count` command

## API dependency

| Purpose | Request |
|---|---|
| Result total | `GET https://hiringcafe.com/?searchState=<urlencoded JSON>&page=0` |

The count is `props.pageProps.ssrTotalCount`. A separate count endpoint must not be used.

Historical verification result: usable when this PR shipped. On 2026-10-11, the CLI host received HTTP 403 with `cf-mitigated: challenge`; PR 9.1 replaces this route for count with HiringCafe's documented MCP search response. Dead or partially known count routes remain excluded.

## Scope

- Add `hiringcafe count [query]`.
- Add optional `--json`.
- Reuse the search-state builder and SSR client.
- Always request page 0.
- Default output is exactly one integer and newline.

## Non-goals

- No job normalization.
- No separate count request.
- No additional page fetch.

## Acceptance criteria

- Default mode prints one valid integer.
- JSON mode includes request state and integer count.
- Missing `ssrTotalCount` exits 1 rather than returning zero.
- Invalid state/page exits 2.
- No partial JSON is emitted on error.

## Traceability

Source: `roadmap.md`, Phase 1, PR 1.4.
