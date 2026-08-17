# PR 2.3 — Browser auth flow

## Status

Blocked. Do not implement yet.

OAuth popups are constrained by Firebase authorized-domain configuration, and localhost behavior has not been verified. Use PR 2.1 token import until this route is proven.

## API dependencies before implementation

Must all be verified from a real account:

1. The Firebase login route available to the CLI-hosted local page.
2. The selected provider’s Firebase popup/redirect flow.
3. The callback that exposes only a Firebase refresh token to the CLI.

No HiringCafe application REST endpoint is otherwise required.

Verification result: not usable or implementable yet; localhost/provider callback behavior remains unverified.

## Future scope

- Open a local login page using the public web Firebase config.
- Let the user authenticate in their normal browser.
- Receive only the refresh token over loopback.
- Store the token using PR 2.1.
- Enforce a one-time state token and bounded timeout.

## Permanent exclusions

- No headless provider login.
- No collection or transmission of provider passwords by the CLI.
- No reading credentials from the user’s existing browser profile.

## Acceptance gate

This spec becomes implementable only after a roadmap amendment records:

- exact login URL/domain behavior,
- provider success and failure behavior,
- callback validation behavior,
- sanitized request/response evidence with no tokens.

## Traceability

Source: `roadmap.md`, Phase 2, PR 2.3.
