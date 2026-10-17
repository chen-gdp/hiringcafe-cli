---
name: hiringcafe-cli
description: Install and operate the HiringCafe CLI for public job search, job details, authentication, and saved-job listing. Consult its versioned support limits before account mutations or troubleshooting.
---

# HiringCafe CLI

Use this skill to operate the installed CLI. For repository changes, also follow the contributor guidance below.

## Install and check the version

Requires Python 3.11–3.14. If the command is missing, install it with `uv tool install hiringcafe-cli` (or `pipx install hiringcafe-cli`). For a one-off invocation, use `uvx --from hiringcafe-cli hiringcafe --version`.

```bash
hiringcafe --version
hiringcafe --help
hiringcafe search --help
```

Check the relevant subcommand's help when using a different version. The CLI itself connects to HiringCafe's MCP endpoint over HTTPS; no separate MCP plugin or account is needed for public reads.

`HIRINGCAFE_BASE_URL` overrides the HTTPS service base for testing. Keep the default `https://hiringcafe.com` for normal use; authenticated marketplace requests also use that base, so never point it at an untrusted service.

## Capability snapshot

CLI **v0.2.0**, audited **2026-10-17**, documented **2026-10-18**. A successful check is evidence for that run, not a guarantee of future network availability. Use the repository's current [roadmap](../../../roadmap.md) and [README](../../../README.md) when assessing later releases.

| Capability | Status and limits |
|---|---|
| `search`, `count`, `job show`; JSON/JSONL | Live-verified. Search returns at most 10 jobs, at most one per company. Count can exceed the number returned. |
| `auth status` and existing-session refresh | Live-verified; this does not verify a fresh login flow. |
| `saved-jobs list` | Live-verified, at most 20 records. `--stage` exists and has offline coverage; each stage was not live-tested. Default listing excludes hidden jobs. |
| `auth import`, `auth logout` | Offline-tested; the audit did not replace/delete real credentials. |
| Email/password `auth login` | Implemented; fresh login was not live-tested in this audit. |
| `saved-jobs save` | Blocked/broken: raw hydration returned HTTP 403; document paths and history serialization also contain defects. |
| `saved-jobs stage`, `saved-jobs remove` | Broken document-read prerequisite: requests omit the `savedJobs/` collection. Stage changes also have history/hidden-state defects. |
| Cache/purge | Cache hits and isolated purge verified; `--no-cache` passes offline coverage. TTL override caveat below. |
| `probe` | Live public search/detail probe verified; does not verify auth or mutations. |
| Browser OAuth and advanced features | Unimplemented: structured filters/facets, search/saved-job pagination, tracker search/details, boards, notes/tags/journal, alerts, resume upload. |

The upstream [MCP documentation](https://hiringcafe.com/documentation/hiringcafe-claude-connector) describes structured filters, but this CLI sends only search text and a fixed limit. A country or salary in the query is not evidence that the corresponding structured filter was applied. Never present returned jobs as a complete result set.

Do not describe v0.2.0 mutations as working or run them as diagnostic probes. For a requested mutation, explain the known blocker; recheck support after a verified implementation fix. Never bypass a challenge or substitute an unverified write endpoint.

## Commands and output

```bash
hiringcafe search "python developer" --json
hiringcafe search "python developer" --jsonl
hiringcafe count "python developer" --json
hiringcafe job show <objectID> --json
hiringcafe auth status --json
hiringcafe saved-jobs list --json
hiringcafe saved-jobs list --stage applied --json
hiringcafe cache purge
LIVE=1 hiringcafe probe
```

Replace `<objectID>` with a search result's `id`; do not use arbitrary words as IDs. Preserve returned application and HiringCafe attribution links.

- `search --json`: jobs in `result.jobs`, total in `result.totalCount`, `paginationSupported: false` inside `result`.
- `search --jsonl`: one job object per line, without an envelope. Choose either JSON or JSONL.
- `count --json`: `count`; `job show --json`: `job`; `saved-jobs list --json`: `jobs`; `auth status --json`: `authenticated`. JSON envelopes have `version: 1`.
- Only these commands accept `--json`; only search accepts `--jsonl`. Login/import/logout, mutations, cache purge, and probe emit human-readable output.
- Read exit status before parsing stdout. Diagnostics/cache notices go to stderr. `auth status --json` with no session emits `authenticated: false` and exits 4.
- Search accepts only `--page 0 --pages 1`. Search/count accept `--raw-search-state '{"searchQuery":"python"}'` as an alternative to positional query text; other fields are rejected.
- Saved-job stages: `saved`, `applied`, `interviewing`, `offer`, `rejected`, `ghosted`, `hidden`. Use `list --stage hidden` to request hidden jobs.
- Mutation syntax exists but is broken in this snapshot: `saved-jobs save <objectID> [--stage saved]`, `saved-jobs stage <objectID> --stage applied`, `saved-jobs remove <objectID> [--yes]`.
- `probe` makes live public requests only with `LIVE=1`. Without it, exit 0 means skipped, not verified. Run a probe only when live verification is relevant; avoid repetitive polling.

## Authentication and local data

Reuse the session with `auth status --json`. If login is needed, have the user run `hiringcafe auth login --email <email>` in their secure terminal. It accepts a HiringCafe email/password credential through hidden input (or `HIRINGCAFE_PASSWORD`); it is not Google/Microsoft browser OAuth. Never request a provider password in chat.

`hiringcafe auth import` reads a refresh token from stdin, falling back to `HIRINGCAFE_REFRESH_TOKEN` after empty input. For an already securely provisioned environment variable, `hiringcafe auth import </dev/null` avoids waiting on stdin. Do not obtain tokens by inspecting browser profiles. `auth logout` deletes the local session; it does not log out the website.

Only the refresh token is persisted in an owner-only session file; passwords and short-lived ID tokens are not persisted by the CLI.

| Data | Default path | Override |
|---|---|---|
| Session | `~/.config/hiringcafe-cli/session.json` | `HIRINGCAFE_CONFIG_HOME` selects the directory containing `session.json` |
| Public cache | `~/.cache/hiringcafe-cli/cache/v1/` | `HIRINGCAFE_CACHE_HOME` selects the root containing `cache/v1/` |

Search/count share a 900-second cache; job details use 86400 seconds. A valid hit avoids the network; a miss/expiry requires it. `--no-cache` on search/count/job show bypasses reads and writes; any nonempty `HIRINGCAFE_NO_CACHE` does the same. Authenticated operations are never cached.

`--cache-ttl SECONDS` sets expiry for newly written entries, but v0.2.0 ignores it when reading an existing entry, even with zero. Use `--no-cache` for freshness. `cache purge` removes the selected cache's entries; do not routinely purge a user's cache to diagnose DNS.

## Errors and DNS

| Exit | Agent response |
|---|---|
| 0 | Success, subject to the probe skip exception above |
| 1 | Inspect stderr: transport, HTTP, parse, or API failure; never report it as zero matches |
| 2 | Correct arguments; unsupported filters/pages also use this code |
| 3 | HTTP 429 from the web transport; wait before another request and respect Retry-After when available |
| 4 | No stored credential; public reads can still run |
| 5 | Credential rejected; user reauthentication is needed |
| 6 | Missing write prerequisite/conflict; inspect state, do not blindly repeat a mutation |

`mcp transport failed: ... Name or service not known` means name resolution failed before the service returned a response. The reported intermittent failure remains unresolved. Compare the same command in the failing execution environment and the user's normal terminal; record exit/error without secrets. OAuth, changing query text, or `--no-cache` does not repair DNS. Do not infer an empty result or a bad credential from this error.

MCP public requests have no automatic retry, although a separate legacy GET retry policy exists. If a public read appears transiently interrupted, one bounded retry is reasonable; stop on repeated failure and report the environment evidence. Never automatically retry authenticated mutations or repeatedly retry an HTTP 403 challenge.

## Account and credential safety

- Never ask the user to paste a password, refresh/ID token, cookie, or bearer token into chat.
- Do not inspect `.env`, credential files, browser profiles, or cookies. Never print or persist credentials in logs, fixtures, tests, or documentation.
- Saved-job data is private. Return only the fields needed for the user's request.
- After mutation support is repaired, act only on the user's authorized target and change. `remove --yes` bypasses the interactive prompt; use it only when that removal is already authorized.
- Do not automatically retry authenticated mutations or hide auth/write errors.

## Repository changes

- Read `AGENTS.md`, `roadmap.md`, and the matching `specs/pr-*/spec.md` before implementation.
- Every implementation change must have a spec and follow the roadmap. If verification disproves an API or behavior assumption, update the spec and roadmap in the same PR.
- Keep normal tests offline; use live probes only when explicitly relevant and opt-in.
