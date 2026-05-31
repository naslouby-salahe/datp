"""GB-03 tau-shrink threshold variant.

Interpolates between B1 (global) and B2 (per-client) thresholds:
    tau_k(lambda) = lambda * tau_k_local + (1 - lambda) * tau_global
for lambda in tau_shrink_lambdas (from config).
lambda=0 reproduces B1; lambda=1 reproduces B2.
No single lambda is selected post-hoc - the full lambda curve is the result.

Outputs (when write_outputs=True):
  <base_dir>/analysis/tau_shrink_table.csv
  <base_dir>/analysis/tau_shrink_curve.png
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import TYPE_CHECKING

from dataclasses import dataclass

import numpy as np

from datp.analyses.cells import (
    AnalysisCellContext,
    iter_analysis_cell_contexts,
    load_verified_safe_cells,
)
from datp.analyses.evaluation import (
    derive_tau_global,
    evaluate_threshold_result,
)
from datp.analyses.io import ensure_analysis_dir, write_analysis_csv
from datp.analyses.plotting import saved_figure
from datp.analyses.runners import analysis_runner
from datp.core.types import AnalysisRowBase, FrozenModel
from datp.validation.constants import SCALAR_METRIC_TOLERANCE
from datp.thresholding.thresholds import derive_threshold
from datp.core.types import ClientThreshold
from datp.config.models import DatpConfig
from datp.core.enums import Baseline, Regime
from datp.core.identity import BaselineRunId, TrainingCellId
from datp.core.errors import fmt
from datp.evaluation.metrics import EvaluationResult
from datp.scoring.loading import ScoreProvider

if TYPE_CHECKING:
    from datp.config.models import ThresholdConfig

from datp.analyses.constants import TAU_SHRINK_CURVE_PNG, TAU_SHRINK_TABLE_CSV

_MODULE = __name__


class TauShrinkRow(AnalysisRowBase):
    lambda_val: float
    cv_fpr: float
    mean_fpr: float
    macro_f1: float
    coverage_ratio: float
    eligible_count: int


class TauShrinkResult(FrozenModel):
    rows: list[TauShrinkRow]
    lambdas: list[float]
    verified_safe_cell_count: int
    b1_reference_cv_fpr: float | None
    b2_reference_cv_fpr: float | None
    endpoint_verified: bool


@dataclass(frozen=True, slots=True)
class _TauShrinkCellBaselines:
    tau_global: float
    b1_eval: EvaluationResult
    b2_eval: EvaluationResult
    b2_client_thresholds: list[ClientThreshold]
    score_provider: ScoreProvider


def _validate_tau_shrink_inputs(lambdas: list[float], q: float, n_min: int) -> None:
    if not lambdas:
        raise ValueError(
            fmt(_MODULE, "tau_shrink_lambdas is empty", "non-empty list", "empty list")
        )
    if not (0.0 < q < 1.0):
        raise ValueError(fmt(_MODULE, f"q={q} out of range", "0 < q < 1", str(q)))
    if n_min < 1:
        raise ValueError(
            fmt(_MODULE, f"n_min={n_min} must be >= 1", "n_min >= 1", str(n_min))
        )


def _prepare_cell_baselines(
    ctx: AnalysisCellContext,
    threshold_cfg: "ThresholdConfig",
) -> _TauShrinkCellBaselines:
    """Load cal errors, derive B1/B2 thresholds, and evaluate both."""
    tau_global, b1_result = derive_tau_global(
        ctx.calibration_errors, regime=ctx.regime, threshold_cfg=threshold_cfg,
        seed=ctx.seed, alpha=ctx.alpha_value,
    )

    b2_result = derive_threshold(
        Baseline.B2,
        ctx.calibration_errors,
        n_min=threshold_cfg.n_min,
        q=threshold_cfg.q,
        tau_global=tau_global,
        regime=ctx.regime,
        threshold_cfg=threshold_cfg,
        seed=ctx.seed,
        alpha=ctx.alpha_value,
    )

    b1_eval = evaluate_threshold_result(
        b1_result, ctx.score_provider, ctx.regime, ctx.seed, ctx.alpha_value
    )
    b2_eval = evaluate_threshold_result(
        b2_result, ctx.score_provider, ctx.regime, ctx.seed, ctx.alpha_value
    )

    return _TauShrinkCellBaselines(
        tau_global=tau_global,
        b1_eval=b1_eval,
        b2_eval=b2_eval,
        b2_client_thresholds=list(b2_result.client_thresholds),
        score_provider=ctx.score_provider,
    )


def _build_shrink_threshold_result(
    lam: float,
    tau_global: float,
    b2_client_thresholds: list[ClientThreshold],
    regime: Regime,
    seed: int,
    alpha_f: float | None,
):
    """Build interpolated ThresholdResult for one lambda value (0 < lambda < 1)."""
    from datp.thresholding.eligibility import build_threshold_result

    run = BaselineRunId(
        cell=TrainingCellId(regime=regime, seed=seed, alpha=alpha_f),
        baseline=Baseline.B2,
    )
    interpolated: dict[str, float] = {}
    pending: list[str] = []

    for client_threshold in b2_client_thresholds:
        client_id = client_threshold.client_id
        if client_threshold.calibration_pending:
            pending.append(client_id)
            interpolated[client_id] = tau_global
        else:
            interpolated[client_id] = (
                lam * client_threshold.threshold + (1.0 - lam) * tau_global
            )

    return build_threshold_result(
        run=run,
        tau_global=tau_global,
        eligible_thresholds=interpolated,
        pending_clients=pending,
        b3_metadata=None,
        b4_metadata=None,
    )


def _evaluate_shrink_lambda(
    lam: float,
    cell_baselines: _TauShrinkCellBaselines,
    regime: Regime,
    seed: int,
    alpha_f: float | None,
) -> EvaluationResult:
    """Evaluate one lambda; reuses pre-computed B1/B2 evaluations at endpoints."""
    if math.isclose(lam, 0.0):
        return cell_baselines.b1_eval
    if math.isclose(lam, 1.0):
        return cell_baselines.b2_eval

    thr_result = _build_shrink_threshold_result(
        lam,
        cell_baselines.tau_global,
        cell_baselines.b2_client_thresholds,
        regime,
        seed,
        alpha_f,
    )
    return evaluate_threshold_result(
        thr_result, cell_baselines.score_provider, regime, seed, alpha_f
    )


def _build_shrink_rows_for_cell(
    ctx: AnalysisCellContext,
    cell_baselines: _TauShrinkCellBaselines,
    lambdas: list[float],
) -> list[TauShrinkRow]:
    rows: list[TauShrinkRow] = []
    for lam in lambdas:
        eval_result = _evaluate_shrink_lambda(
            lam, cell_baselines, ctx.regime, ctx.seed, ctx.alpha_value
        )
        rows.append(
            TauShrinkRow(
                lambda_val=lam,
                regime=ctx.regime,
                seed=ctx.seed,
                alpha=ctx.alpha_label,
                cv_fpr=eval_result.cv_fpr,
                mean_fpr=eval_result.mean_fpr,
                macro_f1=eval_result.p10_macro_f1,
                coverage_ratio=eval_result.coverage_ratio,
                eligible_count=eval_result.eligible_count,
            )
        )
    return rows


def _check_shrink_endpoint_row(row: TauShrinkRow, b1_ref: float, b2_ref: float) -> bool:
    """Regime-A no-alpha rows must reproduce B1/B2 at lambda=0/1; others pass."""
    if row.regime != Regime.A or row.alpha is not None:
        return True
    if math.isclose(row.lambda_val, 0.0):
        return abs(row.cv_fpr - b1_ref) <= SCALAR_METRIC_TOLERANCE
    if math.isclose(row.lambda_val, 1.0):
        return abs(row.cv_fpr - b2_ref) <= SCALAR_METRIC_TOLERANCE
    return True


def _verify_shrink_endpoints(
    rows: list[TauShrinkRow],
    b1_ref: float | None,
    b2_ref: float | None,
) -> bool:
    if b1_ref is None or b2_ref is None:
        return False
    return all(_check_shrink_endpoint_row(r, b1_ref, b2_ref) for r in rows)


def _write_outputs(result: TauShrinkResult, base_dir: Path) -> None:
    write_analysis_csv(base_dir, TAU_SHRINK_TABLE_CSV, result.rows, TauShrinkRow)
    _write_curve(result, ensure_analysis_dir(base_dir) / TAU_SHRINK_CURVE_PNG)


@analysis_runner(writer_func=_write_outputs)
def run_tau_shrink(
    base_dir: Path,
    *,
    config: DatpConfig,
) -> TauShrinkResult:
    lambdas = config.analysis.tau_shrink_lambdas

    _validate_tau_shrink_inputs(lambdas, config.threshold.q, config.threshold.n_min)

    safe_cells = load_verified_safe_cells(base_dir)

    b1_ref: float | None = None
    b2_ref: float | None = None
    rows: list[TauShrinkRow] = []

    for ctx in iter_analysis_cell_contexts(safe_cells):
        cell_baselines = _prepare_cell_baselines(ctx, config.threshold)

        if ctx.regime == Regime.A and ctx.alpha_label is None:
            b1_ref = cell_baselines.b1_eval.cv_fpr
            b2_ref = cell_baselines.b2_eval.cv_fpr

        rows.extend(_build_shrink_rows_for_cell(ctx, cell_baselines, lambdas))

    return TauShrinkResult(
        rows=rows,
        lambdas=list(lambdas),
        verified_safe_cell_count=len(safe_cells),
        b1_reference_cv_fpr=b1_ref,
        b2_reference_cv_fpr=b2_ref,
        endpoint_verified=_verify_shrink_endpoints(rows, b1_ref, b2_ref),
    )


def _write_curve(result: TauShrinkResult, path: Path) -> None:
    regime_a_rows = [r for r in result.rows if r.regime == Regime.A and r.alpha is None]
    if not regime_a_rows:
        return

    with saved_figure(path, figsize=(8, 5)) as (fig, ax):
        for lam in result.lambdas:
            lam_rows = [r for r in regime_a_rows if math.isclose(r.lambda_val, lam)]
            if not lam_rows:
                continue
            avg_cv = float(np.mean([r.cv_fpr for r in lam_rows]))
            ax.scatter(lam, avg_cv, s=60, zorder=3)

        ax.set_xlabel("lambda (shrinkage factor)")
        ax.set_ylabel("CV(FPR)")
        ax.set_title("tau-Shrink - Regime A (averaged over seeds)")
        ax.axvline(0.0, color="gray", linestyle="--", alpha=0.4, label="B1 (lambda=0)")
        ax.axvline(1.0, color="gray", linestyle="--", alpha=0.4, label="B2 (lambda=1)")
        ax.legend()
        ax.grid(True, alpha=0.3)
