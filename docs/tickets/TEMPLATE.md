# TXX — Ticket Title

## Status

`NOT_STARTED`

## Phase

Phase name from the active journal plan.

## Source Plan References

- `docs/journal/PRE_CODING_PLAN.md`
- `docs/journal/CODING_PLAN.md`
- `docs/journal/EXPERIMENT_PLAN.md`
- `docs/journal/POST_EXPERIMENT_PLAN.md`

## Goal

Clear one-paragraph goal.

## Why This Exists

Explain why this ticket is necessary.

## Scope

- Included work item 1
- Included work item 2

## Out of Scope

- Excluded work item 1
- Excluded work item 2

## Human Intervention Required

Status: `NO`

If yes, specify:

- Required action:
- Required path or decision:
- Blocking reason:
- Unblocks:

## Dependencies

- Previous ticket:
- Required files:
- Required decisions:
- Required artifacts:

## Previous-Ticket Check

Before starting this ticket:

1. Check `docs/tickets/ticket_progress.md`.
2. Confirm all previous tickets are `DONE`, `SKIPPED_WITH_REASON`, or correctly blocked.
3. If any previous ticket is incomplete, stop and return to that ticket first.
4. Record the decision in `docs/tickets/ticket_progress.md`.

## Existing Code to Inspect First

- `src/...`
- `src/...`

## Existing Tests to Inspect First

- `tests/...`
- `tests/...`

## Files Likely Touched

- `src/...`
- `tests/...`
- `docs/...`

## Implementation Requirements

- Requirement 1
- Requirement 2

## Refactoring Requirements

Before implementation, check:

1. Does this already exist?
2. Should this be an enum?
3. Should this be a constant?
4. Should this be a config value?
5. Should this be a schema?
6. Can existing logic be reused?
7. Can duplicated logic be removed?
8. Can the code be shorter and clearer?
9. Can obsolete code be deleted?
10. Can tests be simplified?

## Schema, Enum, Constant, and Config Checks

- Existing enums checked:
- Existing constants checked:
- Existing schemas checked:
- Existing config models checked:
- New structure justified:

## Test Requirements

- Unit tests:
- Integration tests:
- Edge cases:
- Failure cases:
- Existing tests to adapt:
- Obsolete tests to delete:

## Commands to Run

Targeted commands:

```bash

```

Final validation commands:

```bash

```

## Full-Suite Trigger Condition

Run the full required suite only after all implementation and targeted fixes are complete, or when this ticket is marked as breaking.

Do not run the full suite after every small edit.

## Acceptance Criteria

- Criterion 1
- Criterion 2
- Criterion 3

## Stop Conditions

Stop if:

- A scientific invariant conflict appears.
- Required human intervention is missing.
- Required source data is unavailable.
- Existing code ownership is unclear.
- Implementation would duplicate existing logic.
- Tests reveal a deeper architectural issue.
- The ticket requires changing scope beyond the active journal plans.

## Implementation Notes

Notes for the implementation agent.