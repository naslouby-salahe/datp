# T11–T15 Implementation Audit

**Date:** 2026-05-24
**Implementor:** orchestrator-agent
**Method:** Code-verified — all acceptance criteria checked against actual source and tests.

---

## Per-Ticket Verdicts

| Ticket | Verdict | Summary |
|--------|---------|---------|
| T11 | **PASS** | JS Divergence vs DATP Benefit. Per-client JS(P_client ‖ P_pooled), Spearman ρ vs ΔFPR. 7 tests. |
| T12 | **PASS** | Threshold-Shift vs ΔFPR/ΔTPR. τ_B2−τ_B1 per client, scatter plots. All clients included. 5 tests. |
| T13 | **PASS (SUPPRESSED)** | Alert-Burden Table. N-BaIoT has no timestamps/flow rates → suppression note. 4 tests. |
| T14 | **PASS** | B3 Preservation. Family-mean threshold reproduced from stored scores. 4 tests. |
| T15 | **PASS** | Regime C Severity. α-sweep gap analysis with missing-cell suppression. 4 tests. |

---

## Files Created

| File | Ticket | Description |
|------|--------|-------------|
| `src/datp/analyses/js_divergence_benefit.py` | T11 | JS divergence per-client vs pool, Spearman correlation, scatter plot |
| `src/datp/analyses/threshold_shift.py` | T12 | τ-shift vs ΔFPR/ΔTPR, all clients included |
| `src/datp/analyses/alert_burden.py` | T13 | Suppression-only — N-BaIoT lacks timestamps/flow rates |
| `src/datp/analyses/b3_preservation.py` | T14 | B3 reproduction from stored scores via DEVICE_FAMILY_MAP |
| `src/datp/analyses/regime_c_severity.py` | T15 | Regime C α-sweep gap analysis with suppression for missing α |
| `tests/unit/analyses/test_js_divergence_benefit.py` | T11 | 7 test cases |
| `tests/unit/analyses/test_threshold_shift.py` | T12 | 5 test cases |
| `tests/unit/analyses/test_alert_burden.py` | T13 | 4 test cases |
| `tests/unit/analyses/test_b3_preservation.py` | T14 | 4 test cases |
| `tests/unit/analyses/test_regime_c_severity.py` | T15 | 4 test cases |

## Files Modified

| File | Change |
|------|--------|
| `src/datp/analyses/__init__.py` | Added exports for all 5 new modules |

---

## Tests Run

```
python -m pytest tests/unit/analyses/ -v
Result: 80 passed in 14.63s
```

### Test breakdown:
| Test File | Cases | Result |
|-----------|-------|--------|
| `test_js_divergence_benefit.py` | 7 | ALL PASS |
| `test_threshold_shift.py` | 5 | ALL PASS |
| `test_alert_burden.py` | 4 | ALL PASS |
| `test_b3_preservation.py` | 4 | ALL PASS |
| `test_regime_c_severity.py` | 4 | ALL PASS |
| T01-T10 tests (existing) | 56 | ALL PASS |
| **Total** | **80** | **ALL PASS** |

Full cross-suite: 124/124 pass (including audit tests).

---

## Quality Gates

| Gate | Result |
|------|--------|
| `ruff check src/datp/analyses/` | All checks passed |
| `pyright src/datp/analyses/` | 0 errors, 0 warnings, 0 informations |
| Unit tests (all analyses) | 80/80 passed |
| Full suite (analyses + audit) | 124/124 passed |

---

## Acceptance Criteria — Per-Ticket

### T11 — JS Divergence vs DATP Benefit
- [x] JS divergence computed per-client vs global pool
- [x] ΔFPR = FPR(B1) − FPR(B2) per client
- [x] Spearman ρ reported via canonical `spearman_correlation()`
- [x] Scatter plot produced (`js_divergence_scatter.png`)
- [x] Table with all clients, seeds, device families (`js_divergence_table.csv`)
- [x] Non-causal framing in metadata ("HYPOTHESIS"/"EMPIRICAL" from spearman.py)
- [x] Uses canonical `js_divergence_n_bins` from config

### T12 — Threshold-Shift vs ΔFPR/ΔTPR
- [x] τ_B2 − τ_B1 computed per client
- [x] ΔFPR and ΔTPR computed per client
- [x] Two scatter plots: shift vs ΔFPR, shift vs ΔTPR
- [x] Per-client table with all values (`threshold_shift_table.csv`)
- [x] All clients included — no filtering
- [x] Device family included per client

### T13 — Alert-Burden Table
- [x] N-BaIoT raw data inspected: 115 statistical features only — NO timestamps, NO flow rates
- [x] Per stop condition: no rate source found → suppression note produced
- [x] `alert_burden_suppression.json` explains the suppression reason
- [x] No invented rates anywhere

### T14 — B3 Preservation
- [x] B3 reproduced via canonical `derive_threshold(Baseline.B3, ...)` 
- [x] DEVICE_FAMILY_MAP used for family grouping (from canonical `nbaiot/spec.py`)
- [x] B3 table row produced (`b3_preservation.csv`)
- [x] Regime A only (B3 is not defined for B/C)
- [x] Stored reference comparison attempted (graceful when absent)

### T15 — Regime C Severity Analysis
- [x] Regime C cells enumerated from VERIFIED_REUSE_SAFE verdicts
- [x] B1−B2 CV(FPR) gap computed per (α, seed)
- [x] α summary with mean ± std across seeds
- [x] Missing α documented in `regime_c_severity_suppression.json`
- [x] Trend figure with error bars (`regime_c_severity_trend.png`)
- [x] Expected α grid: [0.1, 0.3, 0.5, 1.0, 10.0, iid] — verified against found cells

---

## No-Training Confirmation

All 5 analyses are **stored-score analyses only**:
- All load scores via `load_cal_errors()` + `ScoreProvider` (reads Parquet)
- All derive thresholds via `derive_threshold()` (numpy computation on loaded arrays)
- Zero imports from `datp.training`, `datp.models`, `flwr`, `Ray`
- Zero calls to any training or model forward-pass function

---

## No-Drift Confirmation

| Check | Status |
|-------|--------|
| No new Baseline enum members | ✓ |
| No new baseline labels invented | ✓ |
| No retraining | ✓ |
| No experiment execution | ✓ |
| No post-hoc tuning (λ/α/k selection) | ✓ |
| No invented alert rates (T13) | ✓ |
| No attack labels in threshold computation | ✓ |
| B1/B2/B3/B4 definitions unchanged | ✓ |
| AE architecture unchanged | ✓ |
| FedAvg setup unchanged | ✓ |
| Prepare → score → threshold/result → report boundaries preserved | ✓ |
| Config-driven parameters (no module-level scientific constants) | ✓ |
| Canonical enums/constants/paths reused | ✓ |

---

## Output Artifacts Produced (when write_outputs=True)

| Ticket | Artifacts |
|--------|-----------|
| T11 | `analysis/js_divergence_table.csv`, `analysis/js_divergence_scatter.png` |
| T12 | `analysis/threshold_shift_table.csv`, `analysis/threshold_shift_fpr.png`, `analysis/threshold_shift_tpr.png` |
| T13 | `analysis/alert_burden_suppression.json` |
| T14 | `analysis/b3_preservation.csv` |
| T15 | `analysis/regime_c_severity_table.csv`, `analysis/regime_c_severity_trend.png`, `analysis/regime_c_severity_suppression.json` (if missing α) |

---

## Remaining Risks

1. **Regime C live data**: Unit tests use synthetic data. A live run on real `outputs/scores/c/` would verify actual cell completeness.
2. **B3 stored reference**: The B3 preservation module compares against stored `metrics.json` if available; gracefully skips if absent. Live run would exercise the comparison path.
3. **T13 permanently suppressed**: N-BaIoT truly lacks timestamps/flow rates — this is a dataset property, not a code issue.

---

## Final Status

**T11–T15: ALL IMPLEMENTED AND VERIFIED.** Ready for T16.
