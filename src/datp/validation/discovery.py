from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from datp.artifacts.constants import METRICS_FILE, SCORING_MANIFEST_FILE
from datp.artifacts.directories import RESULTS_DIR, SCORES_DIR
from datp.artifacts.run_formatting import ALPHA_PREFIX, SEED_PREFIX
from datp.core.enums import (
    Baseline,
    Regime,
)
from datp.core.identity import parse_alpha_dir


def completed_metric_paths(base_dir: Path) -> list[Path]:
    return sorted(
        (base_dir / RESULTS_DIR).glob(f"*/*/{SEED_PREFIX}*/**/{METRICS_FILE}")
    )


def parse_metric_path(
    base_dir: Path, path: Path
) -> tuple[Regime, Baseline, int, float | None]:
    """Parse ``<results_root>/<regime>/<baseline>/seed_N[/alpha_a]/metrics.json``."""
    rel = path.relative_to(base_dir / RESULTS_DIR)
    parts = rel.parts
    regime = Regime(parts[0])
    baseline = Baseline(parts[1])
    seed_segment = parts[2]
    if not seed_segment.startswith(SEED_PREFIX):
        raise ValueError(
            f"Expected seed segment with prefix {SEED_PREFIX!r}, got {seed_segment!r}"
        )
    seed = int(seed_segment.removeprefix(SEED_PREFIX))
    alpha = parse_alpha_dir(parts[3]) if len(parts) > 4 else None
    return regime, baseline, seed, alpha


@dataclass(frozen=True, slots=True)
class ScoreCellLocation:
    """Identifies one score cell on disk: ``<base_dir>/scores/<regime>/seed_N[/alpha_*]/``."""

    regime: Regime
    seed: int
    alpha: float | None
    cell_dir: Path


def iter_score_cells(base_dir: Path) -> list[ScoreCellLocation]:
    """Enumerate score cells (directories containing ``scoring_manifest.json``) under ``<base_dir>/scores/``."""
    scores_root = base_dir / SCORES_DIR
    if not scores_root.exists():
        return []
    cells: list[ScoreCellLocation] = []
    for manifest_path in sorted(
        scores_root.glob(f"*/{SEED_PREFIX}*/{SCORING_MANIFEST_FILE}")
    ):
        cells.append(_parse_score_cell(scores_root, manifest_path.parent))
    for manifest_path in sorted(
        scores_root.glob(f"*/{SEED_PREFIX}*/{ALPHA_PREFIX}*/{SCORING_MANIFEST_FILE}")
    ):
        cells.append(_parse_score_cell(scores_root, manifest_path.parent))
    return cells


def _parse_score_cell(scores_root: Path, cell_dir: Path) -> ScoreCellLocation:
    rel = cell_dir.relative_to(scores_root)
    parts = rel.parts
    regime = Regime(parts[0])
    seed_segment = parts[1]
    if not seed_segment.startswith(SEED_PREFIX):
        raise ValueError(
            f"Expected seed segment with prefix {SEED_PREFIX!r}, got {seed_segment!r}"
        )
    seed = int(seed_segment.removeprefix(SEED_PREFIX))
    alpha = parse_alpha_dir(parts[2]) if len(parts) > 2 else None
    return ScoreCellLocation(regime=regime, seed=seed, alpha=alpha, cell_dir=cell_dir)
