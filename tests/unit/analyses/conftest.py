"""Shared fixtures for analyses unit tests."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import polars as pl

from datp.artifacts.constants import (
    MODEL_CHECKPOINT,
    SCORING_MANIFEST_FILE,
    SCORING_SENTINEL,
)
from datp.artifacts.directories import SCORES_DIR
from datp.audit.constants import CELL_VERDICTS_JSON
from datp.audit.enums import ReuseVerdict
from datp.core.enums import Regime, ScoringStage
from datp.data.common.storage import write_artifact
from datp.evaluation.metric_keys import SCORE_COLUMN


def write_scores(path: Path, values: np.ndarray) -> None:
    """Write a single Parquet score file."""
    write_artifact(pl.DataFrame({SCORE_COLUMN: values.astype(np.float32)}), path)


def deterministic_scores(
    client_idx: int, stage: ScoringStage, seed: int = 7
) -> np.ndarray:
    """Deterministic per-client per-stage synthetic scores."""
    rng = np.random.default_rng(seed * client_idx + hash(stage.value) % 50)
    if stage == ScoringStage.CAL:
        return rng.uniform(0.01, 0.10, size=300).astype(np.float32)
    if stage == ScoringStage.TEST_BENIGN:
        return rng.uniform(0.01, 0.12, size=200).astype(np.float32)
    return rng.uniform(0.20, 0.80, size=400).astype(np.float32)


def build_score_cell(
    base_dir: Path,
    *,
    regime: Regime,
    seed: int,
    client_ids: list[str],
    alpha: str | None = None,
) -> Path:
    """Build a complete synthetic score cell with all artifacts."""
    alpha_segment = f"/alpha_{alpha}" if alpha else ""
    cell_dir = base_dir / SCORES_DIR / regime.value / f"seed_{seed}{alpha_segment}"
    cell_dir.mkdir(parents=True, exist_ok=True)

    for stage in (ScoringStage.CAL, ScoringStage.TEST_BENIGN, ScoringStage.TEST_ATTACK):
        stage_dir = cell_dir / stage.value
        stage_dir.mkdir(parents=True, exist_ok=True)
        for i, cid in enumerate(client_ids):
            write_scores(
                stage_dir / f"{cid}.parquet",
                deterministic_scores(i, stage),
            )

    ckpt_dir = base_dir / "checkpoints" / regime.value / f"seed_{seed}"
    if alpha:
        ckpt_dir = ckpt_dir / f"alpha_{alpha}"
    ckpt = ckpt_dir / MODEL_CHECKPOINT
    ckpt.parent.mkdir(parents=True, exist_ok=True)
    ckpt.write_bytes(b"fixture")

    manifest = {
        "schema_version": "1",
        "dataset": "nbaiot",
        "regime": regime.value,
        "seed": seed,
        "alpha": alpha,
        "model_checkpoint_path": str(ckpt),
        "model_checkpoint_hash": "abc",
        "scoring_code_version": "fixture",
        "score_column_name": SCORE_COLUMN,
        "expected_client_ids": sorted(client_ids),
        "expected_splits": ["cal", "test_benign", "test_attack"],
        "actual_client_ids": sorted(client_ids),
        "actual_splits": ["cal", "test_benign", "test_attack"],
        "records": [
            {"client_id": c, "split": s}
            for c in client_ids
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


def write_verdicts(
    base_dir: Path,
    cell_dir: str,
    *,
    regime: Regime,
    seed: int,
    alpha: str | None = None,
    verdict: str = ReuseVerdict.VERIFIED_REUSE_SAFE,
) -> None:
    """Write cell_verdicts.json with a single cell entry."""
    verdicts_dir = base_dir / SCORES_DIR
    verdicts_dir.mkdir(parents=True, exist_ok=True)
    entry = {
        "cell_dir": cell_dir,
        "regime": regime.value,
        "seed": seed,
        "alpha": alpha,
        "dataset": "nbaiot",
        "verdict": verdict,
    }
    index = {
        "cells": [entry],
        "summary": {
            "total": 1,
            "verified_reuse_safe": (
                1 if verdict == ReuseVerdict.VERIFIED_REUSE_SAFE else 0
            ),
            "reuse_blocked_rerun_required": (
                0 if verdict == ReuseVerdict.VERIFIED_REUSE_SAFE else 1
            ),
            "by_regime": {regime.value: {verdict: 1}},
        },
    }
    (verdicts_dir / CELL_VERDICTS_JSON).write_text(json.dumps(index), encoding="utf-8")
