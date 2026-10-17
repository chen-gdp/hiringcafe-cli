# PR 8.4 — Search filters and facets

## Status

Deferred. Updated 2026-10-18: official MCP filters are documented but not exposed by CLI v0.2.0. The earlier SSR-only design is superseded; verify each selected parameter before implementation. Facets remain independently blocked on their exact contract.

## API dependencies and evidence gate

HiringCafe's [official MCP documentation](https://hiringcafe.com/documentation/hiringcafe-claude-connector) describes structured search filters. Two independent evidence gates remain:

1. **Filters:** verify the documented `search_jobs` parameter schema, types, enums, and live behavior for each filter family proposed for CLI flags. Capture sanitized request/response evidence that the selected parameters are applied. The capability audit did not test individual filters.
2. **Facets:** capture the exact `/api/search-facets` request parameter(s), method, auth requirement, response schema, and a live successful response through the web app. The current anonymous probe only proves `400 {"error":"Invalid or missing facetType."}`.

A route discovered in the JavaScript bundle is not sufficient evidence. Do not infer names, enums, ranges, defaults, or response shapes.

## Scope after verification

- Define explicit filter flags and their mapping to verified MCP arguments before changing the current query-only `--raw-search-state` contract.
- Add one integration test per accepted filter showing the exact normalized MCP arguments.
- Reject unknown values, contradictory flags, and malformed input with exit 2 before HTTP.
- Preserve raw-search-state input precedence and document it exactly.
- Include the canonical full MCP arguments and base URL in the anonymous cache key; pagination is not part of the current contract.
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

- Every accepted flag maps to a verified MCP parameter and value.
- Invalid filter input exits 2 without network access.
- Filter application is reproducible against the live MCP tool during the opt-in probe.
- Cache entries distinguish every semantically different filter value.
- Facets are implemented only from a verified exact endpoint contract.
- No private user-tracking arrays are copied into normalized output.
- Offline unit tests, quality gates, and the opt-in live probe pass.

## Traceability

Source: `roadmap.md`, Phase 8, PR 8.4.
