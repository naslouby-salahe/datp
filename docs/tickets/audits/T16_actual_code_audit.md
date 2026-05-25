# T16 Actual Code Audit

**Date:** 2026-05-24
**Auditor:** orchestrator-agent
**Method:** Read ticket, read source, read tests, ran all quality gates.

---

## Verdict: PASS

---

## Acceptance Criteria Checklist

| # | Criterion | Source | Status |
|---|-----------|--------|--------|
| 1 | CDF figure includes all 9 Regime A devices | Ticket §Acceptance 1 | ✅ `_write_cdf_grid` renders 3×3 subplot grid |
| 2 | Threshold lines for B1, B2, B4 overlaid | Ticket §Acceptance 2 | ✅ `axvline` for b1_tau, b2_tau, b4_tau per client |
| 3 | Failure-mode table uses canonical device names | Ticket §Acceptance 3 | ✅ `DEVICE_DIRS` from `nbaiot/spec.py` |
| 4 | No filtering of devices | Ticket §Acceptance 4 | ✅ Iterates all `sorted(cal_errors)`, no skip logic |
| 5 | Per-client benign/attack empirical CDF | Ticket §Impl Req 1 | ✅ `_empirical_cdf()` for benign + attack |
| 6 | B1, B2, B4 thresholds computed per client | Ticket §Impl Req 3 | ✅ `derive_threshold()` for B1/B2/B4 |
| 7 | Failure modes identified | Ticket §Impl Req 5 | ✅ `_classify_failure()` with 5 categories |
| 8 | Canonical device names used | Ticket §Checks | ✅ Import from `DEVICE_DIRS` |
| 9 | No retraining | All tickets | ✅ Only `derive_threshold` + `ScoreProvider.load_test_scores` |

---

## Files Created

| File | Description |
|------|-------------|
| `src/datp/analyses/mechanism/per_client_cdf.py` | ~240 lines — CDF analysis module |
| `tests/unit/analyses/mechanism/test_per_client_cdf.py` | 12 test cases |

## Files Modified

| File | Change |
|------|--------|
| `src/datp/analyses/__init__.py` | Added `FailureModeRow`, `PerClientCDFResult`, `run_per_client_cdf` exports |
| `docs/tickets/T16.md` | Status `DONE` with resolution record |
| `docs/tickets/ticket_inventory.md` | T16 → `DONE` |
| `docs/tickets/ticket_progress.md` | Current → T17, last completed → T16 |

---

## Tests Run

```
python -m pytest tests/unit/analyses/mechanism/test_per_client_cdf.py -v
Result: 12 passed in 3.38s

python -m pytest tests/unit/analyses/ -q
Result: 92 passed in 15.65s
```

### Test cases:
| Class | Cases | Coverage |
|-------|-------|----------|
| `TestEmpiricalCDF` | 2 | Known array CDF, subsampling |
| `TestClassifyFailure` | 6 | NORMAL, HIGH_FPR_B1, LOW_TPR_B1, HIGH_FPR_B2, LOW_TPR_B2, combined |
| `TestRunPerClientCDF` | 4 | All 9 devices, canonical names, no Regime A error, write_outputs |

---

## Quality Gates

| Gate | Result |
|------|--------|
| `ruff check src/datp/analyses/mechanism/per_client_cdf.py` | All checks passed |
| `pyright src/datp/analyses/mechanism/per_client_cdf.py` | 0 errors, 0 warnings, 0 informations |
| Unit tests (T16) | 12/12 passed |
| Full analysis suite | 92/92 passed |

---

## No-Training Verification

- Zero imports from `datp.training`, `datp.models`, `flwr`, `ray`
- All threshold derivation via `derive_threshold()` (numpy)
- All score loading via `ScoreProvider` (Parquet reads)

---

## No-Drift Verification

- No new Baseline enum members
- No new baseline labels
- No retraining
- No experiment execution
- B1/B2/B4 definitions unchanged
- Config-driven parameters
- Canonical modules reused

---

## Remaining Risks

None. T16 is a straightforward stored-score visualization/analysis.
