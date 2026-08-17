# PR 3.5 — `saved-jobs remove`

## API dependencies

| Purpose | Request |
|---|---|
| Read current stage | Firestore REST `GET .../documents/savedJobs/${uid}_${objectID}` |
| Delete marketplace list entry | `POST https://hiringcafe.com/api/removeJobFromList` |
| Delete document when captured app behavior requires | Firestore REST `DELETE .../documents/savedJobs/${uid}_${objectID}` |

Observed marketplace body:

```json
{
  "job_id": "<objectID>",
  "user_token": "<Firebase ID token>",
  "stage": "<current stage>",
  "should_delete": true
}
```

## Precondition

Verified web-app delete behavior:

- Read the saved document to obtain `objectID` and current `stage`.
- Call `POST /api/removeJobFromList` with `should_delete:true`.
- Require a successful HTTP response.
- Perform no additional client-side Firestore delete; the marketplace endpoint owns deletion.

Verification result: the marketplace endpoint is usable and no separate client-side Firestore delete exists in the web app. Keep removal uncached.

## Scope

- Add `hiringcafe saved-jobs remove <objectID> --yes`.
- Require confirmation interactively unless `--yes` is supplied.
- Read the current saved document.
- Call the marketplace removal endpoint with `should_delete: true`.
- Perform Firestore deletion only if captured web behavior does.
- Never mutate before confirmation.

## Non-goals

- No bulk remove.
- No hide-only operation.
- No automatic retry.

## Acceptance criteria

- Removed job no longer appears in `saved-jobs list`.
- Unknown saved job exits 6.
- Interactive refusal exits 2 without network mutation.
- Missing/rejected credentials exit 4/5.
- Marketplace or Firestore failure exits 1 and is not reported as complete success.
- No token or personal data appears in output.

## Traceability

Source: `roadmap.md`, Phase 3, PR 3.5.
