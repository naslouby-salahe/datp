"""GB-03 τ-shrink threshold variant.

Interpolates between B1 (global) and B2 (per‑client) thresholds:
    τ_k(λ) = λ · τ_k_local + (1 − λ) · τ_global
for λ ∈ tau_shrink_lambdas (from config).  λ=0 reproduces B1; λ=1 reproduces B2.
No single λ is selected post‑hoc — the full λ curve is the result.

Outputs (when write_outputs=True):
  <base_dir>/analysis/tau_shrink_table.csv
  <base_dir>/analysis/tau_shrink_curve.png
"""

from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import TYPE_CHECKING

import attrs
import numpy as np
from pydantic import BaseModel, ConfigDict

from datp.analyses._common import (
    evaluate_threshold_result,
    load_cal_errors,
    load_verified_safe_cells,
    parse_alpha_str,
)
from datp.artifacts.directories import ANALYSIS_DIR
from datp.audit.constants import SCALAR_METRIC_TOLERANCE
from datp.baselines.common.thresholds import derive_threshold
from datp.baselines.common.types import ClientThreshold
from datp.config.compose import compose_config
from datp.config.models import DatpConfig
from datp.core.enums import Baseline, Regime
from datp.core.errors import fmt
from datp.evaluation.metrics import EvaluationResult
from datp.evaluation.score_loading import ScoreProvider

if TYPE_CHECKING:
    from datp.config.models import ThresholdConfig

_MODULE = "analyses.tau_shrink"

TAU_SHRINK_TABLE_CSV = "tau_shrink_table.csv"
TAU_SHRINK_CURVE_PNG = "tau_shrink_curve.png"


class TauShrinkRow(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    lambda_val: float
    regime: Regime
    seed: int
    alpha: str | None
    cv_fpr: float
    mean_fpr: float
    macro_f1: float
    coverage_ratio: float
    eligible_count: int


class TauShrinkResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    rows: list[TauShrinkRow]
    lambdas: list[float]
    verified_safe_cell_count: int
    b1_reference_cv_fpr: float | None
    b2_reference_cv_fpr: float | None
    endpoint_verified: bool


# ── Internal typed dataclasses ──────────────────────────────────────────────


@attrs.define(frozen=True, slots=True)
class _TauShrinkCellMeta:
    """Parsed metadata from one VERIFIED_REUSE_SAFE cell verdict entry."""
    cell_dir: Path
    regime: Regime
    seed: int
    alpha_str: str | None
    alpha_float: float | None


@attrs.define(frozen=True, slots=True)
class _TauShrinkCellBaselines:
    """Pre-computed B1 and B2 baselines for one cell."""
    tau_global: float
    b1_eval: EvaluationResult
    b2_eval: EvaluationResult
    b2_client_thresholds: list[ClientThreshold]
    score_provider: ScoreProvider


# ── Refactored helpers ─────────────────────────────────────────────────────


def _validate_tau_shrink_inputs(
    lambdas: list[float],
    q: float,
    n_min: int,
) -> None:
    """Guard: raise ValueError if tau-shrink inputs are invalid."""
    if not lambdas:
        raise ValueError(fmt(_MODULE, "tau_shrink_lambdas is empty", "non-empty list", "empty list"))
    if not (0.0 < q < 1.0):
        raise ValueError(fmt(_MODULE, f"q={q} out of range", "0 < q < 1", str(q)))
    if n_min < 1:
        raise ValueError(fmt(_MODULE, f"n_min={n_min} must be >= 1", "n_min >= 1", str(n_min)))


def _parse_cell_meta(cell: dict) -> _TauShrinkCellMeta:
    """Parse a single cell verdict entry into typed metadata."""
    return _TauShrinkCellMeta(
        cell_dir=Path(cell["cell_dir"]),
        regime=Regime(cell["regime"]),
        seed=int(cell["seed"]),
        alpha_str=cell.get("alpha"),
        alpha_float=parse_alpha_str(cell.get("alpha")),
    )


def _prepare_cell_baselines(
    *,
    cell_dir: Path,
    regime: Regime,
    seed: int,
    alpha_f: float | None,
    n_min: int,
    q: float,
    threshold_cfg: "ThresholdConfig",
) -> _TauShrinkCellBaselines:
    """Load calibration errors, derive B1/B2 thresholds, and evaluate both."""
    cal_errors = load_cal_errors(cell_dir)

    b1_result = derive_threshold(
        Baseline.B1, cal_errors, n_min=n_min, q=q, tau_global=0.0,
        regime=regime, threshold_cfg=threshold_cfg,
    )
    tau_global = float(b1_result.tau_global)

    b2_result = derive_threshold(
        Baseline.B2, cal_errors, n_min=n_min, q=q, tau_global=tau_global,
        regime=regime, threshold_cfg=threshold_cfg,
    )

    score_provider = ScoreProvider(cell_dir)
    b1_eval = evaluate_threshold_result(b1_result, score_provider, regime, seed, alpha_f)
    b2_eval = evaluate_threshold_result(b2_result, score_provider, regime, seed, alpha_f)

    return _TauShrinkCellBaselines(
        tau_global=tau_global,
        b1_eval=b1_eval,
        b2_eval=b2_eval,
        b2_client_thresholds=list(b2_result.client_thresholds),
        score_provider=score_provider,
    )


def _build_shrink_threshold_result(
    lam: float,
    tau_global: float,
    b2_client_thresholds: list[ClientThreshold],
):
    """Build interpolated ThresholdResult for one λ value (0 < λ < 1)."""
    from datp.baselines.common.calibration_eligibility import build_threshold_result

    interpolated: dict[str, float] = {}
    pending: list[str] = []

    for ct in b2_client_thresholds:
        cid = ct.client_id
        if ct.calibration_pending:
            pending.append(cid)
            interpolated[cid] = tau_global
        else:
            interpolated[cid] = lam * ct.threshold + (1.0 - lam) * tau_global

    return build_threshold_result(
        strategy=Baseline.B2,
        tau_global=tau_global,
        eligible_thresholds=interpolated,
        pending_clients=pending,
        b3_metadata=None,
        b4_metadata=None,
    )


def _evaluate_shrink_lambda(
    lam: float,
    tau_global: float,
    b1_eval: EvaluationResult,
    b2_eval: EvaluationResult,
    b2_client_thresholds: list[ClientThreshold],
    score_provider: ScoreProvider,
    regime: Regime,
    seed: int,
    alpha_f: float | None,
) -> EvaluationResult:
    """Return the EvaluationResult for one λ value.

    λ=0 reuses the pre-computed B1 evaluation; λ=1 reuses B2;
    otherwise thresholds are interpolated and evaluated fresh.
    """
    if math.isclose(lam, 0.0):
        return b1_eval
    if math.isclose(lam, 1.0):
        return b2_eval

    thr_result = _build_shrink_threshold_result(lam, tau_global, b2_client_thresholds)
    return evaluate_threshold_result(thr_result, score_provider, regime, seed, alpha_f)


def _build_shrink_rows_for_cell(
    cell_meta: _TauShrinkCellMeta,
    cell_baselines: _TauShrinkCellBaselines,
    lambdas: list[float],
) -> list[TauShrinkRow]:
    """Build TauShrinkRow for every λ value for a single cell."""
    rows: list[TauShrinkRow] = []
    for lam in lambdas:
        eval_result = _evaluate_shrink_lambda(
            lam=lam,
            tau_global=cell_baselines.tau_global,
            b1_eval=cell_baselines.b1_eval,
            b2_eval=cell_baselines.b2_eval,
            b2_client_thresholds=cell_baselines.b2_client_thresholds,
            score_provider=cell_baselines.score_provider,
            regime=cell_meta.regime,
            seed=cell_meta.seed,
            alpha_f=cell_meta.alpha_float,
        )
        rows.append(TauShrinkRow(
            lambda_val=lam,
            regime=cell_meta.regime,
            seed=cell_meta.seed,
            alpha=cell_meta.alpha_str,
            cv_fpr=eval_result.cv_fpr,
            mean_fpr=eval_result.mean_fpr,
            macro_f1=eval_result.p10_macro_f1,
            coverage_ratio=eval_result.coverage_ratio,
            eligible_count=eval_result.eligible_count,
        ))
    return rows


def _check_shrink_endpoint_row(
    row: TauShrinkRow,
    b1_ref: float,
    b2_ref: float,
) -> bool:
    """Return True if *row* is consistent with the B1/B2 endpoint references.

    Only Regime‑A, no‑alpha rows are checked; all others pass automatically.
    """
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
    """Verify that λ=0 rows reproduce B1 and λ=1 rows reproduce B2 within tolerance."""
    if b1_ref is None or b2_ref is None:
        return False
    return all(_check_shrink_endpoint_row(r, b1_ref, b2_ref) for r in rows)


# ── Main orchestrator ──────────────────────────────────────────────────────


def run_tau_shrink(
    base_dir: Path,
    *,
    config: DatpConfig | None = None,
    write_outputs: bool = False,
) -> TauShrinkResult:
    """Orchestrate τ-shrink analysis across all VERIFIED_REUSE_SAFE cells."""
    cfg = config or compose_config(regime=Regime.A, baseline=Baseline.B1, seed=0)
    lambdas = cfg.analysis.tau_shrink_lambdas
    q = cfg.threshold.q
    n_min = cfg.threshold.n_min

    _validate_tau_shrink_inputs(lambdas, q, n_min)

    resolved = base_dir.resolve()
    safe_cells = load_verified_safe_cells(resolved)

    b1_ref: float | None = None
    b2_ref: float | None = None
    rows: list[TauShrinkRow] = []

    for cell in safe_cells:
        cell_meta = _parse_cell_meta(cell)
        cell_baselines = _prepare_cell_baselines(
            cell_dir=cell_meta.cell_dir,
            regime=cell_meta.regime,
            seed=cell_meta.seed,
            alpha_f=cell_meta.alpha_float,
            n_min=n_min,
            q=q,
            threshold_cfg=cfg.threshold,
        )

        if cell_meta.regime == Regime.A and cell_meta.alpha_str is None:
            b1_ref = cell_baselines.b1_eval.cv_fpr
            b2_ref = cell_baselines.b2_eval.cv_fpr

        rows.extend(_build_shrink_rows_for_cell(cell_meta, cell_baselines, lambdas))

    endpoint_ok = _verify_shrink_endpoints(rows, b1_ref, b2_ref)

    result = TauShrinkResult(
        rows=rows,
        lambdas=list(lambdas),
        verified_safe_cell_count=len(safe_cells),
        b1_reference_cv_fpr=b1_ref,
        b2_reference_cv_fpr=b2_ref,
        endpoint_verified=endpoint_ok,
    )

    if write_outputs:
        _write_outputs(result, resolved)

    return result


def _write_outputs(result: TauShrinkResult, base_dir: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    analysis_dir = base_dir / ANALYSIS_DIR
    analysis_dir.mkdir(parents=True, exist_ok=True)

    # CSV
    fieldnames = [
        "lambda", "regime", "seed", "alpha", "cv_fpr", "mean_fpr",
        "macro_f1", "coverage_ratio", "eligible_count",
    ]
    csv_path = analysis_dir / TAU_SHRINK_TABLE_CSV
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in result.rows:
            writer.writerow({
                "lambda": row.lambda_val,
                "regime": row.regime.value,
                "seed": row.seed,
                "alpha": row.alpha,
                "cv_fpr": row.cv_fpr,
                "mean_fpr": row.mean_fpr,
                "macro_f1": row.macro_f1,
                "coverage_ratio": row.coverage_ratio,
                "eligible_count": row.eligible_count,
            })

    # Curve figure — Regime A only, average across seeds
    regime_a_rows = [r for r in result.rows if r.regime == Regime.A and r.alpha is None]
    if not regime_a_rows:
        return

    fig, ax = plt.subplots(figsize=(8, 5))
    for lam in result.lambdas:
        lam_rows = [r for r in regime_a_rows if math.isclose(r.lambda_val, lam)]
        if not lam_rows:
            continue
        avg_cv = float(np.mean([r.cv_fpr for r in lam_rows]))
        ax.scatter(lam, avg_cv, s=60, zorder=3)

    ax.set_xlabel("λ (shrinkage factor)")
    ax.set_ylabel("CV(FPR)")
    ax.set_title("τ-Shrink — Regime A (averaged over seeds)")
    ax.axvline(0.0, color="gray", linestyle="--", alpha=0.4, label="B1 (λ=0)")
    ax.axvline(1.0, color="gray", linestyle="--", alpha=0.4, label="B2 (λ=1)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(analysis_dir / TAU_SHRINK_CURVE_PNG, dpi=150)
    plt.close(fig)
