# PR 11.5 — Recovery patch release

## Scope and gate

Release v0.2.1 after the reviewed Phase 11 recovery PRs and required Python 3.11–3.14 CI pass. Record precisely which fixes are verified, any unresolved upstream blockers, and remaining feature limitations in changelog, README, roadmap and skill. Do not describe unresolved hydration/OAuth as complete.

## Verification and publication

- Build wheel/sdist, validate version/artifact contents and checksums, and smoke-test installed artifact help plus offline tests.
- Merge reviewed stack in dependency order with gh stack; tag the exact verified release commit.
- Use the existing environment-scoped Trusted Publishing workflow, verify workflow success, GitHub release and PyPI v0.2.1 artifact metadata/digests.
- Install the published version on chen-lappy with uv and repeat uncached public reads plus authenticated read-only checks.
- Keep structured filters and browser OAuth as the next existing-spec work; this patch release alone does not complete the broader goal.
