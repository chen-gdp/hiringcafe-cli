# PR 3.4 — `saved-jobs stage`

## API dependencies

| Purpose | Request |
|---|---|
| Read current document | Firestore REST `GET .../documents/savedJobs/${uid}_${objectID}` |
| Update stage/history | Firestore REST `PATCH .../documents/savedJobs/${uid}_${objectID}` |
| Marketplace stage sync | `POST https://hiringcafe.com/api/updateMarketplaceJobStageForUser` |
| Old-list removal when applicable | `POST https://hiringcafe.com/api/removeJobFromList` |

Observed bodies:

```json
{
  "job_id": "<objectID>",
  "user_token": "<Firebase ID token>",
  "stage": "<new stage>"
}
```

```json
{
  "job_id": "<objectID>",
  "user_token": "<Firebase ID token>",
  "stage": "<old stage>",
  "should_delete": false
}
```

Verification result: all listed dependencies are usable. The marketplace call precedes the Firestore update, and old-list cleanup applies only to `saved`, `applied`, or `hidden`.

## Precondition

Verified transition behavior:

1. Call marketplace stage sync with the new stage.
2. Update Firestore `stage`, `dateSaved`, and append `{stage, at}` through `stageHistory` `arrayUnion`.
3. Set `firstSavedAt` to the prior `dateSaved`/current timestamp only if it was previously absent.
4. If the old stage is `saved`, `applied`, or `hidden` and differs from the new stage, call `removeJobFromList` with `should_delete:false` for that old stage.

## Scope

- Add `hiringcafe saved-jobs stage <objectID> --stage <stage>`.
- Validate the new stage.
- Require an existing saved document.
- Update Firestore stage/history exactly as the web app does.
- Call marketplace stage update.
- Call old-list removal only for old stages where the web app does so.

## Non-goals

- No notes.
- No bulk updates.
- No automatic retry.

## Acceptance criteria

- Unknown saved job exits 6.
- Invalid stage exits 2.
- Missing/rejected credentials exit 4/5.
- Transition result matches the web app for the same state.
- Marketplace/removal failures are visible.
- No token or personal data is logged.

## Traceability

Source: `roadmap.md`, Phase 3, PR 3.4.
