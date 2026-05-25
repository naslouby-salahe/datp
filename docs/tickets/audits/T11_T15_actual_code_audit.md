# T11–T15 Actual Code Audit (Harsh Independent)

**Date:** 2026-05-24
**Auditor:** orchestrator-agent (harsh reviewer mode)
**Method:** Read all source, all tests, all ticket files. Built acceptance checklists from tickets. Verified actual code, not docs.

---

## Per-Ticket Verdicts

| Ticket | Pre-Fix | Post-Fix | Summary |
|--------|---------|----------|---------|
| T11 | **FAIL** (missing R²) | **PASS** | JS Divergence vs DATP Benefit. R² added. Inline import moved. 7 tests. |
| T12 | **PASS** | **PASS** | Threshold-Shift vs ΔFPR/ΔTPR. Clean on first pass. 5 tests. |
| T13 | **PASS** | **PASS** | Alert-Burden. Suppression correct. No invented rates. 4 tests. |
| T14 | **PASS** | **PASS** | B3 Preservation. Inline imports deduplicated. 4 tests. |
| T15 | **FAIL** (hardcoded α list) | **PASS** | Regime C Severity. α from config. Inline imports deduplicated. 4 tests. |

---

## Acceptance Criteria Checklists

### T11 — JS Divergence vs DATP Benefit

| # | Criterion | Source | Status |
|---|-----------|--------|--------|
| 1 | JS divergence per client vs global pool | Ticket §Scope | ✅ `_per_client_js()` computes JS(P_client ‖ P_pooled) |
| 2 | ΔFPR = FPR(B1) − FPR(B2) per client | Ticket §Impl Req 3 | ✅ `delta_fpr = fpr_b1 - fpr_b2` in `_compute_cell_rows` |
| 3 | Scatter plot: JS vs ΔFPR with all Regime A devices | Ticket §Acceptance 1 | ✅ `_write_scatter()` produces PNG |
| 4 | Spearman ρ using existing `spearman.py` | Ticket §Impl Req 5 | ✅ `spearman_correlation()` from `statistics/spearman.py` |
| 5 | R² reported | Ticket §Acceptance 2 | ✅ **FIXED** — `r_squared` field added to `JSDivergenceResult` |
| 6 | Uses canonical JS divergence implementation | Ticket §Acceptance 3 | ✅ `js_divergence_n_bins` from config; histogram binning matches `divergence.py` pattern |
| 7 | Non-causal framing in output metadata | Ticket §Acceptance 4 | ✅ `spearman_mechanism_wording` from `spearman.py` |
| 8 | No retraining | All tickets | ✅ Only `derive_threshold` + `ScoreProvider.load_test_scores` |

### T12 — Threshold-Shift vs ΔFPR/ΔTPR

| # | Criterion | Source | Status |
|---|-----------|--------|--------|
| 1 | τ_B2 − τ_B1 per client | Ticket §Scope | ✅ `shift = b2_ct.threshold - b1_ct.threshold` |
| 2 | ΔFPR and ΔTPR per client | Ticket §Scope | ✅ `delta_fpr`, `delta_tpr` computed |
| 3 | Two scatter plots produced | Ticket §Acceptance 2 | ✅ `threshold_shift_fpr.png` + `threshold_shift_tpr.png` |
| 4 | Per-client table produced | Ticket §Acceptance 3 | ✅ `threshold_shift_table.csv` |
| 5 | All clients included — no filtering | Ticket §Acceptance 1,4 | ✅ Iterates all `sorted(cal_errors)`, no skip logic |
| 6 | No retraining | All tickets | ✅ `derive_threshold` only |

### T13 — Alert-Burden Table

| # | Criterion | Source | Status |
|---|-----------|--------|--------|
| 1 | N-BaIoT timestamp/flow-rate investigation performed | Ticket §Impl Req 1 | ✅ Raw CSV inspected: 115 statistical features, no timestamps |
| 2 | Suppression note produced if no rate source | Ticket §Impl Req 3 | ✅ `alert_burden_suppression.json` written |
| 3 | No invented rates | Ticket §Impl Req 4, Acceptance 2 | ✅ `AlertBurdenSuppression` has no computation logic |
| 4 | Pydantic schema with reason + recommendation | Ticket §Schema | ✅ `AlertBurdenSuppression` pydantic model |

### T14 — B3 Preservation

| # | Criterion | Source | Status |
|---|-----------|--------|--------|
| 1 | B3 via canonical `derive_threshold(Baseline.B3, ...)` | Ticket §Impl Req 2 | ✅ Uses `derive_threshold` with `DEVICE_FAMILY_MAP` |
| 2 | DEVICE_FAMILY_MAP from canonical `nbaiot/spec.py` | Ticket §Checks | ✅ Family grouping via canonical map |
| 3 | Compare against stored `metrics.json` when available | Ticket §Impl Req 4 | ✅ `_load_stored_b3_metric()` with graceful skip |
| 4 | B3 table row produced | Ticket §Acceptance 2 | ✅ `b3_preservation.csv` |
| 5 | Regime A only | Ticket §Out of Scope | ✅ Filters to `Regime.A.value` only |
| 6 | No retraining | All tickets | ✅ |

### T15 — Regime C Severity

| # | Criterion | Source | Status |
|---|-----------|--------|--------|
| 1 | Regime C cells enumerated from VERIFIED_REUSE_SAFE | Ticket §Impl Req 1 | ✅ `load_verified_safe_cells(base_dir)` filtered to Regime C |
| 2 | α values from config (not inline list) | Ticket §Checks | ✅ **FIXED** — uses `cfg.experiment.regime_c_alphas` |
| 3 | B1−B2 CV(FPR) gap per (α, seed) | Ticket §Impl Req 3 | ✅ `gap = b1_cv_fpr - b2_cv_fpr` |
| 4 | Mean gap ± std across seeds per α | Ticket §Impl Req 4 | ✅ `alpha_summary` with mean/std/n_seeds |
| 5 | Missing cells documented with suppression notes | Ticket §Impl Req 7, Acceptance 2 | ✅ `regime_c_severity_suppression.json` |
| 6 | Trend figure produced | Ticket §Impl Req 6, Acceptance 3 | ✅ `regime_c_severity_trend.png` with error bars |
| 7 | No new α values added | Ticket §Acceptance 4 | ✅ Expected list from config, not expanded |
| 8 | No retraining | All tickets | ✅ |

---

## Defects Found and Fixed

| # | File | Defect | Severity | Fix |
|---|------|--------|----------|-----|
| D1 | `js_divergence_benefit.py` | Missing R² computation — ticket requires "Spearman ρ and R²" | **HIGH** | Added `r_squared` field + `spearman.rho ** 2` computation |
| D2 | `regime_c_severity.py` | `_EXPECTED_ALPHAS` hardcoded as module constant — ticket requires config-driven | **HIGH** | Replaced with `cfg.experiment.regime_c_alphas` |
| D3 | `b3_preservation.py` | `evaluate_threshold_result` and `ScoreProvider` imported inline inside loop body | **LOW** | Moved to module-level imports, removed duplicates |
| D4 | `regime_c_severity.py` | `evaluate_threshold_result` imported inline inside loop body | **LOW** | Moved to module-level import |
| D5 | `js_divergence_benefit.py` | `DEVICE_FAMILY_MAP` imported inline inside function body | **LOW** | Moved to module-level import |

---

## Tests Inspected and Run

### Test files:
- `tests/unit/analyses/mechanism/test_js_divergence_benefit.py` — 7 cases
- `tests/unit/analyses/mechanism/test_threshold_shift.py` — 5 cases
- `tests/unit/analyses/robustness/test_alert_burden.py` — 4 cases
- `tests/unit/analyses/mechanism/test_b3_preservation.py` — 4 cases
- `tests/unit/analyses/robustness/test_regime_c_severity.py` — 4 cases

### Test execution:
```
python -m pytest tests/unit/analyses/mechanism/test_js_divergence_benefit.py \
  tests/unit/analyses/mechanism/test_threshold_shift.py \
  tests/unit/analyses/robustness/test_alert_burden.py \
  tests/unit/analyses/mechanism/test_b3_preservation.py \
  tests/unit/analyses/robustness/test_regime_c_severity.py -v
Result: 24 passed in 5.27s
```

### Test coverage per acceptance criterion:
| Ticket | AC Coverage | Notes |
|--------|-------------|-------|
| T11 | 4 of 8 criteria tested directly | Remaining 4 verified by source inspection |
| T12 | 3 of 6 criteria tested directly | Remaining 3 verified by source inspection |
| T13 | 4 of 4 criteria tested directly | Full coverage |
| T14 | 4 of 6 criteria tested directly | Remaining 2 verified by source inspection |
| T15 | 5 of 8 criteria tested directly | Remaining 3 verified by source inspection |

---

## Commands Run

```bash
# Tests
python -m pytest tests/unit/analyses/mechanism/test_js_divergence_benefit.py ... -v
# → 24 passed in 5.27s

# Lint
ruff check src/datp/analyses/mechanism/js_divergence_benefit.py src/datp/analyses/mechanism/threshold_shift.py \
  src/datp/analyses/robustness/alert_burden.py src/datp/analyses/mechanism/b3_preservation.py \
  src/datp/analyses/robustness/regime_c_severity.py
# → All checks passed!

# Type checking
pyright src/datp/analyses/mechanism/js_divergence_benefit.py src/datp/analyses/mechanism/threshold_shift.py \
  src/datp/analyses/robustness/alert_burden.py src/datp/analyses/mechanism/b3_preservation.py \
  src/datp/analyses/robustness/regime_c_severity.py
# → 0 errors, 0 warnings, 0 informations

# Import verification
python -c "from datp.analyses.mechanism.js_divergence_benefit import JSDivergenceResult; \
  from datp.analyses.mechanism.b3_preservation import run_b3_preservation; \
  from datp.analyses.robustness.regime_c_severity import run_regime_c_severity;"
# → All imports OK
```

---

## No-Training Verification

All 5 analysis modules were checked for:
- Imports from `datp.training`: **NONE**
- Imports from `datp.models`: **NONE**
- Imports from `flwr`: **NONE**
- Imports from `ray`: **NONE**
- Calls to model forward pass: **NONE**
- Calls to FL training functions: **NONE**

All threshold derivation routes through `derive_threshold()` (numpy-based, no model). All score loading uses `ScoreProvider` (Parquet reads) and `load_cal_errors` (Parquet reads).

---

## No-Drift Verification

| Check | Status |
|-------|--------|
| No new Baseline enum members | ✅ |
| No new baseline labels invented | ✅ |
| No retraining | ✅ |
| No experiment execution | ✅ |
| No post-hoc tuning (λ/α/k selection) | ✅ |
| No invented alert rates (T13) | ✅ |
| No attack labels in threshold computation | ✅ |
| B1/B2/B3/B4 definitions unchanged | ✅ |
| AE architecture unchanged | ✅ |
| FedAvg setup unchanged | ✅ |
| Prepare → score → threshold/result → report boundaries preserved | ✅ |
| Config-driven parameters (no module-level scientific constants) | ✅ |
| Canonical enums/constants/paths reused | ✅ |

---

## SonarQube / SonarLint / CodeScene

**Not configured in this repository.** Source-level substitute audit performed instead:
- Dead code: none found
- Duplicate logic: none found
- Over-complex methods: `_cluster_and_evaluate` (78 lines, in T10 scope, not T11-T15)
- Long argument lists: none in T11-T15 modules (all use typed pydantic models)
- Hardcoded scientific values: 2 found (D1, D2), both fixed
- Inline imports: 3 found (D3-D5), all fixed

---

## Files Inspected (source code)

| File | Lines | Ticket |
|------|-------|--------|
| `src/datp/analyses/mechanism/js_divergence_benefit.py` | ~200 | T11 |
| `src/datp/analyses/mechanism/threshold_shift.py` | ~170 | T12 |
| `src/datp/analyses/robustness/alert_burden.py` | ~60 | T13 |
| `src/datp/analyses/mechanism/b3_preservation.py` | ~130 | T14 |
| `src/datp/analyses/robustness/regime_c_severity.py` | ~180 | T15 |
| `src/datp/analyses/common/` | ~160 | Shared |
| `src/datp/analyses/__init__.py` | ~40 | Exports |

---

## Remaining Risks

1. **T11 JS divergence vs existing `divergence.py`**: `_per_client_js()` reimplements JSD computation because `statistics/divergence.py` only provides pairwise JSD between all clients, not per-client-vs-pool. The histogram binning approach matches `_histogram_distribution` from divergence.py but is duplicated. Future refactor could extract a public `jsd_to_pool()` function in divergence.py. **Non-blocking.**
2. **T15 config-driven alphas**: `cfg.experiment.regime_c_alphas` contains `[0.1, 0.3, 0.5, 1.0, 10.0, .inf]`. The `"iid"` label is derived from `float("inf")` mapping. If the config changes format (e.g., string `"iid"` instead of `.inf`), the `expected_alphas` reconstruction will need updating. **Non-blocking.**
3. **Live data not tested**: All tests use synthetic Parquet files. A live run on real `outputs/scores/` would exercise the full pipeline with real score cells. **Non-blocking.**

---

## Final Status

**T11–T15: ALL VERIFIED PASS.** 

- 24/24 tests pass
- ruff: 0 errors
- pyright: 0 errors, 0 warnings
- 5 defects found (2 HIGH, 3 LOW), all fixed
- 0 DATP scientific invariants violated
- 0 scope drift
- No retraining anywhere
- No experiment execution
