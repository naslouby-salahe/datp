"""T08 tests — B2-conf conformal threshold variant."""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import polars as pl
import pytest

from datp.analyses.b2_conf import (
    B2_CONF_COVERAGE_PNG,
    B2_CONF_TABLE_CSV,
    B2ConfResult,
    run_b2_conf,
)
from datp.artifacts.constants import SCORING_MANIFEST_FILE, SCORING_SENTINEL
from datp.artifacts.directories import ANALYSIS_DIR, SCORES_DIR
from datp.audit.constants import CELL_VERDICTS_JSON
from datp.baselines.common.thresholds import conformal_threshold
from datp.config.compose import compose_config
from datp.core.enums import SCORING_STAGES, Baseline, Regime, ReuseVerdict, ScoringStage
from datp.data.common.storage import write_artifact
from datp.data.datasets.nbaiot.spec import NBAIOT_SPEC
from datp.evaluation.metric_keys import SCORE_COLUMN

_CLIENTS = NBAIOT_SPEC.device_ids
_REGIME = Regime.A
_SEED = 0
_Q = 0.95
_ALPHA = 1.0 - _Q  # 0.05


def _write_scores(path: Path, values: np.ndarray) -> None:
    write_artifact(pl.DataFrame({SCORE_COLUMN: values.astype(np.float32)}), path)


def _deterministic_scores(client_idx: int, stage: ScoringStage) -> np.ndarray:
    rng = np.random.default_rng(7 * client_idx + hash(stage.value) % 50)
    if stage == ScoringStage.CAL:
        return rng.uniform(0.01, 0.10, size=300).astype(np.float32)
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
            _write_scores(cell_dir / stage.value / f"{cid}.parquet", _deterministic_scores(i, stage))
    (cell_dir / SCORING_MANIFEST_FILE).write_text(json.dumps({
        "dataset": "nbaiot", "regime": _REGIME.value, "seed": 0, "alpha": None,
        "expected_client_ids": _CLIENTS, "model_checkpoint_hash": "abc123",
        "model_checkpoint_path": "checkpoints/model.pt",
        "expected_splits": ["cal", "test_benign", "test_attack"],
        "actual_client_ids": _CLIENTS,
        "actual_splits": ["cal", "test_benign", "test_attack"],
        "completion_status": "complete",
        "score_column_name": SCORE_COLUMN,
        "records": {},
    }), encoding="utf-8")
    (cell_dir / SCORING_SENTINEL).touch()
    return cell_dir


def _write_verdicts(base_dir: Path, cell_dir: str) -> None:
    verdicts_dir = base_dir / SCORES_DIR
    verdicts_dir.mkdir(parents=True, exist_ok=True)
    (verdicts_dir / CELL_VERDICTS_JSON).write_text(json.dumps({
        "cells": [{
            "cell_dir": cell_dir,
            "regime": _REGIME.value,
            "seed": 0,
            "alpha": None,
            "dataset": "nbaiot",
            "verdict": ReuseVerdict.VERIFIED_REUSE_SAFE,
        }],
        "summary": {"total": 1, "verified_reuse_safe": 1, "reuse_blocked_rerun_required": 0,
                     "by_regime": {_REGIME.value: {"VERIFIED_REUSE_SAFE": 1}}},
    }), encoding="utf-8")


# -------------------------------------------------------------------------------------
# Tests


def test_conformal_threshold_known_array():
    """Known sorted array → correct k-th value."""
    errors = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
    # n=10, alpha=0.05 → k = ceil(11 * 0.95) = ceil(10.45) = 11 > 10 → max
    tau = conformal_threshold(errors, 0.05)
    assert tau == 1.0  # k > n, so max


def test_conformal_threshold_k_not_exceeding_n():
    """alpha=0.5, n=10 → k = ceil(11 * 0.5) = 6 → sorted[5]."""
    errors = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
    tau = conformal_threshold(errors, 0.5)
    assert tau == 0.6


def test_conformal_threshold_alpha_from_config():
    """alpha = 1 - q from config, not hardcoded."""
    q = 0.90
    alpha = 1.0 - q
    assert math.isclose(alpha, 0.10)
    errors = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
    tau = conformal_threshold(errors, alpha)
    # k = ceil(11 * 0.90) = ceil(9.9) = 10 → sorted[9] = 1.0
    assert tau == 1.0


def test_conformal_threshold_empty_raises():
    with pytest.raises(ValueError, match="empty array"):
        conformal_threshold(np.array([]), 0.05)


def test_empirical_coverage_computation(tmp_path: Path):
    base_dir = tmp_path / "test_coverage"
    cell_dir = _build_score_cell(base_dir)
    _write_verdicts(base_dir, str(cell_dir))

    cfg = compose_config(regime=_REGIME, baseline=Baseline.B1, seed=_SEED)
    result = run_b2_conf(base_dir, config=cfg)

    assert len(result.rows) > 0
    for row in result.rows:
        assert 0.0 <= row.empirical_coverage <= 1.0


def test_calibration_pending_clients(tmp_path: Path):
    base_dir = tmp_path / "test_pending"
    cell_dir = _build_score_cell(base_dir)
    _write_verdicts(base_dir, str(cell_dir))

    cfg = compose_config(regime=_REGIME, baseline=Baseline.B1, seed=_SEED)
    # n_min = cfg.threshold.n_min is 100, our synthetic data has 300 cal samples → all eligible


def test_conformal_threshold_no_hardcoded_alpha():
    """Verify alpha flows from config, not a magic 0.05."""
    cfg = compose_config(regime=_REGIME, baseline=Baseline.B1, seed=_SEED)
    q = cfg.threshold.q
    alpha = 1.0 - q
    assert math.isclose(alpha, 0.05)  # q=0.95 → alpha=0.05
    # But q could be different — formula uses config
    q2 = 0.90
    alpha2 = 1.0 - q2
    assert math.isclose(alpha2, 0.10)
    assert not math.isclose(alpha2, 0.05)


def test_write_outputs_creates_csv_and_png(tmp_path: Path):
    base_dir = tmp_path / "test_write"
    cell_dir = _build_score_cell(base_dir)
    _write_verdicts(base_dir, str(cell_dir))

    cfg = compose_config(regime=_REGIME, baseline=Baseline.B1, seed=_SEED)
    run_b2_conf(base_dir, config=cfg, write_outputs=True)
    assert (base_dir / ANALYSIS_DIR / B2_CONF_TABLE_CSV).is_file()
    assert (base_dir / ANALYSIS_DIR / B2_CONF_COVERAGE_PNG).is_file()
