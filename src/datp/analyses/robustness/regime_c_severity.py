"""GB-11 Regime C Severity Analysis.

Analyzes CV(FPR) gap (B1 - B2) over alpha values in Regime C.
Documents how heterogeneity severity (controlled by Dirichlet alpha)
relates to the B1-B2 threshold personalization gap.

Missing alpha/IID cells are documented with explicit suppression notes.
No Regime C retraining.

Outputs (when write_outputs=True):
  <base_dir>/analysis/regime_c_severity_table.csv
  <base_dir>/analysis/regime_c_severity_trend.png
  <base_dir>/analysis/regime_c_severity_suppression.json (if missing cells)
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from datp.analyses.cells import (
    iter_analysis_cell_contexts,
    load_safe_cells_for_regime,
)
from datp.analyses.evaluation import (
    derive_tau_global,
    evaluate_threshold_result,
)
from datp.analyses.io import (
    ensure_analysis_dir,
    write_analysis_csv,
    write_analysis_json,
)
from datp.analyses.plotting import saved_figure
from datp.analyses.runners import analysis_runner
from datp.core.types import AnalysisRowBase, FrozenModel
from datp.thresholding.thresholds import derive_threshold
from datp.config.models import DatpConfig
from datp.core.enums import Baseline, Regime

from datp.analyses.constants import (
    REGIME_C_SEVERITY_SUPPRESSION_JSON,
    REGIME_C_SEVERITY_TABLE_CSV,
    REGIME_C_SEVERITY_TREND_PNG,
)

_MODULE = __name__


class SeverityRow(AnalysisRowBase):
    b1_cv_fpr: float
    b2_cv_fpr: float
    gap: float
    eligible_count: int


class SeverityResult(FrozenModel):
    rows: list[SeverityRow]
    alpha_summary: list[dict]  # alpha, mean_gap, std_gap, n_seeds
    missing_alphas: list[str]
    suppressed: bool


def _alpha_key(alpha_label: str | None) -> float:
    if alpha_label is None or alpha_label == "iid":
        return float("inf")
    return float(alpha_label)


def _alpha_summary(rows: list[SeverityRow]) -> list[dict]:
    summary: list[dict] = []
    for alpha_label in sorted({r.alpha for r in rows}, key=_alpha_key):
        alpha_rows = [r for r in rows if r.alpha == alpha_label]
        gaps = np.array([r.gap for r in alpha_rows])
        summary.append(
            {
                "alpha": alpha_label,
                "mean_gap": float(gaps.mean()),
                "std_gap": float(gaps.std(ddof=1)) if gaps.size > 1 else 0.0,
                "n_seeds": len(alpha_rows),
            }
        )
    return summary


def _write_outputs(result: SeverityResult, base_dir: Path) -> None:
    write_analysis_csv(base_dir, REGIME_C_SEVERITY_TABLE_CSV, result.rows, SeverityRow)
    if result.suppressed:
        write_analysis_json(
            base_dir,
            REGIME_C_SEVERITY_SUPPRESSION_JSON,
            {
                "note": "Some expected Regime C alpha values are missing from verified cells.",
                "missing_alphas": result.missing_alphas,
                "action": (
                    "These cells were not included in the analysis. "
                    "Re-run T02/T04 to verify completeness."
                ),
            },
        )
    _write_trend(result, base_dir)


@analysis_runner(writer_func=_write_outputs)
def run_regime_c_severity(
    base_dir: Path,
    *,
    config: DatpConfig,
) -> SeverityResult:
    q = config.threshold.q
    n_min = config.threshold.n_min

    cells = load_safe_cells_for_regime(
        base_dir,
        Regime.C,
        caller_module=_MODULE,
    )

    found_alphas = {c.alpha for c in cells}
    expected_alpha_labels = {
        None if a == float("inf") else str(a) for a in config.experiment.regime_c_alphas
    }
    missing = sorted(
        [(a if a is not None else "iid") for a in expected_alpha_labels - found_alphas],
        key=lambda x: float("inf") if x == "iid" else float(x),
    )

    rows: list[SeverityRow] = []
    for ctx in iter_analysis_cell_contexts(cells):
        tau_global, b1 = derive_tau_global(
            ctx.calibration_errors, regime=Regime.C, threshold_cfg=config.threshold
        )
        b2 = derive_threshold(
            Baseline.B2,
            ctx.calibration_errors,
            n_min=n_min,
            q=q,
            tau_global=tau_global,
            regime=Regime.C,
            threshold_cfg=config.threshold,
        )

        b1_eval = evaluate_threshold_result(
            b1, ctx.score_provider, Regime.C, ctx.seed, ctx.alpha_value
        )
        b2_eval = evaluate_threshold_result(
            b2, ctx.score_provider, Regime.C, ctx.seed, ctx.alpha_value
        )

        rows.append(
            SeverityRow(
                regime=ctx.regime,
                alpha=ctx.alpha_label,
                seed=ctx.seed,
                b1_cv_fpr=float(b1_eval.cv_fpr),
                b2_cv_fpr=float(b2_eval.cv_fpr),
                gap=float(b1_eval.cv_fpr - b2_eval.cv_fpr),
                eligible_count=b1_eval.eligible_count,
            )
        )

    return SeverityResult(
        rows=rows,
        alpha_summary=_alpha_summary(rows),
        missing_alphas=missing,
        suppressed=len(missing) > 0,
    )


def _write_trend(result: SeverityResult, base_dir: Path) -> None:
    if not result.alpha_summary:
        return

    alphas = [s["alpha"] for s in result.alpha_summary]
    means = [s["mean_gap"] for s in result.alpha_summary]
    stds = [s["std_gap"] for s in result.alpha_summary]

    x_pos = range(len(alphas))
    out_path = ensure_analysis_dir(base_dir) / REGIME_C_SEVERITY_TREND_PNG
    with saved_figure(out_path, figsize=(6, 4)) as (fig, ax):
        ax.errorbar(x_pos, means, yerr=stds, fmt="o-", capsize=4)
        ax.set_xticks(x_pos)
        ax.set_xticklabels(alphas)
        ax.set_xlabel("Dirichlet alpha")
        ax.set_ylabel("B1 - B2 CV(FPR) Gap")
        ax.set_title("Regime C: Heterogeneity Severity vs DATP Benefit")
        ax.axhline(y=0, color="gray", linestyle="--", linewidth=0.5)
