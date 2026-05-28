# Refactor Workboard

This is the main operational board. It tracks packets, locks, progress, re-audits, and final status.

---

## Status vocabulary

| Status | Meaning |
|---|---|
| `NOT_STARTED` | Packet exists but work has not started. |
| `READY` | Packet is ready and has clear scope. |
| `READY_AFTER_PKT_000` | Packet is ready only after PKT-000 completes readiness and inventory. |
| `READY_AFTER_PKT_001` | Packet is ready only after PKT-001 completes or reaches a safe handoff point. |
| `ACTIVE` | One agent/session is currently working on it. |
| `BLOCKED` | Work cannot continue until a recorded blocker is resolved. |
| `IN_REVIEW` | Implementation is done; review and repair loop is active. |
| `REPAIR_REQUIRED` | Review found issues that must be fixed. |
| `REAUDIT_REQUIRED` | Packet passed once but must be checked again after integration or related packets. |
| `DONE` | Packet passed implementation, tests, review, and later re-audit. |

---

## Planning philosophy

This workflow is discovery-driven.

The maps and move plans are guardrails, not rigid scripts.

The agent must:

```text
inspect the real repository
identify issues
classify ownership
fix the smallest safe batch
update plans and maps
run checks
re-audit
continue or hand off with evidence
```

Living ledgers:

```text
AI Workflow/MOVE_PLAN.md
AI Workflow/TEST_MOVE_PLAN.md
AI Workflow/TEST_IMPACT_MAP.md
AI Workflow/PATTERN_LEDGER.md
AI Workflow/AUDIT_CODE.md
AI Workflow/SCIENTIFIC_CONTRACT_AUDIT.md
AI Workflow/state/PROJECT_MAP.md
```

Target guardrails:

```text
AI Workflow/REFACTOR_MAP.md
AI Workflow/TEST_REFACTOR_MAP.md
```

If real code contradicts a plan, inspect first, record evidence, and update the stale plan.

Do not ask the user to manually plan every move.

Do not stop at reporting issues when the active packet authorizes fixing them.

No wrappers, redirects, compatibility aliases, old package shells, or old-path preservation tests are allowed.

---

## Current active packet

| Field | Value |
|---|---|
| Active packet | `PKT-003-cross-package-pattern-sweep` |
| Active role | Main orchestrator / DeepSeek V4 Pro |
| Current status | `ACTIVE` |
| Last updated | 2026-05-28 |
| Current file locks | None |
| Next action | PKT-002 complete: ~40 test moves, 7 batches. Test structure mirrors production. Run Vulture/Refurb/Semgrep for pattern signals. |

---

## Packet board

| Packet | Title | Status | Owner/tool | Locked files | Required checks | Re-audit trigger |
|---|---|---|---|---|---|---|
| PKT-000 | Readiness and inventory | `REAUDIT_REQUIRED` | DeepSeek V4 Pro | Workflow files only | ✓ Complete: git clean, tools verified, static baseline recorded, state files updated | After PKT-001 validates project map |
| PKT-001 | Discovery-driven `src/datp` structure ownership repair | `REAUDIT_REQUIRED` | DeepSeek V4 Pro | All src/datp restructured | ✓ 52 moves, 8 batches, ruff clean, pyright unchanged | After PKT-002 validates test structure |
| PKT-002 | Discovery-driven `tests` structure ownership repair | `REAUDIT_REQUIRED` | DeepSeek V4 Pro | All tests restructured | ✓ ~40 moves, 7 batches, ruff clean, test structure mirrors production | After PKT-003 |
| PKT-003 | Cross-package pattern sweep | `READY` | DeepSeek V4 Pro | TBD | Ruff, Pyright, optional Vulture/Refurb/Semgrep as useful | After each centralization packet |
| PKT-004 | Artifact and path construction centralization | `NOT_STARTED` | DeepSeek V4 Pro | TBD | Impacted artifact/path tests | After integration |
| PKT-005 | Baseline, regime, enum, and constant centralization | `NOT_STARTED` | DeepSeek V4 Pro | TBD | Ruff, Pyright, impacted domain/config/thresholding tests | After PKT-007 |
| PKT-006 | Score loading and metric parsing consolidation | `NOT_STARTED` | DeepSeek V4 Pro | TBD | Impacted scoring/evaluation/reporting tests | After PKT-007 |
| PKT-007 | Eligibility and calibration logic consolidation | `NOT_STARTED` | DeepSeek V4 Pro | TBD | Impacted threshold/calibration tests + scientific audit | After PKT-009 |
| PKT-008 | Test fixture and skipped-test cleanup | `NOT_STARTED` | DeepSeek V4 Pro | TBD | Targeted pytest, optional Vulture | After PKT-009 |
| PKT-009 | Quality gate repair | `NOT_STARTED` | DeepSeek V4 Pro | TBD | Ruff, Pyright, impacted pytest, optional CodeScene/Vulture/Refurb/Semgrep, optional final Sonar only if healthy | Final review |
| PKT-010 | Integration, hostile review, scientific re-audit | `NOT_STARTED` | DeepSeek + Claude Sonnet/Codex o3 if needed | TBD | Final targeted checks, project-map re-audit, stale-path audit | Final gate |
| PROJECT-MAP | Living project map maintenance | `READY` | DeepSeek V4 Pro | `AI Workflow/state/PROJECT_MAP.md` | Update after Graphify/package moves/tool findings/test-structure changes | Every major refactor |
| TEST-MAP | Living test ownership map maintenance | `READY` | DeepSeek V4 Pro | `AI Workflow/TEST_REFACTOR_MAP.md`, `AI Workflow/TEST_MOVE_PLAN.md`, `AI Workflow/TEST_IMPACT_MAP.md` | Update after test moves and production package moves | Every test ownership change |

---

## Active ownership questions

These are not manual tasks for Salaheddine.

The agent must answer them from real code and update the maps and ledgers.

| ID | Question | Why it matters | Status |
|---|---|---|---|
| OWN-001 | Does `src/datp/training/scoring.py` generate scores, load scores, or both? | Decides whether the logic belongs in `federated` or `scoring`. | `TO_INSPECT` |
| OWN-002 | Does `src/datp/evaluation/score_loading.py` overlap with baseline scoring helpers? | Prevents duplicate score loading and schema drift. | `TO_INSPECT` |
| OWN-003 | Does `src/datp/baselines/common/training.py` train, adapt model loading, or support evaluation only? | Prevents thresholding from owning training logic. | `TO_INSPECT` |
| OWN-004 | Does `src/datp/pipeline/training.py` orchestrate training or implement training? | Decides between `experiments/stages` and `federated`. | `TO_INSPECT` |
| OWN-005 | Are baseline/regime enums duplicated across packages? | Prevents semantic drift and string-literal spread. | `TO_INSPECT` |
| OWN-006 | Do tests preserve old internal import paths? | Must be removed; no backwards-compatibility tests. | `TO_INSPECT` |
| OWN-007 | Are fixture builders duplicated across unit/integration/e2e tests? | Prevents brittle tests and inconsistent test setup. | `TO_INSPECT` |

---

## Approved optional tools

| Tool | Status | Check command | Install command | Run command | Notes |
|---|---|---|---|---|---|
| Vulture | `AVAILABLE` | ✓ vulture 2.16 | Already installed | `uv run vulture src/datp tests --min-confidence 80` | Findings are suspects; verify before deletion. |
| Refurb | `AVAILABLE` | ✓ refurb 2.3.1 | Already installed | `uv run refurb src/datp tests` | Apply only clarity-improving suggestions. |
| Semgrep | `AVAILABLE` | ✓ semgrep 1.164.0 | Already installed | `uv run semgrep scan --config auto src/datp tests` | Triage security/static-analysis findings. |

---

## Explicitly excluded tools

| Tool | Status | Reason |
|---|---|---|
| Repomix | `EXCLUDED` | Too token-expensive for this workflow unless explicitly approved later. |
| Git worktrees | `EXCLUDED` | Not needed for current workflow unless parallel filesystem isolation becomes necessary. |
| CodeQL | `EXCLUDED` | Not needed locally now; Semgrep is enough for local security/static checks. |
| deptry | `EXCLUDED` | Not needed now; avoid adding extra dependency-noise. |

---

## Discovery log

| Date | Packet | Discovery command or inspection | Finding summary | Follow-up |
|---|---|---|---|---|
| 2026-05-28 | PKT-002 | 7 batches, ~40 test moves. Tests restructured to mirror production ownership. Old dirs removed: cli, models, training, baselines, pipeline, sweep, audit, analyses/common/threshold_variants/comparators. Ruff clean, pyright unchanged. | Advance to PKT-003. |

---

## File locks

| File / directory | Locked by | Packet | Started | Reason | Status |
|---|---|---|---|---|---|
| None |  |  |  |  |  |

---

## Completed work evidence

| Packet | Changed files | Commands run | Tests run | Review result | Re-audit result |
|---|---|---|---|---|---|
| None yet |  |  |  |  |  |

---

## Deferred checks

| Check | Reason deferred | Owner | Must run before | Status |
|---|---|---|---|---|
| Full E2E tests | Too heavy by default in WSL | TBD | Only if directly impacted and explicitly approved | `DEFERRED` |
| Training/experiment runs | Out of scope for refactoring workflow | TBD | Never without explicit approval | `DEFERRED` |
| Local Sonar | Local Sonar has been unreliable | TBD | Optional final audit only if healthy and stable | `DEFERRED` |
| Vulture | Optional dead-code suspect pass | TBD | Before large deletion/cleanup claims | `PENDING_CHECK` |
| Refurb | Optional modernization pass | TBD | Before final polish if useful | `PENDING_CHECK` |
| Semgrep | Optional security/static pass | TBD | Before final quality review if useful | `PENDING_CHECK` |
| Full test suite | Too broad by default during ownership moves | TBD | Before final integration only if resource-safe | `DEFERRED` |
| E2E execution after folder moves | Structure-only E2E moves should start with collection | TBD | Run actual E2E only if directly required and approved | `DEFERRED` |

---

## Default quality gate

| Check | Role | Default |
|---|---|---|
| `git status --short` | Safety and handoff evidence | Required |
| `python -m ruff check src/datp tests` | Lint/static cleanup | Required after code/test changes |
| `python -m pyright` | Type/Pylance-equivalent gate | Required after type/import/interface changes |
| `python -m pytest <impacted-test-paths>` | Behavior verification | Required after code/test changes |
| `python -m pytest --collect-only tests/e2e` | Safe E2E structure check after E2E folder moves | Conditional |
| `cs delta` / `cs review` / `make codescene-check` | Complexity and hotspot signal | Optional/useful |
| `uv run vulture src/datp tests --min-confidence 80` | Dead-code suspect discovery | Optional/useful |
| `uv run refurb src/datp tests` | Modernization/readability suggestions | Optional/useful |
| `uv run semgrep scan --config auto src/datp tests` | Security/static-analysis signal | Optional/useful |
| Sonar | Optional final local audit only | Not default |

---

## Escalation log

| Date | Packet | Tool/model | Reason | Outcome |
|---|---|---|---|---|
| None yet |  |  |  |  |

---

## Re-audit queue

| Item | Why it must be re-audited | Trigger | Status |
|---|---|---|---|
| Every completed packet | A previous pass is only evidence, not proof. | Related packet completion and final hostile review. | `PENDING` |
| `AI Workflow/state/PROJECT_MAP.md` | Project structure and ownership assumptions become stale after refactors. | After Graphify refresh, package moves, wrapper deletion, optional-tool findings, or test-structure changes. | `PENDING` |
| `AI Workflow/TEST_REFACTOR_MAP.md` | Test ownership assumptions become stale after production package moves. | After PKT-001, PKT-002, and final stale-path audit. | `PENDING` |
| `AI Workflow/TEST_MOVE_PLAN.md` | Test move status becomes stale after actual file moves. | After every test move batch. | `PENDING` |
| `AI Workflow/TEST_IMPACT_MAP.md` | Impacted-test commands become stale after package/test moves. | After every production or test ownership move. | `PENDING` |
| Graphify evidence | Graph evidence becomes stale after major moves. | After ownership changes or package restructuring. | `PENDING` |
| Vulture findings | Dead-code suspects may be false positives. | Before deletion and after import/test changes. | `PENDING` |
| Refurb findings | Modernization suggestions may create churn. | Before applying and after tests. | `PENDING` |
| Semgrep findings | Security/static findings require triage. | Before final quality review. | `PENDING` |
| Sonar policy | Local Sonar is unreliable and should not silently become a blocker. | Before any final-quality use of Sonar. | `PENDING` |
| Old test paths | Tests must not keep obsolete internal package names alive. | After PKT-001 and PKT-002. | `PENDING` |

---

## Stale-path audit commands

Run after PKT-001 and PKT-002:

```bash
rg "datp\.baselines|datp\.training|datp\.models|datp\.pipeline|datp\.sweep|datp\.audit|datp\.analyses\.common|datp\.analyses\.threshold_variants|datp\.analyses\.comparators" tests src/datp
find src/datp -maxdepth 4 -type d | sort
find tests -type d | sort
python -m pytest --collect-only tests
```

Any remaining old path must be either:

```text
a real current production owner
a documented deferred move
a blocker
```

It must not be a wrapper, redirect, compatibility alias, old package shell, or old-path preservation test.
