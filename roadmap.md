# HiringCafe CLI Roadmap

## Status

**Active — official read-only MCP behavior is documented and live-verified; legacy anonymous web routes are currently Cloudflare-challenged from CLI clients.**

Verified against the live site on 2026-10-11 (Asia/Jakarta) and HiringCafe's current integration documentation. The public MCP connector is an official read-only integration; the older SSR and job-description routes below were historically verified but are not currently usable from the CLI's network path.

### Current capability audit — CLI v0.2.0

Recorded 2026-10-18 from the 2026-10-17 audit. These findings supersede older working-feature claims below; `Merged` records implementation history, not current operational success.

| Capability | Evidence and current limit |
|---|---|
| Public search/count/details, JSON/JSONL | Live reads succeeded; CLI returns at most 10 jobs, one per company, without pagination. No login or separate MCP plugin is required. |
| Existing-session refresh/status and saved-job listing | Live checks succeeded. Listing returns at most 20 jobs; stage filtering exists, but each stage was not separately live-tested. |
| Auth import/logout; email/password login | Import/logout pass offline tests; fresh email login was not live-tested. Browser OAuth is unimplemented. |
| Saved-job save/stage/remove | Broken or blocked. Hydration returned HTTP 403. Document GET/PATCH paths omit `savedJobs/`; the correct collection path retrieved an existing document while the CLI path returned 403. Save/stage encode history transforms incorrectly, and stage changes omit `isHidden`. No live mutations were attempted. |
| Cache and purge | Cache hits and isolated purge succeeded. Offline reproduction showed `--cache-ttl 0` still reads an existing valid entry; use `--no-cache` for fresh data. |
| DNS and retries | The reported DNS failure did not reproduce. Its cause remains unresolved; MCP requests do not automatically retry. OAuth and cache bypass do not repair DNS. |
| Structured filters/facets | Not exposed by the CLI. Upstream MCP documents structured filters; this is not proof that each filter has been live-verified. Facet discovery remains separately unverified. |

The audit's 105 passing offline tests and pre-commit checks do not establish that account writes work: their mocks skip the defective request construction. Follow-up implementation PRs must add specs and verify the relevant transport contracts before claiming recovery. See [PR 10.1](specs/pr-10.1-shared-agent-skill/spec.md) for this documentation correction.

This file is the project source of truth. Every PR must reference one PR spec below. If implementation proves a spec wrong, update this roadmap in the same PR before changing code.

## Implementation status

Statuses are the audit source for agents and contributors. Update this table in the same PR that changes a PR's state.

| PR | Status | Notes |
|---|---|---|
| 0.1 Minimal CLI package | Merged | Implemented in PR #1. |
| 0.2 Live endpoint regression probe | Merged | Implemented in PR #3. |
| 1.1 HTTP and SSR client | Merged | Implemented in PR #5. |
| 1.2 Search state contract | Merged | Implemented in PR #7. |
| 1.3 `search` command | Merged | Implemented in PR #9. |
| 1.4 `count` command | Merged | Implemented in PR #10. |
| 1.5 `job show` command | Merged | Implemented in PR #11. |
| 2.1 Firebase session, import, and email login | Merged | Implemented in PR #12. |
| 2.2 `auth status` | Merged | Implemented in PR #12. |
| 2.3 `auth login` browser flow | Deferred | Blocked on a verified browser OAuth route and localhost authorization behavior. |
| 2.4 `auth logout` | Merged | Implemented in PR #12. |
| 3.1 Saved-job models | Merged | Implemented in PR #13. |
| 3.2 `saved-jobs list` | Merged | Implemented in PR #12. |
| 3.3 `saved-jobs save` | Merged | Implemented in PR #13. |
| 3.4 `saved-jobs stage` | Merged | Implemented in PR #14. |
| 3.5 `saved-jobs remove` | Merged | Implemented in PR #15. |
| 4.1 Multi-page search | Merged | Implemented in PR #16. |
| 4.2 Retry policy | Merged | Implemented in PR #17. |
| 5.1 Anonymous read cache | Merged | Implemented in PR #18. |
| 6.1 Public repository baseline | Merged | Implemented in PR #20. |
| 6.2 CI, Ruff, and pre-commit | Merged | Implemented in PR #22. |
| 6.3 Secure session storage | Merged | Implemented in PR #21. |
| 6.4 Agent-focused README | Merged | Implemented in PR #24. |
| 6.5 Roadmap status hygiene | Merged | Implemented in PR #25. |
| 7.1 Saved-job write integrity | Merged | Implemented in PR #26. |
| 7.2 Cache isolation and hardening | Merged | Implemented in PR #27 and landed through recovery PR #29. |
| 7.3 Python 3.11-3.14 support | Merged | Implemented in PR #28 and landed through recovery PR #29. |
| 7.4 Production resilience follow-ups | Merged | Implemented in PR #31. |
| 8.1 Agent JSON coverage | Deferred | Add after Phase 7 blockers; mutation/auth schema agreed with users. |
| 8.2 Multi-page cache and duplicate handling | Deferred | Add after Phase 7 blockers; pagination behavior measured. |
| 8.3 PyPI release automation | Merged | Release workflow, artifact verification, checksums, and Trusted Publishing are ready for the first `v*` tag. |
| 8.3.1 Release test stability | Merged | Implemented in PR #41. |
| 8.3.2 PyPI checksum isolation | Merged | Implemented in PR #42; uncovered checksum verifier path handling. |
| 8.3.3 Release artifact staging | Merged | Implemented in PR #43; released as `v0.1.4`. |
| 8.3.4 Runtime package version sync | Merged | Implemented in PR #44; released as `v0.1.5`. |
| 8.3.5 Published-package README guide | Merged | Implemented in PR #45. |
| 8.4 Search filters and facets | Deferred | MCP filters are documented but not exposed; verify each selected filter. Exact facet contract remains unknown. |
| 8.5 Tracker search and saved-job details | Deferred | Requires verified authenticated response captures. |
| 8.6 Saved-job list pagination | Deferred | Requires cursor semantics or a verified higher-limit query. |
| 8.7 Browser OAuth login | Deferred | Spec ready in PR 2.3; live loopback/provider behavior remains unverified. |
| 8.8 Additional CI assurance | Deferred | Add after Phase 7; static-analysis scope selected. |
| 9.1 First-party read-only MCP transport | Merged | Implemented in PR #46; released as `v0.2.0`. |
| 10.1 Shared HiringCafe CLI agent skill | Open | Implemented in stacked PR #48; capability and audit corrections included. |


## Product goal

Provide a deterministic CLI for humans and autonomous agents to:

1. Search HiringCafe jobs without a browser.
2. Inspect a job description.
3. Authenticate through Firebase while collecting credentials only through explicit user-owned input.
4. List and mutate the authenticated user's saved jobs.

## Non-goals

- Scraping or mirroring the full jobs database.
- Resume upload, alerts, notes, admin features, or internal endpoints.
- Browser automation for provider login.
- Hiding endpoint failures as empty results.
- Storing any password or repeatedly prompting for it.

## Runtime decision

Use Python 3.11+. Phase 0/1 uses only the standard library (`urllib`, `json`, `html.parser`). Phase 2/3 uses documented Google REST endpoints directly — Firebase Identity Toolkit for token refresh and the Firestore REST API for `savedJobs` — so there is no SDK dependency and no service account. The `firebase-admin` SDK is explicitly wrong here: it authenticates as a project admin, while this CLI must act as the signed-in user.

Dependencies are allowed only when a PR spec names the reason. The initial package has no dependencies and no framework.

## Verified endpoint inventory

Base URL: `https://hiringcafe.com`. The user-facing `hiring.cafe` domain redirects there.

### Anonymous endpoints

| Status | Purpose | Method and route | Verified result |
|---|---|---|---|
| **Historically verified; currently challenged** | Search jobs | `GET /?searchState=<urlencoded JSON>&page=<n>` | Returned `__NEXT_DATA__` on 2026-08-17. On 2026-10-11, `chen-lappy` received HTTP 403 with Cloudflare's `cf-mitigated: challenge`; do not spoof browser headers or reuse challenge cookies. |
| **Historically verified; currently challenged** | Raw job description | `GET /api/job-description?id=<objectID>` | Returned the raw job object historically. On 2026-10-11, `chen-lappy` received HTTP 403 with Cloudflare's `cf-mitigated: challenge`. `saved-jobs save` still depends on this raw response and is not covered by the read-only MCP connector. |
| **Official and live-verified** | Public job search and details | `POST /api/mcp`, JSON-RPC `tools/call` for `search_jobs` and `get_job_details` | HiringCafe documents this endpoint for any MCP-compatible client. No sign-in; read-only public data. `search_jobs` returns one job per company, accepts `limit` 1–25 (default 10), and has no pagination contract. Responses are JSON-RPC with Markdown text content. Per-IP rate limits apply; returned links carry Claude attribution parameters. [Official connector documentation](https://hiringcafe.com/documentation/hiringcafe-claude-connector). |
| **Official; not selected** | ChatGPT job search/details | `POST /api/chatgpt/mcp`, JSON-RPC tools `search_hiringcafe_jobs` and `get_hiringcafe_job_details` | Documented read-only integration with a separate response/tool contract and ChatGPT attribution. Not used by this CLI. [Official ChatGPT app documentation](https://hiringcafe.com/documentation/hiringcafe-chatgpt-app). |
| Reachable, unknown contract | Generic jobs | `GET /api/jobs` | Returned `{"jobs":[]}` anonymously; useful semantics unknown. Do not build on it. |
| Reachable, unknown contract | Marketplace count | `GET /api/getMarketplaceJobsCount` | Returned `{"count":0}` anonymously; useful semantics unknown. Do not build on it. |
| Requires exact unknown parameter | Facets | `GET /api/search-facets` | Returns `400 {"error":"Invalid or missing facetType."}`. Common guesses were rejected. Deferred until the exact value is captured from the app. |
| Disproven | Old search API | `POST /api/search-jobs` | `405 Method not allowed`. |
| Partially verified | Internal search API | `GET /api/search-jobs` | `401 Unauthorized`; no anonymous contract. Do not use it while SSR search works. |
| Disproven | Old total count | `/api/search-jobs/get-total-count` | Not present in current bundles and returns 404. |
| Disproven | Standalone SSR route | `/ssr/search-jobs` | Returns 404. Search SSR is the home route. |

Historical SSR observations (observed 2026-08-17; not a current CLI transport contract):

- Live cache headers on 2026-08-17: `cache-control: private, no-store`; a representative search response was about 1 MB. HTTP/shared caching cannot reuse it, so only an explicit local TTL cache may do so.
- Only `searchQuery` and `page` are verified CLI inputs.
- The server may enrich `searchState`; for example, an IP-derived country location was added during verification.
- `ssrPageSize` was 40, but page size is server-controlled and must not be a CLI promise.
- A page may contain more `ssrHits` than `ssrPageSize` because grouped cards can unpack into multiple unique postings. In one probe, 40 unique `collapse_key`/`source_and_board_token` groups produced 124 unique `objectID` hits.
- Pagination was verified with `page=0`, `1`, and `2`. All pages retained the same `searchState`; only a malformed earlier probe suggested otherwise.
- On 2026-10-11, both the root search request and the raw job-description request returned a Cloudflare challenge to the CLI host. This is a network access-control response, not evidence that the old response schemas changed.
- The MCP connector's read-only scope does not include profiles, saved jobs, tracker data, resume uploads, alerts, or writes. Authenticated write flows must continue to use separately verified APIs and must not be inferred from the MCP connector.
- `count` must be derived from `ssrTotalCount` on page 0, not from the length of `ssrHits`.

Useful `ssrHits` fields observed:

- Identity and application: `objectID`, `source`, `apply_url`, `is_expired`.
- Title: `job_information.title` and `job_information.job_title_raw`.
- Company: `enriched_company_data.name`; fallback `v5_processed_job_data.company_name`.
- Location: `v5_processed_job_data.formatted_workplace_location`; lists such as `workplace_cities`, `workplace_states`, and `workplace_countries` are also available.
- Classification: `v5_processed_job_data.workplace_type`, `commitment`, `job_category`, `role_type`, `seniority_level`.
- Dates and compensation: `estimated_publish_date`, compensation min/max fields by frequency.
- Grouping: `collapse_key` and `source_and_board_token`.

The CLI must not copy user-tracking arrays such as `viewedByUsers`, `savedFromUsers`, `appliedFromUsers`, or `hiddenFromUsers` into normal output.

Job-description cache observation: one live hit returned `cache-control: public`, an ETag, and an `age` header, but no usable max-age lifetime. It is safe for explicit local TTL caching, but the CLI must choose the lifetime rather than trust the server to specify one.

### Firebase and authenticated behavior

The web app uses Firebase client auth and Firestore. Relevant public web configuration observed in the bundle:

- Firebase app name: `candidate-client`
- Project ID: `hiringcafe-ec4d6`
- Auth domain: `hiringcafe-ec4d6.firebaseapp.com`

The normal public Firebase web API key is embedded in the client bundle. It identifies the web client rather than authenticating a user. Keep it isolated in one Firebase config module and out of logs/fixtures. It must never be confused with a user credential.

Firebase token responses are `no-cache, no-store, max-age=0, must-revalidate` and contain credentials. They are never cacheable.

Observed login methods:

- Google, Microsoft, and Facebook OAuth popups.
- Firebase email/password with email verification.

The CLI must not collect an OAuth provider password. For the verified Firebase email/password method, the CLI may accept the account password through hidden interactive input or the existing `HIRINGCAFE_PASSWORD` environment variable, immediately exchange it for a Firebase refresh token, and discard the password. It must never log, cache, or persist the password.

Saved jobs are Firestore documents, with marketplace REST calls as secondary synchronization:

| Status | Purpose | Data or request | Verified result |
|---|---|---|---|
| Bundle-verified | Saved job storage | Firestore collection `savedJobs`, document ID `${uid}_${objectID}` | Fields observed in app logic: `objectID`, `owner`, `dateSaved`, `stage`, `stageHistory`, `isHidden`, `counted_milestones`, `firstSavedAt`, `userNote`, `journal`, `tags`, `nextAction`. The full search-hit object is merged into each document, with private user-tracking arrays removed before writing. |
| Live-verified | Tracker list | Firestore REST `POST .../documents:runQuery` | A structured query on `savedJobs` with owner and stage filters, `dateSaved` ordering, and limit 20 works with a Firebase ID token. `documents/savedJobs?filter=...` is not a valid Firestore REST contract. |
| Bundle-verified | Save/update stage | Firestore write plus `POST /api/updateMarketplaceJobStageForUser` with JSON `{job_id, user_token, stage}` | `user_token` is a Firebase ID token. |
| Bundle-verified | List removal from a stage | `POST /api/removeJobFromList` with `{job_id, user_token, stage, should_delete:false}` | Used when moving out of selected old stages. |
| Bundle-verified | Delete saved job | `POST /api/removeJobFromList` with `{job_id, user_token, stage, should_delete:true}` | Unauthenticated empty-body probe returned `400 Missing job_id, user_token, or stage`, confirming the body fields. |
| Bundle-verified | Tracker search index | `POST /api/tracker/searchIndex` with `{user_token}` | Returns `{entries:[...]}` in app logic; used by tracker/export/search. Firebase refresh remains the lighter `auth status` check. |
| Reachable, auth required | Boards | `/api/boards/*`, including `GET /api/boards/saved` | Anonymous request returned 401. Contract unknown; do not build on it while Firestore read is known. |

Authenticated behavior was verified from the JavaScript chunks loaded by the signed-in tracker page on 2026-08-17. No credential, UID, email, cookie, or account data was stored in project documentation.

The verified ordered tracker stages are `saved`, `applied`, `interviewing`, `offer`, `rejected`, `ghosted`, and `hidden`. The first six are pipeline stages; `hidden` is separate. Marketplace list cleanup occurs only when moving out of `saved`, `applied`, or `hidden`.

Do not use `/api/admin/*` or `/api/internals/*`.

## Target commands

Phase 1:

```bash
hiringcafe search "python developer" --json
hiringcafe search "python developer" --raw-search-state '{"searchQuery":"python developer"}' --json
hiringcafe count "python developer"
hiringcafe job show <objectID> --json
```

Phase 2:

```bash
hiringcafe auth import
hiringcafe auth status --json
hiringcafe auth logout
```

Phase 3:

```bash
hiringcafe saved-jobs list --json
hiringcafe saved-jobs save <objectID> --stage saved
hiringcafe saved-jobs stage <objectID> --stage applied
hiringcafe saved-jobs remove <objectID> --yes
```

Later, only after a concrete need:

```bash
hiringcafe search ... --pages 3 --jsonl
hiringcafe facets ...
hiringcafe tracker list --json
```

## Output and exit contract

Machine mode is explicit (`--json` or `--jsonl`). stdout contains only parseable machine output. Diagnostics go to stderr.

JSON search output includes:

```json
{
  "version": 1,
  "query": {"searchState": {}, "page": 0},
  "result": {
    "totalCount": 3067,
    "companyCount": 555,
    "pageSize": 40,
    "isLastPage": false,
    "jobs": []
  }
}
```

The example count is illustrative, not guaranteed. Normalized jobs contain at least:

```json
{
  "id": "objectID",
  "title": "job_information.title",
  "company": "enriched_company_data.name",
  "location": "v5_processed_job_data.formatted_workplace_location",
  "url": "apply_url",
  "source": "source",
  "workplaceType": "v5_processed_job_data.workplace_type",
  "commitment": "v5_processed_job_data.commitment",
  "publishedAt": "v5_processed_job_data.estimated_publish_date",
  "expired": "is_expired"
}
```

Missing optional values are `null`; missing `objectID` is an API parsing error. Raw job objects may be exposed later with `--raw-jobs` if agents prove the normalized subset insufficient.

| Exit code | Meaning |
|---:|---|
| 0 | Success |
| 1 | Transport, HTTP, parsing, or unexpected API error |
| 2 | Invalid CLI arguments or search state |
| 3 | Rate limited |
| 4 | No stored credential |
| 5 | Credential exists but cannot be refreshed or is rejected |
| 6 | Confirmed write conflict or prerequisite missing |

## Phase 0 — Governance and bootstrap

### PR 0.1 — Minimal CLI package

#### Spec

Create the smallest installable Python CLI.

In scope:

- `pyproject.toml` and executable `hiringcafe` entry point.
- `hiringcafe --help`.
- `hiringcafe --version`.
- One runnable smoke check.
- README installation and usage stub.

Out of scope:

- Networking, parsing, auth, and business commands.

Acceptance criteria:

- Local package link/install runs `hiringcafe --help` with exit 0.
- `--version` prints the package semantic version.
- Help documents the exit-code contract.
- No runtime dependency is added.

### PR 0.2 — Live endpoint regression probe

#### Spec

Preserve the verification performed for this roadmap as a small runnable check, not a fixture-only test.

In scope:

- One offline parser test using a minimized `__NEXT_DATA__` fixture.
- One explicitly opt-in live probe (`LIVE=1`) for:
  - search page 0,
  - search page 1,
  - job description for the first search hit.
- Live probe prints status, presence of required SSR keys, and one object ID; it does not save personal data.

Out of scope:

- Authenticated probes.
- A general scraping harness.

Acceptance criteria:

- Offline test runs in the normal test command.
- Live probe fails if `__NEXT_DATA__`, `ssrHits`, `ssrTotalCount`, `ssrPage`, or `ssrIsLastPage` disappears.
- Live probe is skipped unless explicitly enabled.
- Roadmap endpoint table is updated if behavior differs.

## Phase 1 — Anonymous search and job details

### PR 1.1 — HTTP and SSR client

#### Spec

Create one module that owns all HiringCafe web traffic.

In scope:

- Immutable base URL default (`https://hiringcafe.com`) and environment override for tests.
- Browser-like headers.
- Timeout.
- URL construction for `searchState` and `page`.
- HTML retrieval.
- Extraction and JSON parsing of `__NEXT_DATA__`.
- Validation that required page properties exist.
- Typed errors carrying HTTP status and endpoint name.

Out of scope:

- Cookie management.
- Retry.
- Auth.

Acceptance criteria:

- `GET /?searchState=...&page=1` returns parsed `pageProps`.
- Missing or malformed `__NEXT_DATA__` is a parse error, never an empty result.
- Non-2xx and transport failures are distinguishable.
- No command module constructs a HiringCafe URL directly.

### PR 1.2 — Search state contract

#### Spec

Support only inputs verified in this roadmap.

In scope:

- Build `{"searchQuery":"..."}` from positional query text.
- Accept complete `--raw-search-state` as JSON.
- Accept `--page` as a nonnegative integer.
- Reject unknown/malformed JSON and invalid page values.
- Preserve supplied object keys and types without silent transformation.

Out of scope:

- Location, workplace, commitment, date, salary, and facet filters. The server may support them, but their exact schemas were not captured and must not be guessed.
- Page size override.

Acceptance criteria:

- Query mode and raw mode generate correctly URL-encoded requests.
- Empty query and empty raw object are allowed only if the live site allows them; otherwise they exit 2.
- Invalid raw JSON exits 2 without network traffic.
- The first added filter requires a roadmap amendment backed by a captured working `searchState`.

### PR 1.3 — `search` command

#### Spec

Implement:

```bash
hiringcafe search "python developer" --page 0 --json
```

In scope:

- One SSR request.
- Output envelope version 1.
- Normalized jobs plus page metadata.
- Human-readable fallback when `--json` is omitted.
- Deterministic job ordering: preserve `ssrHits` order.

Out of scope:

- Multi-page orchestration.
- Table formatting beyond a simple default.
- Filtering after retrieval.

Acceptance criteria:

- Every returned item has a nonempty `id`.
- Output count equals `ssrHits.length`; grouped/unpacked postings are not discarded.
- `ssrError` non-null becomes exit 1.
- Network/API failures print no partial JSON to stdout.
- Invalid arguments exit 2.

### PR 1.4 — `count` command

#### Spec

Implement:

```bash
hiringcafe count "python developer"
hiringcafe count "python developer" --json
```

In scope:

- Reuse the search-state builder and SSR client.
- Request page 0 only.
- Read `ssrTotalCount`.

Out of scope:

- Fetching or normalizing `ssrHits`.
- A separate count endpoint.

Acceptance criteria:

- Default mode prints exactly one integer and newline.
- JSON mode includes request state and count.
- Missing `ssrTotalCount` is a parse error, not zero.

### PR 1.5 — `job show` command

#### Spec

Implement:

```bash
hiringcafe job show <objectID> --json
```

In scope:

- `GET /api/job-description?id=<objectID>`.
- Validate nonempty ID and response `job`.
- Return normalized description plus safe raw job metadata needed by later save behavior.

Out of scope:

- HTML-to-text conversion beyond normalizing whitespace.
- Caching.

Acceptance criteria:

- Real object ID returns HTTP 200 and valid JSON.
- Missing ID exits 2.
- 404/400 and malformed JSON exit 1.
- No user-tracking arrays are emitted.

## Phase 2 — Firebase authentication

Authentication is a prerequisite for all Phase 3 behavior.

### PR 2.1 — Firebase session model, token import, and email login

#### Spec

Define the only credential representation used by the CLI.

In scope:

- Store a Firebase refresh token, not a provider password.
- Add `hiringcafe auth login --email`: read the password through hidden input or `HIRINGCAFE_PASSWORD`, call Firebase `signInWithPassword`, store the returned refresh token, and discard the password.
- Import a refresh token through stdin or a file descriptor; never as a visible argv value.
- Ephemeral ID token refresh through Firebase auth.
- Session file at the platform user config directory, for example `~/.config/hiringcafe-cli/session.json` on macOS/Linux.
- Create session directory and file with owner-only permissions.
- Version field for future migration.
- Delete local session on logout.

Out of scope:

- OAuth login.
- OAuth password collection.
- Encryption of the local refresh token beyond filesystem permissions; document this limitation.

Acceptance criteria:

- Imported refresh token can obtain an ID token.
- Session file mode rejects group/other access.
- Import cancels cleanly and leaves no partial file.
- Token values never appear in stdout, stderr, logs, fixtures, or errors.
- Agent automation is supported through stdin or `HIRINGCAFE_REFRESH_TOKEN`; a visible argv token is never accepted.

### PR 2.2 — `auth status`

#### Spec

Implement:

```bash
hiringcafe auth status --json
hiringcafe auth status
```

In scope:

- Detect missing session.
- Refresh an ID token from the stored refresh token.
- Report anonymous user ID/email only if available and only in JSON mode when explicitly useful.
- Distinguish invalid/expired refresh from transport failure.

Out of scope:

- Saved-job reads.
- Automatic interactive re-login.

Acceptance criteria:

- Valid credential exits 0.
- No file exits 4.
- Firebase rejection/expired refresh exits 5.
- Network failure exits 1, not 5.
- JSON output never includes refresh or ID tokens.

### PR 2.3 — `auth login` browser flow

#### Spec

Do **not** implement this yet. OAuth popups are restricted by Firebase authorized-domain configuration, and localhost behavior has not been verified. Build only after a real-account capture proves a route that does not require the CLI to see a provider password.

Potential future flow, if verified:

1. CLI opens a local login page using the same Firebase web config.
2. User chooses Google, Microsoft, Facebook, or email/password in their own browser.
3. Local page obtains the Firebase user and refresh token.
4. CLI receives only the refresh token over loopback, stores it, and closes the flow.

In scope:

- Loopback callback and strict single-use state token.
- Timeout and cancellation.
- Clear instruction that provider credentials are entered only into the browser.
- Fallback message directing users to `auth import` if browser flow cannot run.

Out of scope:

- Headless provider login.
- Typing, storing, or passing an email/password to Firebase from the CLI.
- Reading credentials from the user's existing browser profile.

Acceptance criteria:

- A roadmap amendment records the verified browser route and provider behavior.
- Successful login stores a refresh token and `auth status` exits 0.
- Cancelled/expired flow leaves no partial session.
- Loopback server accepts only the expected one-time callback.
- No token or provider credential appears in terminal output.

### PR 2.4 — `auth logout`

#### Spec

Implement:

```bash
hiringcafe auth logout
```

In scope:

- Firebase client sign-out where supported.
- Delete the local session file.
- Idempotent behavior when no session exists.

Out of scope:

- Deleting saved jobs or account data.
- Clearing unrelated browser sessions.

Acceptance criteria:

- Session file is removed.
- Running logout with no session still exits 0.
- Failure to remove an existing file exits 1.

## Phase 3 — Saved jobs

Blocked only by Phase 2. The authenticated data contract is verified from the signed-in tracker bundle. Sanitize all personal data before committing fixtures.

### PR 3.1 — Saved-job models

#### Spec

Define normalized saved-job output.

Required normalized fields:

- `id` from `objectID`.
- `savedAt` from `dateSaved`.
- `stage`.
- `stageHistory`.
- `hidden` from `isHidden`.
- Search fields available after joining or hydration: title, company, location, URL.
- `documentId` from the Firestore document ID.

In scope:

- Minimal fixture with synthetic IDs and timestamps.
- Firestore Timestamp conversion to ISO-8601 UTC.
- Missing required identifier handling.
- Explicit stage values copied from the verified tracker list.

Out of scope:

- Save/remove mutations.
- Local database/cache.

Acceptance criteria:

- Every normalized field documents its raw source.
- Missing `objectID` or `owner` is an error.
- Invalid stage is rejected.
- Fixtures contain no real UID, email, bearer token, or personal job data.

### PR 3.2 — `saved-jobs list`

#### Spec

Implement:

```bash
hiringcafe saved-jobs list --json
```

In scope:

- Firebase/Firestore structured query for the current user's `savedJobs`.
- Use `POST .../documents:runQuery` with `where owner == uid`, optionally `where stage == selected stage`, otherwise `stage in pipelineStages`; order by `dateSaved` descending and limit to 20 documents.
- Auth failure and permission-denied handling.
- Deterministic ordering by `dateSaved` descending, with document ID as tie-breaker.

Out of scope:

- Marketplace board endpoints.
- Local caching.

Acceptance criteria:

- Valid credential returns normalized saved jobs.
- Missing credential exits 4.
- Rejected/expired credential exits 5.
- Permission denied is exit 1 with a clear message, never an empty list.

### PR 3.3 — `saved-jobs save`

#### Spec

Implement:

```bash
hiringcafe saved-jobs save <objectID> --stage saved
```

In scope:

- Validate object ID and stage.
- Fetch job detail if the search object was not supplied.
- Firestore `setDoc(..., {merge:true})` equivalent at document `${uid}_${objectID}`.
- Marketplace sync with `POST /api/updateMarketplaceJobStageForUser`.
- Preserve existing stage history according to captured app behavior.

Out of scope:

- Bulk save.
- Editing job descriptions.

Acceptance criteria:

- New and repeated saves are idempotent at the document level.
- Successful Firestore write with failed marketplace sync reports a partial success/error, never silent full success.
- Invalid stage exits 2.
- No mutation is attempted without a fresh ID token.

### PR 3.4 — `saved-jobs stage`

#### Spec

Implement:

```bash
hiringcafe saved-jobs stage <objectID> --stage applied
```

In scope:

- Read current saved document.
- Update Firestore stage/history using captured app behavior.
- Call marketplace stage update.
- When moving out of a stage that the app removes, call `removeJobFromList` with `should_delete:false`.

Out of scope:

- Free-text notes.
- Bulk stage changes.

Acceptance criteria:

- Unknown saved job exits 6.
- Invalid stage exits 2.
- Stage transitions match the web app for the same account state.
- Marketplace sync failure is visible.

### PR 3.5 — `saved-jobs remove`

#### Spec

Implement:

```bash
hiringcafe saved-jobs remove <objectID> --yes
```

In scope:

- Interactive confirmation unless `--yes` is supplied.
- Read current stage.
- `POST /api/removeJobFromList` with `should_delete:true`.
- Verify Firestore document removal when the captured app behavior requires it.

Out of scope:

- Bulk removal.
- Hiding without deletion.

Acceptance criteria:

- Removed document/job no longer appears in list.
- Unknown saved job exits 6.
- Interactive refusal exits 2 and performs no network mutation.
- Agents can use `--yes` deterministically.

## Phase 4 — Agent ergonomics

### PR 4.1 — Multi-page search

#### Spec

Implement:

```bash
hiringcafe search "python developer" --pages 3 --jsonl
```

In scope:

- Sequential page requests.
- Stop at `ssrIsLastPage` or requested page count.
- One JSON object per line in `--jsonl` mode.
- Preserve source order.

Out of scope:

- Concurrent requests.
- Resume state.

Acceptance criteria:

- No page beyond the requested count is fetched.
- `ssrIsLastPage` stops iteration early.
- Rate limit exits 3.

### PR 4.2 — Retry policy

#### Spec

Add bounded transport resilience.

In scope:

- Retry only idempotent anonymous GETs.
- Exponential backoff with jitter.
- Retry only transport failures, 408, 429, and 5xx.
- Rate limit remains exit 3 after bounded retries.

Out of scope:

- Blind retry of saved-job mutations.
- Background queues.

Acceptance criteria:

- Mutation commands never auto-retry unless an explicit request idempotency key is verified.
- Retry count and total timeout are bounded.
- Timeout diagnostics name the endpoint.

## Phase 5 — Explicit local caching

### PR 5.1 — Anonymous read cache

#### Spec

Add a small, explicit TTL cache only for anonymous reads. Do not use HTTP heuristic caching.

In scope:

- Cache normalized search/count envelopes keyed by base URL, canonical `searchState`, and page.
- Cache normalized job-show output keyed by base URL and object ID.
- Default TTL: 15 minutes for search/count, 24 hours for job details.
- `--no-cache` bypasses reads and writes.
- `--cache-ttl <seconds>` overrides the endpoint-family default.
- `hiringcafe cache purge` clears the cache.
- Versioned owner-only cache files with atomic replacement.
- Cache hit/miss diagnostics on stderr.

Out of scope:

- Caching authenticated reads, token exchanges, tracker search, or mutations.
- Conditional HTTP revalidation; the required server lifetime/max-age contract is absent.
- A daemon or background refresh.

Acceptance criteria:

- A repeated identical search/count/job-show request can complete without a HiringCafe HTTP request.
- TTL expiry triggers a fresh request and replaces the entry.
- `--no-cache` and `cache purge` never read or preserve old entries.
- Cache keys distinguish base URL, search state, page, and object ID.
- No bearer token, refresh token, cookie, UID, email, or authenticated response is written.
- A corrupt cache entry is discarded and treated as a miss; it never produces fabricated results.

## Deferred

Do not build without a verified contract and concrete user need:

- Filter flags beyond query/page.
- Facets.
- AI search.
- Tracker search index and notes.
- Job boards.
- Job view/activity marking.
- Reset job list.
- Alerts, resume upload, or admin/internal features.
- Database storage or a plugin system.

## Appendix A — Complete discovered endpoint inventory

Extracted from every JavaScript chunk loaded by `https://hiringcafe.com/` on 2026-08-17. Query-string construction variants were deduplicated. Dynamic Next.js route templates are preserved. Official MCP routes were verified from current documentation on 2026-10-11.

Route discovery is not an API contract. Unless the main endpoint inventory marks a route verified, its method, body, auth requirement, and response schema are unknown or only partially known. Do not implement a discovered route solely because it appears here.

### CLI-relevant routes

Previously probed routes (current status is in the main endpoint inventory):

```text
/api/job-description
/api/jobs
/api/getMarketplaceJobsCount
/api/search-facets
/api/search-jobs
/api/removeJobFromList
/api/tracker/searchIndex
/api/updateMarketplaceJobStageForUser
/api/mcp
/api/chatgpt/mcp
```

Discovered but contract unknown; potentially relevant after capture:

```text
/api/ai-search/agent/[...path]
/api/ai-search/filter-jobs
/api/ai-search/hydrate-jobs
/api/ai-search/parse-filters
/api/ai-search/search-index
/api/boards
/api/boards/[id]
/api/boards/me
/api/boards/public/[slug]
/api/boards/public/actions/apply-click
/api/boards/public/actions/subscribe
/api/boards/public/counts
/api/boards/saved
/api/boards/saved/check
/api/boards/stars
/api/boards/stars/check
/api/company-jobs
/api/company-signals
/api/getCountry
/api/job-search-feedback
/api/jobSummaryGPT
/api/markJobActivity
/api/markJobViewed
/api/resetJobList
/api/searchLocation
/api/share-links
/api/share-links/resolve
/api/similar-job-titles
```

### Other discovered web routes

Content and public flows:

```text
/api/digest/unsubscribe/[token]
/api/early_access_features/
/api/markdown/insights/:slug
/api/markdown/insights/[slug]
/api/markdown/work-here/:slug
/api/markdown/work-here/[slug]
/api/product_tours/
/api/surveys/
/api/unsubscribe/[type]/[token]
/api/web_experiments/
```

Applicant and marketplace flows:

```text
/api/applicant/addNotes
/api/applicant/createApplicant
/api/applicant/createApplicantWithSeeker
/api/applicant/dashboardWithToken/[candidateToken]
/api/applicant/generateShareLink
/api/applicant/getPublicJob/[requisitionId]
/api/applicant/getResumeTokens
/api/applicant/messages/getMessages
/api/applicant/messages/postMessage
/api/applicant/rejectApplicant
/api/applicant/reportApplicant
/api/applicant/screens/getApplicantScreenInfo
/api/applicant/screens/getScreen
/api/applicant/screens/getScreenStatus
/api/applicant/screens/markInitialScreenSubmitted
/api/applicant/sharedProfile/[share_token]
/api/applicant/talent_network/createProfile
/api/applicant/talent_network/getJobInvites
/api/applicant/talent_network/ipLocation
/api/applicant/talent_network/parsedResume
/api/applicant/talent_network/respondToInvite
/api/applicant/talent_network/resumeParseStatuses
/api/applicant/talent_network/setAvailabilityStage
/api/applicant/updateApplicant
/api/applicant/updateApplicantResume
/api/applicant/withdrawApplication
/api/marketplaceFunctions/allApplicantsAddGPTResumeData
/api/marketplaceFunctions/findApplicantsMessageCreate
/api/marketplaceFunctions/findApplicantsMessageReply
/api/marketplaceFunctions/reportJob
/api/marketplaceFunctions/resumeDelete
/api/marketplaceFunctions/resumeDeleteSeekerPool
/api/marketplaceFunctions/resumeUpdateSeekerPool
/api/marketplaceFunctions/resumeUpload
/api/marketplaceFunctions/resumeUploadSeekerPool
/api/marketplaceFunctions/triggerResumeGpt
/api/marketplaceFunctions/triggerResumeGptSeekerPool
/api/marketplaceFunctions/updateListedJobInfo
/api/partnerships/jobget
/api/videoask/refreshAccessToken
/api/webhooks/initialScreenVideoAsk
/api/webhooks/videoask
/api/webhooks/videoask_seeker_profile_verification
/api/webhooks/videoaskpitchupdate
```

Community content:

```text
/api/ugc/create-comment
/api/ugc/get-comments
```

Scheduled task trigger:

```text
/api/cronEndpoints/triggerDailyNotifications
```

### Discovered admin routes — excluded

These are out of scope regardless of accessibility:

```text
/api/admin/board/acceptInvite
/api/admin/board/changeBoard
/api/admin/board/createBoard
/api/admin/board/getAdmins
/api/admin/board/getBoards
/api/admin/board/getInvite
/api/admin/board/manageAdmins
/api/admin/inbox/sendMessageToApplicant
/api/admin/job
/api/admin/job/create
/api/admin/job/patch
/api/admin/payment/addCredits
/api/admin/payment/boostJob
/api/admin/payment/getPaymentMethods
/api/admin/payment/payBillByMonth
/api/admin/payment/savePaymentInfo
/api/admin/payment/stripeSetupIntent
/api/admin/payment/subscribeBoardToApplicantPool
/api/admin/payment/updatePaymentMethod
/api/admin/search/helpers
/api/admin/search/searchFacet
/api/admin/search/searchTalent
/api/admin/specialCases/deleteJob
/api/admin/specialCases/jobStep
/api/admin/specialCases/shareJobAdmin
/api/admin/talent_network/invite_candidate
/api/admin/userManagement/sessionLogin
/api/admin/userManagement/sessionLogout
/api/admin/userManagement/spoofUser
/api/admin/videoScreen/createForm
/api/admin/videoScreen/createQuestion
/api/admin/videoScreen/deleteQuestion
/api/admin/videoScreen/publicUpdateVideoScreenQuestion
/api/admin/videoScreen/reorderQuestions
/api/admin/videoScreen/updateQuestionMetadata
/api/admin/videoScreen/updateVideoaskTitle
/api/adminpublicjob/getJobIdWithToken
/api/adminpublicjob/updateJobPublic
```

### Discovered internal routes — excluded

These are out of scope regardless of accessibility:

```text
/api/internals/adhoc-alerts
/api/internals/adhoc-epochs
/api/internals/adhoc-epochs-batch
/api/internals/adhoc-observability
/api/internals/adhoc-overview
/api/internals/adhoc-scraper
/api/internals/adhoc-verify
/api/internals/ai-search-conversation-detail
/api/internals/ai-search-conversations
/api/internals/applicantPreSubmitToScreen
/api/internals/ats-breakdown
/api/internals/customCall
/api/internals/elastic-firestore-comparison
/api/internals/enrichment-stats
/api/internals/firestore-dashboard
/api/internals/getBoardData
/api/internals/getJobData
/api/internals/getPendingApplicants
/api/internals/getUserData
/api/internals/handleBudget
/api/internals/handleCredits
/api/internals/internalAdminCleanup
/api/internals/internalDeleteApplicant
/api/internals/internalFreeJobBoost
/api/internals/internalGetToolData
/api/internals/internalMoveApplicant
/api/internals/job-search-feedback-report
/api/internals/job-trends
/api/internals/jobImport/fetchJobList
/api/internals/jobImport/importJobToBoard
/api/internals/marketplace/deleteJob
/api/internals/marketplace/getReportedJobs
/api/internals/marketplace/purgeBoard
/api/internals/marketplaceJobAction
/api/internals/pipeline-status
/api/internals/probe-agent/[...path]
/api/internals/processApplicant
/api/internals/removeBoardFromUser
/api/internals/toggleBoardFlags
/api/internals/updateJobFieldsAsAdmin
/api/internals/updateUserMasterCall
```

## Documentation and PR rules

- Every PR description links to its phase and PR spec.
- Every PR spec is executable documentation at `specs/pr-<id>-<slug>/spec.md`; changes to scope, API dependency, or acceptance criteria require a spec update in the same PR.
- Every user-facing command and exit code is documented in README by the end of its PR.
- Endpoint behavior changes update this roadmap before or in the same PR as code.
- Tests cover parsers, state building, auth branches, and mutation decisions without unnecessary fixtures.
- No commit, fixture, log, or issue may contain a refresh token, ID token, provider password, cookie, real UID, email, or private saved-job data.

## Phase 6 — Production repository

### PR 6.1 — Public repository baseline

#### Spec

Prepare the repository for public visibility without changing CLI behavior:

- Add MIT license, package metadata, changelog, and security policy.
- Replace private/draft repository language with a public unofficial CLI README.
- Document Git installation, authentication, local storage, cache behavior, retries, commands, and exit codes.

#### Out of scope

- Publishing to PyPI.
- Creating a version tag or release.
- Repository visibility changes.

#### Acceptance criteria

- The README clearly states that the project is unofficial and not affiliated with Hiring Cafe.
- Public users can install from Git and authenticate using documented commands.
- Security reporting and credential expectations are documented.
- Existing tests continue to pass.

### PR 6.2 — CI, Ruff, and pre-commit

#### Spec

Add automated quality gates without changing CLI behavior:

- Add Ruff formatting/linting and pre-commit configuration.
- Add GitHub Actions CI for locked sync, format check, lint, tests, and package build.
- Pin workflow actions to immutable commit SHAs.
- Apply only mechanical code fixes required by the configured rules.

#### Out of scope

- Adding runtime dependencies.
- Live-network CI.
- Publishing packages or releases.

#### Acceptance criteria

- Pre-commit runs Ruff and standard hygiene hooks locally.
- CI runs on pull requests and pushes to `main`.
- CI has least-privilege permissions, a bounded timeout, and SHA-pinned actions.
- Existing source passes format/lint checks.
- Existing tests and package build pass.

### PR 6.3 — Secure session storage

#### Spec

Close the local session permission race without changing the session format:

- Create new configuration directories with mode `0700`.
- Use a private unpredictable temporary file in the session directory, force `0600` before writing the refresh token, and clean it up on failure.
- Preserve atomic replacement, sync-before-replace, and the final owner-only session mode.

#### Out of scope

- OS keychain storage.
- Changing credential representation.
- Encrypting the refresh token.

#### Acceptance criteria

- A newly created configuration directory is owner-only.
- No interval exists where the temporary file containing the refresh token is group/world readable.
- Failed writes do not leave refresh-token temporary files behind.
- Existing tests and quality checks pass.

### PR 6.4 — Agent-focused README

#### Spec

Make the public README immediately useful to autonomous agents:

- Lead with a concrete search command and the CLI’s automation value.
- Add an agent install-and-verify path with `uv tool install`.
- Show JSON/JSONL consumption and noninteractive refresh-token import.
- Document stdout/stderr separation, stable exit actions, and retry/cache/auth safety boundaries.
- Preserve the unofficial-client warning and accurate beta/deferred status.

#### Out of scope

- New CLI behavior.
- Website copy, screenshots, or release assets.
- Changing authentication or storage formats.

#### Acceptance criteria

- README commands match the implemented CLI surface.
- Security, cache, retry, local-data, and exit-code statements remain accurate.
- Markdown/pre-commit checks pass.

### PR 6.5 — Roadmap status hygiene

#### Spec

Make roadmap completion explicit and machine-readable:

- Add an implementation-status table covering every PR 0.1–6.5.
- Use only `Merged`, `Open`, or `Deferred` statuses.
- Record the implementing GitHub PR for merged work.
- Record the blocking reason for deferred work.
- Require every state-changing PR to update the table in the same change.

#### Out of scope

- Reopening completed behavior.
- Changing PR scope or adding product features.
- Automatically syncing statuses from GitHub.

#### Acceptance criteria

- Every roadmap PR has exactly one status row.
- Statuses match repository history and open/deferred state.
- Merged rows reference their implementing GitHub PR.
- Deferred rows state why they are blocked.
- Pre-commit checks pass.

## Phase 7 — Production hardening

Phase 7 closes the current production-blocking audit findings. It does not expand product scope.

### PR 7.1 — Saved-job write integrity

#### Spec

Keep trusted saved-job fields authoritative when hydrating a job before a Firestore merge-write:

- Expand the sanitized hydrated job first.
- Set `objectID`, `owner`, `stage`, `dateSaved`, `isHidden`, `stageHistory`, and `counted_milestones` after it.
- Preserve removal of private user-tracking arrays.
- Add a regression test with malicious values in the hydrated source payload.

#### Out of scope

- Changing the document shape, stage transitions, or marketplace synchronization.

#### Acceptance criteria

- A hydrated payload cannot override ownership, identity, stage, timestamps, visibility, or tracking history.
- Existing save tests and quality gates pass.

### PR 7.2 — Cache isolation and hardening

#### Spec

Close cache isolation and file-write race findings:

- Key search and job-description caches by the active `WebClient.base_url`, not a hardcoded production hostname.
- Write cache entries through a private unpredictable temporary file, force mode `0600` before writing, flush and sync it, atomically replace the destination, and remove the temporary file on failure.
- Preserve cache versioning, TTL behavior, corruption handling, and owner-only directory expectations.

#### Out of scope

- Conditional HTTP revalidation, authenticated caching, background refresh, or a new cache format.

#### Acceptance criteria

- Identical requests against different configured base URLs never share entries.
- No interval exists where a new cache file is group/world readable.
- Failed writes do not leave temporary files or replace valid entries.
- Existing cache behavior and quality gates pass.

### PR 7.3 — Python 3.11-3.14 support

#### Spec

Make the stdlib-only package support the user-requested Python matrix:

- Require Python `>=3.11`.
- Keep runtime dependencies empty.
- Replace Python-3.12-only standard-library use with 3.11-compatible equivalents.
- Run CI on Python 3.11, 3.13, and 3.14 in addition to 3.12.
- Update documentation and agent rules to the supported range.

#### Out of scope

- Shipping interpreter-specific wheels, adding compatibility dependencies, or supporting Python 3.10 or earlier.

#### Acceptance criteria

- CI passes the complete 3.11-3.14 matrix.
- Package metadata, linter target, documentation, and implementation agree.
- Existing tests and package build pass.

### PR 7.4 — Production resilience follow-ups

#### Spec

Close resilience findings found by the production re-review:

- Treat invalid JSON or an incompatible cache schema as a cache miss, delete the entry, and continue.
- Reject a saved-job document whose `stage` is missing or unsupported before marketplace deletion.
- Bound HiringCafe, Firebase, and Firestore response reads at 8 MiB.
- Catch anonymous HiringCafe transport failures and map them to exit 1.
- Apply the same usable-old-stage guard to stage transitions.
- Restrict `HIRINGCAFE_BASE_URL` to HTTPS; local plaintext overrides are intentionally not supported.
- Pin CI actions to immutable commit SHAs, grant only `contents: read`, and cap the job at 10 minutes.

#### Out of scope

- Streaming parsers, spooled response files, authenticated caching, or additional static-analysis jobs.

#### Acceptance criteria

- Corrupt and wrong-schema cache entries self-heal without fabricating data.
- Legacy saved-job documents cannot reach deletion with an unknown stage.
- Legacy saved-job documents cannot reach stage mutation with an unknown old stage.
- Oversized external responses fail with a bounded-read error.
- Offline anonymous calls produce an exit-1 diagnostic rather than a traceback.
- Configured non-HTTPS base URLs are rejected before any credential-bearing request.
- CI remains least-privilege, time-bounded, and immutable-action-pinned.
- Tests, lint, formatting, pre-commit, and package build pass.

## Phase 8 — Post-hardening follow-ups

These are intentionally deferred until Phase 7 is merged. Each item needs its own PR spec before implementation; do not bundle unrelated work.

- 8.1 `--json` coverage for mutations and auth commands after the schema is agreed with agent users.
- 8.2 Multi-page JSONL cache reuse plus duplicate-ID handling across pages.
- 8.3 Tagged PyPI releases, build artifacts, checksums, and Trusted Publishing distribution.
- 8.4 Filter flags and facets only after a working `searchState` or exact facet contract is captured.
- 8.5 Tracker search and saved-job notes/tags/journal only after authenticated response captures are verified.
- 8.6 Saved-job list pagination after cursor semantics or a higher-limit contract is verified.
- 8.7 Browser OAuth login, using the PR 2.3 specification and verification blocker.
- 8.8 Additional CI assurance (for example mypy, Dependabot, or CodeQL) after the desired scope is selected.

### PR 8.3 — PyPI release automation

#### Spec

Publish versioned releases to PyPI:

- Publish only from immutable `v*` tags.
- Build the sdist and universal wheel with the existing `uv build` backend.
- Use GitHub Trusted Publishing; store no PyPI token.
- Publish to `https://upload.pypi.org/legacy/` and attach identical artifacts/checksums to the GitHub release.
- Pin actions by SHA and grant only the permissions required for OIDC publication.
- Document the protected GitHub environment and PyPI trusted-publisher setup.
- Update README and changelog for PyPI installation.

#### Out of scope

- TestPyPI rehearsal unless the first production release fails, semantic-version automation, platform wheels, and HiringCafe feature changes.

#### Acceptance criteria

- Non-release pushes never publish.
- A tag publishes exactly once and produces identical local/CI artifacts.
- PyPI installation works on Python 3.11–3.14 with no runtime dependencies.
- No credential enters the workflow or artifacts.
- Documentation and release runbook match the implemented workflow.

### PR 8.3.5 — Published-package README guide

#### Spec

Make the public README match the now-published PyPI package:

- Add PyPI, Python-version, CI, and license badges.
- Put persistent and one-shot installation commands before advanced usage.
- Add a table of contents.
- Consolidate the supported command surface into a scannable reference.
- Keep agent automation, auth safety, local storage, caching, and exit-code contracts accurate.
- Correct PR 8.3.4 roadmap status to merged.

#### Out of scope

- New CLI behavior, new API endpoints, screenshots, and release workflow changes.

#### Acceptance criteria

- Every documented command exists in the installed CLI.
- Installation instructions work for the published PyPI package.
- The unofficial-client and beta-status warnings remain visible.
- Markdown/pre-commit checks pass.

### PR 8.4 — Search filters and facets

#### Spec

Add only contract-verified search inputs:

- Verify the documented MCP parameter schema and live behavior for each selected filter before exposing a CLI flag. The earlier SSR-only design is superseded by the official MCP transport.
- Reproduce filter application through `search_jobs`; text keywords alone do not establish structured filtering.
- Capture the exact `/api/search-facets` method, parameters, auth requirement, and response schema before implementing `facets`.
- Reject invalid values with exit 2 before HTTP.
- Cache by the canonical complete MCP arguments and base URL; do not invent pagination.
- Keep user-tracking arrays out of normalized output.

#### Out of scope

- AI-search endpoints, client-side filtering, fuzzy parsing, dependencies, and guessed contracts.

#### Acceptance criteria

- Every accepted flag traces to verified live behavior.
- Invalid input performs no network request.
- Facets exist only after their exact endpoint contract is verified.
- Offline tests and the opt-in live probe pass.

### PR 8.7 — Browser OAuth login

#### Spec

Use the complete blocked PR 2.3 specification:

- Verify the real browser route, provider behavior, and loopback callback first.
- Implement `hiringcafe auth login --browser` with the standard library only.
- Use a single-use state, PKCE where supported, loopback-only binding, and a bounded timeout.
- Exchange no provider password and persist only the Firebase refresh token.
- Leave no partial session on cancellation or failure.

#### Out of scope

- Headless login, browser-profile credential access, embedded OAuth secrets, and provider automation.

#### Acceptance criteria

- Verified live evidence is recorded before implementation.
- Successful browser login stores the existing session format and `auth status` succeeds.
- Cancelled, expired, malformed, or replayed callbacks write no session.
- No token or credential appears in output or tests.

## Phase 9 — First-party read transport recovery

The anonymous page and raw job-detail routes now receive Cloudflare challenges from the CLI host. This phase moves only public reads to HiringCafe's documented integration interface; it does not infer account or mutation capabilities from that interface.

### PR 9.1 — Official MCP read transport

#### Spec

- Replace `search`, `count`, and `job show` reads with the documented `POST /api/mcp` JSON-RPC `tools/call` interface.
- Use only the verified `search_jobs` and `get_job_details` tools. Keep Firebase auth and saved-job mutation transports separate.
- Normalize the observed Markdown tool responses into the existing agent-facing JSON shape. Reject unrecognized or incomplete response text rather than returning false empty results.
- Use the documented default limit of 10 (upstream maximum 25), one-job-per-company behavior, lack of pagination, per-IP rate limits, and attribution-bearing links.
- Keep the local cache, but use new cache-key namespaces so old SSR/raw-detail entries cannot be mistaken for MCP data.
- Update the opt-in live probe and user documentation to report the new read scope and remaining saved-job-save limitation.

#### Out of scope

- Solving/bypassing Cloudflare challenges, copying browser cookies, changing user agents to evade access controls, or retrying rate-limited MCP POSTs.
- Pagination, filters/facets, account/profile/tracker reads, saved-job writes, resume upload, or alerts.
- Changing the Firebase auth/session format or any authenticated mutation payload.

#### Acceptance criteria

- The live endpoint and both tools are verified from the documented API; tests use synthetic Markdown only and contain no real job or contact data.
- Search uses the documented default limit of 10 (upstream maximum 25); unsupported pages and raw filters fail before HTTP.
- Count handles both a nonempty result-count header and HiringCafe's observed explicit no-results response.
- Job details retain their attribution URL, return a nonempty description, and show a usable page link in human output; unknown tool output fails clearly.
- HTTP 429 is surfaced as rate-limited without automatic POST retry; HTTP and JSON-RPC failures do not print response bodies or credentials.
- Cache entries use distinct MCP keys; normal tests remain offline and the opt-in probe exposes no job data.
- README, changelog, endpoint inventory, and this spec agree on the read-only scope and limitations.

## Phase 10 — Agent integration and usability

This phase packages project-specific agent instructions in the repository so agents can discover supported CLI workflows and respect account and API boundaries.

### PR 10.1 — Shared HiringCafe CLI agent skill

#### Spec

- Add a portable `SKILL.md` under `.agents/skills/hiringcafe-cli/` for agents using the installed CLI or working in this repository.
- Include a versioned capability snapshot: live public reads, session status, and saved-job listing; offline-tested import/logout; unverified fresh email login; broken/blocked save/stage/remove; and unimplemented browser OAuth and advanced features.
- Document installation, command/output examples, cache/storage controls, exit codes, the TTL caveat, and the unresolved DNS issue. Distinguish CLI filter limitations from documented upstream MCP filters.
- Tell agents to check the installed CLI version and command help, use structured output, distinguish errors from empty results, and respect cache/rate-limit behavior.
- Define credential privacy and explicit authorization boundaries for account data and saved-job mutations.
- Require repository contributors to follow `AGENTS.md`, `roadmap.md`, and the corresponding `specs/pr-*/spec.md` before implementation.
- Link to the skill from the README's agent section.

#### Out of scope

- New commands, API endpoints, runtime dependencies, credential access, or changes to CLI behavior.
- Claiming full HiringCafe feature parity, working saved-job mutations, or resolution of the intermittent DNS failure.

#### Acceptance criteria

- A repo-aware agent can find and follow the skill without machine-specific paths or user/account details.
- Skill statements match README and roadmap support status; unsupported features are not presented as implemented.
- No runtime endpoint/API behavior is added; audit evidence and official documentation inform the capability snapshot without another live mutation or login.
- README, skill, roadmap, and this spec pass the repository's documentation and pre-commit checks.
