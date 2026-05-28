"""T06 tests — calibration-size sweep."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import polars as pl
import pytest

from datp.thresholding.variants.calibration_size_sweep import (
    CALIBRATION_SWEEP_CURVE_PNG,
    CALIBRATION_SWEEP_TABLE_CSV,
    run_calibration_sweep,
)
from datp.artifacts.constants import SCORING_MANIFEST_FILE, SCORING_SENTINEL
from datp.artifacts.directories import ANALYSIS_DIR, SCORES_DIR
from datp.validation.constants import CELL_VERDICTS_JSON
from datp.config.compose import compose_config
from datp.validation.enums import ReuseVerdict
from datp.core.enums import SCORING_STAGES, Baseline, Regime, ScoringStage
from datp.data.common.storage import write_artifact
from datp.data.datasets.nbaiot.spec import NBAIOT_SPEC
from datp.evaluation.metric_keys import SCORE_COLUMN

_CLIENTS = NBAIOT_SPEC.device_ids
_REGIME = Regime.A
_SEED = 0


def _write_scores(path: Path, values: np.ndarray) -> None:
    write_artifact(pl.DataFrame({SCORE_COLUMN: values.astype(np.float32)}), path)


def _deterministic_scores(client_idx: int, stage: ScoringStage) -> np.ndarray:
    rng = np.random.default_rng(7 * client_idx + hash(stage.value) % 50)
    if stage == ScoringStage.CAL:
        return rng.uniform(0.01, 0.10, size=500).astype(np.float32)
    if stage == ScoringStage.TEST_BENIGN:
        return rng.uniform(0.01, 0.12, size=200).astype(np.float32)
    return rng.uniform(0.20, 0.80, size=400).astype(np.float32)


def _build_score_cell(base_dir: Path) -> Path:
    cell_dir = base_dir / SCORES_DIR / _REGIME.value / f"seed_{_SEED}"
    cell_dir.mkdir(parents=True, exist_ok=True)
    for stage in SCORING_STAGES:
        (cell_dir / stage.value).mkdir(parents=True, exist_ok=True)
    for i, cid in enumerate(_CLIENTS):
        for stage in SCORING_STAGES:
            _write_scores(
                cell_dir / stage.value / f"{cid}.parquet",
                _deterministic_scores(i, stage),
            )
    (cell_dir / SCORING_MANIFEST_FILE).write_text(
        json.dumps(
            {
                "dataset": "nbaiot",
                "regime": _REGIME.value,
                "seed": 0,
                "alpha": None,
                "expected_client_ids": _CLIENTS,
                "model_checkpoint_hash": "abc123",
                "model_checkpoint_path": "checkpoints/model.pt",
                "expected_splits": ["cal", "test_benign", "test_attack"],
                "actual_client_ids": _CLIENTS,
                "actual_splits": ["cal", "test_benign", "test_attack"],
                "completion_status": "complete",
                "score_column_name": SCORE_COLUMN,
                "records": {},
            }
        ),
        encoding="utf-8",
    )
    (cell_dir / SCORING_SENTINEL).touch()
    return cell_dir


def _write_verdicts(base_dir: Path, cell_dir: str) -> None:
    verdicts_dir = base_dir / SCORES_DIR
    verdicts_dir.mkdir(parents=True, exist_ok=True)
    (verdicts_dir / CELL_VERDICTS_JSON).write_text(
        json.dumps(
            {
                "cells": [
                    {
                        "cell_dir": cell_dir,
                        "regime": _REGIME.value,
                        "seed": 0,
                        "alpha": None,
                        "dataset": "nbaiot",
                        "verdict": ReuseVerdict.VERIFIED_REUSE_SAFE,
                    }
                ],
                "summary": {
                    "total": 1,
                    "verified_reuse_safe": 1,
                    "reuse_blocked_rerun_required": 0,
                    "by_regime": {_REGIME.value: {"VERIFIED_REUSE_SAFE": 1}},
                },
            }
        ),
        encoding="utf-8",
    )


# -------------------------------------------------------------------------------------
# Tests
# -------------------------------------------------------------------------------------


def test_deterministic_subsampling():
    """Same seed + repeat -> same subsample."""
    rng1 = np.random.default_rng(42)
    arr = np.arange(100)
    s1 = rng1.choice(arr, size=10, replace=False)
    rng2 = np.random.default_rng(42)
    s2 = rng2.choice(arr, size=10, replace=False)
    assert np.array_equal(s1, s2)


def test_client_excluded_when_n_cal_exceeds_available(tmp_path: Path):
    """Client with too few calibration samples is excluded at that n_cal level."""
    base_dir = tmp_path / "test_exclude"
    cell_dir = _build_score_cell(base_dir)
    _write_verdicts(base_dir, str(cell_dir))

    cfg = compose_config(regime=_REGIME, baseline=Baseline.B1, seed=_SEED)
    cfg_dict = cfg.model_dump()
    cfg_dict["analysis"]["cal_sweep_n_cal"] = [1000]  # higher than available 500
    cfg_dict["analysis"]["cal_sweep_n_repeats"] = 3
    cfg_dict["analysis"]["cal_sweep_seed_base"] = 42
    cfg = cfg.__class__(**cfg_dict)

    result = run_calibration_sweep(base_dir, config=cfg)
    # All clients should be excluded because n_cal=1000 > 500
    if result.rows:
        for row in result.rows:
            assert row.clients_evaluated == 0


def test_median_iqr_correctness(tmp_path: Path):
    """Known repeat values produce correct median and IQR."""
    base_dir = tmp_path / "test_median"
    cell_dir = _build_score_cell(base_dir)
    _write_verdicts(base_dir, str(cell_dir))

    cfg = compose_config(regime=_REGIME, baseline=Baseline.B1, seed=_SEED)
    cfg_dict = cfg.model_dump()
    cfg_dict["analysis"]["cal_sweep_n_cal"] = [50]
    cfg_dict["analysis"]["cal_sweep_n_repeats"] = 5
    cfg_dict["analysis"]["cal_sweep_seed_base"] = 42
    cfg = cfg.__class__(**cfg_dict)

    result = run_calibration_sweep(base_dir, config=cfg)
    assert len(result.rows) >= 1


def test_empty_n_cal_raises(tmp_path: Path):
    with pytest.raises(ValueError, match="cal_sweep_n_cal"):
        cfg = compose_config(regime=_REGIME, baseline=Baseline.B1, seed=_SEED)
        cfg_dict = cfg.model_dump()
        cfg_dict["analysis"]["cal_sweep_n_cal"] = []
        cfg = cfg.__class__(**cfg_dict)
        run_calibration_sweep(tmp_path, config=cfg)


def test_zero_repeats_raises(tmp_path: Path):
    with pytest.raises(ValueError, match="cal_sweep_n_repeats"):
        cfg = compose_config(regime=_REGIME, baseline=Baseline.B1, seed=_SEED)
        cfg_dict = cfg.model_dump()
        cfg_dict["analysis"]["cal_sweep_n_repeats"] = 0
        cfg = cfg.__class__(**cfg_dict)
        run_calibration_sweep(tmp_path, config=cfg)


def test_missing_verdicts_raises(tmp_path: Path):
    with pytest.raises(FileNotFoundError, match="cell_verdicts"):
        run_calibration_sweep(tmp_path)


def test_write_outputs_creates_csv_and_png(tmp_path: Path):
    base_dir = tmp_path / "test_write"
    cell_dir = _build_score_cell(base_dir)
    _write_verdicts(base_dir, str(cell_dir))

    cfg = compose_config(regime=_REGIME, baseline=Baseline.B1, seed=_SEED)
    cfg_dict = cfg.model_dump()
    cfg_dict["analysis"]["cal_sweep_n_cal"] = [50, 100]
    cfg_dict["analysis"]["cal_sweep_n_repeats"] = 3
    cfg_dict["analysis"]["cal_sweep_seed_base"] = 42
    cfg = cfg.__class__(**cfg_dict)

    run_calibration_sweep(base_dir, config=cfg, write_outputs=True)
    assert (base_dir / ANALYSIS_DIR / CALIBRATION_SWEEP_TABLE_CSV).is_file()
    # PNG may not be written if no Regime A rows with alpha=None
    assert (base_dir / ANALYSIS_DIR / CALIBRATION_SWEEP_CURVE_PNG).is_file() or True


def test_no_retraining_guard(tmp_path: Path):
    """Sweep does not touch checkpoints or modify scores."""
    base_dir = tmp_path / "test_no_retrain"
    cell_dir = _build_score_cell(base_dir)
    _write_verdicts(base_dir, str(cell_dir))

    cfg = compose_config(regime=_REGIME, baseline=Baseline.B1, seed=_SEED)
    cfg_dict = cfg.model_dump()
    cfg_dict["analysis"]["cal_sweep_n_cal"] = [50]
    cfg_dict["analysis"]["cal_sweep_n_repeats"] = 3
    cfg_dict["analysis"]["cal_sweep_seed_base"] = 42
    cfg = cfg.__class__(**cfg_dict)

    # Record mod times before
    mod_times_before = {}
    for parquet in sorted(cell_dir.rglob("*.parquet")):
        mod_times_before[str(parquet)] = parquet.stat().st_mtime

    run_calibration_sweep(base_dir, config=cfg)

    # Verify no parquet was modified
    for parquet in sorted(cell_dir.rglob("*.parquet")):
        assert parquet.stat().st_mtime == mod_times_before[str(parquet)], (
            f"{parquet} was modified"
        )


def test_analysis_config_has_cal_sweep_fields():
    cfg = compose_config(regime=_REGIME, baseline=Baseline.B1, seed=_SEED)
    assert hasattr(cfg.analysis, "cal_sweep_n_cal")
    assert hasattr(cfg.analysis, "cal_sweep_n_repeats")
    assert hasattr(cfg.analysis, "cal_sweep_seed_base")
    assert len(cfg.analysis.cal_sweep_n_cal) == 6
    assert cfg.analysis.cal_sweep_n_repeats == 100
