# HiringCafe CLI

A private, spec-driven Python CLI for [Hiring Cafe](https://hiringcafe.com/) job search, job details, authentication, and saved-job tracking. It is designed for both human use and autonomous agents, with explicit JSON output and stable exit codes.

## Status

PR 0.2 and PR 1.1 are implemented: executable bootstrap, exit-code contract, offline SSR parser coverage,
an explicitly opt-in live probe, and the shared anonymous HTTP/SSR client.

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

Normal tests never access the network. Current commands are intentionally limited to `--help`,
`--version`, and `probe`; search and auth commands arrive with their roadmap PRs.

## Repository conventions

- Python code follows [`AGENTS.md`](AGENTS.md) and the roadmap.
- Live network probes are opt-in and never run by default.
- Never commit credentials, Firebase tokens, cookies, real UIDs, emails, or private account data.
