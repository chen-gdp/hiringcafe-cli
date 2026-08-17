# HiringCafe CLI

An unofficial, spec-driven Python CLI for [Hiring Cafe](https://hiringcafe.com/) job search and saved-job tracking. It is designed for people and autonomous agents, with machine-readable JSON output and stable exit codes.

This project is not affiliated with, endorsed by, or supported by Hiring Cafe. Use your own account, respect the service, and expect upstream APIs to change without notice.

## Status

Beta. The documented search, job-detail, authentication, and saved-job workflows are implemented and covered by isolated tests. PR 2.3, the browser OAuth login flow, remains intentionally deferred.

- Product plan and verified endpoint inventory: [`roadmap.md`](roadmap.md)
- Implementation specifications: [`specs/`](specs/)

## Install

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/):

```bash
uv tool install git+https://github.com/chen-gdp/hiringcafe-cli.git
hiringcafe --version
```

Run from a checkout without a global install:

```bash
uv sync
uv run hiringcafe --help
```

## Authenticate

The CLI uses Hiring Cafe’s Firebase email/password login and stores only the returned Firebase refresh token.

```bash
hiringcafe auth login --email you@example.com
hiringcafe auth status --json
hiringcafe auth logout
```

The password is read through hidden input, exchanged once, and discarded. Automation can provide a refresh token through stdin:

```bash
printf '%s\n' "$HIRINGCAFE_REFRESH_TOKEN" | hiringcafe auth import
```

Local data:

| Data | Location | Notes |
|---|---|---|
| Refresh token | `~/.config/hiringcafe-cli/session.json` | owner-only file; removed by logout |
| Anonymous cache | `~/.cache/hiringcafe-cli/cache/v1/` | public search/job data only |

Set `HIRINGCAFE_CONFIG_HOME` or `HIRINGCAFE_CACHE_HOME` to use different roots. Firebase ID tokens and account passwords are never written to disk.

## Search and inspect jobs

```bash
hiringcafe search "python developer" --page 0 --json
hiringcafe search --raw-search-state '{"searchQuery":"python developer"}' --json
hiringcafe search "python developer" --pages 3 --jsonl
hiringcafe count "python developer" --json
hiringcafe job show <objectID> --json
```

## Saved jobs

These commands use your real Hiring Cafe account. Review the object ID and confirmation prompts before mutating data.

```bash
hiringcafe saved-jobs list --json
hiringcafe saved-jobs save <objectID> --stage saved
hiringcafe saved-jobs stage <objectID> --stage interviewing
hiringcafe saved-jobs remove <objectID> --yes
```

Valid stages are `saved`, `applied`, `interviewing`, `offer`, `rejected`, `ghosted`, and `hidden`.

## Performance and retries

Anonymous search/count responses use a 15-minute local TTL cache; job details use 24 hours. Cache status is written to stderr.

```bash
hiringcafe search "python developer" --no-cache
hiringcafe search "python developer" --cache-ttl 3600
hiringcafe cache purge
```

Anonymous GETs retry transport failures, HTTP 408/429, and 5xx twice with bounded jittered backoff. Authenticated mutations are never retried and authenticated responses are never cached.

## Exit codes

| Code | Meaning |
|---:|---|
| `0` | success |
| `1` | transport, HTTP, parsing, or API error |
| `2` | invalid arguments or search state |
| `3` | rate limited |
| `4` | no stored credential |
| `5` | stored credential rejected |
| `6` | write conflict or prerequisite missing |

## Development

```bash
uv sync
uv run pytest
uv run hiringcafe --help
uv run pre-commit run --all-files
```

Normal tests do not access the network. Run the verified anonymous endpoint probe explicitly:

```bash
LIVE=1 uv run hiringcafe probe
```

## Repository conventions

- Python code follows [`AGENTS.md`](AGENTS.md) and the roadmap.
- Every implementation change traces to `specs/pr-*/spec.md`.
- Live network probes are opt-in and never run by default.
- Never commit credentials, Firebase tokens, cookies, real UIDs, emails, or private account data.
