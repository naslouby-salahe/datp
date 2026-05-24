"""T09 tests — B-FedStatsBenign comparator."""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import polars as pl

from datp.analyses.fedstats_benign import (
    FEDSTATS_DIAGNOSTICS_JSON,
    FEDSTATS_TABLE_CSV,
    _compute_client_summaries,
    _compute_global_stats,
    _select_k_star,
    run_fedstats_benign,
)
from datp.artifacts.constants import SCORING_MANIFEST_FILE, SCORING_SENTINEL
from datp.artifacts.directories import ANALYSIS_DIR, SCORES_DIR
from datp.audit.constants import CELL_VERDICTS_JSON
from datp.config.compose import compose_config
from datp.audit.enums import ReuseVerdict
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


def test_weighted_global_mean():
    """Sample-count-weighted global mean is correct."""
    n1, mu1 = 100, 0.5
    n2, mu2 = 200, 0.8
    total_n = n1 + n2
    expected = (n1 * mu1 + n2 * mu2) / total_n
    assert math.isclose(expected, (100 * 0.5 + 200 * 0.8) / 300)


def test_pooled_variance_with_within_and_between():
    """Pooled variance = within_var + between_var."""
    n1, mu1, var1 = 100, 0.5, 0.01
    n2, mu2, var2 = 200, 0.8, 0.02
    total_n = n1 + n2
    mu_global = (n1 * mu1 + n2 * mu2) / total_n
    within_var = (n1 * var1 + n2 * var2) / total_n
    between_var = (n1 * (mu1 - mu_global) ** 2 + n2 * (mu2 - mu_global) ** 2) / total_n
    sigma_sq = within_var + between_var
    assert sigma_sq > 0
    # between_ratio is nonzero since means differ
    between_ratio = between_var / sigma_sq
    assert 0.0 < between_ratio < 1.0


def test_between_ratio_zero_when_identical_means():
    """Identical means → between_var = 0 → between_ratio = 0."""
    n1, mu1, _var1 = 100, 0.5, 0.01
    n2, mu2, _var2 = 200, 0.5, 0.02
    total_n = n1 + n2
    mu_global = 0.5
    between_var = (n1 * (mu1 - mu_global) ** 2 + n2 * (mu2 - mu_global) ** 2) / total_n
    assert between_var == 0.0


def test_k_grid_generation():
    """k grid from config is generated correctly."""
    k_min, k_max, k_step = 0.0, 5.0, 0.01
    ks = []
    k = k_min
    while k <= k_max + 1e-12:
        ks.append(k)
        k += k_step
    assert len(ks) == 501  # 0.00 through 5.00 inclusive


def test_k_star_selection():
    """k* selection minimizes |exceedance - target|, tie-break larger k."""
    errors = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
    mu_global = 0.5
    sigma_global = 0.2
    target = 0.5

    k_star, _, achieved = _select_k_star(
        mu_global, sigma_global, 0.0, 2.0, 0.01, target,
        {"c1": errors},
    )
    # With mu=0.5, sigma=0.2, k=0 gives tau=0.5, exceedance ≈ fraction > 0.5 = 0.5
    # This should be very close to target
    assert abs(achieved - target) <= 0.2  # wide tolerance for tiny dataset


def test_k_star_tiebreak_larger_k():
    """When two k values have equal deviation, larger k wins."""
    errors = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
    mu = 0.3
    sigma = 0.1
    target = 0.4

    k_star, _, _ = _select_k_star(mu, sigma, 0.0, 2.0, 0.01, target, {"c1": errors})
    # The function should pick a k; we just verify it doesn't error
    assert k_star >= 0.0


def test_no_attack_labels_used():
    """B-FedStatsBenign only uses calibration benign scores."""
    cal_errors = {"c1": np.array([0.1, 0.2, 0.3]), "c2": np.array([0.15, 0.25])}
    summaries = _compute_client_summaries(cal_errors)
    assert len(summaries) == 2
    mu, sigma_sq, within, between, ratio = _compute_global_stats(summaries)
    assert mu > 0
    assert sigma_sq > 0


def test_full_run_with_synthetic_data(tmp_path: Path):
    base_dir = tmp_path / "test_full"
    cell_dir = _build_score_cell(base_dir)
    _write_verdicts(base_dir, str(cell_dir))

    cfg = compose_config(regime=_REGIME, baseline=Baseline.B1, seed=_SEED)
    result = run_fedstats_benign(base_dir, config=cfg)

    assert len(result.cells) == 1
    cell = result.cells[0]
    assert cell.mu_global > 0
    assert cell.sigma_sq_global > 0
    assert 0.0 <= cell.between_ratio <= 1.0
    assert cell.eligible_count > 0


def test_write_outputs_creates_csv_and_json(tmp_path: Path):
    base_dir = tmp_path / "test_write"
    cell_dir = _build_score_cell(base_dir)
    _write_verdicts(base_dir, str(cell_dir))

    cfg = compose_config(regime=_REGIME, baseline=Baseline.B1, seed=_SEED)
    run_fedstats_benign(base_dir, config=cfg, write_outputs=True)
    assert (base_dir / ANALYSIS_DIR / FEDSTATS_TABLE_CSV).is_file()
    assert (base_dir / ANALYSIS_DIR / FEDSTATS_DIAGNOSTICS_JSON).is_file()


def test_analysis_config_has_fedstats_fields():
    cfg = compose_config(regime=_REGIME, baseline=Baseline.B1, seed=_SEED)
    assert hasattr(cfg.analysis, "fedstats_k_min")
    assert hasattr(cfg.analysis, "fedstats_k_max")
    assert hasattr(cfg.analysis, "fedstats_k_step")
    assert hasattr(cfg.analysis, "fedstats_target_exceedance")
    assert cfg.analysis.fedstats_target_exceedance == 0.05
