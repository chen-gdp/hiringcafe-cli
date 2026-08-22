# PR 7.1 — Saved-job write integrity

## Scope

- Keep trusted saved-job fields authoritative over hydrated source-job fields.
- Expand the sanitized hydrated job before setting identity, ownership, stage, timestamp, visibility, and tracking fields.
- Preserve removal of private user-tracking arrays.
- Add a regression test containing malicious values in the hydrated payload.

## Out of scope

- Changing the Firestore document shape.
- Changing stage transitions or marketplace synchronization.
- Adding notes, tags, boards, or new saved-job fields.

## Acceptance criteria

- A hydrated payload cannot override `objectID`, `owner`, `stage`, `dateSaved`, `isHidden`, `stageHistory`, or `counted_milestones`.
- Existing hydration, Firestore write, marketplace sync, and failure tests pass.
- Ruff and the full test suite pass.

## Traceability

Source: `roadmap.md`, Phase 7, PR 7.1.
