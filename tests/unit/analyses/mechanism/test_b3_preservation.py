"""Unit tests for B3 Preservation analysis (T14)."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import polars as pl
import pytest

from datp.analyses.mechanism.b3_preservation import run_b3_preservation
from datp.artifacts.constants import (
    MODEL_CHECKPOINT,
    SCORING_MANIFEST_FILE,
    SCORING_SENTINEL,
)
from datp.artifacts.directories import SCORES_DIR
from datp.validation.enums import ReuseVerdict
from datp.core.enums import ScoringStage
from datp.data.common.storage import write_artifact
from datp.evaluation.metric_keys import SCORE_COLUMN

_CLIENTS = (
    "Danmini_Doorbell",
    "Ecobee_Thermostat",
    "Ennio_Doorbell",
    "Provision_PT_737E_Security_Camera",
    "Provision_PT_838_Security_Camera",
)
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


def _write_score(path: Path, values: np.ndarray) -> None:
    write_artifact(pl.DataFrame({SCORE_COLUMN: values.astype(np.float32)}), path)


class TestB3Preservation:
    def test_produces_rows_for_each_seed(self, tmp_path: Path):
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

        result = run_b3_preservation(base_dir)
        assert len(result.rows) == 1
        assert result.rows[0].seed == _SEED
        assert result.rows[0].cv_fpr >= 0
        assert result.rows[0].coverage_ratio >= 0

    def test_b3_uses_families(self, tmp_path: Path):
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

        result = run_b3_preservation(base_dir)
        assert result.rows[0].client_count == 5
        assert result.rows[0].eligible_count >= 0

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
            run_b3_preservation(base_dir)

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

        run_b3_preservation(base_dir, write_outputs=True)
        csv_path = base_dir / "analysis" / "b3_preservation.csv"
        assert csv_path.is_file()
        header = csv_path.read_text(encoding="utf-8").splitlines()[0]
        assert header == (
            "seed,cv_fpr,mean_fpr,coverage_ratio,eligible_count,client_count,within_tolerance"
        )
