# PR 11.4 — Public-read DNS and transport resilience

## Verified dependency and diagnosis

Only allowlisted search_jobs/get_job_details at POST /api/mcp are read-only per official HiringCafe documentation. The reported name-resolution failure precedes any HTTP response. Latest local/remote live checks worked; that does not establish the failing execution environment's root cause.

## Scope

- Retry only transient public-read transport failures and HTTP 408/5xx with bounded existing jitter/backoff, at most two retries, and a monotonic total request/retry deadline (30 seconds by default).
- Keep HTTP 429/403, invalid JSON/RPC/content, TLS certificate validation failures, and permanently invalid configuration non-retryable. Respect existing rate-limit exit 3; do not hammer rate limits.
- Preserve no retries for auth, Firestore, and marketplace mutations.
- Provide credential-safe diagnostics distinguishing DNS resolution from other transport failures and suggesting checking the same command in the actual execution environment. Never serialize arbitrary URLError content, request bodies, tokens, or URLs with user input.
- Compare hostname resolution and fresh public reads locally and on chen-lappy through the relevant execution paths; record only sanitized results and limits of diagnosis.
- Tests simulate DNS-then-success, exhaustion, timeout/deadline, HTTP errors, certificate errors, malformed payloads, and mutation single-attempt behavior with fake clocks/sleep.

## Acceptance

Transient resolution can recover without user retries; persistent failures terminate within the bounded budget with exit 1 and useful safe diagnostics. Current inability to reproduce the original sandbox failure is documented; resilience does not claim to repair host networking.
