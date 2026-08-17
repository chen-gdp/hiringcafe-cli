# PR 1.2 — Search state contract

## API dependency

Consumes the same SSR contract as PR 1.1:

`GET /?searchState=<urlencoded JSON>&page=<n>`

This PR is pure request-state construction and performs no network call.

Verification result: `searchQuery` and URL `page` were verified live; richer state fields remain unusable until captured.

## Scope

- Build `{"searchQuery":"..."}` from positional query text.
- Accept complete JSON through `--raw-search-state`.
- Accept `--page` as a nonnegative integer.
- Preserve raw object keys and value types.
- Reject malformed JSON and invalid page values with exit code 2.

## Verified state fields

- `searchQuery`

The `page` value is a URL query parameter, not a field inside `searchState`.

## Explicitly unsupported

- Location.
- Workplace type.
- Commitment.
- Date filters.
- Salary.
- Facets.
- Page-size override.

These may exist in richer server state, but their schemas were not captured and must not be guessed.

## Acceptance criteria

- Query mode produces a JSON object with only `searchQuery`.
- Raw mode preserves the supplied object without transformation.
- Generated URLs use correct percent-encoding.
- Invalid JSON fails before any network operation.
- Invalid page values exit 2.
- Tests cover query mode, raw mode, malformed JSON, and invalid page.

## Traceability

Source: `roadmap.md`, Phase 1, PR 1.2.
