# PR 10.1 — Shared HiringCafe CLI agent skill

## Purpose

Make supported HiringCafe CLI workflows and their safety boundaries discoverable to agents working in this repository, without relying on a maintainer's private Codex skill or machine-specific setup.

## Verified API dependency

This documentation-only PR adds no runtime API dependency. Public search/count/job details use the documented read-only MCP transport. The capability correction recorded on 2026-10-18 incorporates the 2026-10-17 audit: live public reads, session refresh, and saved-job listing succeeded; legacy hydration returned HTTP 403; an existing saved-job document was readable through the correct collection path but not the path constructed by the CLI. Synthetic request inspection also exposed malformed history writes, missing hidden-state updates, and ineffective TTL overrides for existing cache entries. No live account mutations were performed.

HiringCafe's [official connector documentation](https://hiringcafe.com/documentation/hiringcafe-claude-connector), checked on 2026-10-18, documents structured filters. These are not exposed by CLI v0.2.0; individual filter behavior was not live-tested in this audit. Correct the obsolete upstream-filter claim without implementing new API behavior.

## Scope

- Add `.agents/skills/hiringcafe-cli/SKILL.md` with portable usage, support boundaries, and account-safety instructions.
- Link the skill from the README's “For agents” section.
- Add Phase 10.1 and its status row to the roadmap.
- Include installation, every current command family, output shapes, cache controls, storage paths, and actionable exit-code/DNS guidance.
- Distinguish live-verified, offline-tested, implemented-but-unverified, broken, and unimplemented capabilities for v0.2.0.
- Correct README and roadmap support claims and the obsolete SSR dependency in the deferred filters spec.

## Out of scope

- CLI implementation, new endpoints, dependency changes, installation automation, or live API probes.
- Claiming support for filters/facets, tracker search, saved-job pagination, boards, notes/tags/journal, alerts, resume upload, or browser OAuth.
- Treating save/stage/remove as working flows, repairing their implementation, or claiming the intermittent DNS failure is resolved.

## Acceptance criteria

- The skill lives in the repository and has no references to a particular user's machine, account, or credentials.
- It directs agents to check the installed CLI's version/help and consult the current README/roadmap instead of treating a version-specific capability snapshot as permanent.
- It documents structured output, errors/rate limits/cache, auth privacy, private saved-job data, and explicit authorization for mutations.
- It explains that the CLI connects to MCP itself, public reads need no login, and browser OAuth is unimplemented.
- It records the saved-job mutation defects and TTL caveat without exposing private audit data.
- Every listed command and output flag matches the parser; examples use synthetic queries and placeholders only.
- README and roadmap link/explain the skill consistently; no runtime behavior changes.
- Documentation validation, pre-commit, and `git diff --check` pass.
