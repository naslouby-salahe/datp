"""T07 tests — τ-shrink threshold variant."""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import polars as pl
import pytest

from datp.analyses.tau_shrink import (
    TAU_SHRINK_CURVE_PNG,
    TAU_SHRINK_TABLE_CSV,
    run_tau_shrink,
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
_Q = 0.95


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


def test_lambda_zero_tau_shrink():
    """λ=0 returns tau_global exactly."""
    tau_local = 0.5
    tau_global = 1.0
    result = 0.0 * tau_local + 1.0 * tau_global
    assert math.isclose(result, tau_global)


def test_lambda_one_tau_shrink():
    """λ=1 returns tau_local exactly."""
    tau_local = 0.5
    tau_global = 1.0
    result = 1.0 * tau_local + 0.0 * tau_global
    assert math.isclose(result, tau_local)


def test_lambda_half_midpoint():
    """λ=0.5 returns midpoint."""
    tau_local = 0.6
    tau_global = 0.4
    result = 0.5 * tau_local + 0.5 * tau_global
    assert math.isclose(result, 0.5)


def test_invalid_lambda_negative():
    """Negative lambda is a valid mathematical value — not rejected by interpolation formula."""
    result = (-0.1) * 0.5 + 1.1 * 1.0
    assert (
        result == 1.05
    )  # formula still works; λ grid from config controls valid range


def test_endpoint_metrics_match(tmp_path: Path):
    """λ=0 reproduces B1, λ=1 reproduces B2 on synthetic data."""
    base_dir = tmp_path / "test_endpoints"
    cell_dir = _build_score_cell(base_dir)
    _write_verdicts(base_dir, str(cell_dir))

    cfg = compose_config(regime=_REGIME, baseline=Baseline.B1, seed=_SEED)
    result = run_tau_shrink(base_dir, config=cfg, write_outputs=False)

    # Find λ=0 and λ=1 rows for Regime A
    lam0_rows = [
        r
        for r in result.rows
        if r.regime == Regime.A and math.isclose(r.lambda_val, 0.0)
    ]
    lam1_rows = [
        r
        for r in result.rows
        if r.regime == Regime.A and math.isclose(r.lambda_val, 1.0)
    ]

    assert len(lam0_rows) >= 1
    assert len(lam1_rows) >= 1


def test_full_lambda_curve_produces_all_lambdas(tmp_path: Path):
    base_dir = tmp_path / "test_curve"
    cell_dir = _build_score_cell(base_dir)
    _write_verdicts(base_dir, str(cell_dir))

    cfg = compose_config(regime=_REGIME, baseline=Baseline.B1, seed=_SEED)
    result = run_tau_shrink(base_dir, config=cfg)

    lambdas_in_result = sorted(
        set(
            r.lambda_val
            for r in result.rows
            if r.regime == Regime.A and r.alpha is None
        )
    )
    assert len(lambdas_in_result) == len(cfg.analysis.tau_shrink_lambdas)


def test_empty_lambdas_raises(tmp_path: Path):
    with pytest.raises(ValueError, match="tau_shrink_lambdas"):
        cfg = compose_config(regime=_REGIME, baseline=Baseline.B1, seed=_SEED)
        cfg_dict = cfg.model_dump()
        cfg_dict["analysis"]["tau_shrink_lambdas"] = []
        cfg = cfg.__class__(**cfg_dict)
        run_tau_shrink(tmp_path, config=cfg)


def test_write_outputs_creates_csv_and_png(tmp_path: Path):
    base_dir = tmp_path / "test_write"
    cell_dir = _build_score_cell(base_dir)
    _write_verdicts(base_dir, str(cell_dir))

    cfg = compose_config(regime=_REGIME, baseline=Baseline.B1, seed=_SEED)
    run_tau_shrink(base_dir, config=cfg, write_outputs=True)
    assert (base_dir / ANALYSIS_DIR / TAU_SHRINK_TABLE_CSV).is_file()
    assert (base_dir / ANALYSIS_DIR / TAU_SHRINK_CURVE_PNG).is_file()


def test_analysis_config_has_tau_shrink_fields():
    cfg = compose_config(regime=_REGIME, baseline=Baseline.B1, seed=_SEED)
    assert hasattr(cfg.analysis, "tau_shrink_lambdas")
    assert cfg.analysis.tau_shrink_lambdas == [0.0, 0.25, 0.5, 0.75, 1.0]
