# SPDX-License-Identifier: Proprietary
"""Tests for checkpoint saving and convergence artifact persistence."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest
import torch.nn as nn

from datp.artifacts.names import ArtifactFile
from datp.config.models import ConvergenceConfig
from datp.core.enums import ConvergenceStatus, ConvergenceSummaryKey
from datp.federated.checkpoints import (
    ConvergenceSnapshot,
    save_checkpoint,
    save_convergence_artifacts,
)


def _make_conv_cfg(
    *,
    rounds_initial: int = 5,
    rounds_max: int = 100,
    relative_threshold: float = 0.03,
    window: int = 4,
    round_timeout_s: float = 3600.0,
) -> ConvergenceConfig:
    return ConvergenceConfig(
        rounds_initial=rounds_initial,
        rounds_max=rounds_max,
        relative_threshold=relative_threshold,
        window=window,
        round_timeout_s=round_timeout_s,
    )


def test_save_checkpoint_writes_final_path_atomically(tmp_path: Path) -> None:
    model = nn.Linear(2, 1)

    ckpt_file = save_checkpoint(model, tmp_path)

    assert ckpt_file.name == "model.pt"
    assert ckpt_file.exists()
    assert not (tmp_path / "model.pt.tmp").exists()


class TestSaveConvergenceArtifacts:
    def test_writes_both_files_atomically(self, tmp_path: Path) -> None:
        snapshot = ConvergenceSnapshot(
            loss_history=[1.0, 0.8, 0.6],
            converged_round=3,
            criterion_value=0.05,
        )
        cfg = _make_conv_cfg()

        save_convergence_artifacts(tmp_path, snapshot, cfg)

        curve = tmp_path / ArtifactFile.CONVERGENCE_CURVE
        summary = tmp_path / ArtifactFile.CONVERGENCE_SUMMARY
        assert curve.exists()
        assert summary.exists()
        assert not (tmp_path / "convergence_curve.csv.tmp").exists()
        assert not (tmp_path / "convergence_summary.json.tmp").exists()

    def test_curve_contains_expected_columns(self, tmp_path: Path) -> None:
        snapshot = ConvergenceSnapshot(
            loss_history=[1.0, 0.8],
            converged_round=2,
            criterion_value=0.01,
        )
        save_convergence_artifacts(tmp_path, snapshot, _make_conv_cfg())

        df = pd.read_csv(tmp_path / ArtifactFile.CONVERGENCE_CURVE)
        assert list(df.columns) == ["round", "fedavg_weighted_benign_val_loss"]
        assert len(df) == 2
        assert df["round"].tolist() == [1, 2]

    def test_summary_converged(self, tmp_path: Path) -> None:
        snapshot = ConvergenceSnapshot(
            loss_history=[2.0, 1.5, 1.0],
            converged_round=3,
            criterion_value=0.02,
        )
        save_convergence_artifacts(tmp_path, snapshot, _make_conv_cfg())

        payload = json.loads(
            (tmp_path / ArtifactFile.CONVERGENCE_SUMMARY).read_text()
        )
        assert payload[ConvergenceSummaryKey.CONVERGENCE_ROUND] == 3
        assert payload[ConvergenceSummaryKey.CONVERGENCE_CRITERION] == 0.02
        assert payload[ConvergenceSummaryKey.CONVERGENCE_STATUS] == ConvergenceStatus.CONVERGED
        assert payload[ConvergenceSummaryKey.ACTUAL_ROUNDS] == 3
        assert payload[ConvergenceSummaryKey.ROUNDS_INITIAL] == 5

    def test_summary_not_converged(self, tmp_path: Path) -> None:
        snapshot = ConvergenceSnapshot(
            loss_history=[3.0, 2.9, 2.8],
            converged_round=None,
            criterion_value=None,
        )
        save_convergence_artifacts(tmp_path, snapshot, _make_conv_cfg())

        payload = json.loads(
            (tmp_path / ArtifactFile.CONVERGENCE_SUMMARY).read_text()
        )
        assert payload[ConvergenceSummaryKey.CONVERGENCE_ROUND] is None
        assert payload[ConvergenceSummaryKey.CONVERGENCE_CRITERION] is None
        assert payload[ConvergenceSummaryKey.CONVERGENCE_STATUS] == ConvergenceStatus.NOT_CONVERGED

    def test_empty_loss_history(self, tmp_path: Path) -> None:
        snapshot = ConvergenceSnapshot(
            loss_history=[],
            converged_round=None,
            criterion_value=None,
        )
        save_convergence_artifacts(tmp_path, snapshot, _make_conv_cfg())

        payload = json.loads(
            (tmp_path / ArtifactFile.CONVERGENCE_SUMMARY).read_text()
        )
        assert payload[ConvergenceSummaryKey.ACTUAL_ROUNDS] == 0
        assert payload[ConvergenceSummaryKey.WEIGHTED_LOSS] == []


class TestConvergenceSnapshot:
    def test_construction(self) -> None:
        s = ConvergenceSnapshot(
            loss_history=[1.0, 0.5],
            converged_round=2,
            criterion_value=0.01,
        )
        assert s.loss_history == [1.0, 0.5]
        assert s.converged_round == 2
        assert s.criterion_value == 0.01

    def test_none_fields(self) -> None:
        s = ConvergenceSnapshot(
            loss_history=[],
            converged_round=None,
            criterion_value=None,
        )
        assert s.converged_round is None
        assert s.criterion_value is None

    def test_is_frozen(self) -> None:
        s = ConvergenceSnapshot(
            loss_history=[1.0],
            converged_round=1,
            criterion_value=0.0,
        )
        with pytest.raises(Exception):
            s.converged_round = 5  # type: ignore[misc]
