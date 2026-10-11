# PR 1.5 — `job show` command

## API dependency

| Purpose | Request |
|---|---|
| Job description | `GET https://hiringcafe.com/api/job-description?id=<objectID>` |

Verified response shape begins with `{"job":{"job_information":{"description":"..."}}}`.

Historical verification result: usable for anonymous detail reads when this PR shipped. On 2026-10-11, the CLI host received HTTP 403 with `cf-mitigated: challenge`; PR 9.1 replaces `job show` reads with HiringCafe's documented MCP connector. The original response's ETag had no usable lifetime; local TTL caching is governed by PR 5.1.

## Scope

- Add `hiringcafe job show <objectID> --json`.
- Validate nonempty object ID.
- Parse the JSON response.
- Require a nonempty response object at `job`.
- Return normalized description and safe job metadata.
- Normalize whitespace only; preserve description HTML/content.
- Provide a human-readable fallback.

## Non-goals

- No HTML-to-text conversion.
- No caching.
- No search join.
- No user-tracking arrays.

## Acceptance criteria

- Missing/empty object ID exits 2.
- HTTP 400/404 and malformed JSON exit 1.
- Successful JSON mode emits one valid JSON document.
- Empty or missing `job` exits 1.
- User IDs, emails, cookies, and bearer tokens never appear in output.

## Traceability

Source: `roadmap.md`, Phase 1, PR 1.5.
