# PR 2.1 — Firebase session, token import, and email login

## API dependencies

| Purpose | Endpoint |
|---|---|
| Exchange refresh token for ID token | `POST https://securetoken.googleapis.com/v1/token?key=<web API key>` with `grant_type=refresh_token&refresh_token=<token>` |
| Email/password login | `POST https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=<web API key>` with `{email,password,returnSecureToken:true}` |

Required Firebase configuration from the web bundle:

- App name: `candidate-client`
- Project: `hiringcafe-ec4d6`
- Auth domain: `hiringcafe-ec4d6.firebaseapp.com`

Use the standard library for this request. The public Firebase web API key identifies the client; it is not a user credential and must not be printed.

Verification result: usable for refresh-token exchange. Responses send `no-cache, no-store, max-age=0, must-revalidate` and contain tokens; never cache them.

Verification result: `signInWithPassword` is usable and was verified live on 2026-08-17 with a real account. It returned HTTP 200, an ID token, and `expiresIn=3600`.

## Scope

- Store a Firebase refresh token, never a provider password.
- Add `hiringcafe auth login --email`.
- Read the password from hidden input, falling back to `HIRINGCAFE_PASSWORD` for automation.
- Exchange credentials once through Firebase `signInWithPassword`.
- Store the returned refresh token and discard the password.
- Read the token from stdin or `HIRINGCAFE_REFRESH_TOKEN`; reject visible argv input.
- Refresh ID tokens only in memory.
- Store session metadata in the platform user config directory.
- Create the file with owner-only permissions.
- Include a session format version.
- Delete the session on logout.

## Security boundaries

- Never prompt for or accept an OAuth provider password.
- Never log, cache, or persist the Firebase account password.
- Never log refresh or ID tokens.
- Never include tokens in errors or fixtures.
- Filesystem permissions are the only local-at-rest protection; document this limitation.

## Non-goals

- No OAuth login.
- No Firestore access.
- No saved-job operations.

## Acceptance criteria

- A valid refresh token obtains an ID token.
- Invalid refresh token is distinguishable from network failure.
- Session file denies group/other access.
- Cancelled import leaves no partial session file.
- Token values never appear in stdout, stderr, logs, tests, or fixtures.

## Traceability

Source: `roadmap.md`, Phase 2, PR 2.1.
