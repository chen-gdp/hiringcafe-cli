# PR 9.1 — Official MCP read transport

Release target: `0.2.0`; the service-supported search surface no longer includes the CLI's prior multi-page behavior.

## Problem

The CLI's historical anonymous reads use the site home route and `/api/job-description`. On 2026-10-11, requests from `chen-lappy` received HTTP 403 with Cloudflare's `cf-mitigated: challenge` header. This is an access-control challenge, not evidence of a bad Firebase session or a changed job ID. The supported fix must not imitate or reuse a browser challenge session.

## Verified API dependency

HiringCafe documents a public, unauthenticated, read-only MCP server at `https://hiringcafe.com/api/mcp`. The documentation says any MCP-compatible client can connect, identifies Streamable HTTP with JSON responses, and lists `initialize`, `tools/list`, `tools/call`, and `ping` methods. The CLI host successfully called `search_jobs` and `get_job_details` on 2026-10-11.

Official contract:

- `POST /api/mcp`, `Content-Type: application/json`, JSON-RPC 2.0.
- `tools/call` with `params.name="search_jobs"` and a `search` string; `limit` accepts 1–25 (default 10).
- `search_jobs` returns one job per company. No pagination argument or pagination contract is documented.
- `tools/call` with `params.name="get_job_details"` and a `job_id` from a result.
- Tool output is text in `result.content[].text`; live verification showed Markdown, not a structured job object.
- The connector reads public job data only. It cannot access saved jobs, profiles, resumes, application history, or perform writes.
- Requests are rate-limited by IP; HTTP 429 may include `Retry-After`. Heavy automated use is not supported.
- Job links include Claude attribution parameters. Preserve the URL exactly as returned.

Source: [HiringCafe Claude Connector documentation](https://hiringcafe.com/documentation/hiringcafe-claude-connector). HiringCafe also documents a separate ChatGPT MCP endpoint, but this PR intentionally uses only `/api/mcp` and the Claude connector's generic MCP-compatible interface.

## Scope

- Keep the user-facing `hiringcafe search`, `hiringcafe count`, and `hiringcafe job show` commands; use the first-party MCP endpoint internally.
- Normalize only fields observed in the Markdown contract. Preserve the version-1 envelope and existing `url` meaning (employer apply URL); use `null` when the MCP search response does not provide that value. Add `hiringCafeUrl` for the attributed HiringCafe page link.
- Use the documented default limit of 10; do not add a limit flag in this PR. Never request more than the documented maximum of 25.
- Accept only a plain query or raw search state containing `searchQuery`; reject filters and unsupported nonzero pages / multi-page requests before network access.
- Search mapping: title/link from each `### [title](url)` heading, company from the following strong-text line, location/workplace/employment/seniority/posted from matching bullet labels, and ID from the `Job ID` bullet. Unprovided `source`, `expired`, `companyCount`, and apply URL remain `null`.
- Detail mapping: title and `hiringCafeUrl` from the linked top-level heading; apply URL from `View & apply`; ID must match the requested ID; description is the nonempty `Full description` section.
- Human `job show` output displays the employer apply link when available, otherwise the attributed HiringCafe page URL.
- Remove email-address strings from MCP text before normalization, caching, or output, in line with the repository's data-handling rules.
- Parse the documented no-results message as zero. Treat missing counts, malformed job blocks, unknown job IDs, empty detail text, MCP error results, and malformed JSON as errors—not empty success.
- Keep existing TTL caching, but namespace MCP search and job-detail keys separately from prior SSR/raw responses.
- Update the opt-in live probe to exercise search and detail without printing the query result, job ID, description, or any contact data.
- Update the README, changelog, roadmap, and endpoint-dependent historical specs to make current limitations explicit.

## Out of scope

- Any saved-job, tracker, account, authentication, resume, alert, or write behavior. In particular, `saved-jobs save` still needs raw job hydration from the currently challenged `/api/job-description` route; this PR must not claim that command is repaired.
- Cloudflare bypass, challenge solving, browser cookie import/storage, user-agent spoofing, guessed endpoints, and automatic retries of MCP POSTs.
- MCP session establishment or tool discovery on every command if direct `tools/call` remains live-verified; avoid extra round trips.
- Pagination, search filters, facets, structured MCP response assumptions, and new runtime dependencies.

## Acceptance criteria

- Offline tests assert the exact JSON-RPC request method, tool names, argument shapes, and bounded response reads.
- Parser tests use fabricated/redacted Markdown and cover one result, multiple results, no results, malformed count, missing job ID, and detail output.
- Output and cache contain no email-address strings from external tool text.
- Search/count/detail outputs are valid JSON and never log response bodies, cookies, tokens, account IDs, emails, or private saved-job data.
- Search result URLs preserve all returned attribution parameters.
- `hiringCafeUrl` preserves the MCP attribution URL; the existing `url` field retains its employer-apply semantics.
- Human job-detail output includes a usable first-party page link when an employer apply link is unavailable.
- `--page` other than zero, `--pages` other than one, and unsupported raw filter state exit 2 before HTTP.
- 429 maps to the existing rate-limit exit 3 and MCP calls are not automatically retried.
- Existing saved-job operations and their API payloads are unchanged; known dependence of `saved-jobs save` on the challenged raw detail route is documented.
- The `LIVE=1` probe checks the supported MCP search and detail path and prints only success/failure labels.
- Full offline tests, Ruff, pre-commit, and package build pass on the project's supported Python matrix in CI.
