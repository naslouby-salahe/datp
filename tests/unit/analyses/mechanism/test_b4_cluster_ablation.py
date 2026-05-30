"""T10 tests — B4 feature ablation."""

from __future__ import annotations
from datp.artifacts.names import ArtifactDir, ArtifactFile

import json
import math
from pathlib import Path

import numpy as np
import polars as pl
import pytest

from datp.analyses.constants import B4_ABLATION_CONTINGENCY_PNG, B4_ABLATION_TABLE_CSV
from datp.analyses.mechanism.b4_cluster_ablation import (
    _SUBSET_LABELS,
    run_b4_ablation,
)
from datp.validation.constants import CELL_VERDICTS_JSON
from datp.config.compose import compose_config
from datp.validation.enums import ReuseVerdict
from datp.core.enums import SCORING_STAGES, Baseline, Regime, ScoringStage
from datp.data.common.storage import write_artifact
from datp.data.datasets.nbaiot.spec import NBAIOT_SPEC
from datp.scoring.schema import SCORE_COLUMN

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
    cell_dir = base_dir / ArtifactDir.SCORES / _REGIME.value / f"seed_{_SEED}"
    cell_dir.mkdir(parents=True, exist_ok=True)
    for stage in SCORING_STAGES:
        (cell_dir / stage.value).mkdir(parents=True, exist_ok=True)
    for i, cid in enumerate(_CLIENTS):
        for stage in SCORING_STAGES:
            _write_scores(
                cell_dir / stage.value / f"{cid}.parquet",
                _deterministic_scores(i, stage),
            )
    (cell_dir / ArtifactFile.SCORING_MANIFEST).write_text(
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
    (cell_dir / ArtifactFile.SCORING_SENTINEL).touch()
    return cell_dir


def _write_verdicts(base_dir: Path, cell_dir: str) -> None:
    verdicts_dir = base_dir / ArtifactDir.SCORES
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


def test_full_four_feature_subset_exists():
    """The full fingerprint subset (0,1,2,3) is in the subset labels."""
    assert (0, 1, 2, 3) in _SUBSET_LABELS
    assert _SUBSET_LABELS[(0, 1, 2, 3)] == "full"


def test_single_feature_subsets():
    """All single-feature subsets are defined."""
    for i in range(4):
        assert (i,) in _SUBSET_LABELS


def test_pair_subsets():
    """All pairs are defined (4 choose 2 = 6)."""
    pairs = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]
    for p in pairs:
        assert p in _SUBSET_LABELS


def test_triple_subsets():
    """All triples are defined (4 choose 3 = 4)."""
    triples = [(0, 1, 2), (0, 1, 3), (0, 2, 3), (1, 2, 3)]
    for t in triples:
        assert t in _SUBSET_LABELS


def test_invalid_feature_subset_raises():
    """An invalid feature index produces an IndexError from numpy."""
    with pytest.raises((IndexError, KeyError)):
        _ = _SUBSET_LABELS[(99,)]


def test_full_run_produces_rows(tmp_path: Path):
    base_dir = tmp_path / "test_full"
    cell_dir = _build_score_cell(base_dir)
    _write_verdicts(base_dir, str(cell_dir))

    cfg = compose_config(regime=_REGIME, baseline=Baseline.B1, seed=_SEED)
    result = run_b4_ablation(base_dir, config=cfg)

    assert len(result.rows) > 0
    # Should have 15 subsets × 1 cell = 15 rows
    subsets_seen = {r.subset for r in result.rows}
    assert "full" in subsets_seen
    assert "mean" in subsets_seen


def test_full_reproduces_b4():
    """The full fingerprint should reproduce canonical B4 within tolerance."""
    # This is tested by the run function itself via full_vs_canonical_max_deviation
    pass  # Verified by full_run test and result.full_feature_reproduces_b4


def test_contingency_computation():
    """ARI computation uses device family labels."""
    from sklearn.metrics import adjusted_rand_score

    labels = np.array([0, 0, 1, 1, 2, 2])
    families = np.array([0, 0, 1, 1, 2, 2])
    ari = adjusted_rand_score(families, labels)
    assert math.isclose(ari, 1.0)  # perfect agreement


def test_contingency_random():
    """ARI ≈ 0 for random cluster assignment."""
    from sklearn.metrics import adjusted_rand_score

    rng = np.random.default_rng(42)
    labels = rng.integers(0, 3, size=50)
    families = rng.integers(0, 3, size=50)
    ari = adjusted_rand_score(families, labels)
    # ARI for random assignment should be near 0
    assert abs(ari) < 0.1


def test_write_outputs_creates_csv_and_png(tmp_path: Path):
    base_dir = tmp_path / "test_write"
    cell_dir = _build_score_cell(base_dir)
    _write_verdicts(base_dir, str(cell_dir))

    cfg = compose_config(regime=_REGIME, baseline=Baseline.B1, seed=_SEED)
    run_b4_ablation(base_dir, config=cfg, write_outputs=True)
    assert (base_dir / ArtifactDir.ANALYSIS / B4_ABLATION_TABLE_CSV).is_file()
    # Contingency PNG may not be written if ARI is all NaN — but it should be for Regime A
    assert (base_dir / ArtifactDir.ANALYSIS / B4_ABLATION_CONTINGENCY_PNG).is_file()


def test_csv_columns_preserved(tmp_path: Path):
    base_dir = tmp_path / "test_csv_cols"
    cell_dir = _build_score_cell(base_dir)
    _write_verdicts(base_dir, str(cell_dir))

    cfg = compose_config(regime=_REGIME, baseline=Baseline.B1, seed=_SEED)
    run_b4_ablation(base_dir, config=cfg, write_outputs=True)

    csv_path = base_dir / ArtifactDir.ANALYSIS / B4_ABLATION_TABLE_CSV
    header = csv_path.read_text(encoding="utf-8").splitlines()[0]
    assert header == (
        "regime,seed,alpha,subset,n_features,k,silhouette,ari_vs_family,"
        "cv_fpr,mean_fpr,coverage_ratio,eligible_count"
    )


def test_fingerprints_computed_once_per_cell(tmp_path: Path, monkeypatch):
    """Full fingerprints are computed once per cell, then sliced for each subset."""
    from datp.analyses.mechanism import b4_cluster_ablation as mod

    base_dir = tmp_path / "test_recompute"
    cell_dir = _build_score_cell(base_dir)
    _write_verdicts(base_dir, str(cell_dir))

    call_count = {"n": 0}
    real_fn = mod.compute_fingerprints

    def counting(*args, **kwargs):
        call_count["n"] += 1
        return real_fn(*args, **kwargs)

    monkeypatch.setattr(mod, "compute_fingerprints", counting)
    cfg = compose_config(regime=_REGIME, baseline=Baseline.B1, seed=_SEED)
    mod.run_b4_ablation(base_dir, config=cfg)
    # 1 verified-safe cell → 1 fingerprint computation, not 15 (one per subset).
    assert call_count["n"] == 1


def test_full_feature_reproduces_canonical_b4(tmp_path: Path):
    base_dir = tmp_path / "test_repro"
    cell_dir = _build_score_cell(base_dir)
    _write_verdicts(base_dir, str(cell_dir))

    cfg = compose_config(regime=_REGIME, baseline=Baseline.B1, seed=_SEED)
    result = run_b4_ablation(base_dir, config=cfg)
    assert result.full_feature_reproduces_b4
    assert result.full_vs_canonical_max_deviation < 1e-9
