from __future__ import annotations

import dataclasses
from pathlib import Path

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
from datp.core.identity import format_alpha_dir, seed_segment


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
        if not isinstance(regime, Regime):
            raise TypeError(f"ExperimentLocator.for_main: regime must be Regime, got {type(regime)!r}")
        return cls(
            result_root=base_dir / RESULTS_DIR / regime.value,
            ckpt_root=base_dir / CHECKPOINTS_DIR / regime.value,
            score_root=base_dir / SCORES_DIR / regime.value,
            log_root=base_dir / LOGS_DIR / regime.value,
        )

    def result(self, baseline: Baseline, seed: int, alpha: float | None = None) -> Path:
        if not isinstance(baseline, Baseline):
            raise TypeError(
                f"ExperimentLocator.result: baseline must be Baseline, got {type(baseline)!r}"
            )
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
        if stage is not None and not isinstance(stage, ScoringStage):
            raise TypeError(f"ExperimentLocator.score: stage must be ScoringStage, got {type(stage)!r}")
        p = self.score_root / _seed_segment(seed, alpha)
        if stage is not None:
            p = p / stage.value
        if client_id is not None:
            p = p / f"{client_id}.parquet"
        return p

    def log(self, baseline: Baseline, seed: int, alpha: float | None = None) -> Path:
        if not isinstance(baseline, Baseline):
            raise TypeError(f"ExperimentLocator.log: baseline must be Baseline, got {type(baseline)!r}")
        return self.log_root / baseline.value / _seed_segment(seed, alpha)
