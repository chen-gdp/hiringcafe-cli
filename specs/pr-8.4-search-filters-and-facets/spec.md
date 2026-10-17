# PR 8.4 — Search filters and facets

## Status

Verified filters implemented by PR #54, checked 2026-10-18. The first verified CLI surface is location, workplace, employment type, and result limit. Other documented upstream filter families require their own verification before expansion. Facets remain independently blocked on their exact contract. The earlier SSR-only design is superseded.

## Verified contract and CLI mapping

The live `tools/list` schema declares no required fields and disallows additional properties. Official documentation confirms filters-only searches. The CLI keeps its existing `searchQuery` raw-state key for compatibility and translates it to MCP `search`.

| CLI input (search and count) | MCP argument | Validation |
|---|---|---|
| positional query / raw searchQuery | search | String; may be empty |
| --location TEXT | location | Nonempty trimmed string; city/state/country or remote, interpreted by HiringCafe, not an exclusive country boundary |
| --workplace VALUE (repeatable) | workplace_types | Nonempty array of Remote, Hybrid, Onsite |
| --employment-type VALUE (repeatable) | employment_types | Nonempty array of Full Time, Part Time, Contract, Internship, Temporary, Seasonal, Volunteer |
| --limit N | limit | CLI integer 1–25, default 10; upstream schema is number with this range stated in its description |

Arrays select alternatives within a family; separate filter families combine. Canonicalize arrays by deduplicating and sorting. No technology argument is present in the verified schema, so do not expose one.

### Input, output, and cache contract

- Existing positional query and `--raw-search-state` are mutually exclusive. Raw state must contain string searchQuery and may additionally contain location, workplace_types, employment_types, and limit. Reject every other key, malformed type, empty filter array/string, invalid enum, boolean/fractional/out-of-range limit before any cache or network access.
- Do not combine raw state with explicitly supplied filter/limit flags; reject ambiguity with exit 2. With flags, the query may be omitted for filters-only searches.
- Retain version-1 envelopes and the default unfiltered query representation. Echo canonical filters in query.searchState; omit the default limit from that state, include a non-default limit. result.pageSize is the requested limit, not an exact returned count. At most one job/company and no pagination remain upstream limits.
- Key anonymous search/count cache entries by a new transport schema name, configured base URL, and full canonical MCP arguments including effective limit. Equivalent raw/flag or reordered-array requests must share the same canonical envelope; semantically distinct arguments must not collide. Count continues sharing matching search entries.
- Preserve existing Python call signatures through optional trailing arguments/defaults and preserve TTL/bypass behavior. Existing Python calls search("", 0, raw_state) and count("", raw_state) use an empty-string sentinel and remain valid. The CLI must independently reject an explicitly supplied positional query, including an empty string, alongside raw state. No runtime dependency is added.

### Live evidence — 2026-10-18

Using search="software engineer": an unfiltered request returned 10/175634 matches. United States with limit 1 returned 1/75484, with explicit country metadata. Germany with limit 25 returned 25/7473; 12 explicitly named Germany, while other results described broader regions or worldwide eligibility. This does not establish exclusive country enforcement.

Remote returned 5/19446 and Onsite 5/107349; all five result workplace fields matched each selection. Contract returned 5/3979 and Full Time 5/162180; every employment field contained the requested value, including multi-valued postings. Combined Remote+Onsite and Full Time+Contract requests returned 5 results with matching alternative metadata and larger union counts. Germany+Remote+Full Time returned 5/1196; all five were remote and included Full Time, with locations including Germany and broader eligible regions. Counts are run-specific, not stable fixtures.

Implementation tests must inspect exact normalized MCP arguments for each accepted family and validate before cache/client construction. The opt-in probe must exercise structured arguments and detect contradictory workplace/employment metadata without printing job payloads or claiming strict location enforcement. Facet code remains prohibited until its separate gate clears.

### Implementation verification — 2026-10-18

- All 470 offline tests and all pre-commit checks passed. Transport tests inspect exact MCP requests, canonical envelopes/cache keys, supported enums and limits, and invalid-before-I/O behavior for search and count. Independent review identified the legacy Python empty-query/raw-state convention; the fix and two regressions preserve it without weakening CLI conflict checks.
- The opt-in live probe passed public search, details, and the combined Germany/Remote/Full Time request with matching type metadata.
- A CLI-level isolated-cache check passed the initial miss, equivalent raw-state cache hit, shared count entry, and a fresh limit-25 request. The fresh request returned 25 jobs, each Remote and including Full Time. Only aggregate counts and booleans were logged.
- These checks do not verify every geographic string or individual employment enum against live postings, facets, authentication, or saved-job mutations. Published v0.2.1 does not include these flags; installation guidance remains explicitly versioned.

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
