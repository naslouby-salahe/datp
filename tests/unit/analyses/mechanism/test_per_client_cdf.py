"""Unit tests for Per-Client CDF / Failure-Mode analysis (T16)."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import polars as pl
import pytest

from datp.analyses.mechanism.per_client_cdf import (
    _classify_failure,
    _empirical_cdf,
    run_per_client_cdf,
)
from datp.artifacts.constants import (
    MODEL_CHECKPOINT,
    SCORING_MANIFEST_FILE,
    SCORING_SENTINEL,
)
from datp.artifacts.directories import SCORES_DIR
from datp.audit.enums import ReuseVerdict
from datp.core.enums import ScoringStage
from datp.data.common.storage import write_artifact
from datp.data.datasets.nbaiot.spec import DEVICE_DIRS
from datp.evaluation.metric_keys import SCORE_COLUMN

_CLIENTS = DEVICE_DIRS
_SEED = 0


def _write_score(path: Path, values: np.ndarray) -> None:
    write_artifact(pl.DataFrame({SCORE_COLUMN: values.astype(np.float32)}), path)


def _build_score_cell(base_dir: Path) -> Path:
    cell_dir = base_dir / SCORES_DIR / "a" / f"seed_{_SEED}"
    cell_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(42)
    for stage in (ScoringStage.CAL, ScoringStage.TEST_BENIGN, ScoringStage.TEST_ATTACK):
        stage_dir = cell_dir / stage.value
        stage_dir.mkdir(parents=True, exist_ok=True)
        for i, cid in enumerate(_CLIENTS):
            shift = 0.1 * i
            size = 300 if stage == ScoringStage.CAL else 200
            _write_score(
                stage_dir / f"{cid}.parquet",
                rng.normal(0.5 + shift, 0.2, size).astype(np.float32),
            )
    ckpt = base_dir / "checkpoints" / "a" / f"seed_{_SEED}" / MODEL_CHECKPOINT
    ckpt.parent.mkdir(parents=True, exist_ok=True)
    ckpt.write_bytes(b"fixture")
    manifest = {
        "schema_version": "1",
        "dataset": "nbaiot",
        "regime": "a",
        "seed": _SEED,
        "alpha": None,
        "model_checkpoint_path": str(ckpt),
        "model_checkpoint_hash": "abc",
        "scoring_code_version": "fixture",
        "score_column_name": SCORE_COLUMN,
        "expected_client_ids": sorted(_CLIENTS),
        "expected_splits": ["cal", "test_benign", "test_attack"],
        "actual_client_ids": sorted(_CLIENTS),
        "actual_splits": ["cal", "test_benign", "test_attack"],
        "records": [
            {"client_id": c, "split": s}
            for c in _CLIENTS
            for s in ("cal", "test_benign", "test_attack")
        ],
        "completion_status": "complete",
        "generated_at_utc": "2026-01-01T00:00:00+00:00",
    }
    (cell_dir / SCORING_MANIFEST_FILE).write_text(
        json.dumps(manifest), encoding="utf-8"
    )
    (cell_dir / SCORING_SENTINEL).write_text("done\n", encoding="utf-8")
    return cell_dir


class TestEmpiricalCDF:
    def test_known_array(self):
        x, y = _empirical_cdf(np.array([1.0, 2.0, 3.0, 4.0]), n_points=0)
        assert len(x) == 4
        assert y[0] == 0.0
        assert y[-1] == 1.0

    def test_subsamples_to_n_points(self):
        x, y = _empirical_cdf(
            np.random.default_rng(42).normal(0, 1, 2000), n_points=100
        )
        assert len(x) <= 100


class TestClassifyFailure:
    def test_normal(self):
        assert _classify_failure(0.05, 0.95, 0.03, 0.97) == "NORMAL"

    def test_high_fpr_b1(self):
        assert "HIGH_FPR_B1" in _classify_failure(0.15, 0.95, 0.03, 0.97)

    def test_low_tpr_b1(self):
        assert "LOW_TPR_B1" in _classify_failure(0.05, 0.80, 0.03, 0.97)

    def test_high_fpr_b2(self):
        assert "HIGH_FPR_B2" in _classify_failure(0.05, 0.95, 0.15, 0.97)

    def test_low_tpr_b2(self):
        assert "LOW_TPR_B2" in _classify_failure(0.05, 0.95, 0.03, 0.80)

    def test_combined(self):
        result = _classify_failure(0.15, 0.80, 0.12, 0.85)
        assert "HIGH_FPR_B1" in result
        assert "LOW_TPR_B1" in result


class TestRunPerClientCDF:
    def test_all_9_devices_included(self, tmp_path: Path):
        base_dir = tmp_path
        cell_dir = _build_score_cell(base_dir)
        scores_dir = base_dir / SCORES_DIR
        verdicts = {
            "cells": [
                {
                    "verdict": ReuseVerdict.VERIFIED_REUSE_SAFE,
                    "regime": "a",
                    "cell_dir": str(cell_dir),
                    "seed": _SEED,
                    "alpha": None,
                    "dataset": "nbaiot",
                }
            ]
        }
        (scores_dir / "cell_verdicts.json").write_text(json.dumps(verdicts))

        result = run_per_client_cdf(base_dir)
        assert result.n_devices == 9
        assert len(result.rows) == 9

    def test_canonical_device_names(self, tmp_path: Path):
        base_dir = tmp_path
        cell_dir = _build_score_cell(base_dir)
        scores_dir = base_dir / SCORES_DIR
        verdicts = {
            "cells": [
                {
                    "verdict": ReuseVerdict.VERIFIED_REUSE_SAFE,
                    "regime": "a",
                    "cell_dir": str(cell_dir),
                    "seed": _SEED,
                    "alpha": None,
                    "dataset": "nbaiot",
                }
            ]
        }
        (scores_dir / "cell_verdicts.json").write_text(json.dumps(verdicts))

        result = run_per_client_cdf(base_dir)
        device_names = {r.device for r in result.rows}
        assert device_names == set(DEVICE_DIRS)

    def test_no_regime_a_raises(self, tmp_path: Path):
        base_dir = tmp_path
        scores_dir = base_dir / SCORES_DIR
        scores_dir.mkdir(parents=True)
        verdicts = {
            "cells": [
                {
                    "verdict": ReuseVerdict.VERIFIED_REUSE_SAFE,
                    "regime": "b",
                    "cell_dir": str(scores_dir / "b" / "seed_0"),
                    "seed": 0,
                    "alpha": None,
                    "dataset": "nbaiot",
                }
            ]
        }
        (scores_dir / "cell_verdicts.json").write_text(json.dumps(verdicts))
        with pytest.raises(FileNotFoundError, match="Regime A"):
            run_per_client_cdf(base_dir)

    def test_write_outputs(self, tmp_path: Path):
        base_dir = tmp_path
        cell_dir = _build_score_cell(base_dir)
        scores_dir = base_dir / SCORES_DIR
        verdicts = {
            "cells": [
                {
                    "verdict": ReuseVerdict.VERIFIED_REUSE_SAFE,
                    "regime": "a",
                    "cell_dir": str(cell_dir),
                    "seed": _SEED,
                    "alpha": None,
                    "dataset": "nbaiot",
                }
            ]
        }
        (scores_dir / "cell_verdicts.json").write_text(json.dumps(verdicts))

        run_per_client_cdf(base_dir, write_outputs=True)
        assert (base_dir / "analysis" / "per_client_failure_modes.csv").is_file()
        assert (base_dir / "analysis" / "per_client_cdf_grid.png").is_file()
