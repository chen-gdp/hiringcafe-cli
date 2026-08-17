# PR 2.2 — `auth status`

## API dependency

| Purpose | Endpoint |
|---|---|
| Validate stored credential and refresh ID token | `POST https://securetoken.googleapis.com/v1/token?key=<web API key>` with `grant_type=refresh_token&refresh_token=<token>` |

No HiringCafe REST endpoint is required. `/api/tracker/searchIndex` is now verified as `POST {user_token}` → `{entries:[...]}`, but Firebase refresh is a lighter and sufficient credential check.

Verification result: usable. Firebase refresh distinguishes invalid credentials from transport failure; its response is never cacheable.

## Scope

- Add `hiringcafe auth status` and `hiringcafe auth status --json`.
- Detect whether a session file exists.
- Attempt ID-token refresh when a refresh token exists.
- Distinguish no credential, rejected/expired credential, and transport failure.
- Exclude the user ID and every token; emit only authentication state.

## Exit behavior

| State | Exit |
|---|---:|
| Credential usable | 0 |
| No session file | 4 |
| Refresh token rejected/expired | 5 |
| Network/transport failure | 1 |

## Non-goals

- No saved-job read.
- No automatic re-login.
- No browser flow.

## Acceptance criteria

- Valid credential exits 0.
- Missing credential exits 4.
- Firebase rejection exits 5.
- Network failure exits 1, not 5.
- JSON output excludes refresh and ID tokens.

## Traceability

Source: `roadmap.md`, Phase 2, PR 2.2.
