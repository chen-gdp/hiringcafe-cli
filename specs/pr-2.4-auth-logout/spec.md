# PR 2.4 — `auth logout`

## API dependency

None required.

Firebase client sign-out may be called only if the selected local auth implementation requires it; remote service availability must not determine whether local credential deletion succeeds.

Verification result: usable as a local-only operation; no remote endpoint is required.

## Scope

- Add `hiringcafe auth logout`.
- Remove the local session file created by PR 2.1.
- Clear in-memory auth state.
- Succeed when no session exists.

## Non-goals

- No saved-job deletion.
- No account deletion.
- No clearing the user’s browser sessions.

## Acceptance criteria

- Existing session file is removed.
- Missing session file still exits 0.
- Failure to remove an existing file exits 1.
- Logout output contains no token values.

## Traceability

Source: `roadmap.md`, Phase 2, PR 2.4.
