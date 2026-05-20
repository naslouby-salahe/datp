from __future__ import annotations

from pathlib import Path

import pytest

from datp.artifacts.directories import OUTPUTS_DIR
from datp.artifacts.paths import ExperimentLocator
from datp.core.enums import (
    Baseline,
    Regime,
)


@pytest.mark.integration
def test_same_artifact_path_all_baselines() -> None:
    loc = ExperimentLocator.for_main(Path(OUTPUTS_DIR), Regime.A)
    paths = [
        loc.score(seed=0) for _ in (Baseline.B1, Baseline.B2, Baseline.B3, Baseline.B4)
    ]

    assert len(set(paths)) == 1, f"Expected one unique path, got {set(paths)}"

    # .score() must NOT accept a 'baseline' keyword argument — verify by inspection
    import inspect

    sig = inspect.signature(loc.score)
    assert "baseline" not in sig.parameters, (
        "ExperimentLocator.score() must not accept a 'baseline' parameter -- "
        "scores are shared across B1/B2/B3/B4"
    )
