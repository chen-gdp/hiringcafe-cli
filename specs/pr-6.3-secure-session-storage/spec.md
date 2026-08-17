# PR 6.3 — Secure session storage

## Scope

- Close the temporary-session-file permission race.
- Ensure the configuration directory is owner-only when created by the CLI.
- Preserve atomic session replacement and the existing session format.

## Security contract

- Create the parent directory with mode `0700`.
- Create the temporary token file with mode `0600` at creation time, before secret data is written.
- Replace the final session atomically.
- Keep the final session mode `0600`.
- Never make an existing shared configuration root more permissive.

## Acceptance criteria

- A newly created config directory has mode `0700`.
- The temporary file is `0600` during the interval when it contains the refresh token.
- The final session remains `0600`.
- Atomic replacement behavior and session JSON format remain unchanged.
- Existing tests and Ruff checks pass.

## Traceability

Source: `roadmap.md`, Phase 6, PR 6.3.
