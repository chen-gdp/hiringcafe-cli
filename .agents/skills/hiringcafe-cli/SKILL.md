---
name: hiringcafe-cli
description: Use the HiringCafe CLI for supported public job search and details, or explicitly requested actions on saved jobs. Check current project docs and do not imply unsupported features work.
---

# HiringCafe CLI

Use this skill when an agent needs to operate the HiringCafe CLI or make a change to this repository.

## Check current support first

- Check `hiringcafe --version` and the relevant command's `--help`; installed versions may differ from this checkout.
- For current feature status and examples, consult `README.md` and `roadmap.md` in the repository.
- Prefer `--json` or `--jsonl` for automation. Parse stdout separately from stderr, and never treat a nonzero exit or API error as an empty result.
- Respect service rate limits. Use `--no-cache` only when fresh anonymous data is needed.

## Supported workflows and limits

- Public `search`, `count`, and `job show` use HiringCafe's documented read-only MCP interface. Search returns at most 10 results, at most one per company; filtering and pagination are unavailable through this interface.
- Auth commands support email login, refresh-token import, status, and logout. Authenticated saved-job commands support listing, changing stage, and removing jobs, subject to the user's existing session.
- `saved-jobs save` is present but may fail because its raw job-hydration endpoint is challenged from the CLI host. Do not bypass the challenge, reuse browser cookies, or repeatedly retry it.
- Filters/facets, tracker search, saved-job pagination, custom boards, notes/tags/journal, alerts, resume upload, and browser OAuth are not supported unless the current README and roadmap say otherwise.

## Account and credential safety

- Reuse an existing login by checking `hiringcafe auth status`. If authentication is needed, have the user complete login in a secure terminal; never ask them to paste a password, refresh/ID token, cookie, or bearer token into chat.
- Do not inspect `.env`, credential files, browser profiles, or cookies. Never print or persist credentials in logs, fixtures, tests, or documentation.
- Saved-job data is private. Return only the fields needed for the user's request.
- `stage` and `remove` change the user's real account. Perform them only after the user explicitly requests the specific change; verify the target job and intended stage first. Treat removal as destructive and require confirmation.
- Do not automatically retry authenticated mutations or hide auth/write errors.

## Repository changes

- Read `AGENTS.md`, `roadmap.md`, and the matching `specs/pr-*/spec.md` before implementation.
- Every implementation change must have a spec and follow the roadmap. If verification disproves an API or behavior assumption, update the spec and roadmap in the same PR.
- Keep normal tests offline; use live probes only when explicitly relevant and opt-in.
