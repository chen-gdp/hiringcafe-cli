# HiringCafe CLI Agent Rules

## Project contract

- `roadmap.md` is the source of truth for scope, verified API behavior, phases, and PR boundaries.
- Every code change must trace to `specs/pr-<id>-<slug>/spec.md`.
- If implementation disproves a roadmap/spec assumption, update the roadmap and spec in the same PR before changing code.
- Do not implement an endpoint merely because it appears in the route appendix. Use only dependencies whose spec says they are verified and usable.
- Keep runtime dependencies empty unless the roadmap and target PR spec explicitly require and justify one.
- Python 3.11–3.14 and the standard library are the default platform.

## Architecture

- Keep business/domain logic independent of HTTP, Firebase, Firestore, CLI parsing, storage, and cache adapters.
- Put each external system behind one narrow module so callers depend on project interfaces rather than transport details.
- Keep functions single-purpose; use guard clauses and early returns instead of deep nesting.
- Prefer composition and small dataclasses over inheritance.
- Normalize at system boundaries; keep output contracts stable once a PR ships them.
- Use streaming or bounded reads when handling large API responses.

## Code style and typing

- Follow strict PEP 8 with a 120-character line limit.
- Type all public functions and public class attributes.
- Prefer built-in generics: `list[str]`, `dict[str, Any]`, `X | None`.
- Order imports: standard library, third-party, local.
- Use `snake_case` for functions and variables, `PascalCase` for classes, and `UPPER_SNAKE_CASE` for constants.
- Document every public module, class, method, and function in Google Python Style:
  concise summary, `Attributes`, `Args`, `Returns`, and `Raises` only when applicable.

## Security boundaries

- Never collect, store, transmit, log, or commit a provider password.
- Never store refresh tokens, ID tokens, cookies, bearer headers, real UIDs, emails, or private saved-job data in fixtures, logs, documentation, tests, or output.
- Store local credentials only in owner-only files using the session format defined by PR 2.1.
- Validate and normalize all external input at CLI, HTTP, Firebase, and Firestore boundaries.
- Never cache or retry authenticated mutations. Follow the cache and retry exclusions in the roadmap exactly.
- Scrub diagnostics before showing HTTP request bodies or response data.

## Testing

- Use pytest with Arrange-Act-Assert structure.
- Name tests `test_<unit>_<condition_or_expected_result>`.
- Include exact `Condition:` and `Expected:` docstrings for nontrivial tests.
- Isolate HTTP/auth/storage behavior behind fakes; do not hit live services in the normal test command.
- Live probes must be explicitly opt-in (for example `LIVE=1`) and must never print credentials or personal data.
- Cover parser failures, invalid input, auth branches, cache expiry, and mutation decision paths without overfitting to full live payloads.

## Common commands

Prefix shell commands with `rtk` when available.

```bash
uv sync
uv run pytest
uv run hiringcafe --help
uv run pre-commit run --all-files
```

Use `rtk` for compact git/file operations:

```bash
rtk git status
rtk git diff
rtk pytest
```
