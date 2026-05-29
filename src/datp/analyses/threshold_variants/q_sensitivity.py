"""GB-01 q-sensitivity analysis.

Evaluates B1/B2/B4 thresholds and metrics at q in q_grid (from config) using
verified stored score cells (T04 verdict = VERIFIED_REUSE_SAFE). No FL training
is performed; all computations use stored score Parquet files.

Outputs (when write_outputs=True):
  <base_dir>/analysis/q_sensitivity_table.csv
  <base_dir>/analysis/q_sensitivity_heatmap.png
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

from datp.analyses.cells import (
    iter_analysis_cell_contexts,
    load_verified_safe_cells,
)
from datp.analyses.evaluation import (
    derive_tau_global,
    evaluate_threshold_result,
)
from datp.analyses.io import ensure_analysis_dir, write_analysis_csv
from datp.analyses.plotting import plt
from datp.analyses.types import FrozenModel
from datp.artifacts.constants import METRICS_FILE
from datp.artifacts.paths import ExperimentLocator
from datp.validation.constants import SCALAR_METRIC_TOLERANCE
from datp.thresholding.thresholds import derive_threshold
from datp.config.models import DatpConfig
from datp.core.enums import Baseline, Regime
from datp.core.errors import fmt
from datp.core.identity import alpha_from_label

from datp.analyses.constants import Q_SENSITIVITY_HEATMAP_PNG, Q_SENSITIVITY_TABLE_CSV

_MODULE = __name__

_Q_SENSITIVITY_BASELINES = (Baseline.B1, Baseline.B2, Baseline.B4)
_BASELINE_LABELS = {Baseline.B1: "B1", Baseline.B2: "B2", Baseline.B4: "B4"}


class QSensitivityRow(FrozenModel):
    q: float
    regime: Regime
    seed: int
    alpha: str | None
    baseline: Baseline
    cv_fpr: float
    mean_fpr: float
    coverage_ratio: float
    eligible_count: int
    client_count: int


class QSensitivityResult(FrozenModel):
    rows: list[QSensitivityRow]
    reference_q: float
    verified_safe_cell_count: int
    reference_q_max_deviation: float
    reference_q_verified: bool


def _reference_q_max_deviation(
    rows: list[QSensitivityRow],
    base_dir: Path,
    reference_q: float,
) -> float:
    """Max absolute deviation of reference_q rows from stored metrics.json cv_fpr."""
    max_dev = 0.0
    for row in rows:
        if not math.isclose(row.q, reference_q):
            continue
        alpha_f = alpha_from_label(row.alpha)
        locator = ExperimentLocator.for_main(base_dir, row.regime)
        metrics_path = locator.result(row.baseline, row.seed, alpha_f) / METRICS_FILE
        if not metrics_path.is_file():
            continue
        stored = json.loads(metrics_path.read_text(encoding="utf-8"))
        stored_cv_fpr = stored.get("cv_fpr")
        if stored_cv_fpr is None:
            continue
        max_dev = max(max_dev, abs(float(stored_cv_fpr) - row.cv_fpr))
    return max_dev


def run_q_sensitivity(
    base_dir: Path,
    *,
    q_grid: list[float],
    config: DatpConfig | None = None,
    write_outputs: bool = False,
) -> QSensitivityResult:
    """Evaluate B1/B2/B4 at each q in q_grid on all VERIFIED_REUSE_SAFE score cells."""
    if not q_grid:
        raise ValueError(
            fmt(_MODULE, "q_grid cannot be empty", "non-empty list", "empty list")
        )

    from datp.config.compose import compose_analysis_config

    cfg = config if config is not None else compose_analysis_config()
    resolved = base_dir.resolve()
    safe_cells = load_verified_safe_cells(resolved)

    rows: list[QSensitivityRow] = []
    for ctx in iter_analysis_cell_contexts(safe_cells):
        for q in q_grid:
            tau_global, b1_result = derive_tau_global(
                ctx.calibration_errors,
                regime=ctx.regime,
                threshold_cfg=cfg.threshold,
                q=q,
            )

            for baseline in _Q_SENSITIVITY_BASELINES:
                threshold_result = (
                    b1_result
                    if baseline == Baseline.B1
                    else derive_threshold(
                        baseline,
                        ctx.calibration_errors,
                        n_min=cfg.threshold.n_min,
                        q=q,
                        tau_global=tau_global,
                        regime=ctx.regime,
                        threshold_cfg=cfg.threshold,
                    )
                )
                evaluation = evaluate_threshold_result(
                    threshold_result,
                    ctx.score_provider,
                    ctx.regime,
                    ctx.seed,
                    ctx.alpha_value,
                )
                rows.append(
                    QSensitivityRow(
                        q=q,
                        regime=ctx.regime,
                        seed=ctx.seed,
                        alpha=ctx.alpha_label,
                        baseline=baseline,
                        cv_fpr=evaluation.cv_fpr,
                        mean_fpr=evaluation.mean_fpr,
                        coverage_ratio=evaluation.coverage_ratio,
                        eligible_count=evaluation.eligible_count,
                        client_count=evaluation.client_count,
                    )
                )

    reference_q = cfg.threshold.q
    max_dev = _reference_q_max_deviation(rows, resolved, reference_q)
    result = QSensitivityResult(
        rows=rows,
        reference_q=reference_q,
        verified_safe_cell_count=len(safe_cells),
        reference_q_max_deviation=max_dev,
        reference_q_verified=max_dev <= SCALAR_METRIC_TOLERANCE,
    )

    if write_outputs:
        _write_outputs(result, resolved)

    return result


def _write_outputs(result: QSensitivityResult, base_dir: Path) -> None:
    write_analysis_csv(base_dir, Q_SENSITIVITY_TABLE_CSV, result.rows, QSensitivityRow)
    _write_heatmap(result, ensure_analysis_dir(base_dir) / Q_SENSITIVITY_HEATMAP_PNG)


def _write_heatmap(result: QSensitivityResult, path: Path) -> None:
    if not result.rows:
        return

    all_regimes = sorted({r.regime for r in result.rows}, key=lambda r: r.value)
    q_sorted = sorted({r.q for r in result.rows})

    n_regimes = len(all_regimes)
    fig, axes = plt.subplots(
        1, n_regimes, figsize=(3.5 * n_regimes, 3.0), squeeze=False
    )

    for ax_idx, regime in enumerate(all_regimes):
        ax = axes[0][ax_idx]
        regime_rows = [r for r in result.rows if r.regime == regime]
        baselines_present = sorted(
            {r.baseline for r in regime_rows}, key=lambda b: b.value
        )

        heat = np.full((len(baselines_present), len(q_sorted)), np.nan)
        for ri, bl in enumerate(baselines_present):
            for qi, q_val in enumerate(q_sorted):
                matching = [
                    r.cv_fpr
                    for r in regime_rows
                    if r.baseline == bl and math.isclose(r.q, q_val)
                ]
                if matching:
                    heat[ri, qi] = float(
                        np.mean(
                            [v for v in matching if not math.isnan(v)] or [math.nan]
                        )
                    )

        im = ax.imshow(heat, aspect="auto", cmap="viridis", vmin=0)
        ax.set_title(f"Regime {regime.value.upper()}", fontsize=9)
        ax.set_xticks(range(len(q_sorted)))
        ax.set_xticklabels([str(q) for q in q_sorted], fontsize=8)
        ax.set_yticks(range(len(baselines_present)))
        ax.set_yticklabels(
            [_BASELINE_LABELS.get(bl, bl.value) for bl in baselines_present], fontsize=8
        )
        ax.set_xlabel("q", fontsize=8)
        ax.set_ylabel("Baseline", fontsize=8)
        fig.colorbar(im, ax=ax, label="Mean CV(FPR)")

    fig.suptitle("q-Sensitivity: Mean CV(FPR) by q and Baseline", fontsize=9)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
