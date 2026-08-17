# HiringCafe CLI

A private, spec-driven Python CLI for [Hiring Cafe](https://hiringcafe.com/) job search, job details, authentication, and saved-job tracking. It is designed for both human use and autonomous agents, with explicit JSON output and stable exit codes.

## Status

Roadmap PRs 0.1 through 5.1 are implemented as a draft stack. PR 2.3 (browser OAuth flow) remains intentionally deferred until its route is verified.

- Product plan and verified endpoint inventory: [`roadmap.md`](roadmap.md)
- Implementation specifications: [`specs/`](specs/)
- Every code PR must implement the matching `specs/pr-*/spec.md` and update the roadmap/spec first if the live API differs.

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)

The initial runtime has no third-party dependencies.

## Development

```bash
uv sync
uv run pytest
uv run hiringcafe --help
uv run hiringcafe --version
```

Run the verified anonymous endpoint probe explicitly:

```bash
LIVE=1 uv run hiringcafe probe
```

Search one page:

```bash
uv run hiringcafe search "python developer" --page 0 --json
uv run hiringcafe search --raw-search-state '{"searchQuery":"python developer"}' --json
```

Count matching jobs:

```bash
uv run hiringcafe count "python developer"
uv run hiringcafe count "python developer" --json
```

Inspect a job:

```bash
uv run hiringcafe job show <objectID> --json
```

Authenticate using Firebase. The CLI stores only a refresh token in an owner-only file:

```bash
hiringcafe auth login --email you@example.com
printf '%s\n' "$HIRINGCAFE_REFRESH_TOKEN" | hiringcafe auth import
hiringcafe auth status --json
hiringcafe saved-jobs list --json
hiringcafe saved-jobs save <objectID> --stage saved
hiringcafe saved-jobs stage <objectID> --stage interviewing
hiringcafe saved-jobs remove <objectID> --yes
hiringcafe search "python developer" --pages 3 --jsonl
hiringcafe auth logout

Anonymous search and job-detail GETs retry transport failures, HTTP 408/429, and 5xx twice with bounded jittered backoff. Authenticated mutations never retry.

Anonymous search/count (15-minute TTL) and job detail (24-hour TTL) responses use an owner-only local cache. Use `--no-cache` to bypass it, `--cache-ttl <seconds>` to override it for one command, or run `hiringcafe cache purge`.

Normal tests never access the network.

## Repository conventions

- Python code follows [`AGENTS.md`](AGENTS.md) and the roadmap.
- Live network probes are opt-in and never run by default.
- Never commit credentials, Firebase tokens, cookies, real UIDs, emails, or private account data.
