# HiringCafe CLI

A private, spec-driven Python CLI for [Hiring Cafe](https://hiringcafe.com/) job search, job details, authentication, and saved-job tracking. It is designed for both human use and autonomous agents, with explicit JSON output and stable exit codes.

## Status

PRs 0.2 through 1.2 are implemented: executable bootstrap, exit-code contract, offline SSR parser coverage,
an explicitly opt-in live probe, shared anonymous HTTP/SSR client, and verified search-state contract.

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
hiringcafe auth logout
```

Saved-job commands are implemented in stacked roadmap PRs through PR 3.5.

Normal tests never access the network. Current commands are intentionally limited to `--help`,
`--version`, and `probe`; search and auth commands arrive with their roadmap PRs.

## Repository conventions

- Python code follows [`AGENTS.md`](AGENTS.md) and the roadmap.
- Live network probes are opt-in and never run by default.
- Never commit credentials, Firebase tokens, cookies, real UIDs, emails, or private account data.
