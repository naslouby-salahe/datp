"""Analysis-cell selection, filtering, and context construction."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from pydantic import BaseModel, ConfigDict

from datp.validation.enums import ReuseVerdict
from datp.core.enums import Regime
from datp.core.errors import fmt
from datp.core.identity import alpha_from_label
from datp.data.catalog import DatasetID
from datp.scoring.loading import ScoreProvider

_MODULE = __name__


class CellEntry(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)
    cell_dir: str
    regime: Regime
    seed: int
    alpha: str | None = None
    dataset: DatasetID
    verdict: ReuseVerdict


@dataclass(frozen=True, slots=True)
class AnalysisCellContext:
    """Pre-loaded context for one analysis cell; test scores are loaded lazily."""

    cell: CellEntry
    cell_dir: Path
    regime: Regime
    seed: int
    alpha_label: str | None
    alpha_value: float | None
    calibration_errors: dict[str, np.ndarray]
    score_provider: ScoreProvider


def load_verified_safe_cells(base_dir: Path) -> list[CellEntry]:
    from datp.analyses.io import load_cell_verdicts

    return [
        c
        for c in load_cell_verdicts(base_dir)
        if c.verdict == ReuseVerdict.VERIFIED_REUSE_SAFE
    ]


def _matches_alpha(
    cell: CellEntry,
    alpha_values: tuple[str | None, ...] | None,
) -> bool:
    if alpha_values is None:
        return True
    cell_alpha = cell.alpha if cell.alpha is not None else "iid"
    return cell_alpha in alpha_values or (cell.alpha is None and None in alpha_values)


def load_safe_cells_for_regime(
    base_dir: Path,
    regime: Regime,
    *,
    alpha_values: tuple[str | None, ...] | None = None,
    require_non_empty: bool = True,
    caller_module: str = _MODULE,
) -> list[CellEntry]:
    """Load verified-safe cells filtered by regime and optional alpha values.

    When ``alpha_values`` is None, cells with any alpha are accepted.
    ``"iid"`` is treated as equivalent to ``None``.
    Raises ``FileNotFoundError`` when ``require_non_empty`` and no cells match.
    """
    cells = [
        c
        for c in load_verified_safe_cells(base_dir)
        if c.regime == regime and _matches_alpha(c, alpha_values)
    ]
    if require_non_empty and not cells:
        regime_desc = f"Regime {regime.value.upper()}"
        alpha_desc = f" with alpha in {alpha_values}" if alpha_values else ""
        raise FileNotFoundError(
            fmt(
                caller_module,
                f"No verified {regime_desc}{alpha_desc} cells",
                f"VERIFIED_REUSE_SAFE cells for regime '{regime.value}'{alpha_desc}",
                "none",
            )
        )
    return cells


def iter_analysis_cell_contexts(
    cells: Sequence[CellEntry],
) -> Iterator[AnalysisCellContext]:
    """Yield AnalysisCellContext for each cell, loading calibration errors once."""
    from datp.analyses.io import load_cal_errors

    for cell in cells:
        cell_dir = Path(cell.cell_dir)
        yield AnalysisCellContext(
            cell=cell,
            cell_dir=cell_dir,
            regime=cell.regime,
            seed=cell.seed,
            alpha_label=cell.alpha,
            alpha_value=alpha_from_label(cell.alpha),
            calibration_errors=load_cal_errors(cell_dir),
            score_provider=ScoreProvider(cell_dir),
        )
