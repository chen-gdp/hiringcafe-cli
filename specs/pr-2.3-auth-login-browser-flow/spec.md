# PR 2.3 — Browser auth flow

## Status

Blocked. Do not implement yet.

OAuth popups are constrained by Firebase authorized-domain configuration. On 2026-10-18, the public Identity Toolkit project-config request succeeded and listed `localhost` and the existing project Firebase auth domain as authorized. This clears the domain-configuration uncertainty, not the provider/callback gate. Use PR 2.1 token import until the real flow is proven. This is also the operative specification for deferred roadmap item PR 8.7.

## API dependencies before implementation

Must all be verified from a real account:

1. The Firebase login route available to the CLI-hosted local page.
2. The selected provider’s Firebase popup/redirect flow.
3. The callback that exposes only a Firebase refresh token to the CLI.

No HiringCafe application REST endpoint is otherwise required.

Verification result: not usable or implementable yet; localhost/provider callback behavior remains unverified.

The candidate local page must open at `http://localhost:<random-port>` while listening only on IPv4 loopback; `127.0.0.1` is the bind address, not an assumed authorized Firebase browser origin. A user-completed provider sign-in and success/cancellation callback remain to be verified. Never change the project's authorized domains as part of this CLI work.

## Future scope

- Command: `hiringcafe auth login --browser`.
- Open a local login page using the public web Firebase config.
- Let the user authenticate in their normal browser.
- Receive only the Firebase refresh token over loopback; the ephemeral ID token must not cross into CLI storage.
- Store the token using PR 2.1.
- Bind the loopback server to `127.0.0.1`, use a random available port, and refuse non-loopback bindings.
- Generate a single-use 256-bit state value and use PKCE where the verified Firebase flow supports it.
- Enforce a bounded timeout and clean cancellation.
- Complete the loopback handshake exactly once; reject replay, unexpected origin/method, malformed status, or missing state.
- Print only non-sensitive progress and failure diagnostics.

## Permanent exclusions

- No headless provider login.
- No collection or transmission of provider passwords by the CLI.
- No reading credentials from the user’s existing browser profile.
- No OAuth client secret embedded in the CLI.
- No broad local-network listener.
- No token values in logs, diagnostics, tests, callbacks, or documentation.

## Acceptance gate

This spec becomes implementable only after a roadmap amendment records:

- exact login URL/domain behavior,
- provider success and failure behavior,
- callback validation behavior,
- sanitized request/response evidence with no tokens.

## Test and delivery requirements

- Fake the browser opener and loopback HTTP interaction; normal tests remain offline.
- Cover success, user cancellation, timeout, state mismatch, replay, and transport failure.
- Verify no partial session is written until the complete validated callback succeeds.
- Verify the session is stored through the existing owner-only atomic PR 2.1 mechanism.
- Keep runtime dependencies empty; use only the Python standard library.

## Traceability

Source: `roadmap.md`, Phase 2, PR 2.3.
