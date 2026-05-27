# Test Impact Map

This file tracks tests impacted by each packet.

Tests must be behavior-focused and must move with the code.

The target test ownership map is:

```text
AI Workflow/TEST_REFACTOR_MAP.md
```

The concrete test move ledger is:

```text
AI Workflow/TEST_MOVE_PLAN.md
```

---

## Test policy

- Update impacted tests in the same packet as production changes.
- Move tests when production ownership changes.
- Run impacted tests first.
- Run package-level tests when justified.
- Avoid full E2E by default in WSL.
- Do not leave skipped, xfailed, or commented-out tests unresolved.
- Do not preserve old internal import paths.
- Do not create redirect tests.
- Do not create wrapper tests.
- Do not create alias-preservation tests.
- CUDA-dependent tests should not be silently skipped when CUDA is expected; record the reason and policy.
- If Vulture, Refurb, or Semgrep findings lead to code changes, run impacted tests afterward.
- Optional tool findings are not test evidence by themselves.

---

## No-backwards-compatibility test rule

No backwards compatibility is allowed for internal package moves.

Do not leave tests that preserve old internal paths such as:

```text
datp.baselines
datp.training
datp.models
datp.pipeline
datp.sweep
datp.audit
datp.analyses.common
datp.analyses.threshold_variants
datp.analyses.comparators
```

Once production code moves, update tests directly to the new canonical imports.

Do not write tests that old paths still work.

Do not mark old-path import tests as skipped or xfailed.

Delete obsolete test folders after imports are corrected.

---

## Test command inventory

| Scope | Command | Default? | Notes |
|---|---|---|---|
| Ruff | `python -m ruff check src/datp tests` | Yes | Run after refactors. |
| Pyright | `python -m pyright` | Yes when types/imports changed | Captures Pylance-class issues. |
| Impacted tests | `python -m pytest <paths>` | Yes | Primary strategy. |
| Package tests | `python -m pytest tests/<package>` | Conditional | Use when package boundaries moved. |
| E2E collection | `python -m pytest --collect-only tests/e2e` | Conditional | Safer first step after E2E moves. |
| Vulture | `uv run vulture src/datp tests --min-confidence 80` | Optional | Dead-code suspects; verify before deletion. |
| Refurb | `uv run refurb src/datp tests` | Optional | Modernization suggestions; apply only if clarity improves. |
| Semgrep | `uv run semgrep scan --config auto src/datp tests` | Optional | Security/static-analysis findings; triage required. |
| Full test suite | `python -m pytest` | Not default | Use only when justified and resource-safe. |
| Full E2E | project-specific | Deferred | Avoid unless directly impacted and explicitly approved. |

---

## Optional tool retest rule

If a tool causes a code or test change, retest the affected behavior.

| Tool | Typical change | Required retest |
|---|---|---|
| Vulture | Delete unused code/imports/classes/functions | Import tests, related unit tests, package tests when ownership changes. |
| Refurb | Modernize expressions/control flow/API usage | Related unit tests and Pyright. |
| Semgrep | Security/static fix | Targeted tests for changed behavior plus Pyright/Ruff. |

Do not apply a tool suggestion without mapping it to impacted tests.

---

## Current old test ownership to remove

These paths are expected to disappear after the production package move completes:

```text
tests/unit/baselines
tests/unit/training
tests/unit/models
tests/unit/pipeline
tests/unit/sweep
tests/unit/audit
tests/unit/analyses/common
tests/unit/analyses/threshold_variants
tests/unit/analyses/comparators
tests/integration/baselines
tests/integration/training
tests/integration/sweep
```

These paths may remain only if the matching production package is still canonical at that point.

If the production package moved, the tests must move too.

---

## Target test ownership

| Production owner | Unit test owner | Integration test owner |
|---|---|---|
| `src/datp/app/cli` | `tests/unit/app/cli` | Usually none unless CLI behavior crosses package boundaries. |
| `src/datp/modeling` | `tests/unit/modeling` | Usually none. |
| `src/datp/federated` | `tests/unit/federated` | `tests/integration/federated` |
| `src/datp/scoring` | `tests/unit/scoring` | `tests/integration/scoring` |
| `src/datp/thresholding` | `tests/unit/thresholding` | `tests/integration/thresholding` |
| `src/datp/experiments` | `tests/unit/experiments` | `tests/integration/experiments` |
| `src/datp/validation` | `tests/unit/validation` | `tests/integration/validation` |
| `src/datp/analyses` | `tests/unit/analyses` | Usually none unless consuming cross-run artifacts. |
| `src/datp/data` | `tests/unit/data` | `tests/integration/data` |
| `src/datp/reporting` | `tests/unit/reporting` | `tests/integration/reporting` |
| `src/datp/statistics` | `tests/unit/statistics` | Usually none. |
| `src/datp/artifacts` | `tests/unit/artifacts` | Usually through thresholding/scoring/integration tests. |
| `src/datp/config` | `tests/unit/config` | Usually none. |
| `src/datp/core` | `tests/unit/core` | Usually none. |
| `src/datp/domain` | `tests/unit/domain` | Usually none. |

---

## Impact map

| Packet | Production files touched | Tests to update | Commands to run | Deferred checks | Status |
|---|---|---|---|---|---|
| PKT-000 | Workflow files only | None | `git status --short`, tool versions, optional tool check/install | Full suite | `READY` |
| PKT-001 | `src/datp` structure | Tests impacted by production moves | `python -m ruff check src/datp tests`, `python -m pyright`, `python -m pytest <impacted-test-paths>` | Full E2E | `READY_AFTER_PKT_000` |
| PKT-002 | `tests` structure | All tests with old ownership paths | `python -m ruff check src/datp tests`, `python -m pyright`, targeted pytest by moved package | Full E2E unless directly required | `READY_AFTER_PKT_001` |
| PKT-003 | Cross-package pattern sweep | Tests covering centralized patterns | Ruff, Pyright, impacted pytest, optional Vulture/Refurb/Semgrep | Full E2E | `PENDING` |
| PKT-004 | Artifact and path construction centralization | Artifact/path tests and integration layout tests | Impacted artifact/path tests | Full E2E | `PENDING` |
| PKT-005 | Baseline, regime, enum, and constant centralization | Domain/core/thresholding/config tests | Ruff, Pyright, impacted tests | Full E2E | `PENDING` |
| PKT-006 | Score loading and metric parsing consolidation | Scoring/evaluation/thresholding/reporting tests | Impacted score/metrics tests | Full E2E | `PENDING` |
| PKT-007 | Eligibility and calibration logic consolidation | Thresholding/evaluation/validation tests | Impacted threshold/calibration tests + scientific audit | Full E2E | `PENDING` |
| PKT-008 | Test fixture and skipped-test cleanup | Fixture users and skipped/xfail tests | Targeted pytest; optional Vulture | Full suite unless safe | `PENDING` |
| PKT-009 | Quality gate repair | Any impacted tests | Ruff, Pyright, impacted pytest, optional CodeScene/Vulture/Refurb/Semgrep | Full E2E | `PENDING` |
| PKT-010 | Integration, hostile review, scientific re-audit | Final impacted tests | Final targeted checks; optional hostile review | Heavy experiments | `PENDING` |

---

## PKT-001 impacted tests by production move

| Production move | Old tests | New tests | Required command |
|---|---|---|---|
| `src/datp/cli` -> `src/datp/app/cli` | `tests/unit/cli` | `tests/unit/app/cli` | `python -m pytest tests/unit/app/cli` |
| `src/datp/models` -> `src/datp/modeling` | `tests/unit/models` | `tests/unit/modeling` | `python -m pytest tests/unit/modeling` |
| `src/datp/training` -> `src/datp/federated` | `tests/unit/training`, `tests/integration/training` | `tests/unit/federated`, `tests/integration/federated` | `python -m pytest tests/unit/federated tests/integration/federated` |
| scoring extracted from training/evaluation/baselines | `tests/unit/training/test_scoring.py`, `tests/integration/training/test_score_artifacts.py` | `tests/unit/scoring`, `tests/integration/scoring` | `python -m pytest tests/unit/scoring tests/integration/scoring` |
| `src/datp/baselines` -> `src/datp/thresholding` | `tests/unit/baselines`, `tests/integration/baselines` | `tests/unit/thresholding`, `tests/integration/thresholding` | `python -m pytest tests/unit/thresholding tests/integration/thresholding` |
| threshold variants/comparators moved from analyses | `tests/unit/analyses/threshold_variants`, `tests/unit/analyses/comparators` | `tests/unit/thresholding/variants`, `tests/unit/thresholding/comparators` | `python -m pytest tests/unit/thresholding/variants tests/unit/thresholding/comparators` |
| `src/datp/pipeline` and `src/datp/sweep` -> `src/datp/experiments` | `tests/unit/pipeline`, `tests/unit/sweep`, `tests/integration/sweep` | `tests/unit/experiments`, `tests/integration/experiments` | `python -m pytest tests/unit/experiments tests/integration/experiments` |
| `src/datp/audit` -> `src/datp/validation` | `tests/unit/audit` | `tests/unit/validation` | `python -m pytest tests/unit/validation` |
| `src/datp/analyses/common` flattened | `tests/unit/analyses/common` | `tests/unit/analyses` | `python -m pytest tests/unit/analyses` |
| E2E regime folders consolidated | `tests/e2e/regime_a`, `tests/e2e/regime_b`, `tests/e2e/regime_c` | `tests/e2e/regimes` | `python -m pytest --collect-only tests/e2e` |

---

## Skipped/xfailed/commented test ledger

| Test | Current marker/state | Reason | Required action | Packet | Status |
|---|---|---|---|---|---|
| TBD | TBD | Initial sweep not done. | Search and classify. | PKT-002 | `OPEN` |

Search command:

```bash
rg "skip|xfail|pytest\.skip|pytest\.mark\.skip|pytest\.mark\.xfail|pass\s*#|TODO|commented" tests
```

Do not remove skips blindly.

Classify them first.

Fix unjustified skips and xfails.

---

## Optional tool findings ledger

| Tool | Finding | Files impacted | Tests required | Status |
|---|---|---|---|---|
| Vulture | TBD | TBD | TBD | `NOT_RUN` |
| Refurb | TBD | TBD | TBD | `NOT_RUN` |
| Semgrep | TBD | TBD | TBD | `NOT_RUN` |

---

## Failure ledger

| Command | Failure | Root cause | Fix packet | Retest command | Status |
|---|---|---|---|---|---|
| None yet |  |  |  |  |  |

---

## Test structure completion checklist

A test-structure packet is not complete until:

1. old ownership paths are removed or justified by real current production ownership;
2. imports point to canonical production packages;
3. no tests validate obsolete internal paths;
4. no wrappers or redirect tests were added;
5. no skipped/xfail tests hide import failures;
6. impacted tests pass;
7. Ruff passes;
8. Pyright passes;
9. `PROJECT_MAP.md` is updated;
10. `TEST_MOVE_PLAN.md` is updated;
11. a later re-audit confirms no stale paths remain.