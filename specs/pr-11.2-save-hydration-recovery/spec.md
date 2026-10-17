# PR 11.2 — Verified save hydration recovery

## Status and evidence gate

Investigating. The legacy GET /api/job-description returned 403 in the audit. Public MCP search/details work but return text, not the original saved-job object. Do not fabricate raw fields, copy browser cookies, bypass challenges, or use admin/internal routes.

### Additional evidence — 2026-10-18

- The legacy hydration route, a public job page, and a build-qualified Next.js job-data request returned HTTP 403 with `cf-mitigated: challenge` from the CLI host. No challenge bypass or cookie reuse was attempted.
- The ordinary browser renders public job data. Its DOM-embedded job object contains raw `objectID`, source/board fields, job_information, v5_processed_job_data, and enriched_company_data. This is schema evidence, not an accessible CLI hydration transport.
- Public MCP search returns short public job IDs and attributed job-page URLs. A browser job object's raw `objectID` differs from its public URL slug ID; calling MCP detail with that raw ID returned a tool error. A public ID must not simply be substituted for a raw tracker ID.
- The ChatGPT connector advertises a normalized job/detail schema, not the captured raw tracker object. Reachable empty-body marketplace calls returned validation/server errors, which do not verify authenticated mutations.
- Replacement remains unverified: require both an accessible first-party transport and an authoritative public-to-raw identity mapping, followed by a new-record website roundtrip.

## Scope after verification

- Capture a currently accessible first-party public route and its exact bounded response schema, including the job identity and fields needed by the website's saved-job reader.
- Require returned identity to match the requested job; sanitize user-tracking fields and retain authoritative owner/stage fields.
- Replace the old hydration dependency only after that route and saved-job rendering compatibility are verified. Preserve Firestore/history and marketplace synchronization.
- Record whether marketplace endpoints are currently usable; do not hide their failure or claim success after a partial write.
- Test malformed/missing/mismatched payloads and prove normal saving no longer uses the blocked endpoint.

## Acceptance

Spec and roadmap record sanitized current evidence before code uses the replacement. A temporary new public-job save, stage round-trip, website-compatible read, and cleanup verify the flow without changing pre-existing jobs. If upstream access prevents verification, report the exact blocker and keep this item incomplete.
