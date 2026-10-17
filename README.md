# HiringCafe CLI

Give your AI agent a Hiring Cafe command line: discover jobs, read full postings, and inspect your saved-job list.

[![PyPI](https://img.shields.io/pypi/v/hiringcafe-cli.svg)](https://pypi.org/project/hiringcafe-cli/)
[![Python](https://img.shields.io/pypi/pyversions/hiringcafe-cli.svg)](https://pypi.org/project/hiringcafe-cli/)
[![CI](https://github.com/chen-gdp/hiringcafe-cli/actions/workflows/ci.yaml/badge.svg)](https://github.com/chen-gdp/hiringcafe-cli/actions/workflows/ci.yaml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

```bash
hiringcafe search "python developer" --jsonl
```

The CLI gives your agent structured access to public jobs and, when authenticated, selected actions on your real Hiring Cafe account. Public search and job details use Hiring Cafe's [documented read-only MCP connector](https://hiringcafe.com/documentation/hiringcafe-claude-connector): each search returns at most 10 jobs, with at most one job per company and no pagination or filters yet. Requests are rate-limited; avoid high-frequency automated polling.

**v0.2.1 recovery:** cache freshness overrides and bounded public-read retries are repaired. Saved-job Firestore paths, history, timestamps, visibility, and conflict guards are repaired with transport tests, but account mutations have not passed a live roundtrip. Saving still needs verified raw hydration. Browser OAuth and structured CLI filters remain unimplemented. See the [current recovery status](roadmap.md#current-recovery-status--cli-v021) for evidence and limits.

> **Unofficial client.** This project is not affiliated with, endorsed by, or supported by Hiring Cafe. Use your own account, respect the service, and expect upstream APIs to change.

## Contents

- [Install](#install)
- [For agents](#for-agents)
- [Commands](#commands)
- [Authentication](#authentication)
- [Saved jobs](#saved-jobs)
- [Caching and local data](#caching-and-local-data)
- [Exit codes](#exit-codes)
- [Development](#development)
- [Project status](#project-status)

## Install

HiringCafe CLI is published on PyPI and supports Python 3.11–3.14 with no runtime dependencies.

Install it as a persistent CLI tool:

```bash
uv tool install hiringcafe-cli
```

Or, if you prefer pipx:

```bash
pipx install hiringcafe-cli
```

Run it once without installing anything:

```bash
uvx --from hiringcafe-cli hiringcafe --version
```

Verify the installed version:

```bash
hiringcafe --version
```

## For agents

Agents working in this repository should read the shared [HiringCafe CLI skill](.agents/skills/hiringcafe-cli/SKILL.md)
for supported workflows, safety rules, and known limitations.

The smallest useful loop is install, search, and consume machine-readable output:

```bash
uv tool install hiringcafe-cli
hiringcafe search "python developer" --page 0 --json
```

For a fresh result, bypass the anonymous-read cache:

```bash
hiringcafe search "python developer" --no-cache --json
```

Stream the returned jobs as one JSON object per line (up to 10 results):

```bash
hiringcafe search "python developer" --jsonl
```

Extract the normalized jobs from one JSON page:

```bash
hiringcafe search "python developer" --page 0 --json | jq -c '.result.jobs[]'
```

Ask only for the result count:

```bash
hiringcafe count "python developer" --json
```

Import an existing Firebase refresh token without an interactive password prompt:

```bash
printf '%s\n' "$HIRINGCAFE_REFRESH_TOKEN" | hiringcafe auth import
hiringcafe saved-jobs list --json
```

Agent automation contract:

- JSON success output goes to stdout; diagnostics and cache notices go to stderr.
- Stable exit codes describe transport, input, rate-limit, auth, and conflict outcomes.
- Provider passwords and Firebase ID tokens are never written to disk.
- Authenticated mutations are never retried or cached.
- Anonymous search/count responses use a 15-minute cache; job details use 24 hours.
- Search returns at most 10 jobs, one per company; the CLI does not expose pagination or upstream structured filters.
- The CLI connects to MCP itself; public reads require neither a login nor a separate MCP plugin.
- Public reads retry transient DNS/connection failures and HTTP 408/5xx at most twice within a 30-second caller deadline. HTTP 403/429, permanent DNS failures, certificate errors, malformed responses, and authenticated mutations do not retry.
- DNS errors are network failures, not empty results. Retries do not repair host DNS configuration; the reported intermittent failure remains unexplained.
- Invalid arguments fail before a network request is made.

## Commands

| Command | Purpose |
|---|---|
| `hiringcafe search "query" --json` | Search jobs and print structured JSON |
| `hiringcafe search "query" --jsonl` | Stream up to 10 search results as JSON Lines |
| `hiringcafe count "query" --json` | Print only the result count |
| `hiringcafe job show <objectID> --json` | Inspect one job posting |
| `hiringcafe auth login --email you@example.com` | Authenticate interactively |
| `hiringcafe auth import` | Import an existing Firebase refresh token |
| `hiringcafe auth status --json` | Verify that the stored credential can refresh |
| `hiringcafe auth logout` | Remove the local session |
| `hiringcafe saved-jobs list --json` | List saved jobs |
| `hiringcafe saved-jobs list --stage applied --json` | List up to 20 jobs in one stage |
| `hiringcafe saved-jobs save <objectID>` | Blocked on verified raw hydration; see below |
| `hiringcafe saved-jobs stage <objectID> --stage applied` | Firestore repair tested; live flow unverified |
| `hiringcafe saved-jobs remove <objectID> --yes` | Document-read repair tested; live flow unverified |
| `hiringcafe cache purge` | Remove cached anonymous reads |
| `LIVE=1 hiringcafe probe` | Verify live public search/details only |

Every command supports `--help`, for example:

```bash
hiringcafe search --help
hiringcafe saved-jobs save --help
```

## Authentication

For human use, log in with your Hiring Cafe email:

```bash
hiringcafe auth login --email you@example.com
hiringcafe auth status
```

The password is read from hidden input (or `HIRINGCAFE_PASSWORD` for automation), exchanged once for Firebase credentials, and only the refresh token is stored.

For automation, import a refresh token that you already hold:

```bash
printf '%s\n' "$HIRINGCAFE_REFRESH_TOKEN" | hiringcafe auth import
```

The CLI stores only the refresh token in an owner-only local session file. It does not store your password or short-lived Firebase ID token. Browser OAuth login is intentionally deferred until its real provider and loopback callback behavior can be verified.

The latest audit verified existing-session refresh, not a new email/password login. Token import and logout have offline test coverage. Logging into the website does not automatically authenticate the CLI.

## Saved jobs

`saved-jobs list` reads your account and returns at most 20 records. It excludes hidden jobs unless requested with `--stage hidden`; saved-job pagination is not implemented.

**Full mutation-command support is not yet verified.** v0.2.1 repairs the missing `savedJobs/` collection, atomic history/timestamp encoding, hidden-state changes, and guarded stage writes. Offline transport tests and a disposable hidden-record Firestore create/read/history/conflict/cleanup check passed. The full commands, marketplace synchronization, and website rendering still need a live roundtrip. Save's legacy hydration returns HTTP 403; the read-only MCP connector does not provide writes or a raw object proven compatible with the website.

Public search IDs and raw saved-job `objectID` values can differ. Use an existing saved record's `id` for an explicitly requested stage/removal; do not guess the public-to-raw mapping or run mutations as diagnostic probes. Partial failures can leave Firestore and marketplace state out of sync—inspect state before another mutation.

The following syntax exists, subject to those limits:

```bash
hiringcafe saved-jobs save <objectID> --stage saved
hiringcafe saved-jobs stage <objectID> --stage interviewing
hiringcafe saved-jobs remove <objectID> --yes
```

Valid stages are `saved`, `applied`, `interviewing`, `offer`, `rejected`, `ghosted`, and `hidden`.

## Caching and local data

| Data | Location | Notes |
|---:|---|---|
| Refresh token | `~/.config/hiringcafe-cli/session.json` | Owner-only file; removed by logout |
| Anonymous cache | `~/.cache/hiringcafe-cli/cache/v1/` | Public search and job data only |

Set `HIRINGCAFE_CONFIG_HOME` or `HIRINGCAFE_CACHE_HOME` to use different roots.

```bash
hiringcafe search "python developer" --no-cache
hiringcafe search "python developer" --cache-ttl 3600
hiringcafe cache purge
```

Authenticated saved-job operations are never cached.

`--cache-ttl` enforces both the requested maximum age and the entry's original expiry. Zero TTL always fetches fresh data without storing it; negative TTL exits 2 before cache/network access. Older entries without verifiable write times are discarded on their next read. A longer TTL cannot extend an existing entry's original expiry.

`--no-cache` or `HIRINGCAFE_NO_CACHE=1` bypasses cache reads and writes. A normal cache miss also makes a network request; neither mode fixes DNS.

## Exit codes

| Code | Agent action |
|---:|---|
| `0` | Success |
| `1` | Transport, HTTP, parsing, or API error; inspect stderr |
| `2` | Invalid arguments or search state; fix the request |
| `3` | Rate limited; wait and retry |
| `4` | No stored credential; authenticate first |
| `5` | Stored credential rejected; re-authenticate |
| `6` | Write conflict or prerequisite missing; refresh state |

## Development

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/chen-gdp/hiringcafe-cli.git
cd hiringcafe-cli
uv sync
uv run pytest
uv run hiringcafe --help
uv run pre-commit run --all-files
```

Normal tests do not access the network. The verified anonymous endpoint probe is opt-in:

```bash
LIVE=1 uv run hiringcafe probe
```

Every implementation change traces to `specs/pr-*/spec.md` and the roadmap. Never commit credentials, Firebase tokens, cookies, real UIDs, emails, or private account data.

## Project status

Public search/count/details, existing-session authentication, and saved-job listing passed live checks. v0.2.1 adds cache/DNS resilience and Firestore repairs; saving still needs a verified hydration replacement, and live account mutations remain unverified. The original intermittent DNS cause is unresolved. Passing offline tests does not establish that account writes work. Python 3.11–3.14 CI and tagged PyPI releases are implemented.

Structured filters are documented upstream but not exposed by this CLI; facets, tracker search/details, search/saved-job pagination, boards, notes/tags/journal, alerts, resume upload, and browser OAuth remain unimplemented. See the shared skill for command/output guidance and the versioned capability snapshot.

See [`roadmap.md`](roadmap.md) and [`specs/`](specs/) for the complete implementation status and PR specifications.
