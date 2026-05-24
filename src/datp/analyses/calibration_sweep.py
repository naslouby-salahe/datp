"""GB-02 calibration-size sweep.

Subsamples benign calibration scores at n_cal ∈ cal_sweep_n_cal (from config)
with cal_sweep_n_repeats fixed-seed repeats per cell. For each subsample,
computes B2 per‑client percentile thresholds and evaluates FPR on the held‑out
test_benign scores.  No FL training is performed.

Outputs (when write_outputs=True):
  <base_dir>/analysis/calibration_sweep_table.csv
  <base_dir>/analysis/calibration_sweep_curve.png
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from pydantic import BaseModel, ConfigDict

from datp.analyses._common import (
    compute_cv,
    compute_fpr,
    load_cal_errors,
    load_test_benign_errors,
    load_verified_safe_cells,
)
from datp.artifacts.directories import ANALYSIS_DIR
from datp.baselines.common.thresholds import percentile_threshold
from datp.config.compose import compose_config
from datp.config.models import DatpConfig
from datp.core.enums import Baseline, Regime
from datp.core.errors import fmt

_MODULE = "analyses.calibration_sweep"

CALIBRATION_SWEEP_TABLE_CSV = "calibration_sweep_table.csv"
CALIBRATION_SWEEP_CURVE_PNG = "calibration_sweep_curve.png"

# Baseline B2 only — this is a B2 tautology defense.
_SWEEP_BASELINE = Baseline.B2


class CalibrationSweepRow(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    n_cal: int
    regime: Regime
    seed: int
    alpha: str | None
    median_cv_fpr: float
    iqr_cv_fpr: float
    median_mean_fpr: float
    iqr_mean_fpr: float
    clients_evaluated: int
    clients_excluded: int
    repeats: int


class CalibrationSweepResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    rows: list[CalibrationSweepRow]
    n_cal_grid: list[int]
    n_repeats: int
    verified_safe_cell_count: int


@dataclass(frozen=True)
class _SweepCellData:
    """Pre-loaded data for a single verified-safe score cell."""
    cell_dir: Path
    regime: Regime
    seed: int
    alpha_str: str | None
    cal_errors: dict[str, np.ndarray]
    test_benign_errors: dict[str, np.ndarray]


# ── Helpers: _load_cell_verdicts, _load_cal_errors, _parse_alpha_str,
#    _fpr, _cv, _load_test_benign_errors → imported from datp.analyses._common


def _validate_sweep_inputs(
    n_cal_grid: list[int],
    n_repeats: int,
    verdicts: list[dict],
) -> None:
    """Raise on invalid sweep inputs before any processing."""
    _ = verdicts  # reserved for future verdict-level guards
    if not n_cal_grid:
        raise ValueError(
            fmt(_MODULE, "cal_sweep_n_cal is empty", "non-empty list", "empty list")
        )
    if n_repeats < 1:
        raise ValueError(
            fmt(_MODULE, "cal_sweep_n_repeats must be >= 1", "≥ 1", str(n_repeats))
        )


def _load_sweep_data(
    base_dir: Path,
) -> list[_SweepCellData]:
    """Load VERIFIED_REUSE_SAFE score cells and their calibration/test_benign data."""
    safe_cells = load_verified_safe_cells(base_dir)
    result: list[_SweepCellData] = []
    for cell in safe_cells:
        cell_dir = Path(cell["cell_dir"])
        result.append(_SweepCellData(
            cell_dir=cell_dir,
            regime=Regime(cell["regime"]),
            seed=int(cell["seed"]),
            alpha_str=cell.get("alpha"),
            cal_errors=load_cal_errors(cell_dir),
            test_benign_errors=load_test_benign_errors(cell_dir),
        ))
    return result


def _compute_repeat_fpr(
    cal_errors: dict[str, np.ndarray],
    test_benign_errors: dict[str, np.ndarray],
    n_cal: int,
    q: float,
    seed_base: int,
    repeat: int,
) -> list[float]:
    """Compute per-client FPRs for one repeat, skipping clients with too few cal samples."""
    client_fprs: list[float] = []
    for cid, cal_arr in cal_errors.items():
        if cal_arr.size < n_cal:
            continue
        rng = np.random.default_rng(
            seed_base + hash(cid) % (2 ** 31) + repeat
        )
        subsample = rng.choice(cal_arr, size=n_cal, replace=False)
        tau = percentile_threshold(subsample, q)
        tb = test_benign_errors.get(cid)
        if tb is not None and tb.size > 0:
            client_fprs.append(compute_fpr(tb, tau))
    return client_fprs


def _run_single_sweep_cell(
    cell_data: _SweepCellData,
    n_cal: int,
    q: float,
    seed_base: int,
    n_repeats: int,
) -> CalibrationSweepRow | None:
    """Run all repeats for one (cell, n_cal) pair.

    Returns a CalibrationSweepRow or None when fewer than 2 repeats produce data.
    """
    clients_evaluated = sum(
        1 for arr in cell_data.cal_errors.values() if arr.size >= n_cal
    )
    n_excluded_per_repeat = sum(
        1 for arr in cell_data.cal_errors.values() if arr.size < n_cal
    )

    repeat_fprs: list[float] = []
    for repeat in range(n_repeats):
        client_fprs = _compute_repeat_fpr(
            cell_data.cal_errors,
            cell_data.test_benign_errors,
            n_cal,
            q,
            seed_base,
            repeat,
        )
        if client_fprs:
            repeat_fprs.append(float(np.mean(client_fprs)))

    if len(repeat_fprs) < 2:
        return None

    arr = np.array(repeat_fprs, dtype=np.float64)
    q25 = float(np.percentile(arr, 25))
    q75 = float(np.percentile(arr, 75))
    iqr = q75 - q25

    return CalibrationSweepRow(
        n_cal=n_cal,
        regime=cell_data.regime,
        seed=cell_data.seed,
        alpha=cell_data.alpha_str,
        median_cv_fpr=compute_cv(arr),
        iqr_cv_fpr=iqr,
        median_mean_fpr=float(np.median(arr)),
        iqr_mean_fpr=iqr,
        clients_evaluated=clients_evaluated,
        clients_excluded=n_excluded_per_repeat,
        repeats=len(repeat_fprs),
    )


def _compute_sweep_summary(
    rows: list[CalibrationSweepRow],
    n_cal_grid: list[int],
    n_repeats: int,
    verified_safe_cell_count: int,
) -> CalibrationSweepResult:
    """Wrap computed rows and metadata into the public result model."""
    return CalibrationSweepResult(
        rows=rows,
        n_cal_grid=list(n_cal_grid),
        n_repeats=n_repeats,
        verified_safe_cell_count=verified_safe_cell_count,
    )


def run_calibration_sweep(
    base_dir: Path,
    *,
    config: DatpConfig | None = None,
    write_outputs: bool = False,
) -> CalibrationSweepResult:
    """Evaluate B2 at subsampled calibration sizes on VERIFIED_REUSE_SAFE cells.

    For each n_cal in the grid, each client's calibration errors are subsampled
    n_repeats times with deterministic fixed seeds.  A B2 percentile threshold
    is computed from the subsample and FPR is evaluated on the held-out
    test_benign errors.  The per-cell per-n_cal FPR is the mean over clients;
    CV(FPR) is then computed across the repeat distribution.
    """
    cfg = config or compose_config(regime=Regime.A, baseline=Baseline.B1, seed=0)
    n_cal_grid = cfg.analysis.cal_sweep_n_cal
    n_repeats = cfg.analysis.cal_sweep_n_repeats
    seed_base = cfg.analysis.cal_sweep_seed_base
    q = cfg.threshold.q

    resolved = base_dir.resolve()

    _validate_sweep_inputs(n_cal_grid, n_repeats, [])

    cells_data = _load_sweep_data(resolved)

    rows: list[CalibrationSweepRow] = []
    for cell_data in cells_data:
        for n_cal in n_cal_grid:
            row = _run_single_sweep_cell(
                cell_data, n_cal, q, seed_base, n_repeats,
            )
            if row is not None:
                rows.append(row)

    result = _compute_sweep_summary(
        rows, n_cal_grid, n_repeats, len(cells_data),
    )

    if write_outputs:
        _write_outputs(result, resolved)

    return result


def _write_outputs(result: CalibrationSweepResult, base_dir: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    analysis_dir = base_dir / ANALYSIS_DIR
    analysis_dir.mkdir(parents=True, exist_ok=True)

    # CSV
    fieldnames = [
        "n_cal", "regime", "seed", "alpha", "median_cv_fpr", "iqr_cv_fpr",
        "median_mean_fpr", "iqr_mean_fpr", "clients_evaluated", "clients_excluded", "repeats",
    ]
    csv_path = analysis_dir / CALIBRATION_SWEEP_TABLE_CSV
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in result.rows:
            writer.writerow({
                "n_cal": row.n_cal,
                "regime": row.regime.value,
                "seed": row.seed,
                "alpha": row.alpha,
                "median_cv_fpr": row.median_cv_fpr,
                "iqr_cv_fpr": row.iqr_cv_fpr,
                "median_mean_fpr": row.median_mean_fpr,
                "iqr_mean_fpr": row.iqr_mean_fpr,
                "clients_evaluated": row.clients_evaluated,
                "clients_excluded": row.clients_excluded,
                "repeats": row.repeats,
            })

    # Curve figure
    regime_a_rows = [r for r in result.rows if r.regime == Regime.A and r.alpha is None]
    if not regime_a_rows:
        return

    fig, ax = plt.subplots(figsize=(8, 5))
    for n_cal in result.n_cal_grid:
        n_rows = [r for r in regime_a_rows if r.n_cal == n_cal]
        if not n_rows:
            continue
        medians = [r.median_cv_fpr for r in n_rows]
        # Average across seeds
        avg_median = float(np.mean(medians))
        ax.scatter(n_cal, avg_median, s=60, zorder=3)

    ax.set_xlabel("Calibration samples per client (n_cal)")
    ax.set_ylabel("CV(FPR) over repeats")
    ax.set_title("B2 Calibration-Size Sweep — Regime A")
    ax.set_xscale("log")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(analysis_dir / CALIBRATION_SWEEP_CURVE_PNG, dpi=150)
    plt.close(fig)
