"""Unit tests for JS Divergence vs DATP Benefit analysis (T11)."""

from __future__ import annotations
from datp.artifacts.names import ArtifactDir, ArtifactFile

import json
from pathlib import Path

import numpy as np
import polars as pl
import pytest

from datp.analyses.mechanism.js_divergence_benefit import (
    JSDivergenceResult,
    JSClientRow,
    _per_client_js,
    _write_scatter,
    run_js_divergence,
)
from datp.validation.enums import ReuseVerdict
from datp.core.enums import Regime, ScoringStage
from datp.data.common.storage import write_artifact
from datp.scoring.schema import SCORE_COLUMN

_CLIENTS = ("Danmini_Doorbell", "Ecobee_Thermostat", "Ennio_Doorbell")
_SEED = 0


def _write_scores(path: Path, values: np.ndarray) -> None:
    write_artifact(pl.DataFrame({SCORE_COLUMN: values.astype(np.float32)}), path)


def _build_score_cell(base_dir: Path) -> Path:
    cell_dir = base_dir / ArtifactDir.SCORES / "a" / f"seed_{_SEED}"
    cell_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(42)
    for stage in (ScoringStage.CAL, ScoringStage.TEST_BENIGN, ScoringStage.TEST_ATTACK):
        stage_dir = cell_dir / stage.value
        stage_dir.mkdir(parents=True, exist_ok=True)
        for cid in _CLIENTS:
            size = 300 if stage == ScoringStage.CAL else 200
            _write_scores(
                stage_dir / f"{cid}.parquet",
                rng.normal(0.5, 0.2, size).astype(np.float32),
            )
    ckpt = base_dir / "checkpoints" / "a" / f"seed_{_SEED}" / ArtifactFile.MODEL_CHECKPOINT
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
    (cell_dir / ArtifactFile.SCORING_MANIFEST).write_text(
        json.dumps(manifest), encoding="utf-8"
    )
    (cell_dir / ArtifactFile.SCORING_SENTINEL).write_text("done\n", encoding="utf-8")
    return cell_dir


class TestPerClientJS:
    def test_two_identical_clients_zero_jsd(self):
        rng = np.random.default_rng(42)
        a = rng.normal(0, 1, 1000)
        errors = {"c1": a, "c2": a.copy()}
        jsd = _per_client_js(errors, js_n_bins=32)
        assert 0 <= jsd["c1"] < 0.01
        assert 0 <= jsd["c2"] < 0.01

    def test_distinct_distributions_positive_jsd(self):
        rng = np.random.default_rng(42)
        errors = {
            "low": rng.normal(0, 0.5, 1000),
            "high": rng.normal(5, 0.5, 1000),
        }
        jsd = _per_client_js(errors, js_n_bins=32)
        assert jsd["low"] > 0.01
        assert jsd["high"] > 0.01

    def test_single_client_jsd_is_zero(self):
        rng = np.random.default_rng(42)
        errors = {"only": rng.normal(0, 1, 500)}
        jsd = _per_client_js(errors, js_n_bins=32)
        assert jsd["only"] < 1e-6


class TestJSClientRow:
    def test_frozen_mutation_raises(self):
        row = JSClientRow(
            regime=Regime.A,
            alpha=None,
            client_id="test",
            js_divergence=0.1,
            fpr_b1=0.05,
            fpr_b2=0.02,
            delta_fpr=0.03,
            seed=0,
            device_family="camera",
        )
        with pytest.raises(Exception):
            row.js_divergence = 0.5  # type: ignore[misc]

    def test_forbid_extra_fields_raises(self):
        with pytest.raises(Exception):
            JSClientRow.model_validate(
                {
                    "client_id": "test",
                    "js_divergence": 0.1,
                    "fpr_b1": 0.05,
                    "fpr_b2": 0.02,
                    "delta_fpr": 0.03,
                    "seed": 0,
                    "device_family": "camera",
                    "extra": 1,
                }
            )

    def test_missing_required_field_raises(self):
        with pytest.raises(Exception):
            JSClientRow.model_validate({"js_divergence": 0.1, "fpr_b1": 0.05})


class TestJSDivergenceResult:
    def test_frozen_mutation_raises(self):
        result = JSDivergenceResult(
            rows=[],
            spearman_rho=0.0,
            spearman_p_value=1.0,
            r_squared=0.0,
            spearman_mechanism_wording="HYPOTHESIS",
            n_clients=0,
            n_cells=0,
        )
        with pytest.raises(Exception):
            result.spearman_rho = 0.5  # type: ignore[misc]

    def test_forbid_extra_fields_raises(self):
        with pytest.raises(Exception):
            JSDivergenceResult.model_validate(
                {
                    "rows": [],
                    "spearman_rho": 0.0,
                    "spearman_p_value": 1.0,
                    "r_squared": 0.0,
                    "spearman_mechanism_wording": "HYPOTHESIS",
                    "n_clients": 0,
                    "n_cells": 0,
                    "extra": "bad",
                }
            )


class TestWriteScatter:
    def test_creates_png_file(self, tmp_path: Path):
        row = JSClientRow(
            regime=Regime.A,
            alpha=None,
            client_id="c1",
            js_divergence=0.1,
            fpr_b1=0.05,
            fpr_b2=0.02,
            delta_fpr=0.03,
            seed=0,
            device_family="camera",
        )
        result = JSDivergenceResult(
            rows=[row],
            spearman_rho=0.0,
            spearman_p_value=1.0,
            r_squared=0.0,
            spearman_mechanism_wording="HYPOTHESIS",
            n_clients=1,
            n_cells=1,
        )
        _write_scatter(result, tmp_path)
        png = tmp_path / "analysis" / "js_divergence_scatter.png"
        assert png.is_file()


class TestRunJSDivergence:
    def test_no_regime_a_cells_raises(self, tmp_path: Path):
        base_dir = tmp_path
        scores_dir = base_dir / ArtifactDir.SCORES
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
            run_js_divergence(base_dir)

    def test_synthetic_regime_a_produces_rows(self, tmp_path: Path):
        base_dir = tmp_path
        cell_dir = _build_score_cell(base_dir)
        scores_dir = base_dir / ArtifactDir.SCORES
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

        result = run_js_divergence(base_dir)
        assert result.n_clients == 3
        assert result.n_cells == 1
        assert len(result.rows) == 3
        assert all(isinstance(r.js_divergence, float) for r in result.rows)

    def test_write_outputs_creates_files(self, tmp_path: Path):
        base_dir = tmp_path
        cell_dir = _build_score_cell(base_dir)
        scores_dir = base_dir / ArtifactDir.SCORES
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

        run_js_divergence(base_dir, write_outputs=True)
        table = base_dir / "analysis" / "js_divergence_table.csv"
        png = base_dir / "analysis" / "js_divergence_scatter.png"
        assert table.is_file()
        assert png.is_file()
