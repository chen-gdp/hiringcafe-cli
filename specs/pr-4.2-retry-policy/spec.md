# PR 4.2 — Retry policy

## API dependency

Applies only to idempotent anonymous GETs:

| Route | Retry allowed |
|---|---|
| `GET /?searchState=...&page=...` | Yes |
| `GET /api/job-description?id=...` | Yes |

No authenticated saved-job mutation may be retried.

Verification result: retryable status classification is usable for the two anonymous GET routes. No mutation endpoint has a verified idempotency key, so mutation retry remains disabled.

## Scope

- Retry transport failures, HTTP 408, 429, and 5xx.
- Use bounded exponential backoff with jitter.
- Keep retry count and total timeout bounded.
- Preserve rate-limit exit code 3 after retries.
- Name the endpoint in timeout diagnostics.

## Non-goals

- No saved-job mutation retry.
- No background queue.
- No persistent cache.

## Acceptance criteria

- Configurable retry count and timeout remain bounded.
- 429 exits 3 after retry budget.
- Mutating endpoints remain non-retried.
- Tests cover retryable and non-retryable classifications.

## Traceability

Source: `roadmap.md`, Phase 4, PR 2.
