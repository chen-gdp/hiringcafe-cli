# PR 8.4 — Search filters and facets

## Status

Blocked on verified upstream contracts. Spec prepared; do not implement until the evidence gate below passes.

## API dependencies and evidence gate

HiringCafe has no official public API contract. Two independent blockers must be cleared:

1. **Filters:** capture a complete working `searchState` from the signed-out or signed-in web search UI for each filter family proposed for CLI flags. The captured state must reproduce a narrower result set when sent through the verified SSR search route.
2. **Facets:** capture the exact `/api/search-facets` request parameter(s), method, auth requirement, response schema, and a live successful response through the web app. The current anonymous probe only proves `400 {"error":"Invalid or missing facetType."}`.

A route discovered in the JavaScript bundle is not sufficient evidence. Do not infer names, enums, ranges, defaults, or response shapes.

## Scope after verification

- Extend `--raw-search-state` behavior only with explicit filter flags whose values are represented by the captured contract.
- Add one integration test per accepted filter showing the exact normalized `searchState`.
- Reject unknown values, contradictory flags, and malformed input with exit 2 before HTTP.
- Preserve raw-search-state input precedence and document it exactly.
- Include the canonical full search state, base URL, and page in the anonymous cache key.
- Add `hiringcafe facets` only if the exact facet endpoint contract is verified.
- Return facet output in a versioned JSON envelope and never emit user-tracking arrays.
- Update the live endpoint probe for each newly verified route without storing personal data.
- Update README and roadmap with the verified request/response contract.

## Out of scope

- Client-side filtering after retrieval.
- AI-search endpoints.
- Synonym, fuzzy-match, or natural-language parsing.
- New runtime dependencies.
- Facet caching unless response size and volatility are measured.
- Filters whose contract cannot be captured and reproduced.

## Acceptance criteria

- Every accepted flag maps to a value observed in a working captured `searchState`.
- Invalid filter input exits 2 without network access.
- Search result narrowing is reproducible against the live SSR route during the opt-in probe.
- Cache entries distinguish every semantically different filter value.
- Facets are implemented only from a verified exact endpoint contract.
- No private user-tracking arrays are copied into normalized output.
- Offline unit tests, quality gates, and the opt-in live probe pass.

## Traceability

Source: `roadmap.md`, Phase 8, PR 8.4.
