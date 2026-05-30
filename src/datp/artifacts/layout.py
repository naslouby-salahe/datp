from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from datp.artifacts.names import ArtifactDir, ArtifactFile, FileSuffix
from datp.core.enums import Regime, ScoringStage
from datp.core.identity import (
    BaselineRunId,
    ScoreCellId,
    TrainingCellId,
    format_alpha_dir,
    seed_segment,
)


def _seed_segment(seed: int, alpha: float | None) -> Path:
    p = Path(seed_segment(seed))
    if alpha is not None:
        p = p / format_alpha_dir(alpha)
    return p


@dataclass(frozen=True, slots=True)
class ScoreCellPaths:
    """Resolved paths for a shared score cell (no baseline dimension)."""

    cell: ScoreCellId
    checkpoint_dir: Path
    score_dir: Path
    manifest_path: Path

    def score_file(self, stage: ScoringStage, client_id: str) -> Path:
        return self.score_dir / stage.value / f"{client_id}{FileSuffix.PARQUET}"


@dataclass(frozen=True, slots=True)
class BaselineRunPaths:
    """Resolved paths for a baseline evaluation run."""

    run: BaselineRunId
    result_dir: Path
    log_dir: Path
    metrics_path: Path


@dataclass(frozen=True, slots=True)
class ArtifactLayout:
    """Canonical artifact paths for one regime.

    Checkpoint and score paths intentionally omit baseline: B1-B4 share the
    trained encoder and scores.
    """

    base_dir: Path
    regime: Regime

    @property
    def _checkpoint_root(self) -> Path:
        return self.base_dir / ArtifactDir.CHECKPOINTS / self.regime.value

    @property
    def _score_root(self) -> Path:
        return self.base_dir / ArtifactDir.SCORES / self.regime.value

    @property
    def _result_root(self) -> Path:
        return self.base_dir / ArtifactDir.RESULTS / self.regime.value

    @property
    def _log_root(self) -> Path:
        return self.base_dir / ArtifactDir.LOGS / self.regime.value

    def checkpoint_dir(self, cell: TrainingCellId) -> Path:
        return self._checkpoint_root / _seed_segment(cell.seed, cell.alpha)

    def score_cell(self, cell: ScoreCellId) -> ScoreCellPaths:
        seg = _seed_segment(cell.seed, cell.alpha)
        score_dir = self._score_root / seg
        return ScoreCellPaths(
            cell=cell,
            checkpoint_dir=self._checkpoint_root / seg,
            score_dir=score_dir,
            manifest_path=score_dir / ArtifactFile.SCORING_MANIFEST,
        )

    def score_file(
        self, cell: ScoreCellId, stage: ScoringStage, client_id: str
    ) -> Path:
        return self.score_cell(cell).score_file(stage, client_id)

    def baseline_run(self, run: BaselineRunId) -> BaselineRunPaths:
        seg = _seed_segment(run.seed, run.alpha)
        result_dir = self._result_root / run.baseline.value / seg
        return BaselineRunPaths(
            run=run,
            result_dir=result_dir,
            metrics_path=result_dir / ArtifactFile.METRICS,
            log_dir=self._log_root / run.baseline.value / seg,
        )
