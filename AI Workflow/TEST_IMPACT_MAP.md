# Test Impact Map

This file tracks tests impacted by each packet. Tests must be behavior-focused and must move with the code.

## Test policy

- Update impacted tests in the same packet as production changes.
- Run impacted tests first.
- Run package-level tests when justified.
- Avoid full e2e by default in WSL.
- Do not leave skipped, xfailed, or commented-out tests unresolved.
- CUDA-dependent tests should not be silently skipped when CUDA is expected; record the reason and policy.

## Test command inventory

| Scope | Command | Default? | Notes |
|---|---|---|---|
| Ruff | `python -m ruff check src/datp tests` | Yes | Run after refactors. |
| Pyright | `python -m pyright` | Yes when types/imports changed | Captures Pylance-class issues. |
| Impacted tests | `python -m pytest <paths>` | Yes | Primary strategy. |
| Package tests | `python -m pytest tests/<package>` | Conditional | Use when package boundaries moved. |
| Full test suite | `python -m pytest` | Not default | Use only when justified and resource-safe. |
| Full e2e | project-specific | Deferred | Avoid unless directly impacted and explicitly approved. |

## Impact map

| Packet | Production files touched | Tests to update | Commands to run | Deferred checks | Status |
|---|---|---|---|---|---|
| PKT-000 | Workflow files only | None | `git status --short`, tool versions | None | `READY` |
| PKT-001 | TBD | TBD | Targeted inspection, maybe no tests | Full suite | `PENDING` |
| PKT-002 | TBD | TBD | Ruff/Pyright if code changes | Full e2e | `PENDING` |
| PKT-003 | TBD | TBD | Impacted tests for artifact/path behavior | Full e2e | `PENDING` |
| PKT-004 | TBD | TBD | Ruff, Pyright, impacted tests | Full e2e | `PENDING` |
| PKT-005 | TBD | TBD | Impacted score/metrics tests | Full e2e | `PENDING` |
| PKT-006 | TBD | TBD | Impacted threshold/calibration tests + scientific audit | Full e2e | `PENDING` |
| PKT-007 | TBD | Test suite cleanup | Targeted pytest | Full suite unless safe | `PENDING` |
| PKT-008 | TBD | TBD | Ruff, Pyright, impacted pytest, optional CodeScene | Full e2e | `PENDING` |
| PKT-009 | TBD | TBD | Final targeted checks | Heavy experiments | `PENDING` |

## Skipped/xfailed/commented test ledger

| Test | Current marker/state | Reason | Required action | Packet | Status |
|---|---|---|---|---|---|
| TBD | TBD | Initial sweep not done. | Search and classify. | PKT-007 | `OPEN` |

## Failure ledger

| Command | Failure | Root cause | Fix packet | Retest command | Status |
|---|---|---|---|---|---|
| None yet |  |  |  |  |  |
