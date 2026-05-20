from __future__ import annotations

from pathlib import Path

from datp.artifacts.constants import METRICS_FILE
from datp.artifacts.directories import RESULTS_DIR
from datp.artifacts.run_formatting import SEED_PREFIX
from datp.core.enums import (
    Baseline,
    Regime,
)
from datp.core.identity import parse_alpha_dir


def completed_metric_paths(base_dir: Path) -> list[Path]:
    return sorted((base_dir / RESULTS_DIR).glob(f"*/*/{SEED_PREFIX}*/**/{METRICS_FILE}"))


def parse_metric_path(base_dir: Path, path: Path) -> tuple[Regime, Baseline, int, float | None]:
    """Parse ``<results_root>/<regime>/<baseline>/seed_N[/alpha_a]/metrics.json``."""
    rel = path.relative_to(base_dir / RESULTS_DIR)
    parts = rel.parts
    regime = Regime(parts[0])
    baseline = Baseline(parts[1])
    seed_segment = parts[2]
    if not seed_segment.startswith(SEED_PREFIX):
        raise ValueError(f"Expected seed segment with prefix {SEED_PREFIX!r}, got {seed_segment!r}")
    seed = int(seed_segment.removeprefix(SEED_PREFIX))
    alpha = parse_alpha_dir(parts[3]) if len(parts) > 4 else None
    return regime, baseline, seed, alpha
