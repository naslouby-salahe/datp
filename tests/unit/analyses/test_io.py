"""Unit tests for shared analysis I/O helpers."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from datp.analyses.io import (
    load_cell_verdicts,
    write_analysis_csv,
    write_analysis_json,
)
from datp.analyses.types import FrozenModel
from datp.artifacts.directories import SCORES_DIR
from datp.validation.constants import CELL_VERDICTS_JSON
from datp.core.enums import Regime


class ExampleRow(FrozenModel):
    name: str
    value: int


def test_load_cell_verdicts_reads_entries(tmp_path: Path) -> None:
    verdicts_dir = tmp_path / SCORES_DIR
    verdicts_dir.mkdir(parents=True)
    (verdicts_dir / CELL_VERDICTS_JSON).write_text(
        json.dumps(
            {
                "cells": [
                    {
                        "cell_dir": "scores/a/seed_0",
                        "regime": "a",
                        "seed": 0,
                        "alpha": None,
                        "dataset": "nbaiot",
                        "verdict": "VERIFIED_REUSE_SAFE",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    cells = load_cell_verdicts(tmp_path)

    assert len(cells) == 1
    assert cells[0].regime == Regime.A
    assert cells[0].seed == 0


def test_load_cell_verdicts_raises_when_missing(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_cell_verdicts(tmp_path)


def test_write_analysis_csv_preserves_model_fields(tmp_path: Path) -> None:
    out = write_analysis_csv(
        tmp_path,
        "rows.csv",
        [ExampleRow(name="a", value=1)],
        ExampleRow,
    )

    with out.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    assert out == tmp_path / "analysis" / "rows.csv"
    assert rows == [{"name": "a", "value": "1"}]


def test_write_analysis_json_serializes_model(tmp_path: Path) -> None:
    out = write_analysis_json(tmp_path, "result.json", ExampleRow(name="b", value=2))

    assert out == tmp_path / "analysis" / "result.json"
    assert json.loads(out.read_text(encoding="utf-8")) == {"name": "b", "value": 2}
