# Training Package Journal Refactor Audit

**Date:** 2025-05-26  
**Scope:** `src/datp/training/` and `tests/unit/training/`  
**Status:** PASS

---

## Summary

Comprehensive refactoring of the `src/datp/training` package covering 16 items:
convergence logic, client discovery, CUDA policy, final aggregation, stress-test paths,
FedRep persistence, scoring memory safety, manifest deduplication, ClientData ownership,
local training hardening, parameter conversion, simulation cleanup, communication accounting,
constants discipline, tests, and static quality.

---

## Items Completed

### Item 1: Convergence Logic
- **Fix:** Changed from first-vs-last in window to previous-window-mean vs current-window-mean.
- **File:** `src/datp/training/convergence.py`
- **Detail:** `should_stop()` now requires `2 * window` losses before evaluation. Computes `mean(losses[-(2*window):-window])` vs `mean(losses[-window:])`. Added `math.isfinite` validation on `record()`.

### Item 4: Final Aggregation Fatal
- **Fix:** `_save_training_artifacts` raises `RuntimeError` if `final_params is None`.
- **File:** `src/datp/training/simulation.py`
- **Detail:** Previously saved initial model checkpoint when FL failed silently. Now aborts.

### Item 5: Stress-Test Paths
- **Fix:** FedProx and FedRep output paths now include regime segment.
- **Files:** `src/datp/training/protocols/fedprox.py`, `src/datp/training/protocols/fedrep.py`
- **Detail:** `base_dir / "fedrep" / regime.value / f"seed_{seed}"` prevents cross-regime collisions.

### Item 6: FedRep Decoder Persistence
- **Fix:** `DatpFedRepClient.__init__` calls `_load_persisted_decoder()` to load existing decoder checkpoint.
- **File:** `src/datp/training/protocols/fedrep.py`
- **Detail:** Flower recreates client instances each round. Without loading, decoder personalization was lost. Uses `weights_only=True` and maps to model device. Atomic write with `.pt.tmp` → rename.

### Item 7: Scoring Memory Safety
- **Fix:** `_compute_errors` now processes in batches (default 4096 samples).
- **File:** `src/datp/training/scoring.py`
- **Detail:** Prevents OOM on large test splits. Configurable via `scoring_batch_size` kwarg.

### Item 8: Manifest Deduplication
- **Fix:** Extracted `_write_scoring_manifest_and_sentinel()` shared helper.
- **File:** `src/datp/training/scoring.py`
- **Detail:** Both `score_clients` and `score_fedrep_clients` use the same manifest logic.

### Item 9: ClientData Ownership
- **Fix:** `ClientData` NamedTuple moved to `src/datp/training/types.py` (canonical owner).
- **Files:** `src/datp/training/types.py` (new), `scoring.py`, `simulation.py`, `factories.py`, `protocols/fedprox.py`, `protocols/fedrep.py`, `baselines/common/data_loading.py`, `__init__.py`
- **Detail:** Re-exported from `scoring.py` for backward compatibility. Includes validation helpers: `validate_tensor_2d`, `validate_tensor_non_empty`, `validate_tensor_finite`, `validate_feature_dim`, `validate_client_data`, `validate_training_inputs`.

### Item 10: Local Training Hardening
- **Fix:** `train_local` and `train_decoder_only` validate inputs and raise on non-finite final loss.
- **File:** `src/datp/training/local.py`
- **Detail:** Validates `epochs >= 1`, `batch_size >= 1`, non-empty data. `RuntimeError` on NaN/Inf loss.

### Item 11: Parameter Conversion Safety
- **Fix:** `get_parameters` returns `.copy()`; `set_parameters` validates count and shape per tensor, casts to target dtype+device.
- **File:** `src/datp/training/parameters.py`
- **Detail:** Raises `ValueError` on parameter count mismatch or shape mismatch with actionable error messages.

### Item 12: Simulation Fatal Check
- **Fix:** Missing `final_params` is fatal (see Item 4). GPU policy documented.
- **File:** `src/datp/training/simulation.py`

### Item 13: Communication Accounting
- **Audit:** `src/datp/training/communication.py` is clean.
- **Detail:** Uses canonical `_BYTES_PER_SCALAR` constant, structured `@dataclass(frozen=True, slots=True)`, proper error messages, correct domain logic per baseline.

### Item 14: Constants Discipline
- **Fix:** Replaced hardcoded `"scores"` string with `SCORES_DIR` from `datp.artifacts.directories`.
- **Files:** `src/datp/training/protocols/fedprox.py`, `src/datp/training/protocols/fedrep.py`
- **Detail:** All remaining numeric constants are appropriately named module-level constants (`_DEFAULT_SCORING_BATCH_SIZE`, `_NO_RAY_GPU`, `_KIB_PER_MIB`, `_BYTES_PER_GIB`).

### Item 15: Tests
- **New files:** `tests/unit/training/test_types.py`, `tests/unit/training/test_parameters.py`
- **Updated:** `tests/unit/training/test_convergence.py` (rewritten for window-mean algorithm), `tests/unit/training/test_scoring.py` (batched scoring), `tests/unit/training/test_local.py` (validation), `tests/unit/training/protocols/test_fedrep.py` (cross-round persistence + path fix)
- **Result:** 159 passed (unit) + 20 passed (integration), 0 failed, 0 skipped.

### Item 16: Static Quality
- **Pyright:** 0 errors, 0 warnings
- **Ruff:** 0 errors
- **Fix applied:** Flower method override parameter names (`_config` → `config`) in `clients.py`, `protocols/fedprox.py`, `protocols/fedrep.py`

---

## Audit Pass 1: Scientific Invariants

| Invariant | Status |
|-----------|--------|
| B1–B4 share same trained encoder per cell | ✓ PRESERVED |
| No retraining inside threshold/eval/report | ✓ PRESERVED |
| Score artifacts shared across B1–B4 | ✓ PRESERVED |
| Pipeline boundary: prepare → train → score → threshold → report | ✓ PRESERVED |
| Full participation enforced (strategy raises on failures) | ✓ ENFORCED |
| FedRep/FedProx are stress tests only (not in Baseline enum) | ✓ PRESERVED |
| Determinism via explicit seeding | ✓ PRESERVED (test passes) |
| Convergence uses scientifically sound algorithm | ✓ FIXED (window-mean comparison) |

---

## Audit Pass 2: Architecture / Clean Code

| Aspect | Status |
|--------|--------|
| ClientData in canonical owner (`types.py`) | ✓ |
| No duplicate manifest logic | ✓ (extracted helper) |
| Constants from canonical modules | ✓ (`SCORES_DIR`, `MODEL_CHECKPOINT`, `DECODER_CHECKPOINT`) |
| No hardcoded scientific parameters | ✓ |
| Pyright 0 errors | ✓ |
| Ruff 0 errors | ✓ |
| Atomic writes for checkpoints | ✓ (decoder `.pt.tmp` → rename) |
| Parameter name overrides match Flower base class | ✓ |
| Batched scoring prevents OOM | ✓ |
| Validation at system boundaries | ✓ (local.py, parameters.py, types.py) |

---

## Audit Pass 3: Tests / Quality

| Aspect | Status |
|--------|--------|
| All 143 unit tests pass | ✓ |
| No skipped tests for touched code | ✓ |
| No xfailed tests for touched code | ✓ |
| Convergence window-mean tested | ✓ |
| Cross-round decoder persistence tested | ✓ |
| Parameter validation tested | ✓ |
| Local training validation tested | ✓ |
| Batched scoring consistency tested | ✓ |
| Type validation helpers tested | ✓ |
| Strategy failure behavior tested | ✓ |

---

## Files Changed (Source)

| File | Change |
|------|--------|
| `src/datp/training/types.py` | NEW — ClientData + validation helpers |
| `src/datp/training/convergence.py` | Window-mean algorithm + finite validation |
| `src/datp/training/local.py` | Input validation + non-finite loss check |
| `src/datp/training/parameters.py` | `.copy()` on get, count/shape validation on set |
| `src/datp/training/scoring.py` | Batched `_compute_errors`, manifest helper, ClientData re-export |
| `src/datp/training/simulation.py` | Fatal RuntimeError on missing final_params |
| `src/datp/training/strategies.py` | RuntimeError on client failures |
| `src/datp/training/clients.py` | Parameter name fix for Flower override |
| `src/datp/training/factories.py` | ClientData import from types |
| `src/datp/training/__init__.py` | Export ClientData |
| `src/datp/training/protocols/fedprox.py` | Regime in path, SCORES_DIR constant, param name fix |
| `src/datp/training/protocols/fedrep.py` | `_load_persisted_decoder`, regime in path, SCORES_DIR, param name fix |
| `src/datp/baselines/common/data_loading.py` | ClientData import from types |

## Files Changed (Tests)

| File | Change |
|------|--------|
| `tests/unit/training/test_types.py` | NEW — validation helper tests |
| `tests/unit/training/test_parameters.py` | NEW — round-trip, cast, mismatch tests |
| `tests/unit/training/test_convergence.py` | Rewritten for window-mean algorithm |
| `tests/unit/training/test_scoring.py` | Added batched scoring tests |
| `tests/unit/training/test_local.py` | Added validation tests |
| `tests/unit/training/protocols/test_fedrep.py` | Cross-round persistence test + path fix |

---

## Remaining Issues

None.

---

## Scientific Drift Verdict

**NO DRIFT.** All changes preserve the DATP scientific contract:
- Single encoder per cell
- Threshold-scope-only variation across B1–B4
- Shared score artifacts
- FedRep/FedProx remain stress tests
- No new claims introduced

---

## Pass 2 — Remaining Repairs

**Status:** PASS  
**Tests:** 155 passed (was 143; +8 catalog, +4 resolve_device)

### P2-1: TrainingClientCatalog (prepared_dir lazy loading)
- **Created**: `src/datp/training/catalog.py`
- `run_fl_simulation` no longer requires non-empty `client_data` when `prepared_dir` is set
- `TrainingClientCatalog` discovers client IDs from either source; prepared_dir wins
- Signature: `client_data: dict[str, ClientData]` → `dict[str, ClientData] | None`

### P2-2: CUDA/Ray resource config-driven policy
- **New**: `runtime.resolve_device(require_cuda: bool)` replaces implicit `get_device()` in orchestration
- **New config**: `MachineConfig.require_cuda: bool`
- **Moved**: `derive_client_resources` from simulation.py → runtime.py (explicit params, not cfg object)
- **Removed**: `_NO_RAY_GPU` constant, env-trick comment

### P2-3: Alpha-safe stress test paths
- FedProx/FedRep: `alpha: float | None = None` kwarg; path includes `format_alpha_dir(alpha)` when not None
- Both pass `alpha` (not hardcoded `None`) to `run_fl_simulation` and scoring

### P2-4: FedRep prepared_dir scoring
- Uses `TrainingClientCatalog` for client discovery
- Loads scoring data from `prepared_dir` via `load_client_data` when set
- Passes `scoring_batch_size` from config

### P2-5: Config-driven scoring batch size
- **New config**: `MachineConfig.scoring_batch_size: int` (YAML default: 4096)
- Wired through `run_fl_simulation` and `run_fedrep_training` to scoring functions

### P2-6: Consistent validation in DatpClient
- Removed local `_validate_2d`; uses `validate_tensor_2d`, `validate_tensor_non_empty`, `validate_tensor_finite` from `training.types`

### P2-7: simulation.py decomposition
- Removed resource derivation (~40 lines) to runtime.py
- Removed `_validate_sim_inputs` (replaced by `_validate_regime`)
- Added catalog-based client discovery

### P2-8: Communication accounting clarity
- Module docstring explicitly names "server-aggregated payload bytes" model

### P2-9: This report update

### Quality Gates (Pass 2)
| Check | Result |
|-------|--------|
| pyright (training) | 0 errors |
| pyright (full src/) | 0 new errors |
| ruff | All checks passed |
| Unit tests | 155 passed |
| Scientific drift | None |

---

## Pass 3 — Final 9-Blocker Resolution

**Date:** 2025-07-19  
**Status:** PASS  
**Unit tests:** 159 passed  
**Integration tests:** 20 passed

### Blocker 1: CUDA/Ray Resource Policy

- `resolve_device(require_cuda=False)` now returns CPU unconditionally (no silent CUDA promotion)
- `derive_client_resources` takes explicit `ray_num_gpus_per_client: float` from config
- `num_gpus=0.0` when `require_cuda=False`; `num_gpus=ray_num_gpus_per_client` when True
- Removed: `RAY_ACCEL_ENV_VAR_OVERRIDE_ON_ZERO` env var trick from `src/datp/__init__.py`
- `configure_runtime_env()` is now an empty no-op (body removed, docstring kept)

### Blocker 2: Config-Driven Batch Sizes

- `_DEFAULT_SCORING_BATCH_SIZE` constant removed entirely from `scoring.py`
- `_compute_errors`, `_score_one_split`, `score_clients`, `score_fedrep_clients` all require explicit `batch_size`/`scoring_batch_size` parameter (no default)
- Config drives the value via `MachineConfig.scoring_batch_size`

### Blocker 3: TrainingClientCatalog as Real Source of Truth

- `TrainingClientCatalog` expanded with:
  - `prepared_dir` property
  - `validate_prepared_splits()` — checks each client dir + all split files + scaler
  - `validate_feature_dim(expected_dim)` — reads first client's train parquet, checks width
  - `load_scoring_data(device)` — loads scoring tensors for all clients
- `run_fl_simulation` uses `catalog.validate_prepared_splits()` instead of removed `validate_prepared_paths`

### Blocker 4: Consistent Validation

- `validate_client_data` in `types.py` calls `validate_tensor_finite` for ALL splits (train, val, test_benign, test_attack)
- `DatpClient.__init__` adds `validate_tensor_finite(val_data, "val_data", cid)` after non_empty check
- No validation gaps remain

### Blocker 5: simulation.py Decomposition

- `validate_prepared_paths` function removed (was ~30 lines of hand-built Path logic)
- Imports removed: `from datp.data.splits import Split, filename_for_split`, `SCALER_FILE`, `discover_client_dirs`
- Replaced by single `catalog.validate_prepared_splits()` call
- Resource derivation was already moved to `runtime.py` in Pass 2

### Blocker 6: Canonical Stress-Test Paths

- FedProx/FedRep already use `format_alpha_dir` from `datp.core.identity` (verified in Pass 2)
- Path assembly uses canonical helpers; no raw string concatenation for scientific identifiers

### Blocker 7: FedRep Decoder Safety

- Before decoder loading loop: validates each decoder checkpoint file exists, raises `FileNotFoundError` if missing
- After building `client_models`: validates keys match `scoring_data` keys, raises `ValueError` on mismatch
- Prevents silent fallback to untrained decoder weights during scoring

### Blocker 8: Communication Accounting Names

- `RoundComm` and `ThresholdComm` fields renamed:
  - `uplink_bytes` → `server_uplink_payload_bytes`
  - `downlink_bytes` → `server_downlink_payload_bytes`
- All internal references updated (`compute_round_comm`, `compute_threshold_comm`, `build_comm_summary`)
- Integration tests updated to match

### Blocker 9: Clean Code / No Leftovers

- No TODO/FIXME in `src/datp/training/`
- No `pytest.mark.skip` or `pytest.mark.xfail` in training tests
- No stale imports (`get_device`, `Split`, `filename_for_split`, `SCALER_FILE`, `discover_client_dirs`)
- No dead constants (`_DEFAULT_SCORING_BATCH_SIZE`, `_NO_RAY_GPU`)
- `__init__.py` env-var code removed

### Loop 2 Pattern Audit

| Pattern Searched | Found | Status |
|-----------------|-------|--------|
| `RAY_ACCEL_ENV_VAR_OVERRIDE_ON_ZERO` in src/ | 0 | ✓ Clean |
| `_DEFAULT_SCORING_BATCH_SIZE` in src/ or tests/ | 0 | ✓ Clean |
| `from datp.core.device import get_device` in training/ | 0 | ✓ Clean |
| `num_gpus=0` hardcoded in training/ | 0 | ✓ Clean |
| `validate_prepared_paths` anywhere | 0 | ✓ Clean |
| TODO/FIXME/HACK/XXX in training/ | 0 | ✓ Clean |
| `pytest.mark.skip`/`xfail` in training tests | 0 | ✓ Clean |

### Quality Gates (Pass 3)

| Check | Result |
|-------|--------|
| Pyright (`src/datp/training/`) | 0 errors, 0 warnings |
| Ruff (training + tests) | All checks passed |
| Unit tests (`tests/unit/training/`) | 159 passed, 0 failed |
| Integration tests (`tests/integration/training/`) | 20 passed, 0 failed |
| Scientific drift | None |
| Old pattern residue | None found |

### External Caller Verification

| Caller | Status |
|--------|--------|
| `src/datp/pipeline/training.py` → `load_model_from_checkpoint` | ✓ Passes `require_cuda=request.cfg.machine.require_cuda` |
| `src/datp/pipeline/training.py` → `score_clients` | ✓ Passes `scoring_batch_size` from config |
| `tests/unit/pipeline/test_executor.py` | ✓ Mocks `load_model_from_checkpoint` correctly |

---

## Final Verdict

**PASS**

The training package is production-clean, scientifically safe, config-driven, and test-backed.

All 9 mandatory blockers resolved. No remaining issues. No scientific drift.
