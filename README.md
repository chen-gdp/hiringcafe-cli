# HiringCafe CLI

Give your AI agent Hiring Cafe superpowers: search jobs, inspect postings, and keep your real Hiring Cafe saved-job board in sync without a browser.

[![PyPI](https://img.shields.io/pypi/v/hiringcafe-cli.svg)](https://pypi.org/project/hiringcafe-cli/)
[![Python](https://img.shields.io/pypi/pyversions/hiringcafe-cli.svg)](https://pypi.org/project/hiringcafe-cli/)
[![CI](https://github.com/chen-gdp/hiringcafe-cli/actions/workflows/ci.yaml/badge.svg)](https://github.com/chen-gdp/hiringcafe-cli/actions/workflows/ci.yaml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

```bash
hiringcafe search "python developer" --jsonl
```

The CLI gives your agent structured access to public jobs and, when authenticated, selected actions on your real Hiring Cafe account. Public search and job details use Hiring Cafe's [documented read-only MCP connector](https://hiringcafe.com/documentation/hiringcafe-claude-connector): each search returns at most 10 jobs, with at most one job per company and no pagination or filters yet. Requests are rate-limited; avoid high-frequency automated polling.

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
- Search returns at most 10 jobs, one per company; pagination and filters are not supported by the current upstream interface.
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
| `hiringcafe auth status` | Check whether a local session exists |
| `hiringcafe auth logout` | Remove the local session |
| `hiringcafe saved-jobs list --json` | List saved jobs |
| `hiringcafe saved-jobs save <objectID>` | Save a job |
| `hiringcafe saved-jobs stage <objectID> --stage applied` | Change a job stage |
| `hiringcafe saved-jobs remove <objectID> --yes` | Remove a saved job |
| `hiringcafe cache purge` | Remove cached anonymous reads |

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

## Saved jobs

These commands modify your real Hiring Cafe account. Review object IDs and confirmation prompts before changing data.

`saved-jobs save` currently depends on an older raw job-hydration endpoint that is returning a Cloudflare challenge from the CLI host. It may fail before saving; the read-only MCP connector does not support saved-job writes or provide the raw object needed by this command. Listing, staging, and removing saved jobs use separate authenticated flows.

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

Public search, job details, authentication, saved-job listing/staging/removal, retries, caching, Python 3.11–3.14 CI, and tagged PyPI releases are implemented. Saved-job save is currently blocked by the challenged raw hydration route. Filters/facets, tracker search, saved-job pagination, and browser OAuth login remain deferred until their upstream contracts are verified.

See [`roadmap.md`](roadmap.md) and [`specs/`](specs/) for the complete implementation status and PR specifications.
