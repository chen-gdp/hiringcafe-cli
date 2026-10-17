# PR 11.2 — Verified save hydration recovery

## Status and evidence gate

Investigating. The legacy GET /api/job-description returned 403 in the audit. Public MCP search/details work but return text, not the original saved-job object. Do not fabricate raw fields, copy browser cookies, bypass challenges, or use admin/internal routes.

## Scope after verification

- Capture a currently accessible first-party public route and its exact bounded response schema, including the job identity and fields needed by the website's saved-job reader.
- Require returned identity to match the requested job; sanitize user-tracking fields and retain authoritative owner/stage fields.
- Replace the old hydration dependency only after that route and saved-job rendering compatibility are verified. Preserve Firestore/history and marketplace synchronization.
- Record whether marketplace endpoints are currently usable; do not hide their failure or claim success after a partial write.
- Test malformed/missing/mismatched payloads and prove normal saving no longer uses the blocked endpoint.

## Acceptance

Spec and roadmap record sanitized current evidence before code uses the replacement. A temporary new public-job save, stage round-trip, website-compatible read, and cleanup verify the flow without changing pre-existing jobs. If upstream access prevents verification, report the exact blocker and keep this item incomplete.
