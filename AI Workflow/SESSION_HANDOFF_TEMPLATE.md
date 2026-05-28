# Session Handoff Template

Use this before ending every AI session.

A handoff is mandatory before:

```text
manual stop
quota stop
timeout
tool crash
model switch
tool switch
packet switch
hard blocker
scientific blocker
final completion
```

Write the completed handoff to:

```text
AI Workflow/state/HANDOFFS.md
```

Also update:

```text
AI Workflow/state/ACTIVE_CURSOR.md
AI Workflow/state/RUN_LEDGER.md
AI Workflow/REFACTOR_WORKBOARD.md
```

---

## Session summary

| Field | Value |
|---|---|
| Date/time | `TODO` |
| Tool/model | `TODO` |
| Session name/id | `TODO` |
| Launcher used | `Start_My_Agent` |
| Repository root confirmed | `YES | NO` |
| Git status checked | `YES | NO` |
| Packet | `TODO` |
| Ticket | `TODO` |
| Phase | `DISCOVERY | PLANNING | IMPLEMENTATION | TESTING | REAUDIT | HANDOFF | BLOCKED | COMPLETE` |
| Status at end | `TODO` |

---

## Active goal

```text
TODO
```

---

## Starting state

| Item | Value |
|---|---|
| Previous cursor read | `YES | NO` |
| Previous handoff read | `YES | NO` |
| Previous blockers | `TODO` |
| Previous next action | `TODO` |
| Starting git status summary | `TODO` |

---

## Completed

- `TODO`

---

## Changed files

| File | Change summary | Why | Related packet/ticket |
|---|---|---|---|
| `TODO` | `TODO` | `TODO` | `TODO` |

---

## Files inspected but not changed

| File | Reason inspected | Finding |
|---|---|---|
| `TODO` | `TODO` | `TODO` |

---

## File locks

| File/directory | Lock status | Reason | Next action |
|---|---|---|---|
| `TODO` | `ACTIVE | RELEASED | STALE | NONE` | `TODO` | `TODO` |

---

## Commands run

| Command | Result | Notes |
|---|---|---|
| `TODO` | `PASS | FAIL | SKIPPED | BLOCKED` | `TODO` |

---

## Tests/checks run

| Check | Result | Notes |
|---|---|---|
| `TODO` | `PASS | FAIL | SKIPPED | BLOCKED` | `TODO` |

---

## Failures or unresolved issues

| Issue | Impact | Required next step |
|---|---|---|
| `TODO` | `TODO` | `TODO` |

---

## Deferred checks

| Check | Why deferred | Must run before |
|---|---|---|
| `TODO` | `TODO` | `TODO` |

---

## Assumptions made

| Assumption | Evidence | Where recorded |
|---|---|---|
| `TODO` | `TODO` | `AI Workflow/state/CHECK_FLAGS.md` |

---

## Scientific risks reviewed

| Risk | Result |
|---|---|
| Baseline semantics | `TODO` |
| Stage boundaries | `TODO` |
| Config-driven parameters | `TODO` |
| Unsupported claims | `TODO` |
| B1 versus B2 scope preserved | `TODO` |
| Shared B1 through B4 score artifacts preserved | `TODO` |
| No per-baseline retraining introduced | `TODO` |
| Calibration-Pending handling preserved | `TODO` |
| Regime A confirmatory hierarchy preserved | `TODO` |
| CICIoT2023 not overclaimed | `TODO` |
| Regime C not overclaimed | `TODO` |
| Unsupported privacy claims avoided | `TODO` |
| Unsupported poisoning/evasion claims avoided | `TODO` |
| Unsupported hardware/concept-drift claims avoided | `TODO` |
| Active four-file journal package respected | `TODO` |
| Archived roadmap not used as operational override | `TODO` |

---

## Quality risks reviewed

| Risk | Result |
|---|---|
| Wrappers introduced | `TODO` |
| Redirect modules introduced | `TODO` |
| Compatibility aliases introduced | `TODO` |
| Old package shells preserved | `TODO` |
| Stale imports left behind | `TODO` |
| Dead code suspects reviewed | `TODO` |
| Skipped tests introduced or retained | `TODO` |
| Duplicate constants/enums/schemas introduced | `TODO` |
| Vague utility ownership introduced | `TODO` |
| Long primitive argument lists introduced | `TODO` |
| Test-only helper imported by production code | `TODO` |

---

## Quota/tool issues

| Issue | Evidence | Impact | Next action |
|---|---|---|---|
| `TODO` | `TODO` | `TODO` | `TODO` |

---

## Blockers

| Blocker | Evidence | Fallbacks attempted | Remaining safe work |
|---|---|---|---|
| `TODO` | `TODO` | `TODO` | `TODO` |

---

## Active cursor update

| Field | Value |
|---|---|
| Cursor updated | `YES | NO` |
| Cursor file | `AI Workflow/state/ACTIVE_CURSOR.md` |
| Next phase | `TODO` |
| Next packet | `TODO` |
| Next ticket | `TODO` |
| Next exact step | `TODO` |

---

## Run ledger update

| Field | Value |
|---|---|
| Run ledger updated | `YES | NO` |
| Ledger file | `AI Workflow/state/RUN_LEDGER.md` |
| Last command recorded | `TODO` |
| Last result recorded | `TODO` |

---

## Re-audit requirement

| Scope | Required re-audit | Command or action |
|---|---|---|
| `TODO` | `YES | NO` | `TODO` |

---

## Next exact action

```text
TODO
```

---

## Resume command

```text
Start_My_Agent
```