# PR 3.1 — Saved-job models

## API dependency

Data contract only:

| Purpose | Source |
|---|---|
| Saved job documents | Firestore collection `savedJobs` |
| Document ID | `${uid}_${objectID}` |

Verification result: usable. The collection, document ID, fields, stage order, timestamps, and history shape were verified from the signed-in tracker bundle.

Fields observed in the web bundle:

- `objectID`
- `owner`
- `dateSaved`
- `stage`
- `stageHistory`
- `isHidden`
- `counted_milestones`

Additional verified mutable/display fields:

- `firstSavedAt`
- `userNote`
- `journal`
- `tags`
- `nextAction`
- `docID` (added by the web client when reading Firestore)

## Precondition

Verified from the signed-in tracker bundle:

- Tracker stage order: `saved`, `applied`, `interviewing`, `offer`, `rejected`, `ghosted`, `hidden`.
- `saved`, `applied`, `interviewing`, `offer`, `rejected`, and `ghosted` are pipeline stages; `hidden` is separate.
- Firestore Timestamps are the storage representation.
- A history entry has shape `{stage, at}`; writes append through Firestore `arrayUnion`.

## Scope

- Define normalized saved-job models.
- Convert Firestore timestamps to ISO-8601 UTC.
- Validate `objectID` and `owner`.
- Validate stage against the captured list.
- Add one synthetic fixture only.

## Normalized mapping

| Output | Source |
|---|---|
| `id` | `objectID` |
| `savedAt` | `dateSaved` |
| `stage` | `stage` |
| `stageHistory` | `stageHistory` |
| `hidden` | `isHidden` |
| `documentId` | Firestore document ID (`docID` in the web client) |

Search metadata mapping is allowed only when source data is present; do not invent missing values.

## Non-goals

- No network call.
- No save/remove mutation.
- No cache/database.

## Acceptance criteria

- Every normalized field has a documented source.
- Missing `objectID` or `owner` is an error.
- Invalid stage is rejected.
- Fixture contains synthetic IDs, timestamps, and no personal data.

## Traceability

Source: `roadmap.md`, Phase 3, PR 3.1.
