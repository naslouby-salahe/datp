from __future__ import annotations

from pathlib import Path

import numpy as np

from datp.artifacts.layout import ArtifactLayout
from datp.artifacts.names import PARQUET_GLOB
from datp.core.enums import (
    Regime,
    ScoringStage,
)
from datp.core.errors import fmt, fmt_missing
from datp.core.identity import ScoreCellId, TrainingCellId
from datp.core.logging import get_logger
from datp.scoring.loading import read_score_column

logger = get_logger(__name__)


def load_main_cal_errors(
    regime: Regime,
    seed: int,
    alpha: float | None,
    base_dir: Path,
) -> dict[str, np.ndarray]:
    cell = ScoreCellId(cell=TrainingCellId(regime=regime, seed=seed, alpha=alpha))
    score_dir = ArtifactLayout(base_dir=base_dir, regime=regime).score_cell(cell).score_dir
    cal_dir = score_dir / ScoringStage.CAL.value
    if not cal_dir.exists():
        raise FileNotFoundError(
            fmt_missing("baselines", f"Main calibration scores {cal_dir}")
        )

    client_errors: dict[str, np.ndarray] = {}
    for pf in sorted(cal_dir.glob(PARQUET_GLOB)):
        cid = pf.stem
        client_errors[cid] = read_score_column(pf)

    if not client_errors:
        raise FileNotFoundError(
            fmt(
                "baselines",
                "No calibration score artifacts",
                "at least one .parquet score artifact",
                f"none in {cal_dir}",
            )
        )

    logger.info(
        "loaded calibration errors",
        n_clients=len(client_errors),
        path=str(cal_dir),
    )
    return client_errors
