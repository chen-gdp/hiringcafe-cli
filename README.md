# HiringCafe CLI

Give your AI agent Hiring Cafe superpowers: search jobs, inspect postings, and keep your Hiring Cafe saved-job board in sync without a browser.

```bash
hiringcafe search "python developer" --pages 3 --jsonl
```

The result is stable JSON/JSONL, explicit exit codes, cached anonymous reads, bounded retries, and authenticated actions against your real Hiring Cafe account.

> **Unofficial client.** This project is not affiliated with, endorsed by, or supported by Hiring Cafe. Use your own account, respect the service, and expect upstream APIs to change.

## For agents

Agents can install and verify the CLI in three commands:

```bash
uv tool install git+https://github.com/chen-gdp/hiringcafe-cli.git
hiringcafe --version
hiringcafe search "python developer" --page 0 --json
```

Feed the output directly to your tooling:

```bash
# One JSON object per page
hiringcafe search "python developer" --pages 3 --jsonl

# One line per job
hiringcafe search "python developer" --pages 3 --json | jq -c '.jobs[]'

# Machine-readable result count
hiringcafe count "python developer" --json
```

Import an existing Firebase refresh token without an interactive password prompt:

```bash
printf '%s\n' "$HIRINGCAFE_REFRESH_TOKEN" | hiringcafe auth import
hiringcafe saved-jobs list --json
```

Safe automation contract:

- JSON success output goes to stdout; cache diagnostics go to stderr.
- Stable exit codes describe transport, input, rate-limit, auth, and conflict outcomes.
- Passwords and Firebase ID tokens are never written to disk.
- Authenticated mutations are never retried or cached.
- Anonymous search/count responses use a 15-minute cache; job details use 24 hours.

## For humans

```bash
hiringcafe auth login --email you@example.com
hiringcafe search "python developer" --page 0 --json
hiringcafe job show <objectID> --json
hiringcafe saved-jobs list --json
hiringcafe auth logout
```

The password is read through hidden input, exchanged once, and discarded.

## Saved jobs

These commands modify your real Hiring Cafe account. Review object IDs and confirmation prompts before changing data.

```bash
hiringcafe saved-jobs save <objectID> --stage saved
hiringcafe saved-jobs stage <objectID> --stage interviewing
hiringcafe saved-jobs remove <objectID> --yes
```

Valid stages are `saved`, `applied`, `interviewing`, `offer`, `rejected`, `ghosted`, and `hidden`.

## Local data

| Data | Location | Notes |
|---|---|---|
| Refresh token | `~/.config/hiringcafe-cli/session.json` | owner-only file; removed by logout |
| Anonymous cache | `~/.cache/hiringcafe-cli/cache/v1/` | public search/job data only |

Set `HIRINGCAFE_CONFIG_HOME` or `HIRINGCAFE_CACHE_HOME` to use different roots.

```bash
hiringcafe search "python developer" --no-cache
hiringcafe search "python developer" --cache-ttl 3600
hiringcafe cache purge
```

## Exit codes

| Code | Agent action |
|---:|---|
| `0` | success |
| `1` | transport, HTTP, parsing, or API error; inspect stderr |
| `2` | invalid arguments or search state; fix the request |
| `3` | rate limited; wait and retry |
| `4` | no stored credential; authenticate first |
| `5` | stored credential rejected; re-authenticate |
| `6` | write conflict or prerequisite missing; refresh state |

## Development

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
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

Beta status: search, job details, authentication, and saved-job workflows are implemented. Browser OAuth login remains intentionally deferred. See [`roadmap.md`](roadmap.md) and [`specs/`](specs/).
