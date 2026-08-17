# PR 6.3 — Secure session storage

## Scope

- Close the temporary-session-file permission race.
- Ensure the configuration directory is owner-only when created by the CLI.
- Preserve atomic session replacement and the existing session format.

## Security contract

- Create the parent directory with mode `0700`.
- Create a private, unpredictable temporary token file in the same directory, then force mode `0600` before writing the secret.
- Flush and sync the token to disk before atomic replacement.
- Replace the final session atomically.
- Keep the final session mode `0600`.
- Remove the temporary file on write failure.
- Never make an existing shared configuration root more permissive.

## Acceptance criteria

- A newly created config directory has mode `0700`.
- The temporary file is private and `0600` while it contains the refresh token.
- The final session remains `0600`.
- Atomic replacement behavior and session JSON format remain unchanged.
- A failed save does not leave a token-bearing temporary file behind.
- Existing tests and Ruff checks pass.

## Traceability

Source: `roadmap.md`, Phase 6, PR 6.3.
