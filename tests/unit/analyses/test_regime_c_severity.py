"""Unit tests for Regime C Severity analysis (T15)."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import polars as pl
import pytest

from datp.analyses.regime_c_severity import run_regime_c_severity
from datp.artifacts.constants import MODEL_CHECKPOINT, SCORING_MANIFEST_FILE, SCORING_SENTINEL
from datp.artifacts.directories import SCORES_DIR
from datp.audit.enums import ReuseVerdict
from datp.core.enums import ScoringStage
from datp.data.common.storage import write_artifact
from datp.evaluation.metric_keys import SCORE_COLUMN

_CLIENTS = tuple(f"client_{i}" for i in range(10))
_SEED = 0


def _build_score_cell(base_dir: Path, alpha_label: str, seed: int) -> Path:
    cell_dir = base_dir / SCORES_DIR / "c" / f"seed_{seed}" / f"alpha_{alpha_label}"
    cell_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(42 + seed + hash(alpha_label) % 100)
    for stage in (ScoringStage.CAL, ScoringStage.TEST_BENIGN, ScoringStage.TEST_ATTACK):
        stage_dir = cell_dir / stage.value
        stage_dir.mkdir(parents=True, exist_ok=True)
        for cid in _CLIENTS:
            size = 200 if stage == ScoringStage.CAL else 150
            _write_score(stage_dir / f"{cid}.parquet", rng.normal(0.5, 0.2, size).astype(np.float32))
    ckpt = base_dir / "checkpoints" / "c" / f"seed_{seed}" / f"alpha_{alpha_label}" / MODEL_CHECKPOINT
    ckpt.parent.mkdir(parents=True, exist_ok=True)
    ckpt.write_bytes(b"fixture")
    manifest = {
        "schema_version": "1", "dataset": "nbaiot",
        "regime": "c", "seed": seed, "alpha": alpha_label,
        "model_checkpoint_path": str(ckpt), "model_checkpoint_hash": "abc",
        "scoring_code_version": "fixture", "score_column_name": SCORE_COLUMN,
        "expected_client_ids": sorted(_CLIENTS), "expected_splits": ["cal", "test_benign", "test_attack"],
        "actual_client_ids": sorted(_CLIENTS), "actual_splits": ["cal", "test_benign", "test_attack"],
        "records": [{"client_id": c, "split": s} for c in _CLIENTS for s in ("cal", "test_benign", "test_attack")],
        "completion_status": "complete", "generated_at_utc": "2026-01-01T00:00:00+00:00",
    }
    (cell_dir / SCORING_MANIFEST_FILE).write_text(json.dumps(manifest), encoding="utf-8")
    (cell_dir / SCORING_SENTINEL).write_text("done\n", encoding="utf-8")
    return cell_dir


def _write_score(path: Path, values: np.ndarray) -> None:
    write_artifact(pl.DataFrame({SCORE_COLUMN: values.astype(np.float32)}), path)


class TestRegimeCSeverity:
    def test_no_regime_c_cells_raises(self, tmp_path: Path):
        base_dir = tmp_path
        scores_dir = base_dir / SCORES_DIR
        scores_dir.mkdir(parents=True)
        verdicts = {"cells": [{"verdict": ReuseVerdict.VERIFIED_REUSE_SAFE, "regime": "a", "cell_dir": str(scores_dir / "a" / "seed_0"), "seed": 0, "alpha": None}]}
        (scores_dir / "cell_verdicts.json").write_text(json.dumps(verdicts))
        with pytest.raises(FileNotFoundError, match="Regime C"):
            run_regime_c_severity(base_dir)

    def test_reports_missing_alphas(self, tmp_path: Path):
        base_dir = tmp_path
        scores_dir = base_dir / SCORES_DIR
        scores_dir.mkdir(parents=True)
        cell_dirs = []
        for alpha in ("0.1", "0.5", "iid"):
            cd = _build_score_cell(base_dir, alpha, 0)
            cell_dirs.append(cd)
        verdicts = {
            "cells": [
                {"verdict": ReuseVerdict.VERIFIED_REUSE_SAFE, "regime": "c", "cell_dir": str(cd), "seed": 0, "alpha": alpha}
                for cd, alpha in zip(cell_dirs, ("0.1", "0.5", "iid"))
            ]
        }
        (scores_dir / "cell_verdicts.json").write_text(json.dumps(verdicts))

        result = run_regime_c_severity(base_dir)
        assert result.suppressed
        assert len(result.missing_alphas) > 0
        assert "0.3" in result.missing_alphas or "1.0" in result.missing_alphas

    def test_computes_gap_correctly(self, tmp_path: Path):
        base_dir = tmp_path
        scores_dir = base_dir / SCORES_DIR
        scores_dir.mkdir(parents=True)
        cd = _build_score_cell(base_dir, "0.5", 0)
        verdicts = {"cells": [{"verdict": ReuseVerdict.VERIFIED_REUSE_SAFE, "regime": "c", "cell_dir": str(cd), "seed": 0, "alpha": "0.5"}]}
        (scores_dir / "cell_verdicts.json").write_text(json.dumps(verdicts))

        result = run_regime_c_severity(base_dir)
        assert len(result.rows) == 1
        row = result.rows[0]
        assert abs(row.gap - (row.b1_cv_fpr - row.b2_cv_fpr)) < 1e-12
        assert row.alpha == "0.5"

    def test_write_outputs_with_suppression(self, tmp_path: Path):
        base_dir = tmp_path
        scores_dir = base_dir / SCORES_DIR
        scores_dir.mkdir(parents=True)
        cd = _build_score_cell(base_dir, "0.5", 0)
        verdicts = {"cells": [{"verdict": ReuseVerdict.VERIFIED_REUSE_SAFE, "regime": "c", "cell_dir": str(cd), "seed": 0, "alpha": "0.5"}]}
        (scores_dir / "cell_verdicts.json").write_text(json.dumps(verdicts))

        run_regime_c_severity(base_dir, write_outputs=True)
        assert (base_dir / "analysis" / "regime_c_severity_table.csv").is_file()
        assert (base_dir / "analysis" / "regime_c_severity_suppression.json").is_file()
