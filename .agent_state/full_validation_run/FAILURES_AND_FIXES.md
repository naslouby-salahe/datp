# Failures and Fixes

## Fix 1: Unjustified dataclass defaults (unit test)
- **File**: `tests/unit/core/test_dataclass_architecture.py`
- **Fix**: Added `ScoreCellPaths.checkpoint_round` and `BaselineRunPaths.checkpoint_round` to `_DEFAULTS_ALLOWLIST`
- **Reason**: Both fields have `int | None = None` semantics where None = standard run (not checkpoint-protocol)

## Fix 2: Integration tests — checkpoint protocol artifact paths
- **Files**: `tests/integration/federated/test_fl_simulation.py`, `tests/integration/scoring/test_score_artifacts.py`
- **Fix**: Added `CheckpointProtocolMode.DISABLED` to test configs via `model_copy`
- **Reason**: BASE_CONFIG loads real config.yaml with protocol ENABLED; tests verify FL basics not protocol behavior

## Fix 3: E2E tests — missing checkpoint_round argument
- **Files**: 5 e2e test files (regime_a, regime_b, regime_c, regime_d, diagnostic)
- **Fix**: Added `checkpoint_round=None` to all `load_main_cal_errors` calls
- **Reason**: `load_main_cal_errors` signature now requires explicit `checkpoint_round` positional arg

## Fix 4: E2E tests — checkpoint protocol disabling
- **Files**: Same 5 e2e test files
- **Fix**: Added `CheckpointProtocolMode.DISABLED` in fixture configs
- **Reason**: Same as Fix 2 — tests should not need per-round artifact paths

## Fix 5: Lint — duplicate import
- **File**: `tests/unit/data/datasets/ciciot2023/test_ciciot_prepare.py`
- **Fix**: Removed duplicate `from datp.data.splits import SplitFilename` import

## Fix 6: gate1 — missing test file
- **File**: `tests/unit/data/common/test_manifest.py` (CREATED)
- **Fix**: Created new file with 17 tests covering ManifestMetadata, compute_manifest_hashes, PartitionManifest, create_manifest
- **Reason**: Makefile gate1 target referenced this file but it did not exist

## Fix 7: uv sync --locked failure
- **Fix**: Ran `uv lock` first to regenerate lockfile, then `uv sync --locked`
- **Reason**: Lockfile was out of date after recent dependency changes

## Fix 8: Diagnostic CLI — checkpoint protocol mismatch
- **File**: `src/datp/experiments/diagnostic.py`
- **Fix**: After composing config, disable checkpoint protocol:
  ```python
  cfg = cfg.model_copy(update={"checkpoint_protocol": cfg.checkpoint_protocol.model_copy(update={"mode": CheckpointProtocolMode.DISABLED})})
  ```
- **Reason**: `compose_config()` loads real config.yaml with protocol ENABLED; diagnostic
  ran training with per-round artifact paths but tried to load cal errors from
  standard (non-round) paths → FileNotFoundError. Diagnostic is a quick sanity check,
  not a checkpoint-protocol run.

## Fix 9: Audit — THRESHOLD_RECONSTRUCTION_FAILED (169 warnings → 0)
- **File**: `src/datp/validation/results.py`
- **Fix**: In `_load_run_context`, extract `checkpoint_round` from loaded `metrics` dict.
  When non-None, use `layout.score_cell_for_round(cell, checkpoint_round).score_dir` and
  `layout.checkpoint_dir_for_round(cell, checkpoint_round) / ArtifactFile.MODEL_CHECKPOINT`.
  Removed now-dead `_score_root()` and `_checkpoint_path()` helper functions.
- **Reason**: Both helpers always returned non-round paths; B1–B4 per-round results have
  scores at `outputs/scores/regime/seed_N/round_R/` but audit tried to load from
  `outputs/scores/regime/seed_N/` → no eligible clients → reconstruction failure warning.
- **Verified**: `make audit-results` after fix: 290 runs audited, 0 FAIL cells, 0 THRESHOLD_RECONSTRUCTION_FAILED.
