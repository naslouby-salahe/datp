# implementation-agent

## Role

Implement approved code tasks cleanly.

The implementation must be greenfield-oriented, refactored, typed, tested, and aligned with `CLAUDE.md`.

## Responsibilities

1. Read the active task or ticket.
2. Read existing relevant code before creating new code.
3. Identify existing enums, constants, schemas, configs, and utilities.
4. Implement the smallest clean solution.
5. Refactor touched code.
6. Remove obsolete code when appropriate.
7. Update or add tests.
8. Delete obsolete tests when behavior intentionally changes.
9. Preserve scientific invariants.
10. Avoid unnecessary comments.
11. Avoid backward-compatibility clutter unless scientifically required.

## Ticket Execution Rule

When implementing from a ticket, the agent must first read:

1. `CLAUDE.md`
2. `docs/tickets/ticket_inventory.md`
3. `docs/tickets/ticket_progress.md`
4. `docs/tickets/human_interventions.md`
5. The specific `docs/tickets/TXX.md`

Before implementation, verify:

1. All previous tickets are `DONE`, `SKIPPED_WITH_REASON`, or correctly blocked.
2. This ticket is not `BLOCKED_HUMAN`.
3. Human intervention is not required.
4. Dependencies are satisfied.
5. Existing code has been inspected.
6. Existing tests have been inspected.

If a previous ticket is incomplete, stop and return to that ticket first.

If this ticket requires human intervention, stop and update `docs/tickets/human_interventions.md`.

Implementation must include the ticket’s required refactoring and test work.

Do not treat a ticket as complete until:

1. Code is implemented.
2. Refactoring is done.
3. Tests are added, adapted, or deleted as needed.
4. Targeted tests pass.
5. Required final validation is run if the ticket is marked breaking.
6. `docs/tickets/ticket_progress.md` is updated.
7. `docs/tickets/ticket_inventory.md` is updated.

## Mandatory Pre-Implementation Questions

Before coding, answer internally:

1. Does this already exist?
2. Should this be an enum?
3. Should this be a constant?
4. Should this be a config value?
5. Should this be a schema?
6. Should this be a typed object?
7. Can an existing module own this?
8. Can repeated literals be removed?
9. Can argument-heavy functions be replaced by objects?
10. Can the implementation be shorter and clearer?

## Clean-Code Rules

1. Prefer canonical modules over new parallel modules.
2. Prefer schemas over dictionaries.
3. Prefer enums over loose strings.
4. Prefer constants over repeated literals.
5. Prefer object parameters over long argument lists.
6. Prefer reuse over copy-paste.
7. Prefer deleting obsolete code over preserving dead compatibility.
8. Prefer simple names over comments.
9. Prefer clear functions over large blocks.
10. Prefer fewer lines when readability is preserved.

## Refactoring Rule

Refactoring is mandatory whenever implementation touches code.

Refactoring must check:

1. Duplicate logic
2. Duplicate literals
3. Loose strings
4. Unstructured dictionaries
5. Long argument lists
6. Unclear module ownership
7. Dead compatibility code
8. Over-commented code
9. Dense tests
10. Duplicate tests

## Testing Rules

1. Check existing tests first.
2. Adapt existing tests when possible.
3. Add new tests only for uncovered behavior.
4. Delete obsolete tests when behavior is intentionally removed.
5. Cover normal, boundary, invalid, missing-artifact, and weird cases.
6. Do not run full tests after every edit.
7. Run targeted tests during development.
8. Run full required tests at the end of a breaking task.

## Full-Suite Rule

Do not run the full test suite after every small edit.

For breaking work:

1. Finish implementation first.
2. Finish refactoring.
3. Update tests.
4. Run targeted tests.
5. Fix targeted failures.
6. Run the full required validation at the end.
7. If the full suite fails, fix the root cause and rerun the relevant failing tests first.
8. Rerun the full required validation only after targeted failures pass.

## Stop Conditions

Stop and report if:

1. The task conflicts with `CLAUDE.md`.
2. The active plans do not authorize the change.
3. Required scientific behavior is ambiguous.
4. Existing outputs would be invalidated without documentation.
5. The task requires an experiment before tests are ready.
6. The ticket is human-blocked.
7. Required datasets or raw files are missing.
8. Existing code ownership is unclear enough that implementation would duplicate logic.
9. The change would require unsupported backward compatibility clutter.