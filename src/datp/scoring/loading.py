"""B1/B2/B3/B4 share one ScoreProvider per (regime, seed, alpha) cell; missing artifacts always raise FileNotFoundError."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

from datp.artifacts.constants import PARQUET_SUFFIX, SCORE_COLUMN
from datp.core.enums import ScoringStage
from datp.core.errors import fmt
from datp.data.common.schemas import validate_score_artifact

_MODULE = "scoring.loading"


def read_score_column(path: Path) -> np.ndarray:
    validate_score_artifact(path)
    table = pq.read_table(path, columns=[SCORE_COLUMN])
    chunked = table.column(SCORE_COLUMN)
    return chunked.combine_chunks().to_numpy(zero_copy_only=False).astype(np.float64)


class ScoreProvider:
    def __init__(self, score_root: Path) -> None:
        self._root = score_root

    @property
    def score_root(self) -> Path:
        return self._root

    def load(self, client_id: str, stage: ScoringStage) -> np.ndarray:
        path = self._root / stage / f"{client_id}{PARQUET_SUFFIX}"
        if not path.exists():
            raise FileNotFoundError(
                fmt(
                    _MODULE,
                    f"Missing {stage} score artifact for client '{client_id}'",
                    str(path),
                    "absent",
                )
            )
        return read_score_column(path)

    def load_test_scores(self, client_id: str) -> tuple[np.ndarray, np.ndarray]:
        """Load test_benign and test_attack scores; test_attack may be empty."""
        benign = self.load(client_id, ScoringStage.TEST_BENIGN)
        attack = self.load(client_id, ScoringStage.TEST_ATTACK)
        return benign, attack
