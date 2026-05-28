"""Unit tests for analysis-cell filtering helpers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from datp.analyses.cells import (
    CellEntry,
    load_safe_cells_for_regime,
    load_verified_safe_cells,
)
from datp.artifacts.directories import SCORES_DIR
from datp.validation.constants import CELL_VERDICTS_JSON
from datp.validation.enums import ReuseVerdict
from datp.core.enums import Regime
from datp.data.catalog import DatasetID


def _write_verdicts(tmp_path: Path) -> None:
    verdicts_dir = tmp_path / SCORES_DIR
    verdicts_dir.mkdir(parents=True)
    payload = {
        "cells": [
            {
                "cell_dir": "scores/a/seed_0",
                "regime": "a",
                "seed": 0,
                "alpha": None,
                "dataset": "nbaiot",
                "verdict": "VERIFIED_REUSE_SAFE",
            },
            {
                "cell_dir": "scores/c/seed_1/alpha_0.5",
                "regime": "c",
                "seed": 1,
                "alpha": "0.5",
                "dataset": "nbaiot",
                "verdict": "VERIFIED_REUSE_SAFE",
            },
            {
                "cell_dir": "scores/c/seed_2/alpha_1.0",
                "regime": "c",
                "seed": 2,
                "alpha": "1.0",
                "dataset": "nbaiot",
                "verdict": "REUSE_BLOCKED_RERUN_REQUIRED",
            },
        ]
    }
    (verdicts_dir / CELL_VERDICTS_JSON).write_text(
        json.dumps(payload), encoding="utf-8"
    )


def test_cell_entry_accepts_known_schema() -> None:
    cell = CellEntry(
        cell_dir="scores/a/seed_0",
        regime=Regime.A,
        seed=0,
        dataset=DatasetID.NBAIOT,
        verdict=ReuseVerdict.VERIFIED_REUSE_SAFE,
    )

    assert cell.alpha is None


def test_load_verified_safe_cells_filters_blocked_verdicts(tmp_path: Path) -> None:
    _write_verdicts(tmp_path)

    cells = load_verified_safe_cells(tmp_path)

    assert [cell.seed for cell in cells] == [0, 1]


def test_load_safe_cells_for_regime_filters_alpha(tmp_path: Path) -> None:
    _write_verdicts(tmp_path)

    cells = load_safe_cells_for_regime(
        tmp_path,
        Regime.C,
        alpha_values=("0.5",),
    )

    assert [cell.alpha for cell in cells] == ["0.5"]


def test_load_safe_cells_for_regime_raises_for_required_empty(
    tmp_path: Path,
) -> None:
    _write_verdicts(tmp_path)

    with pytest.raises(FileNotFoundError):
        load_safe_cells_for_regime(tmp_path, Regime.B)
