from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from datp.artifacts.layout import ArtifactLayout
from datp.artifacts.names import ArtifactDir
from datp.core.enums import (
    Baseline,
    Regime,
)
from datp.core.identity import ScoreCellId, TrainingCellId


@pytest.mark.integration
def test_same_artifact_path_all_baselines() -> None:
    layout = ArtifactLayout(base_dir=Path(ArtifactDir.OUTPUTS), regime=Regime.A)
    cell = ScoreCellId(cell=TrainingCellId(regime=Regime.A, seed=0, alpha=None))
    paths = [
        layout.score_cell(cell).score_dir
        for _ in (Baseline.B1, Baseline.B2, Baseline.B3, Baseline.B4)
    ]

    assert len(set(paths)) == 1, f"Expected one unique path, got {set(paths)}"

    # score_cell()/score_file() must NOT accept a 'baseline' argument —
    # scores are shared across B1/B2/B3/B4.
    for method in (layout.score_cell, layout.score_file):
        sig = inspect.signature(method)
        assert "baseline" not in sig.parameters, (
            f"{method.__name__}() must not accept a 'baseline' parameter -- "
            "scores are shared across B1/B2/B3/B4"
        )
