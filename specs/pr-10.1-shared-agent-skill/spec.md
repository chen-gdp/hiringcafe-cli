# PR 10.1 — Shared HiringCafe CLI agent skill

## Purpose

Make supported HiringCafe CLI workflows and their safety boundaries discoverable to agents working in this repository, without relying on a maintainer's private Codex skill or machine-specific setup.

## Verified API dependency

This documentation-only PR adds no API dependency and calls no endpoint. It describes only the CLI capabilities and limitations already recorded in `README.md` and `roadmap.md`. In particular, public search/count/job details use the documented read-only MCP transport; this PR does not add or infer authenticated API behavior.

## Scope

- Add `.agents/skills/hiringcafe-cli/SKILL.md` with portable usage, support boundaries, and account-safety instructions.
- Link the skill from the README's “For agents” section.
- Add Phase 10.1 and its status row to the roadmap.

## Out of scope

- CLI implementation, new endpoints, dependency changes, installation automation, or live API probes.
- Claiming support for filters/facets, tracker search, saved-job pagination, boards, notes/tags/journal, alerts, resume upload, or browser OAuth.
- Treating the challenged `saved-jobs save` hydration request as a supported working flow.

## Acceptance criteria

- The skill lives in the repository and has no references to a particular user's machine, account, or credentials.
- It directs agents to check the installed CLI's version/help and consult the current README/roadmap instead of treating a version-specific capability snapshot as permanent.
- It documents structured output, errors/rate limits/cache, auth privacy, private saved-job data, and explicit authorization for mutations.
- README and roadmap link/explain the skill consistently; no runtime behavior changes.
- Documentation validation, pre-commit, and `git diff --check` pass.
