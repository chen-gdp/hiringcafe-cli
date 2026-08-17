# PR 1.5 — `job show` command

## API dependency

| Purpose | Request |
|---|---|
| Job description | `GET https://hiringcafe.com/api/job-description?id=<objectID>` |

Verified response shape begins with `{"job":{"job_information":{"description":"..."}}}`.

Verification result: usable for anonymous detail reads. One live response exposed `cache-control: public` and an ETag but no usable lifetime; caching is deferred to PR 5.1.

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
