"""GB-02 calibration-size sweep.

Subsamples benign calibration scores at n_cal in cal_sweep_n_cal (from config)
with cal_sweep_n_repeats fixed-seed repeats per cell. For each subsample,
computes B2 per-client percentile thresholds and evaluates FPR on the held-out
test_benign scores.  No FL training is performed.

Outputs (when write_outputs=True):
  <base_dir>/analysis/calibration_sweep_table.csv
  <base_dir>/analysis/calibration_sweep_curve.png
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from datp.analyses.cells import (
    AnalysisCellContext,
    iter_analysis_cell_contexts,
    load_verified_safe_cells,
)
from datp.analyses.evaluation import compute_cv
from datp.analyses.io import (
    ensure_analysis_dir,
    load_test_benign_errors,
    write_analysis_csv,
)
from datp.analyses.plotting import saved_figure
from datp.analyses.runners import analysis_runner
from datp.core.types import AnalysisRowBase, FrozenModel
from datp.thresholding.thresholds import percentile_threshold
from datp.config.models import DatpConfig
from datp.core.enums import Regime
from datp.core.errors import fmt
from datp.evaluation.metrics import compute_fpr

from datp.analyses.constants import (
    CALIBRATION_SWEEP_CURVE_PNG,
    CALIBRATION_SWEEP_TABLE_CSV,
)

_MODULE = __name__

_HASH_MODULUS = 2**31


class CalibrationSweepRow(AnalysisRowBase):
    n_cal: int
    median_cv_fpr: float
    iqr_cv_fpr: float
    median_mean_fpr: float
    iqr_mean_fpr: float
    clients_evaluated: int
    clients_excluded: int
    repeats: int


class CalibrationSweepResult(FrozenModel):
    rows: list[CalibrationSweepRow]
    n_cal_grid: list[int]
    n_repeats: int
    verified_safe_cell_count: int


def _validate_sweep_inputs(n_cal_grid: list[int], n_repeats: int) -> None:
    if not n_cal_grid:
        raise ValueError(
            fmt(_MODULE, "cal_sweep_n_cal is empty", "non-empty list", "empty list")
        )
    if n_repeats < 1:
        raise ValueError(
            fmt(_MODULE, "cal_sweep_n_repeats must be >= 1", ">= 1", str(n_repeats))
        )


def _compute_repeat_fpr(
    cal_errors: dict[str, np.ndarray],
    test_benign_errors: dict[str, np.ndarray],
    n_cal: int,
    q: float,
    seed_base: int,
    repeat: int,
) -> list[float]:
    """Per-client FPRs for one repeat, skipping clients with too few cal samples."""
    client_fprs: list[float] = []
    for cid, client_cal_errors in cal_errors.items():
        if client_cal_errors.size < n_cal:
            continue
        rng = np.random.default_rng(seed_base + hash(cid) % _HASH_MODULUS + repeat)
        subsample = rng.choice(client_cal_errors, size=n_cal, replace=False)
        tau = percentile_threshold(subsample, q)
        tb = test_benign_errors.get(cid)
        if tb is not None and tb.size > 0:
            client_fprs.append(compute_fpr(tb, tau))
    return client_fprs


def _run_single_sweep_cell(
    ctx: AnalysisCellContext,
    test_benign_errors: dict[str, np.ndarray],
    n_cal: int,
    q: float,
    seed_base: int,
    n_repeats: int,
) -> CalibrationSweepRow | None:
    """Returns a row, or None when fewer than 2 repeats produced data."""
    clients_evaluated = sum(
        1 for arr in ctx.calibration_errors.values() if arr.size >= n_cal
    )
    clients_excluded = sum(
        1 for arr in ctx.calibration_errors.values() if arr.size < n_cal
    )

    repeat_fprs: list[float] = []
    for repeat in range(n_repeats):
        client_fprs = _compute_repeat_fpr(
            ctx.calibration_errors,
            test_benign_errors,
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
    iqr = float(np.percentile(arr, 75) - np.percentile(arr, 25))

    return CalibrationSweepRow(
        n_cal=n_cal,
        regime=ctx.regime,
        seed=ctx.seed,
        alpha=ctx.alpha_label,
        median_cv_fpr=compute_cv(arr),
        iqr_cv_fpr=iqr,
        median_mean_fpr=float(np.median(arr)),
        iqr_mean_fpr=iqr,
        clients_evaluated=clients_evaluated,
        clients_excluded=clients_excluded,
        repeats=len(repeat_fprs),
    )


def _write_outputs(result: CalibrationSweepResult, base_dir: Path) -> None:
    write_analysis_csv(
        base_dir, CALIBRATION_SWEEP_TABLE_CSV, result.rows, CalibrationSweepRow
    )
    _write_curve_plot(
        result, ensure_analysis_dir(base_dir) / CALIBRATION_SWEEP_CURVE_PNG
    )


@analysis_runner(writer_func=_write_outputs)
def run_calibration_sweep(
    base_dir: Path,
    *,
    config: DatpConfig,
) -> CalibrationSweepResult:
    """Evaluate B2 at subsampled calibration sizes on VERIFIED_REUSE_SAFE cells.

    For each n_cal in the grid, each client's calibration errors are subsampled
    n_repeats times with deterministic fixed seeds. A B2 percentile threshold
    is computed from the subsample and FPR is evaluated on the held-out
    test_benign errors. The per-cell per-n_cal FPR is the mean over clients;
    CV(FPR) is then computed across the repeat distribution.
    """
    n_cal_grid = config.analysis.cal_sweep_n_cal
    n_repeats = config.analysis.cal_sweep_n_repeats
    seed_base = config.analysis.cal_sweep_seed_base
    q = config.threshold.q

    _validate_sweep_inputs(n_cal_grid, n_repeats)

    safe_cells = load_verified_safe_cells(base_dir)

    rows: list[CalibrationSweepRow] = []
    for ctx in iter_analysis_cell_contexts(safe_cells):
        test_benign_errors = load_test_benign_errors(ctx.cell_dir)
        for n_cal in n_cal_grid:
            row = _run_single_sweep_cell(
                ctx, test_benign_errors, n_cal, q, seed_base, n_repeats
            )
            if row is not None:
                rows.append(row)

    return CalibrationSweepResult(
        rows=rows,
        n_cal_grid=list(n_cal_grid),
        n_repeats=n_repeats,
        verified_safe_cell_count=len(safe_cells),
    )


def _write_curve_plot(result: CalibrationSweepResult, path: Path) -> None:
    regime_a_rows = [r for r in result.rows if r.regime == Regime.A and r.alpha is None]
    if not regime_a_rows:
        return

    with saved_figure(path, figsize=(8, 5)) as (fig, ax):
        for n_cal in result.n_cal_grid:
            n_rows = [r for r in regime_a_rows if r.n_cal == n_cal]
            if not n_rows:
                continue
            avg_median = float(np.mean([r.median_cv_fpr for r in n_rows]))
            ax.scatter(n_cal, avg_median, s=60, zorder=3)

        ax.set_xlabel("Calibration samples per client (n_cal)")
        ax.set_ylabel("CV(FPR) over repeats")
        ax.set_title("B2 Calibration-Size Sweep - Regime A")
        ax.set_xscale("log")
        ax.grid(True, alpha=0.3)
