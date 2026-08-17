# HiringCafe CLI

A private, spec-driven Python CLI for [Hiring Cafe](https://hiringcafe.com/) job search, job details, authentication, and saved-job tracking. It is designed for both human use and autonomous agents, with explicit JSON output and stable exit codes.

## Status

Documentation and API verification are complete. Implementation has not started.

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
```

The CLI entry point is configured. It currently raises `NotImplementedError` because PR 0.1 has not been implemented; useful commands arrive with later roadmap phases.

## Repository conventions

- Python code follows [`AGENTS.md`](AGENTS.md) and the roadmap.
- Live network probes are opt-in and never run by default.
- Never commit credentials, Firebase tokens, cookies, real UIDs, emails, or private account data.
