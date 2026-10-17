# Changelog

## Unreleased

- Initial unofficial Python CLI for Hiring Cafe job search, job details, authentication, saved-job tracking, anonymous-read caching, retries, and stable agent-oriented JSON output.
- Added tagged PyPI release automation using GitHub Trusted Publishing.

## 0.2.1 — 2026-10-18

- Respect requested cache freshness, including zero TTL, and reject negative TTL before I/O. Old cache entries without write timestamps require a fresh fetch.
- Retry transient public-read DNS/connection failures and HTTP 408/5xx at most twice within a 30-second caller deadline. Do not retry HTTP 403/429, permanent DNS failures, certificate errors, malformed responses, or authenticated mutations.
- Add safe DNS diagnostics without exposing arbitrary exception contents. Local and chen-lappy fresh searches passed; the original intermittent environment failure remains unexplained.
- Repair savedJobs document paths, atomic history transforms, timestamp types, hidden-state transitions, and concurrency guards. Transport regressions pass, but live account mutations remain unverified; saving is still blocked by raw hydration and public/raw ID mapping requirements.
- Add the shared agent skill and accurate capability/roadmap documentation. Structured filters and browser OAuth are not part of this patch.

## 0.2.0 — 2026-10-11

- Restore public search, count, and job-detail reads through HiringCafe's documented read-only MCP connector.
- Remove unsupported pagination assumptions and document the saved-job-save limitation caused by the challenged raw hydration route.

## 0.1.5

- Made `hiringcafe --version` read the installed package metadata so it matches PyPI releases.

## 0.1.4

- Staged release artifacts so PyPI receives only distributions while GitHub retains checksums.

## 0.1.3

- Kept the checksum manifest out of the PyPI upload directory while retaining it in GitHub release artifacts.

## 0.1.2

- First PyPI release.
- Fixed release checksum verification and aligned the workflow filename with PyPI Trusted Publishing.
