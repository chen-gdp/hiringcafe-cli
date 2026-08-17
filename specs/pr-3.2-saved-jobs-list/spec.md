# PR 3.2 — `saved-jobs list`

## API dependency

| Purpose | Source |
|---|---|
| Saved jobs | Firestore REST API (`https://firestore.googleapis.com/v1/projects/hiringcafe-ec4d6/databases/(default)/documents/savedJobs`) queried as the signed-in user with the Firebase ID token as bearer credential |

The exact web-app query is verified. `/api/boards/saved` is not a substitute: it is only known to return 401 anonymously and its response contract is unknown.

Verification result: Firestore REST is usable with a Firebase ID token; `/api/boards/saved` is not usable for this feature. Authenticated responses are never cached.

Verified web-app query:

```text
collection: savedJobs
where: owner == uid
where: stage == selected stage (optional)
orderBy: dateSaved, asc or desc by selected sort
limit: 20
cursor: startAfter the last document of the prior page
```

When no tab is selected, the web app filters `stage in [saved, applied, interviewing, offer, rejected, ghosted]` instead of comparing one stage.

## Scope

- Add `hiringcafe saved-jobs list --json`.
- Authenticate through the Phase 2 session.
- Query only the current user’s saved-job documents.
- Default to `dateSaved` descending and 20 documents per page.
- Normalize models through PR 3.1.
- Order by `dateSaved` descending, document ID ascending as tie-breaker.
- Handle auth and permission errors explicitly.

## Non-goals

- No board endpoints.
- No local cache.
- No mutation.
- No hydration through search unless a real capture proves it necessary.

## Acceptance criteria

- Valid credential returns normalized saved jobs.
- Missing credential exits 4.
- Rejected/expired credential exits 5.
- Firestore permission denial exits 1, not an empty list.
- Ordering is deterministic.
- No real UID, email, token, or personal job data is committed.

## Traceability

Source: `roadmap.md`, Phase 3, PR 3.2.
