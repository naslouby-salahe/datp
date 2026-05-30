from __future__ import annotations

import dataclasses
from pathlib import Path

from datp.artifacts.constants import METRICS_FILE, PARQUET_SUFFIX, SCORING_MANIFEST_FILE
from datp.artifacts.directories import (
    CHECKPOINTS_DIR,
    LOGS_DIR,
    RESULTS_DIR,
    SCORES_DIR,
)
from datp.core.enums import (
    Baseline,
    Regime,
    ScoringStage,
)
from datp.core.identity import (
    BaselineRunId,
    ScoreCellId,
    format_alpha_dir,
    seed_segment,
)


def _seed_segment(seed: int, alpha: float | None) -> Path:
    p = Path(seed_segment(seed))
    if alpha is not None:
        p = p / format_alpha_dir(alpha)
    return p


@dataclasses.dataclass(frozen=True, slots=True)
class ExperimentLocator:
    """Checkpoint and score paths intentionally omit baseline: B1–B4 share the trained encoder and scores."""

    result_root: Path
    ckpt_root: Path
    score_root: Path
    log_root: Path

    @classmethod
    def for_main(cls, base_dir: Path, regime: Regime) -> "ExperimentLocator":
        return cls(
            result_root=base_dir / RESULTS_DIR / regime.value,
            ckpt_root=base_dir / CHECKPOINTS_DIR / regime.value,
            score_root=base_dir / SCORES_DIR / regime.value,
            log_root=base_dir / LOGS_DIR / regime.value,
        )

    def result(self, baseline: Baseline, seed: int, alpha: float | None = None) -> Path:
        return self.result_root / baseline.value / _seed_segment(seed, alpha)

    def checkpoint(self, seed: int, alpha: float | None = None) -> Path:
        return self.ckpt_root / _seed_segment(seed, alpha)

    def score(
        self,
        seed: int,
        alpha: float | None = None,
        stage: ScoringStage | None = None,
        client_id: str | None = None,
    ) -> Path:
        p = self.score_root / _seed_segment(seed, alpha)
        if stage is not None:
            p = p / stage.value
        if client_id is not None:
            p = p / f"{client_id}{PARQUET_SUFFIX}"
        return p

    def log(self, baseline: Baseline, seed: int, alpha: float | None = None) -> Path:
        return self.log_root / baseline.value / _seed_segment(seed, alpha)


@dataclasses.dataclass(frozen=True, slots=True)
class ArtifactRoots:
    """Top-level artifact root directories for a regime."""

    checkpoint_root: Path
    score_root: Path
    result_root: Path
    log_root: Path

    @classmethod
    def for_regime(cls, base_dir: Path, regime: Regime) -> ArtifactRoots:
        return cls(
            checkpoint_root=base_dir / CHECKPOINTS_DIR / regime.value,
            score_root=base_dir / SCORES_DIR / regime.value,
            result_root=base_dir / RESULTS_DIR / regime.value,
            log_root=base_dir / LOGS_DIR / regime.value,
        )


@dataclasses.dataclass(frozen=True, slots=True)
class ScoreCellPaths:
    """Resolved paths for a shared score cell (no baseline dimension)."""

    cell: ScoreCellId
    checkpoint_dir: Path
    score_dir: Path
    manifest_path: Path

    @classmethod
    def from_roots(cls, roots: ArtifactRoots, cell: ScoreCellId) -> ScoreCellPaths:
        seg = _seed_segment(cell.seed, cell.alpha)
        score_dir = roots.score_root / seg
        checkpoint_dir = roots.checkpoint_root / seg
        return cls(
            cell=cell,
            checkpoint_dir=checkpoint_dir,
            score_dir=score_dir,
            manifest_path=score_dir / SCORING_MANIFEST_FILE,
        )

    def score_file(self, stage: ScoringStage, client_id: str) -> Path:
        return self.score_dir / stage.value / f"{client_id}{PARQUET_SUFFIX}"


@dataclasses.dataclass(frozen=True, slots=True)
class BaselineRunPaths:
    """Resolved paths for a baseline evaluation run."""

    run: BaselineRunId
    result_dir: Path
    log_dir: Path
    metrics_path: Path

    @classmethod
    def from_roots(cls, roots: ArtifactRoots, run: BaselineRunId) -> BaselineRunPaths:
        seg = _seed_segment(run.seed, run.alpha)
        result_dir = roots.result_root / run.baseline.value / seg
        return cls(
            run=run,
            result_dir=result_dir,
            metrics_path=result_dir / METRICS_FILE,
            log_dir=roots.log_root / run.baseline.value / seg,
        )
