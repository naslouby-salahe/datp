# Move Plan

This file records code movement plans. Moving code is allowed, but it must be deliberate, tested, and finished cleanly.

## Move rules

- Move by responsibility, not by current location.
- Update all imports and tests in the same packet.
- Do not leave wrappers, redirects, compatibility aliases, or dead old modules.
- Delete obsolete files only after all imports are updated and tests pass.
- Record affected tests and scientific risks before moving.
- Re-audit moved areas after related packets finish.

## Planned moves

| Move ID | Source | Target | Reason | Impacted tests | File locks | Status |
|---|---|---|---|---|---|---|
| MOVE-000 | TBD | TBD | No real move planned before repository map. | TBD | TBD | `PENDING` |

## Deleted/retired modules

| Module/file | Reason retired | Replacement | Imports updated | Tests updated | Status |
|---|---|---|---|---|---|
| None yet |  |  |  |  |  |

## Import impact checklist

For every move:

- search all imports of the moved symbol/file;
- update production imports;
- update test imports;
- remove stale import aliases;
- run targeted import tests or the impacted package tests;
- run `python -m pyright` when type boundaries are affected;
- run `python -m ruff check src/datp tests`;
- update `REFACTOR_MAP.md` and `PATTERN_LEDGER.md`.

## No-backwards-compatibility rule

This refactor is greenfield with respect to internal code structure. Do not keep old internal paths alive with wrappers. Correct the codebase to the new canonical ownership instead.
