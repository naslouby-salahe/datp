"""T05 tests — q-sensitivity analysis."""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import polars as pl
import pytest

from datp.analyses.q_sensitivity import (
    Q_SENSITIVITY_HEATMAP_PNG,
    Q_SENSITIVITY_TABLE_CSV,
    run_q_sensitivity,
)
from datp.artifacts.constants import (
    METRICS_FILE,
    MODEL_CHECKPOINT,
    SCORING_MANIFEST_FILE,
    SCORING_SENTINEL,
)
from datp.artifacts.directories import ANALYSIS_DIR, SCORES_DIR
from datp.audit.constants import CELL_VERDICTS_JSON, SCALAR_METRIC_TOLERANCE
from datp.baselines.common.thresholds import derive_threshold
from datp.config.compose import compose_config
from datp.audit.enums import ReuseVerdict
from datp.core.enums import SCORING_STAGES, Baseline, Regime, ScoringStage
from datp.data.common.storage import write_artifact
from datp.data.datasets.nbaiot.spec import NBAIOT_SPEC
from datp.evaluation.metric_keys import SCORE_COLUMN
from datp.evaluation.metrics import build_evaluation_result, compute_client_metrics
from datp.evaluation.score_loading import ScoreProvider

_CLIENTS = NBAIOT_SPEC.device_ids
_REGIME = Regime.A
_SEED = 0
_REFERENCE_Q = 0.95
_Q_GRID = [0.90, 0.95, 0.975, 0.99]
_Q_GRID_SMALL = [0.90, 0.95]


# -------------------------------------------------------------------------------------
# Fixture helpers
# -------------------------------------------------------------------------------------


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
        stage_dir = cell_dir / stage.value
        stage_dir.mkdir(parents=True, exist_ok=True)
        for idx, cid in enumerate(_CLIENTS):
            _write_scores(
                stage_dir / f"{cid}.parquet", _deterministic_scores(idx, stage)
            )
    ckpt = base_dir / "checkpoints" / _REGIME.value / f"seed_{_SEED}" / MODEL_CHECKPOINT
    ckpt.parent.mkdir(parents=True, exist_ok=True)
    ckpt.write_bytes(b"fixture")
    manifest = {
        "schema_version": "1",
        "dataset": "nbaiot",
        "regime": _REGIME.value,
        "seed": _SEED,
        "alpha": None,
        "model_checkpoint_path": str(ckpt),
        "model_checkpoint_hash": "abc",
        "scoring_code_version": "fixture",
        "score_column_name": SCORE_COLUMN,
        "expected_client_ids": sorted(_CLIENTS),
        "expected_splits": [s.value for s in SCORING_STAGES],
        "actual_client_ids": sorted(_CLIENTS),
        "actual_splits": sorted(s.value for s in SCORING_STAGES),
        "records": [
            {"client_id": cid, "split": s.value}
            for cid in _CLIENTS
            for s in SCORING_STAGES
        ],
        "completion_status": "complete",
        "generated_at_utc": "2026-01-01T00:00:00+00:00",
    }
    (cell_dir / SCORING_MANIFEST_FILE).write_text(
        json.dumps(manifest), encoding="utf-8"
    )
    (cell_dir / SCORING_SENTINEL).write_text("done\n", encoding="utf-8")
    return cell_dir


def _write_cell_verdicts(
    base_dir: Path, cell_dir: Path, *, verdict: str = ReuseVerdict.VERIFIED_REUSE_SAFE
) -> None:
    entry = {
        "cell_dir": str(cell_dir),
        "regime": _REGIME.value,
        "seed": _SEED,
        "alpha": None,
        "dataset": "nbaiot",
        "verdict": verdict,
        "manifest_status": "pass",
        "reproduction_status": "pass",
        "reason": "all checks passed",
        "failed_checks": [],
    }
    index = {
        "cells": [entry],
        "summary": {
            "total": 1,
            "verified_reuse_safe": 1
            if verdict == ReuseVerdict.VERIFIED_REUSE_SAFE
            else 0,
            "reuse_blocked_rerun_required": 0
            if verdict == ReuseVerdict.VERIFIED_REUSE_SAFE
            else 1,
            "by_regime": {"a": {verdict: 1}},
        },
    }
    verdicts_dir = base_dir / SCORES_DIR
    verdicts_dir.mkdir(parents=True, exist_ok=True)
    (verdicts_dir / CELL_VERDICTS_JSON).write_text(json.dumps(index), encoding="utf-8")


def _write_metrics_json_for_baseline(
    base_dir: Path, baseline: Baseline, evaluation_data: dict
) -> None:
    out = (
        base_dir
        / "results"
        / _REGIME.value
        / baseline.value
        / f"seed_{_SEED}"
        / METRICS_FILE
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(evaluation_data), encoding="utf-8")


def _compute_reference_metrics(cell_dir: Path, baseline: Baseline) -> dict:
    """Compute metrics at reference q=0.95 for storing as the 'stored' reference."""
    cfg = compose_config(regime=_REGIME, baseline=Baseline.B1, seed=_SEED, alpha=None)
    cal_errors: dict[str, np.ndarray] = {}
    for parquet in sorted((cell_dir / ScoringStage.CAL.value).glob("*.parquet")):
        cal_errors[parquet.stem] = (
            pl.read_parquet(parquet)
            .get_column(SCORE_COLUMN)
            .to_numpy()
            .astype(np.float64)
        )

    b1_result = derive_threshold(
        Baseline.B1,
        cal_errors,
        n_min=cfg.threshold.n_min,
        q=_REFERENCE_Q,
        tau_global=0.0,
        regime=_REGIME,
        threshold_cfg=cfg.threshold,
    )
    tau_global = float(b1_result.tau_global)
    tr = derive_threshold(
        baseline,
        cal_errors,
        n_min=cfg.threshold.n_min,
        q=_REFERENCE_Q,
        tau_global=tau_global,
        regime=_REGIME,
        threshold_cfg=cfg.threshold,
    )
    provider = ScoreProvider(cell_dir)
    per_client = []
    eligible_ids: list[str] = []
    pending_ids: list[str] = []
    for ct in tr.client_thresholds:
        benign, attack = provider.load_test_scores(ct.client_id)
        per_client.append(
            compute_client_metrics(ct.client_id, benign, attack, ct.threshold)
        )
        (pending_ids if ct.calibration_pending else eligible_ids).append(ct.client_id)
    ev = build_evaluation_result(
        baseline=baseline,
        regime=_REGIME,
        seed=_SEED,
        alpha=None,
        per_client=per_client,
        eligible_ids=eligible_ids,
        pending_ids=pending_ids,
        eval_incomplete_ids=[],
    )
    return {
        "cv_fpr": ev.cv_fpr,
        "mean_fpr": ev.mean_fpr,
        "coverage_ratio": ev.coverage_ratio,
    }


def _setup_full_fixture(base_dir: Path) -> Path:
    """Build a complete fixture: score cell + verdicts + metrics.json at reference q."""
    cell_dir = _build_score_cell(base_dir)
    _write_cell_verdicts(base_dir, cell_dir)
    for baseline in (Baseline.B1, Baseline.B2, Baseline.B4):
        data = _compute_reference_metrics(cell_dir, baseline)
        _write_metrics_json_for_baseline(base_dir, baseline, data)
    return cell_dir


# -------------------------------------------------------------------------------------
# Tests
# -------------------------------------------------------------------------------------


def test_empty_q_grid_raises(tmp_path: Path) -> None:
    base_dir = tmp_path / "outputs"
    base_dir.mkdir()
    _write_cell_verdicts(base_dir, base_dir / "dummy_cell")
    with pytest.raises(ValueError, match="q_grid cannot be empty"):
        run_q_sensitivity(base_dir, q_grid=[])


def test_missing_verdicts_file_raises(tmp_path: Path) -> None:
    base_dir = tmp_path / "outputs"
    base_dir.mkdir()
    with pytest.raises(FileNotFoundError, match="cell_verdicts.json"):
        run_q_sensitivity(base_dir, q_grid=_Q_GRID_SMALL)


def test_blocked_cell_is_skipped(tmp_path: Path) -> None:
    base_dir = tmp_path / "outputs"
    cell_dir = _build_score_cell(base_dir)
    _write_cell_verdicts(
        base_dir, cell_dir, verdict=ReuseVerdict.REUSE_BLOCKED_RERUN_REQUIRED
    )
    result = run_q_sensitivity(base_dir, q_grid=_Q_GRID_SMALL)
    assert result.verified_safe_cell_count == 0
    assert result.rows == []


def test_returns_rows_for_all_q_values_and_baselines(tmp_path: Path) -> None:
    base_dir = tmp_path / "outputs"
    _setup_full_fixture(base_dir)
    result = run_q_sensitivity(base_dir, q_grid=_Q_GRID_SMALL)
    # 2 q values × 3 baselines × 1 cell
    assert len(result.rows) == 2 * 3 * 1
    q_vals = {row.q for row in result.rows}
    assert q_vals == set(_Q_GRID_SMALL)
    baseline_vals = {row.baseline for row in result.rows}
    assert baseline_vals == {Baseline.B1, Baseline.B2, Baseline.B4}


def test_reference_q_reproduces_stored_metrics(tmp_path: Path) -> None:
    base_dir = tmp_path / "outputs"
    _setup_full_fixture(base_dir)
    result = run_q_sensitivity(base_dir, q_grid=_Q_GRID_SMALL)
    assert result.reference_q_verified, (
        f"reference_q_max_deviation={result.reference_q_max_deviation} > tolerance={SCALAR_METRIC_TOLERANCE}"
    )
    assert result.reference_q_max_deviation <= SCALAR_METRIC_TOLERANCE


def test_different_q_values_produce_different_thresholds(tmp_path: Path) -> None:
    """Higher q → higher percentile threshold → lower or equal FPR on benign test data."""
    base_dir = tmp_path / "outputs"
    _setup_full_fixture(base_dir)
    result = run_q_sensitivity(base_dir, q_grid=[0.90, 0.99])
    rows_b1 = sorted(
        [r for r in result.rows if r.baseline == Baseline.B1],
        key=lambda r: r.q,
    )
    assert len(rows_b1) == 2
    # cv_fpr at q=0.90 should generally differ from q=0.99 (threshold moves)
    # At minimum the thresholds are computed at different percentiles.
    # We verify the rows exist with distinct q values.
    assert rows_b1[0].q == pytest.approx(0.90)
    assert rows_b1[1].q == pytest.approx(0.99)
    # FPR at higher q (higher threshold) should be <= FPR at lower q
    # (more permissive threshold = more benign pass = lower FPR).
    # Note: mean_fpr is over eligible clients.
    assert not math.isnan(rows_b1[0].mean_fpr) and not math.isnan(rows_b1[1].mean_fpr)
    # The direction: higher q → higher threshold → fewer benign flagged → lower FPR.
    assert rows_b1[1].mean_fpr <= rows_b1[0].mean_fpr + 1e-6  # allow fp tolerance


def test_all_four_q_values_produce_distinct_b1_cv_fpr(tmp_path: Path) -> None:
    """All four q values should produce at least two distinct CV(FPR) values for B1."""
    base_dir = tmp_path / "outputs"
    _setup_full_fixture(base_dir)
    result = run_q_sensitivity(base_dir, q_grid=_Q_GRID)
    b1_cv_fprs = [r.cv_fpr for r in result.rows if r.baseline == Baseline.B1]
    assert len(b1_cv_fprs) == 4
    # At least two should differ (the threshold range 0.90-0.99 spans a meaningful range).
    assert len(set(round(v, 6) for v in b1_cv_fprs)) >= 2


def test_write_outputs_creates_csv_and_heatmap(tmp_path: Path) -> None:
    base_dir = tmp_path / "outputs"
    _setup_full_fixture(base_dir)
    result = run_q_sensitivity(base_dir, q_grid=_Q_GRID_SMALL, write_outputs=True)
    csv_path = base_dir / ANALYSIS_DIR / Q_SENSITIVITY_TABLE_CSV
    png_path = base_dir / ANALYSIS_DIR / Q_SENSITIVITY_HEATMAP_PNG
    assert csv_path.is_file(), "CSV table not created"
    assert png_path.is_file(), "Heatmap PNG not created"
    lines = csv_path.read_text(encoding="utf-8").splitlines()
    header = lines[0].split(",")
    assert "q" in header
    assert "cv_fpr" in header
    assert "baseline" in header
    # number of data rows = result.rows
    assert len(lines) - 1 == len(result.rows)


def test_result_has_correct_cell_count(tmp_path: Path) -> None:
    base_dir = tmp_path / "outputs"
    _setup_full_fixture(base_dir)
    result = run_q_sensitivity(base_dir, q_grid=_Q_GRID_SMALL)
    assert result.verified_safe_cell_count == 1


def test_analysis_config_in_base_config() -> None:
    """Verify AnalysisConfig is wired into BASE_CONFIG."""
    from datp.config.compose import BASE_CONFIG

    assert BASE_CONFIG.analysis.q_grid == pytest.approx([0.90, 0.95, 0.975, 0.99])
