# PR 2.3 — Browser auth flow

## Status

Production login blocked. A nonshipping verification harness is permitted under the procedure below; do not add the CLI flag or a production auth adapter until the acceptance gate clears.

OAuth popups are constrained by Firebase authorized-domain configuration. On 2026-10-18, the public Identity Toolkit project-config request succeeded and listed `localhost` and the existing project Firebase auth domain as authorized. This clears the domain-configuration uncertainty, not the provider/callback gate. Use PR 2.1 token import until the real flow is proven. This is also the operative specification for deferred roadmap item PR 8.7.

## API dependencies before implementation

Must all be verified from a real account:

1. The Firebase login route available to the CLI-hosted local page.
2. The selected provider’s Firebase popup/redirect flow.
3. The callback that exposes only a Firebase refresh token to the CLI.

No HiringCafe application REST endpoint is otherwise required.

Verification result: not usable or implementable yet; localhost/provider callback behavior remains unverified.

The candidate local page must open at `http://localhost:<random-port>` while listening only on IPv4 loopback; `127.0.0.1` is the bind address, not an assumed authorized Firebase browser origin. A user-completed provider sign-in and success/cancellation callback remain to be verified. Never change the project's authorized domains as part of this CLI work.

### Additional preflight evidence — 2026-10-18

- A public `accounts:createAuthUri` request using providerId=google.com, a localhost continueUri, and CODE_FLOW returned HTTP 200, an accounts.google.com authorization host, a localhost redirect host, and an opaque session. No account identifier was submitted and no returned authorization URI or session value was logged. URI generation is not proof that the provider accepts that redirect or that sign-in succeeds.
- The official [Firebase Google sign-in guide](https://firebase.google.com/docs/auth/web/google-signin) documents GoogleAuthProvider and signInWithPopup. Use the Firebase-hosted auth handler through the SDK, not an invented direct OAuth client/redirect configuration.
- The official [CDN setup](https://firebase.google.com/docs/web/alt-setup) currently pins browser modules at 13.0.0. Both app/auth module URLs returned HTTP 200 from this host. Loading them is not provider/callback evidence.
- [In-memory persistence](https://firebase.google.com/docs/auth/web/auth-state-persistence) avoids retaining the verification page's Firebase session in browser storage. The [User interface](https://firebase.google.com/docs/reference/js/auth.user) exposes refreshToken; its usual recommendation to prefer getIdToken is not permission to persist or transfer an ID token to the CLI.

### Nonshipping verification procedure

This procedure exists to obtain the missing live evidence, not to relax the production gate:

1. Keep the temporary harness outside the package and repository. Reuse the existing public Firebase config, FirebaseClient, and SessionStore; add no runtime dependency, provider secret, or shipped CLI command.
2. Serve a user-operated Google sign-in button from localhost with a pinned Firebase browser SDK and inMemoryPersistence. Do not automate provider interaction or inspect browser profiles, cookies, passwords, or token values.
3. Bind only 127.0.0.1 on an OS-assigned port. Validate exact Host and same-origin Origin, method/path, bounded JSON body, a single-use 256-bit state, allowed status/fields, and a fixed overall deadline. Suppress request/body logging and reject replay. The SDK owns provider protocol state; do not claim CLI-controlled PKCE unless separately verified.
4. Receive only a Firebase refresh token in a same-origin loopback POST body on success, never a URL/query/fragment. Error/cancellation callbacks contain no credential or arbitrary provider error text. Keep the page uncached, non-framable, and its Firebase persistence in memory.
5. Validate the received refresh token through FirebaseClient, store it only through SessionStore in an owner-only temporary directory, and verify auth status there. Do not replace the user's existing CLI session. Log only status/count/permission booleans and destroy the temporary session on exit.
6. Exercise malformed input, wrong Host/Origin/state/method/path, replay, cancellation, and timeout with synthetic data before a user-completed flow. A successful fake callback does not clear the live gate.
7. Record actual provider success/cancellation and the isolated-session verification before implementing production login. If user interaction is unavailable, leave the gate blocked and report the missing step.

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
- No real token values in logs, diagnostics, tests, URL callbacks, or documentation. The sole callback credential permitted is the refresh token in the validated same-origin loopback POST body described above.

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
