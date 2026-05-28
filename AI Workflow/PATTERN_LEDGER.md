# Pattern Ledger

This ledger records repeated patterns across packages.

If a problem appears in multiple packages, do not fix it locally in each package.

Promote it into a cross-cutting packet or assign it to a canonical owner.

Use this file together with:

```text
AI Workflow/CLEAN_CODE_RULES.md
AI Workflow/AUDIT_CODE.md
AI Workflow/MOVE_PLAN.md
AI Workflow/TEST_IMPACT_MAP.md
AI Workflow/state/PROJECT_MAP.md
```

---

## Pattern status vocabulary

| Status | Meaning |
|---|---|
| `SUSPECTED` | Pattern is likely present but not fully verified. |
| `CONFIRMED` | Repetition exists in multiple places. |
| `OWNER_DECIDED` | Canonical owner has been selected. |
| `PACKET_CREATED` | A work packet exists to fix it globally. |
| `FIXED_ONCE` | Immediate fix passed but later re-audit is required. |
| `REAUDIT_REQUIRED` | Related changes may have reintroduced the issue. |
| `DONE` | Fixed and later re-audited after integration. |

---

## Initial pattern watchlist

| Pattern | Risk | Search strategy | Canonical owner candidate | Status | Packet |
|---|---|---|---|---|---|
| Repeated score loading | Divergent schema assumptions and fragile downstream code. | Search for score/parquet loading and `reconstruction_error` reads. | `src/datp/scoring` | `SUSPECTED` | PKT-006 |
| Repeated metric parsing | Inconsistent metrics and result shape assumptions. | Search for `metrics.json`, CV/FPR/F1 parsing. | `src/datp/evaluation` or `src/datp/reporting` depending on use. | `SUSPECTED` | PKT-006 |
| Repeated path construction | Output layout drift and duplicate string logic. | Search for `outputs/`, `seed_`, `alpha_`, baseline/regime path fragments. | `src/datp/artifacts` | `SUSPECTED` | PKT-004 |
| Repeated baseline strings | Baseline semantic drift. | Search for `B0`, `B1`, `B2`, `B3`, `B4`, `baseline`. | `src/datp/domain/baselines.py` | `SUSPECTED` | PKT-005 |
| Repeated regime strings | Regime A/B/C/D drift and path bugs. | Search for `regime_a`, `regime_b`, `regime_c`, `regime_d`, `Regime`. | `src/datp/domain/regimes.py` | `SUSPECTED` | PKT-005 |
| Repeated dataset strings | Dataset semantic drift and wrong feature-count assumptions. | Search for `nbaiot`, `ciciot`, `edge_iiotset`, dataset labels. | `src/datp/domain/datasets.py` and `src/datp/data/catalog.py` | `SUSPECTED` | PKT-005 |
| Repeated artifact names | Broken output compatibility and stale names. | Search for model/checkpoint/scaler/manifest/metrics names. | `src/datp/artifacts/constants.py` | `SUSPECTED` | PKT-004 |
| Repeated metric keys | Reporting and evaluation mismatch. | Search for `cv_fpr`, `macro_f1`, `coverage`, `balanced_accuracy`, `fpr`, `tpr`. | `src/datp/evaluation/metric_keys.py` | `SUSPECTED` | PKT-006 |
| Repeated eligibility logic | Calibration-Pending behavior drift. | Search for `n_min`, `eligible`, `Calibration-Pending`, `pending`. | `src/datp/thresholding/eligibility.py` | `SUSPECTED` | PKT-007 |
| Repeated CUDA checks | Inconsistent GPU behavior and skipped tests. | Search for `cuda`, `torch.cuda`, `skipif`, `CUDA`. | `src/datp/core/device.py` | `SUSPECTED` | PKT-009 |
| Repeated config fallbacks | Hidden defaults and scientific parameter drift. | Search for `.get(`, fallback constants, Hydra default overrides. | `src/datp/config` | `SUSPECTED` | PKT-005 |
| Repeated fixture builders | Bloated tests and inconsistent setup. | Search fixture factories and local builders in tests. | `tests/fixtures` | `SUSPECTED` | PKT-008 |
| Repeated primitive argument groups | High complexity and weak domain modeling. | Search long signatures and repeated groups like regime/seed/alpha/baseline/client. | Domain-specific dataclasses. | `SUSPECTED` | PKT-003 |
| Duplicate typed shapes | Confusing return contracts and needless conversions. | Search duplicate `NamedTuple`, dataclass, and result objects with same fields. | Merge into canonical typed object. | `SUSPECTED` | PKT-003 |
| Vague utility/common modules | Hidden ownership and dumping-ground growth. | Search for `utils`, `helpers`, `misc`, `common`, `shared`. | Domain package owner. | `SUSPECTED` | PKT-003 |
| Over-specified docstrings | Noise and stale documentation. | Search Args/Returns docstrings that repeat type hints. | Local cleanup. | `SUSPECTED` | PKT-009 |
| Unsafe assert type narrowing | Runtime behavior changes under `python -O`. | Search `assert .* is not None` and similar narrowing asserts. | Local guard or typed cast with reason. | `SUSPECTED` | PKT-009 |
| Skipped/xfailed/commented tests | Hidden failures and false confidence. | Search `skip`, `xfail`, `pytest.skip`, commented-out tests. | Test owner. | `SUSPECTED` | PKT-008 |
| Old import-path preservation | Backwards-compatibility drift. | Search obsolete package names after moves. | Delete old tests and update imports. | `SUSPECTED` | PKT-001/PKT-002 |

---

## Confirmed patterns

| Pattern ID | Pattern | Locations | Why local fixes are insufficient | Required central abstraction | Status |
|---|---|---|---|---|---|
| PAT-000 | None confirmed yet. | TBD | TBD | TBD | `SUSPECTED` |

---

## Pattern promotion rule

When a repeated pattern is confirmed:

1. Record exact files and symbols.
2. Select one canonical owner.
3. Update `PROJECT_MAP.md`.
4. Update `MOVE_PLAN.md` or `TEST_MOVE_PLAN.md` if movement is required.
5. Create or update a packet if the fix is larger than the active scope.
6. Fix the smallest safe batch.
7. Run impacted checks.
8. Mark `REAUDIT_REQUIRED` until later integration confirms the pattern stayed fixed.

---

## Anti-patterns to remove

- Local duplicate fixes when a repeated pattern exists across packages.
- Wrapper modules that only preserve old import paths.
- Redirect classes or compatibility aliases after code moves.
- Scattered string literals for closed sets.
- Module-level scientific constants that should be config-driven.
- Duplicate enums for the same domain concept.
- Duplicate constants for the same artifact, metric, dataset, baseline, or regime concept.
- Duplicate dataclasses or `NamedTuple` objects with the same meaning.
- Long primitive argument lists where a typed request/result object is needed.
- Vague `utils`, `helpers`, `common`, `misc`, or `shared` modules without a clear owner.
- Test-only helpers imported by production code.
- Tests that keep obsolete internal package names alive.
- Skips, xfails, or commented-out tests that hide real failures.