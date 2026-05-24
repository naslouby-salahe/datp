"""Unit tests for Threshold-Shift vs Delta-FPR/Delta-TPR analysis (T12)."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import polars as pl
import pytest

from datp.analyses.threshold_shift import ThresholdShiftRow, run_threshold_shift
from datp.artifacts.constants import (
    MODEL_CHECKPOINT,
    SCORING_MANIFEST_FILE,
    SCORING_SENTINEL,
)
from datp.artifacts.directories import SCORES_DIR
from datp.audit.enums import ReuseVerdict
from datp.core.enums import ScoringStage
from datp.data.common.storage import write_artifact
from datp.evaluation.metric_keys import SCORE_COLUMN

_CLIENTS = ("Danmini_Doorbell", "Ecobee_Thermostat", "Ennio_Doorbell")
_SEED = 0


def _build_score_cell(base_dir: Path) -> Path:
    cell_dir = base_dir / SCORES_DIR / "a" / f"seed_{_SEED}"
    cell_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(42)
    for stage in (ScoringStage.CAL, ScoringStage.TEST_BENIGN, ScoringStage.TEST_ATTACK):
        stage_dir = cell_dir / stage.value
        stage_dir.mkdir(parents=True, exist_ok=True)
        for cid in _CLIENTS:
            size = 300 if stage == ScoringStage.CAL else 200
            _write_score(
                stage_dir / f"{cid}.parquet",
                rng.normal(0.5, 0.2, size).astype(np.float32),
            )
    ckpt = base_dir / "checkpoints" / "a" / f"seed_{_SEED}" / MODEL_CHECKPOINT
    ckpt.parent.mkdir(parents=True, exist_ok=True)
    ckpt.write_bytes(b"fixture")
    manifest = _make_manifest(cell_dir, str(ckpt))
    (cell_dir / SCORING_MANIFEST_FILE).write_text(
        json.dumps(manifest), encoding="utf-8"
    )
    (cell_dir / SCORING_SENTINEL).write_text("done\n", encoding="utf-8")
    return cell_dir


def _write_score(path: Path, values: np.ndarray) -> None:
    write_artifact(pl.DataFrame({SCORE_COLUMN: values.astype(np.float32)}), path)


def _make_manifest(cell_dir: Path, ckpt_path: str) -> dict:
    return {
        "schema_version": "1",
        "dataset": "nbaiot",
        "regime": "a",
        "seed": _SEED,
        "alpha": None,
        "model_checkpoint_path": ckpt_path,
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


class TestThresholdShiftRow:
    def test_schema_frozen(self):
        row = ThresholdShiftRow(
            client_id="d1",
            tau_b1=0.1,
            tau_b2=0.08,
            shift=-0.02,
            fpr_b1=0.05,
            fpr_b2=0.02,
            delta_fpr=0.03,
            tpr_b1=0.9,
            tpr_b2=0.88,
            delta_tpr=-0.02,
            seed=0,
            device_family="camera",
        )
        with pytest.raises(Exception):
            row.shift = 0.0  # type: ignore[misc]


class TestRunThresholdShift:
    def test_no_regime_a_cells_raises(self, tmp_path: Path):
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
                }
            ]
        }
        (scores_dir / "cell_verdicts.json").write_text(json.dumps(verdicts))
        with pytest.raises(FileNotFoundError, match="Regime A"):
            run_threshold_shift(base_dir)

    def test_all_clients_included(self, tmp_path: Path):
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
                }
            ]
        }
        (scores_dir / "cell_verdicts.json").write_text(json.dumps(verdicts))

        result = run_threshold_shift(base_dir)
        assert result.n_clients == 3
        assert len(result.rows) == 3
        client_ids = {r.client_id for r in result.rows}
        assert client_ids == set(_CLIENTS)

    def test_shift_is_b2_minus_b1(self, tmp_path: Path):
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
                }
            ]
        }
        (scores_dir / "cell_verdicts.json").write_text(json.dumps(verdicts))

        result = run_threshold_shift(base_dir)
        for row in result.rows:
            assert abs(row.shift - (row.tau_b2 - row.tau_b1)) < 1e-12

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
                }
            ]
        }
        (scores_dir / "cell_verdicts.json").write_text(json.dumps(verdicts))

        run_threshold_shift(base_dir, write_outputs=True)
        assert (base_dir / "analysis" / "threshold_shift_table.csv").is_file()
        assert (base_dir / "analysis" / "threshold_shift_fpr.png").is_file()
        assert (base_dir / "analysis" / "threshold_shift_tpr.png").is_file()
