# PR 1.3 — `search` command

## API dependency

| Purpose | Request |
|---|---|
| One page of results | `GET https://hiringcafe.com/?searchState=<urlencoded JSON>&page=<n>` |

No other endpoint is allowed.

Historical verification result: usable when this PR shipped. On 2026-10-11, the CLI host received HTTP 403 with `cf-mitigated: challenge`. PR 9.1 replaces this route for the CLI search command with HiringCafe's documented MCP connector. The original route returned `private, no-store`; local TTL caching is governed by PR 5.1.

## Scope

- Add `hiringcafe search [query] --page <n> --json`.
- Reuse PR 1.1 client and PR 1.2 state builder.
- Emit JSON envelope version 1.
- Normalize each `ssrHits` item.
- Preserve source order.
- Emit `ssrTotalCount`, `ssrCompanyCount`, `ssrPageSize`, `ssrPage`, and `ssrIsLastPage`.
- Provide a simple human-readable fallback without `--json`.

## Normalized job mapping

| Output | Source |
|---|---|
| `id` | `objectID` |
| `title` | `job_information.title` |
| `company` | `enriched_company_data.name`, fallback `v5_processed_job_data.company_name` |
| `location` | `v5_processed_job_data.formatted_workplace_location` |
| `url` | `apply_url` |
| `source` | `source` |
| `workplaceType` | `v5_processed_job_data.workplace_type` |
| `commitment` | `v5_processed_job_data.commitment` |
| `publishedAt` | `v5_processed_job_data.estimated_publish_date` |
| `expired` | `is_expired` |

Never emit user-tracking arrays.

## Non-goals

- No multi-page fetch.
- No post-retrieval filtering.
- No raw-job output.
- No table formatting beyond a simple default.

## Acceptance criteria

- Successful JSON mode prints exactly one valid JSON document to stdout.
- Output count equals `ssrHits.length`; grouped/unpacked postings are not discarded.
- Every normalized job has nonempty `id`, or the command exits 1.
- Non-null `ssrError` exits 1.
- Invalid arguments exit 2.
- Network/API/parse failures exit 1 and produce no partial JSON on stdout.

## Traceability

Source: `roadmap.md`, Phase 1, PR 1.3.
