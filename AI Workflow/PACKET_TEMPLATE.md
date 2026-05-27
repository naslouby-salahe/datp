# Packet Template

Copy this file to `packets/PKT-XXX-short-name.md` before starting a new work packet.

## Packet identity

| Field | Value |
|---|---|
| Packet ID | `PKT-XXX` |
| Title | `TODO` |
| Owner/tool | `DeepSeek V4 Pro unless otherwise recorded` |
| Status | `NOT_STARTED` |
| Created | `TODO` |
| Last updated | `TODO` |

## Purpose

State the exact refactoring/audit purpose. Do not use vague cleanup language.

## Scope

### In scope

- `TODO`

### Out of scope

- training runs;
- heavy experiments;
- unrelated package cleanup;
- scientific baseline changes;
- backwards-compatibility wrappers.

## File locks

| File/directory | Reason | Lock owner | Status |
|---|---|---|---|
| TBD | TBD | TBD | `PENDING` |

## Pre-change audit

| Check | Evidence | Result |
|---|---|---|
| `git status --short` | `TODO` | `TODO` |
| Architecture risk | `TODO` | `TODO` |
| Scientific risk | `TODO` | `TODO` |
| Test impact | `TODO` | `TODO` |
| Pattern impact | `TODO` | `TODO` |

## Implementation checklist

- [ ] Inspect real code before editing.
- [ ] Identify repeated patterns and update `PATTERN_LEDGER.md`.
- [ ] Update imports/tests with moved code.
- [ ] Remove obsolete modules instead of leaving wrappers.
- [ ] Update `REFACTOR_MAP.md` or `MOVE_PLAN.md` if ownership changes.
- [ ] Update `SCIENTIFIC_CONTRACT_AUDIT.md` if scientific logic is touched.
- [ ] Update `TEST_IMPACT_MAP.md`.
- [ ] Run targeted checks.
- [ ] Record deferred checks with reasons.
- [ ] Mark packet `REAUDIT_REQUIRED` after first pass.

## Acceptance criteria

- [ ] Code is cleaner and shorter where appropriate without changing behavior.
- [ ] No wrappers, redirects, or compatibility aliases remain for moved internal code.
- [ ] No Pyright/Pylance issues introduced.
- [ ] No Ruff issues introduced.
- [ ] Impacted tests updated and passing.
- [ ] Scientific invariants preserved.
- [ ] Workboard and audit files updated.
- [ ] Later re-audit scheduled.

## Commands run

| Command | Result | Notes |
|---|---|---|
| `TODO` | `TODO` | `TODO` |

## Handoff

Use `SESSION_HANDOFF_TEMPLATE.md`.
