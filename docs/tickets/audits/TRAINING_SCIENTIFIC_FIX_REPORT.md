# Training Scientific Fix Report

**Date:** 2026-05-25  
**Branch:** journal/datp-extension  
**Verdict:** PASS_WITH_WARNINGS

All critical correctness issues resolved. One structural blocker (FedRep-AE decoder persistence) remains intentionally guarded. No scientific drift introduced.

---

## Executive Summary

Three passes were completed over `src/datp/training/`, related tests, `docs/journal/`, and `docs/tickets/`. Six correctness or consistency issues were found and fixed. Two pre-existing test failures (test fixture mismatch, mock strategy gap) were repaired. All 99 targeted tests now pass.

---

## Files Changed

### Code
| File | Change |
|------|--------|
| `src/datp/training/strategies.py` | Renamed `_failures` → `failures` in `aggregate_evaluate` to match base class signature; eliminates Pyright `reportIncompatibleMethodOverride` ✘ ERROR |
| `src/datp/training/communication.py` | Added non-obvious comments for B2=0 (local-only, no comm) and B4 fingerprint dimensions (4-up/2-down per client) |

### Tests
| File | Change |
|------|--------|
| `tests/unit/training/test_convergence.py` | `TestStallDetection.test_stall_warning_logged`: changed `failures=[]` keyword call → positional call `(1, [...], [])` to match renamed parameter |
| `tests/unit/training/test_scoring.py` | `TestLoadModelFromCheckpoint._write_checkpoint`: replaced hardcoded `input_dim=10, hidden_dims=[8,4]` with `BASE_CONFIG.model` dimensions; checkpoint was silently mismatched against `BASE_CONFIG`-built model |
| `tests/unit/training/test_simulation.py` | `TestClientDataNotMutated`: `build_strategy=lambda *a: None` → `MagicMock` strategy; `run_fl_simulation` accesses `strategy.convergence_monitor` before `make_client_fn`, which broke the test after `simulation.py` was updated |

### Journal Documentation
| File | Change |
|------|--------|
| `docs/journal/CODING_PLAN.md` | Reuse Map: replaced stale `src/datp/training/fl/` path with `src/datp/training/` + `protocols/` |
| `docs/journal/PRE_CODING_PLAN.md` | Repository Readiness table: same stale path fixed |

### Tickets
| File | Change |
|------|--------|
| `docs/tickets/T17.md` | Status corrected from `NOT_STARTED` → `DONE`; Resolution Record added |
| `docs/tickets/T18.md` | Resolution Record added explaining `run_fedrep_training()` `NotImplementedError` guard, root cause, and what remains blocked |
| `docs/tickets/ticket_progress.md` | "Next recommended action" corrected from stale `T19` to `T23 → T26` |

---

## What Was Fixed

1. **Pyright ✘ ERROR in `strategies.py`**: `_failures` had a leading underscore (to suppress unused-variable lint) but the base class `FedAvg.aggregate_evaluate` uses `failures`. Pyright flagged `reportIncompatibleMethodOverride` as a blocking ERROR. Fixed by matching the base class name.

2. **Test failure — wrong keyword arg**: `TestStallDetection` called `strategy.aggregate_evaluate(server_round=1, ..., failures=[])` which failed at runtime because the parameter was named `_failures`. Fixed by switching to positional call.

3. **Test failure — checkpoint shape mismatch**: `TestLoadModelFromCheckpoint._write_checkpoint` built a model with `input_dim=10` but `load_model_from_checkpoint` builds from `BASE_CONFIG.model.input_dim=115`. `load_state_dict` raised `RuntimeError`. Fixed by deriving test checkpoint from `BASE_CONFIG`.

4. **Test failure — mock strategy gap**: `TestClientDataNotMutated` passed `build_strategy=lambda *a: None` but `run_fl_simulation` now reads `strategy.convergence_monitor` before calling `make_client_fn`. Fixed by providing `MagicMock()`.

5. **Communication formula undocumented**: B2's zero comm overhead requires knowing B2 is purely local (non-obvious). B4's 4× uplink/2× downlink multipliers require knowing the fingerprint is `[mean_e, std_e, skew_e, p95_e]`. Added comments at both points.

6. **Stale path references in journal docs**: `src/datp/training/fl/` does not exist (code was refactored into `src/datp/training/` + `protocols/`). Fixed in both CODING_PLAN and PRE_CODING_PLAN.

7. **T17.md status drift**: Inventory and progress files confirmed DONE; ticket file still said NOT_STARTED. Corrected and Resolution Record added.

8. **T18.md missing blocker documentation**: T18 was marked DONE but `run_fedrep_training()` raises `NotImplementedError`. Without explanation, this looks like a code defect. Resolution Record added clarifying the guard is intentional scientific protection and exactly what must be built to unblock it (save each client's decoder state dict to `base_dir/fedrep/{client_id}/decoder.pt`).

9. **ticket_progress.md stale next action**: "Proceed with T19" was never updated after T19 completed (entry 029). Corrected to `T23 → T26`.

---

## Training Scientific Correctness Checklist

| Invariant | Status | Evidence |
|-----------|--------|----------|
| FedAvg is the canonical FL path | VERIFIED | `simulation.py`, `strategies.py`, `DatpFedAvg` extends `flwr.server.strategy.FedAvg` |
| Threshold baselines do not trigger retraining | VERIFIED | B1–B4 all read from shared score parquets; no training call in any baseline module |
| Shared score artifacts live outside B1/B2/B3/B4 subdirs | VERIFIED | `scoring.py` writes to `score_base / stage / {cid}.parquet`; baseline prefix never inserted |
| Convergence: relative change between window start and end | VERIFIED | `convergence.py`: `rel_change = abs(end - start) / abs(start)` where start/end are first/last in window |
| Convergence fires only after `rounds_initial` | VERIFIED | `should_stop()` returns False before `rounds_initial` |
| `get_device()` raises if CUDA unavailable (no silent fallback) | VERIFIED | `device.py` raises `RuntimeError`; `load_model_from_checkpoint` calls it unconditionally |
| FedRep-AE is NOT Ditto | VERIFIED | Module docstring, `DatpFedRepClient` has encoder-only aggregation + per-client decoder; no proximal term; not Ditto |
| FedProx is stress-test only | VERIFIED | `run_fedprox_training()` callable but its results are not promoted to main claims |
| `_STAGE_TO_ATTR` maps CAL → "val" | VERIFIED | `scoring.py`: `ScoringStage.CAL: "val"` — calibration split is the `val` tensor in `ClientData` |
| Ray num_gpus=0.0 for actors is intentional | VERIFIED | `_NO_RAY_GPU = 0.0` constant; actors load on CPU via `_load_scoring_data` |
| Stage boundaries respected | VERIFIED | `run_fl_simulation` trains and scores; threshold baselines are downstream and never call training |

---

## FedRep-AE Status

- **Client logic**: IMPLEMENTED (`protocols/fedrep.py`)
  - Encoder-only aggregation via `get_parameters()` / `set_parameters()`
  - Phase 1: `train_decoder_only()`, Phase 2: `train_local()` (full model)
  - Returns encoder parameters only
- **Naming guard**: IMPLEMENTED — module docstring explicitly states "NOT Ditto"
- **`run_fedrep_training()` guard**: `NotImplementedError` — intentional scientific correctness protection
- **Root cause of block**: Decoder state exists only in ephemeral Ray actor memory; scoring with aggregated encoder + untrained decoder produces misleading reconstruction errors
- **What unblocks it**: Save each client's decoder state dict to `base_dir/fedrep/{client_id}/decoder.pt` at end of `fit()`, then load per-client decoder for scoring
- **Docs/tickets match**: T18.md Resolution Record now documents this precisely
- **Journal experiment GE-02 (FedRep-AE absorption table)**: Cannot run until decoder persistence is implemented

---

## FedProx Status

- **Implementation**: DONE (`protocols/fedprox.py`)
  - `DatpFedProxClient` adds proximal term `(mu/2)||w - w_global||²` to local loss
  - µ grid `{0.0, 0.001, 0.01, 0.1, 1.0}` flows from caller
  - Checkpoint path: `base_dir/fedprox/mu_{mu:g}/seed_{seed}/`
  - FedProx is NOT in `Baseline` enum — stress-test comparator only, not a main claim
- **Docs/tickets match**: T17.md now has accurate DONE status and Resolution Record
- **Scientific framing**: Stress-test comparator; results must not appear in main B1–B4 claim tables

---

## Convergence Status

- **Journal-documented rule**: Relative improvement check over a sliding window, after `rounds_initial` warm-up, with hard cap at `rounds_max`
- **Implemented rule**: `rel_change = abs(end_loss - start_loss) / abs(start_loss)` where `start_loss = window[0]`, `end_loss = window[-1]`; fired when `rel_change <= relative_threshold`
- **Match**: MATCH — no conflict with journal docs
- **Hard cap**: Fires at `rounds_max` regardless of loss (verified by `TestHardCap`)
- **Fix applied**: None needed; confirmed correct

---

## CUDA / Device Status

- **Expected policy**: CUDA required; raise `RuntimeError` if unavailable; no CPU fallback in training/scoring
- **Implemented behavior**: `get_device()` in `core/device.py` raises `RuntimeError` if `not torch.cuda.is_available()`; `load_model_from_checkpoint` calls it unconditionally; confirmed by `test_fails_clearly_when_device_unavailable`
- **Fix applied**: None needed; confirmed correct

---

## Scoring / Checkpoint Status

- **Shared score artifact path**: `outputs/scores/<regime>/seed_<N>[/alpha_<alpha>]/<stage>/<client_id>.parquet`
- **Baseline subdirectory**: Never inserted between `seed_*` and `stage/`
- **Checkpoint path (FedAvg)**: `ckpt_dir / "model.pt"` via `save_checkpoint()`
- **Checkpoint path (FedProx)**: `base_dir/fedprox/mu_{mu:g}/seed_{seed}/model.pt`
- **Checkpoint path (FedRep-AE)**: Blocked — decoder state not persisted
- **`_STAGE_TO_ATTR` mapping**: `CAL → "val"`, `TEST_BENIGN → "test_benign"`, `TEST_ATTACK → "test_attack"` — all confirmed correct
- **Fix applied**: None needed; confirmed correct

---

## Tests Run

| Suite | Result |
|-------|--------|
| `tests/unit/training/` | 98 passed |
| `tests/integration/training/test_comm_overhead.py` | 1 passed |
| **Total** | **99 passed, 0 failed** |

Tests not run (per task hard rule): end-to-end FL simulations, Ray/Flower campaign runs, experiment pipelines.

---

## Remaining Risks

1. **FedRep-AE GE-02 is structurally blocked**: Journal experiment GE-02 cannot produce the absorption table without decoder persistence. This is documented and guarded. No experiment should be launched until `base_dir/fedrep/{client_id}/decoder.pt` save/load is implemented and a repair ticket is created.

2. **FedProx µ=0.0 equivalence untested**: µ=0.0 should produce results identical to plain FedAvg. There is no test verifying this. Low risk (the proximal term vanishes mathematically), but if numerical drift matters for the stress-test comparison it should be verified.

---

## Stable Areas — Do Not Drift

These were verified correct and must not be changed without deliberate review:

- `_STAGE_TO_ATTR` mapping in `scoring.py`
- `get_device()` CUDA-only policy in `core/device.py`
- `ConvergenceMonitor` algorithm (start/end relative change, not half-window means)
- FedRep-AE encoder-only aggregation in `protocols/fedrep.py`
- `_NO_RAY_GPU = 0.0` in `simulation.py`
- Score artifact path structure (never under B1/B2/B3/B4 subdirs)
- `run_fedrep_training()` `NotImplementedError` guard
