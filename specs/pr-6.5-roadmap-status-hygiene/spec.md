# PR 6.5 — Roadmap status hygiene

## Scope

- Add a machine-readable implementation-status ledger for every roadmap PR.
- Make each status auditable by referencing the implementing GitHub PR or blocking reason.
- Require future PRs to update the ledger whenever they change roadmap state.

## Status contract

Use exactly one row per roadmap PR with one of:

- `Merged` — implemented and merged; reference the implementing GitHub PR.
- `Open` — has an open PR or is being implemented; reference the PR or current work.
- `Deferred` — intentionally not implemented; state the concrete blocker or missing verified contract.

The table is the source of truth for quick audits, but it does not replace the detailed phase specs.

## Out of scope

- Reopening completed behavior.
- Changing existing PR scope or adding product features.
- Automatic synchronization from GitHub.

## Acceptance criteria

- Every roadmap PR has exactly one status row.
- Statuses match repository history and open/deferred state.
- Merged rows reference their implementing GitHub PR.
- Deferred rows state why they are blocked.
- Future state changes update the table in the same PR.
- Pre-commit checks pass.

## Traceability

Source: `roadmap.md`, Phase 6, PR 6.5.
