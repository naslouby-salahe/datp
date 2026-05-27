# Refactor Workboard

This is the main operational board. It tracks packets, locks, progress, re-audits, and final status.

## Status vocabulary

| Status | Meaning |
|---|---|
| `NOT_STARTED` | Packet exists but work has not started. |
| `READY` | Packet is ready and has clear scope. |
| `ACTIVE` | One agent/session is currently working on it. |
| `BLOCKED` | Work cannot continue until a recorded blocker is resolved. |
| `IN_REVIEW` | Implementation is done; review and repair loop is active. |
| `REPAIR_REQUIRED` | Review found issues that must be fixed. |
| `REAUDIT_REQUIRED` | Packet passed once but must be checked again after integration or related packets. |
| `DONE` | Packet passed implementation, tests, review, and later re-audit. |

## Current active packet

| Field | Value |
|---|---|
| Active packet | `PKT-000-readiness-and-inventory` |
| Active role | Main orchestrator / DeepSeek V4 Pro |
| Current status | `READY` |
| Last updated | `TODO` |
| Current file locks | None yet |
| Next action | Run PKT-000 and update all workflow files with observed reality. |

## Packet board

| Packet | Title | Status | Owner/tool | Locked files | Required checks | Re-audit trigger |
|---|---|---|---|---|---|---|
| PKT-000 | Readiness and inventory | `READY` | DeepSeek V4 Pro | Workflow files only | `git status --short`, tool versions | After PKT-001 |
| PKT-001 | Repository map and ownership audit | `NOT_STARTED` | DeepSeek V4 Pro | TBD | targeted static inspection | After PKT-002 |
| PKT-002 | Cross-package pattern sweep | `NOT_STARTED` | DeepSeek V4 Pro | TBD | `ruff`, `pyright` as needed | After each centralization packet |
| PKT-003 | Artifact and path construction centralization | `NOT_STARTED` | DeepSeek V4 Pro | TBD | impacted tests | After integration |
| PKT-004 | Baseline, regime, enum, and constant centralization | `NOT_STARTED` | DeepSeek V4 Pro | TBD | impacted tests, pyright | After PKT-006 |
| PKT-005 | Score loading and metric parsing consolidation | `NOT_STARTED` | DeepSeek V4 Pro | TBD | impacted tests | After PKT-006 |
| PKT-006 | Eligibility and calibration logic consolidation | `NOT_STARTED` | DeepSeek V4 Pro | TBD | impacted tests, scientific audit | After PKT-008 |
| PKT-007 | Test fixture and skipped-test cleanup | `NOT_STARTED` | DeepSeek V4 Pro | TBD | targeted pytest | After PKT-008 |
| PKT-008 | Quality gate repair | `NOT_STARTED` | DeepSeek V4 Pro | TBD | ruff, pyright, targeted pytest, optional CodeScene | Final review |
| PKT-009 | Integration, hostile review, scientific re-audit | `NOT_STARTED` | DeepSeek + Claude Sonnet/Codex o3 if needed | TBD | final targeted checks | Final gate |

## File locks

| File / directory | Locked by | Packet | Started | Reason | Status |
|---|---|---|---|---|---|
| None |  |  |  |  |  |

## Completed work evidence

| Packet | Changed files | Commands run | Tests run | Review result | Re-audit result |
|---|---|---|---|---|---|
| None yet |  |  |  |  |  |

## Deferred checks

| Check | Reason deferred | Owner | Must run before | Status |
|---|---|---|---|---|
| Full e2e tests | Too heavy by default in WSL | TBD | Only if directly impacted and explicitly approved | `DEFERRED` |
| Training/experiment runs | Out of scope for refactoring workflow | TBD | Never without explicit approval | `DEFERRED` |

## Escalation log

| Date | Packet | Tool/model | Reason | Outcome |
|---|---|---|---|---|
| None yet |  |  |  |  |

## Re-audit queue

| Item | Why it must be re-audited | Trigger | Status |
|---|---|---|---|
| Every completed packet | A previous pass is only evidence, not proof | Related packet completion and final hostile review | `PENDING` |
