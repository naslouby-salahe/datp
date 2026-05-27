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

## Current active packet

| Field | Value |
|---|---|
| Active packet | `PKT-000-readiness-and-inventory` |
| Active role | Main orchestrator / DeepSeek V4 Pro |
| Current status | `READY` |
| Last updated | `TODO` |
| Current file locks | None yet |
| Next action | Run PKT-000 and update workflow files, tool reality, optional tool install status, Graphify status, and project map from observed reality. |

---

## Packet board

| Packet | Title | Status | Owner/tool | Locked files | Required checks | Re-audit trigger |
|---|---|---|---|---|---|---|
| PKT-000 | Readiness and inventory | `READY` | DeepSeek V4 Pro | Workflow files only | `git status --short`, tool versions, optional tool check/install, readiness inspection | After PKT-001 |
| PKT-001 | `src/datp` structure ownership refactor | `READY_AFTER_PKT_000` | DeepSeek V4 Pro | `src/datp`, impacted tests, workflow maps | Ruff, Pyright, impacted tests by move batch | After PKT-002 |
| PKT-002 | `tests` structure ownership refactor | `READY_AFTER_PKT_001` | DeepSeek V4 Pro | `tests`, test maps, project map | Ruff, Pyright, impacted tests by test move batch | After PKT-003 and final stale-path audit |
| PKT-003 | Cross-package pattern sweep | `NOT_STARTED` | DeepSeek V4 Pro | TBD | Ruff, Pyright, optional Vulture/Refurb/Semgrep as useful | After each centralization packet |
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

## Approved optional tools

| Tool | Status | Check command | Install command | Run command | Notes |
|---|---|---|---|---|---|
| Vulture | `PENDING_CHECK` | `uv run vulture --version || vulture --version || true` | `uv add --dev vulture refurb semgrep` | `uv run vulture src/datp tests --min-confidence 80` | Findings are suspects; verify before deletion. |
| Refurb | `PENDING_CHECK` | `uv run refurb --version || refurb --version || true` | `uv add --dev vulture refurb semgrep` | `uv run refurb src/datp tests` | Apply only clarity-improving suggestions. |
| Semgrep | `PENDING_CHECK` | `uv run semgrep --version || semgrep --version || true` | `uv add --dev vulture refurb semgrep` | `uv run semgrep scan --config auto src/datp tests` | Triage security/static-analysis findings. |

---

## Explicitly excluded tools

| Tool | Status | Reason |
|---|---|---|
| Repomix | `EXCLUDED` | Too token-expensive for this workflow unless explicitly approved later. |
| Git worktrees | `EXCLUDED` | Not needed for current workflow unless parallel filesystem isolation becomes necessary. |
| CodeQL | `EXCLUDED` | Not needed locally now; Semgrep is enough for local security/static checks. |
| deptry | `EXCLUDED` | Not needed now; avoid adding extra dependency-noise. |

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
find tests -type d | sort
python -m pytest --collect-only tests
```

Any remaining old path must be either:

```text
a real current production owner
a documented deferred move
a blocker
```

It must not be a wrapper, redirect, compatibility alias, or old-path preservation test.