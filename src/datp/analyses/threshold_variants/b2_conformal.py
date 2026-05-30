"""GB-04 B2-conf conformal threshold variant.

Per-client split-conformal threshold:
    k = ceil((n + 1) * (1 - alpha)),   alpha = 1 - q (from config)
    tau_i = sorted_errors[k - 1]  (0-indexed)
If k > n (insufficient calibration samples) -> use max(errors) conservative.
Calibration-Pending clients (n_cal < n_min) receive tau_global as fallback.

Reports empirical benign coverage on held-out test_benign and CV(FPR).
Does NOT claim guaranteed attack detection - the guarantee is limited to
marginal benign-distribution coverage (FPR control under exchangeability).

Outputs (when write_outputs=True):
  <base_dir>/analysis/b2_conf_table.csv
  <base_dir>/analysis/b2_conf_coverage.png
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from datp.analyses.cells import (
    AnalysisCellContext,
    iter_analysis_cell_contexts,
    load_verified_safe_cells,
)
from datp.analyses.evaluation import derive_tau_global
from datp.analyses.io import ensure_analysis_dir, write_analysis_csv
from datp.analyses.plotting import saved_figure
from datp.analyses.runners import analysis_runner
from datp.core.types import AnalysisRowBase, FrozenModel
from datp.thresholding.thresholds import conformal_threshold, derive_threshold
from datp.config.models import DatpConfig, ThresholdConfig
from datp.core.enums import Baseline, Regime, ScoringStage
from datp.core.errors import fmt
from datp.evaluation.metrics import compute_empirical_coverage

_MODULE = __name__

B2_CONF_TABLE_CSV = "b2_conf_table.csv"
B2_CONF_COVERAGE_PNG = "b2_conf_coverage.png"


class B2ConfRow(AnalysisRowBase):
    client_id: str
    tau_conformal: float
    tau_b2: float
    empirical_coverage: float
    n_cal: int
    calibration_pending: bool


class B2ConfResult(FrozenModel):
    rows: list[B2ConfRow]
    alpha_conformal: float
    verified_safe_cell_count: int


def _validate_b2_conf_inputs(alpha_conformal: float, q: float) -> None:
    if not (0.0 < alpha_conformal < 1.0):
        raise ValueError(
            fmt(
                _MODULE,
                f"Invalid alpha_conformal={alpha_conformal} from q={q}",
                "0 < alpha < 1",
                str(alpha_conformal),
            )
        )


def _compute_conformal_for_cell(
    ctx: AnalysisCellContext,
    *,
    alpha_conformal: float,
    threshold_cfg: ThresholdConfig,
) -> list[B2ConfRow]:
    """Per-client conformal thresholds for one safe cell.

    B1 (tau_global) and B2 (per-client) are derived from the same calibration
    errors; Calibration-Pending clients fall back to tau_global.
    """
    tau_global, _ = derive_tau_global(
        ctx.calibration_errors, regime=ctx.regime, threshold_cfg=threshold_cfg
    )
    b2_result = derive_threshold(
        Baseline.B2,
        ctx.calibration_errors,
        n_min=threshold_cfg.n_min,
        q=threshold_cfg.q,
        tau_global=tau_global,
        regime=ctx.regime,
        threshold_cfg=threshold_cfg,
    )

    rows: list[B2ConfRow] = []
    for client_threshold in b2_result.client_thresholds:
        calibration_errors = ctx.calibration_errors.get(
            client_threshold.client_id, np.array([])
        )
        n_cal = calibration_errors.size
        tau_conf = (
            tau_global
            if client_threshold.calibration_pending or n_cal == 0
            else conformal_threshold(calibration_errors, alpha_conformal)
        )
        test_benign_errors = ctx.score_provider.load(
            client_threshold.client_id, ScoringStage.TEST_BENIGN
        )
        coverage = (
            compute_empirical_coverage(test_benign_errors, tau_conf)
            if test_benign_errors.size > 0
            else 0.0
        )
        rows.append(
            B2ConfRow(
                regime=ctx.regime,
                seed=ctx.seed,
                alpha=ctx.alpha_label,
                client_id=client_threshold.client_id,
                tau_conformal=tau_conf,
                tau_b2=client_threshold.threshold,
                empirical_coverage=coverage,
                n_cal=n_cal,
                calibration_pending=client_threshold.calibration_pending,
            )
        )
    return rows


def _write_b2_conf_outputs(result: B2ConfResult, base_dir: Path) -> None:
    write_analysis_csv(base_dir, B2_CONF_TABLE_CSV, result.rows, B2ConfRow)
    _write_coverage_plot(result, base_dir)


@analysis_runner(writer_func=_write_b2_conf_outputs)
def run_b2_conf(
    base_dir: Path,
    *,
    config: DatpConfig,
) -> B2ConfResult:
    alpha_conformal = 1.0 - config.threshold.q
    _validate_b2_conf_inputs(alpha_conformal, config.threshold.q)

    safe_cells = load_verified_safe_cells(base_dir)

    rows: list[B2ConfRow] = []
    for ctx in iter_analysis_cell_contexts(safe_cells):
        rows.extend(
            _compute_conformal_for_cell(
                ctx,
                alpha_conformal=alpha_conformal,
                threshold_cfg=config.threshold,
            )
        )

    return B2ConfResult(
        rows=rows,
        alpha_conformal=alpha_conformal,
        verified_safe_cell_count=len(safe_cells),
    )


def _write_coverage_plot(result: B2ConfResult, base_dir: Path) -> None:
    regime_a_rows = [
        r
        for r in result.rows
        if r.regime == Regime.A and r.alpha is None and not r.calibration_pending
    ]
    if not regime_a_rows:
        return

    coverages = [r.empirical_coverage for r in regime_a_rows]
    target = 1.0 - result.alpha_conformal

    out_path = ensure_analysis_dir(base_dir) / B2_CONF_COVERAGE_PNG
    with saved_figure(out_path, figsize=(8, 5)) as (fig, ax):
        ax.hist(coverages, bins=30, alpha=0.7, edgecolor="black")
        ax.axvline(
            target,
            color="red",
            linestyle="--",
            linewidth=2,
            label=f"Target (1-alpha)={target:.3f}",
        )
        ax.set_xlabel("Empirical benign coverage")
        ax.set_ylabel("Client count")
        ax.set_title("B2-conf Empirical Benign Coverage - Regime A")
        ax.legend()
        ax.grid(True, alpha=0.3)
