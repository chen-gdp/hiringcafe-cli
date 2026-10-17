# PR 11.1 — Saved-job Firestore recovery

## Verified API dependencies

- Existing owner query: Firestore `documents:runQuery` on `savedJobs`, live-verified.
- Single-document GET: `documents/savedJobs/<uid>_<objectID>`, live read verified in the capability audit; omitting the collection returned 403.
- Atomic field/history write: Google's documented [Commit](https://firebase.google.com/docs/firestore/reference/rest/v1/projects.databases.documents/commit) and [Write](https://firebase.google.com/docs/firestore/reference/rest/v1/Write) contracts, checked 2026-10-18. `updateTransforms` holds `appendMissingElements.values` containing typed Firestore values; it is not an `arrayValue` field member.
- Marketplace stage/removal contracts remain as captured in PR 3.4/3.5. Their current live availability must be checked before claiming full recovery; no automatic mutation retries.

## Scope

- Centralize collection-qualified, URL-encoded single-document paths; reject invalid document IDs before HTTP.
- Merge fields and append history atomically through a commit, preserving existing history and unrelated fields. Stage updates require the existing document's update time to avoid overwriting a concurrent edit; a conflict exits 6.
- Encode dateSaved/firstSavedAt and history timestamps as Firestore timestamps, matching captured web documents.
- Set isHidden on every stage transition. Keep marketplace synchronization order and partial-failure reporting explicit.
- Preserve public API function signatures where possible; share the write builder between save/update.
- Add transport-level tests that inspect real request construction, plus missing-document/conflict, history-preservation, hidden/unhidden, and no-retry tests.

## Boundaries and verification

This PR does not claim to replace blocked job hydration or repair inaccessible marketplace endpoints. Live checks may read existing saved jobs without printing private values. Verify writes only on a newly created, explicitly scoped test record when live end-to-end validation is possible; never alter an existing user's tracker record as a probe. Do not claim live mutation success from mocked tests.

## Acceptance

- GET and commit resources include savedJobs; transforms follow the documented schema and are in the same atomic write as stage fields.
- History is appended, not replaced; hidden state and timestamp types stay consistent.
- Concurrent-change/missing-document errors are conflicts, and authenticated requests never retry.
- Offline suite, Ruff, pre-commit, and supported Python CI pass; README/skill/roadmap distinguish implementation repair from live verification.

## Live substrate verification — 2026-10-18

A new, randomly identified hidden test record was create-only committed using an existing session, read, merge-updated with an appended history entry, and read again. The service preserved the original history and unrelated title field, returned timestampValue date data, and rejected a stale updateTime as a conflict. A version-guarded DELETE succeeded afterward. No pre-existing job was changed, and no authenticated operation retried.

An absent-document preflight GET returned a permission error, so creation used an atomic exists:false precondition rather than interpreting a denied read as absence. This does not prove website rendering, marketplace synchronization, or the full save/stage/remove commands; PR 11.2 remains open.
