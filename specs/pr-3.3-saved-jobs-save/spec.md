# PR 3.3 — `saved-jobs save`

## API dependencies

| Purpose | Request |
|---|---|
| Hydrate job when needed | `GET https://hiringcafe.com/api/job-description?id=<objectID>` |
| Primary write | Firestore REST `PATCH/CREATE` against `projects/hiringcafe-ec4d6/databases/(default)/documents/savedJobs/${uid}_${objectID}` with an update mask / merge equivalent |
| Marketplace sync | `POST https://hiringcafe.com/api/updateMarketplaceJobStageForUser` |

Marketplace JSON body observed in the web bundle:

```json
{
  "job_id": "<objectID>",
  "user_token": "<Firebase ID token>",
  "stage": "<stage>"
}
```

`user_token` is a Firebase ID token, not a refresh token.

Verification result: all listed dependencies are usable and their order is verified. The Firestore REST equivalent must reproduce the web client's merge write.

Current status amendment (2026-10-11): the raw job hydration route now returns a Cloudflare challenge from the CLI host. The official MCP read connector does not expose the raw job object or support writes. Therefore `saved-jobs save` may fail before its Firestore write until a supported raw-job hydration path is verified; PR 9.1 does not change or claim to repair this flow.

## Precondition

Verified web-app write behavior:

- Hydrate a missing description through `GET /api/job-description` before writing.
- Write document `${uid}_${objectID}` with Firestore merge enabled.
- Set `objectID`, `isHidden = (stage == "hidden")`, `owner = uid`, `dateSaved = now`, and `stage`.
- Append `{stage, at}` to `stageHistory` using `arrayUnion`.
- Initialize `counted_milestones` to an empty object.
- Copy the hydrated job fields, but remove private user-tracking arrays before writing.
- Skip marketplace sync for imported documents when `source == "import"`.

## Scope

- Add `hiringcafe saved-jobs save <objectID> --stage <stage>`.
- Validate object ID and stage before network use.
- Refresh an ID token before mutation.
- Fetch job detail only if required data is unavailable.
- Perform the Firestore merge write using the verified field shape.
- Call marketplace sync after the Firestore write.
- Preserve existing stage history according to captured behavior.

## Non-goals

- No bulk save.
- No retry of either mutation.
- No silent success when marketplace sync fails.

## Acceptance criteria

- First save and repeated save are idempotent at document level.
- Invalid ID/stage exits 2.
- Missing credential exits 4.
- Invalid/expired credential exits 5.
- Firestore failure exits 1 before marketplace sync.
- Marketplace failure is reported as partial failure, not silent full success.
- No token appears in output or logs.

## Traceability

Source: `roadmap.md`, Phase 3, PR 3.3.
