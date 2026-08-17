# HiringCafe CLI

A private, spec-driven Python CLI for [Hiring Cafe](https://hiringcafe.com/) job search, job details, authentication, and saved-job tracking. It is designed for both human use and autonomous agents, with explicit JSON output and stable exit codes.

## Status

PR 0.1 is implemented: the executable bootstrap and exit-code contract are available.

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

Current commands are intentionally limited to `--help` and `--version`; search and auth commands arrive with their roadmap PRs.

## Repository conventions

- Python code follows [`AGENTS.md`](AGENTS.md) and the roadmap.
- Live network probes are opt-in and never run by default.
- Never commit credentials, Firebase tokens, cookies, real UIDs, emails, or private account data.
