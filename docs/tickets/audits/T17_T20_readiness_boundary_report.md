# T17–T20 Readiness Boundary Report

**Date:** 2026-05-24
**Author:** orchestrator-agent
**Status:** STOP — Manual approval required before T17.

---

## Confirmation: T17–T20 NOT Implemented or Executed

| Ticket | Title | Status | Notes |
|--------|-------|--------|-------|
| T17 | FedProx Stress Test Implementation | `NOT_STARTED` | No FedProx code written. No FL training launched. |
| T18 | Ditto/FedRep-AE Fallback Implementation | `NOT_STARTED` | No Ditto/FedRep-AE code written. |
| T19 | Stress-Test Threshold Grid and Absorption | `NOT_STARTED` | No threshold grid or absorption analysis written. |
| T20 | Seed Extension (Seeds 5–9) | `NOT_STARTED` | No seed-extension experiments launched. |

**No FedProx, Ditto, FedRep-AE, stress-test, or seed-extension code was executed. No FL training was launched. No long-running experiments were started.**

---

## Boundary Explanation

```
T16 ← DONE (Phase 2 GB: last stored-score analysis)
─────────────────────────────────────────── BOUNDARY ──
T17 ← NOT_STARTED (Phase 3 GE: stress-test implementation)
T18 ← NOT_STARTED (Phase 3 GE: fallback implementation)
T19 ← NOT_STARTED (Phase 3 GE: threshold grid + absorption)
T20 ← NOT_STARTED (Phase 4: seed extension experiment execution)
```

### What T17–T19 requires (stress-test implementation):
- **T17**: Implement FedProx variant in FL training (`µ` proximal term in client loss). This touches `datp.training.fl` — the first ticket since Phase 1 to modify FL training code. Requires new config fields for `fedprox_mu`.
- **T18**: Implement Ditto and FedRep-AE fallback comparators. Affects `datp.training.fl` and `datp.baselines` — adds new training protocols. Requires new baseline-like labels (not `Baseline` enum members, but supplementary experiment labels).
- **T19**: Run threshold grid over stress-test results from T17–T18. Stored-score analysis like Group GB, but consuming T17–T18 artifacts.

### What T20 requires (experiment execution):
- Extend seeds from 0–4 to 5–9 (5 additional seeds).
- Requires full FL training on all regimes (A/B/C).
- Computationally expensive: 5 seeds × (Regime A + B + 6α Regime C) = ~40 additional training runs.
- Requires GPU, ~1-2 hours per seed for Regime A, more for B/C.

---

## Exact Next Manual Decision Required

Before implementing T17, the user must decide:

1. **FedProx µ parameter**: Value for the proximal term. Typical range: 0.001–1.0. Must be decided before implementation.
2. **Ditto/FedRep-AE scope**: Confirm T18 implements both or only one. FedRep-AE was listed in PRE_CODING_PLAN as fallback-only.
3. **Stress-test scope**: Confirm T19 threshold grid parameters and absorption criteria.
4. **Seed extension timing**: T20 can be parallelized with T17–T19 implementation, but should be authorized separately since it launches actual experiments.

---

## Commands That Would Start Training (NOT RUN)

These commands are listed for reference only. They were **NOT executed**:

```bash
# T17: FedProx stress test would use:
# datp sweep --regime a --supplementary fedprox

# T18: Ditto/FedRep-AE would use:
# datp sweep --regime a --supplementary ditto
# datp sweep --regime a --supplementary fedrep-ae

# T20: Seed extension would use:
# datp sweep --regime a --seeds 5,6,7,8,9
# datp sweep --regime b --seeds 5,6,7,8,9
# datp sweep --regime c --seeds 5,6,7,8,9
```

---

## Prerequisites Before T17

| Prerequisite | Status |
|-------------|--------|
| T01–T04 (Gate 0 verification) | ✅ DONE |
| T05–T16 (all Group GB analyses) | ✅ DONE |
| 40/40 cells VERIFIED_REUSE_SAFE | ✅ Confirmed |
| ruff + pyright clean on all src/ | ✅ Confirmed |
| 92/92 analysis tests pass | ✅ Confirmed |
| CUDA GPU available for FL training | ⚠️ Needs verification before T17–T20 |
| N-BaIoT raw data present | ✅ Confirmed |
| CICIoT2023 raw data present | ✅ Confirmed |

---

## Risks

1. **FL training instability**: FedProx/Ditto/FedRep-AE modify training dynamics. May require hyperparameter tuning. T17–T19 are implementation tasks, not experiment tasks — but training verification steps may be needed.
2. **GPU memory**: FedProx adds computation per round. Memory budget on 11.68 GB system is tight.
3. **Seed extension cost**: 40 additional training runs at ~1-2h/run for Regime A = significant compute time.
4. **B-b permanently suppressed**: CICIoT2023 B-b remains infeasible. T23–T24 implement the formal rejection.

---

## Current State Summary

| Metric | Value |
|--------|-------|
| Tickets complete | T01–T16 (16 of 28) |
| Phase 2 (GB) complete | All 12 stored-score analyses (T05–T16) |
| Tests passing | 92 analysis + 124 full suite |
| Code quality | ruff: 0 errors, pyright: 0 errors |
| DATP invariants | All preserved |
| Scope drift | None |
| Next ticket | T17 — awaiting manual approval |
