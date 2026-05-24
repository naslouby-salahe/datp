"""GB-01 q-sensitivity analysis.

Evaluates B1/B2/B4 thresholds and metrics at q ∈ q_grid (from config) using
verified stored score cells (T04 verdict = VERIFIED_REUSE_SAFE). No FL training
is performed; all computations use stored score Parquet files.

Outputs (when write_outputs=True):
  <base_dir>/analysis/q_sensitivity_table.csv
  <base_dir>/analysis/q_sensitivity_heatmap.png
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import numpy as np
from pydantic import BaseModel, ConfigDict

from datp.analyses._common import (
    evaluate_threshold_result,
    load_cal_errors,
    load_verified_safe_cells,
    parse_alpha_str,
)
from datp.artifacts.constants import METRICS_FILE
from datp.artifacts.directories import ANALYSIS_DIR
from datp.audit.constants import SCALAR_METRIC_TOLERANCE
from datp.baselines.common.thresholds import derive_threshold
from datp.config.compose import compose_config
from datp.config.models import DatpConfig
from datp.core.enums import Baseline, Regime
from datp.core.errors import fmt
from datp.evaluation.score_loading import ScoreProvider

_MODULE = "analyses.q_sensitivity"

Q_SENSITIVITY_TABLE_CSV = "q_sensitivity_table.csv"
Q_SENSITIVITY_HEATMAP_PNG = "q_sensitivity_heatmap.png"

_Q_SENSITIVITY_BASELINES = (Baseline.B1, Baseline.B2, Baseline.B4)

_ALPHA_IID = "iid"


class QSensitivityRow(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

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


class QSensitivityResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    rows: list[QSensitivityRow]
    reference_q: float
    verified_safe_cell_count: int
    reference_q_max_deviation: float
    reference_q_verified: bool


# ── Helpers: _load_cell_verdicts, _load_cal_errors, _evaluate, _parse_alpha_str
#    → imported from datp.analyses._common


def _config_for_cell(
    cfg: DatpConfig | None,
    regime: Regime,
    seed: int,
    alpha_f: float | None,
) -> DatpConfig:
    if cfg is not None:
        return cfg
    return compose_config(regime=regime, baseline=Baseline.B1, seed=seed, alpha=alpha_f)


def _reference_q_max_deviation(
    rows: list[QSensitivityRow],
    base_dir: Path,
    reference_q: float,
) -> float:
    """Return the max absolute deviation of reference_q rows from stored metrics.json cv_fpr."""
    from datp.artifacts.paths import ExperimentLocator  # local import avoids circular at module level

    max_dev = 0.0
    for row in rows:
        if not math.isclose(row.q, reference_q):
            continue
        alpha_f = parse_alpha_str(row.alpha)
        locator = ExperimentLocator.for_main(base_dir, row.regime)
        metrics_path = locator.result(row.baseline, row.seed, alpha_f) / METRICS_FILE
        if not metrics_path.is_file():
            continue
        stored = json.loads(metrics_path.read_text(encoding="utf-8"))
        stored_cv_fpr = stored.get("cv_fpr")
        if stored_cv_fpr is None:
            continue
        dev = abs(float(stored_cv_fpr) - row.cv_fpr)
        max_dev = max(max_dev, dev)
    return max_dev


def run_q_sensitivity(
    base_dir: Path,
    *,
    q_grid: list[float],
    config: DatpConfig | None = None,
    write_outputs: bool = False,
) -> QSensitivityResult:
    """Evaluate B1/B2/B4 at each q in q_grid on all VERIFIED_REUSE_SAFE score cells.

    Validates that q=reference_q (config threshold q, default 0.95) reproduces stored
    cv_fpr within SCALAR_METRIC_TOLERANCE. No FL training is performed.
    """
    if not q_grid:
        raise ValueError(fmt(_MODULE, "q_grid cannot be empty", "non-empty list", "empty list"))

    resolved = base_dir.resolve()
    safe_cells = load_verified_safe_cells(resolved)

    rows: list[QSensitivityRow] = []
    for cell in safe_cells:
        cell_dir = Path(cell["cell_dir"])
        regime = Regime(cell["regime"])
        seed = int(cell["seed"])
        alpha_str: str | None = cell.get("alpha")
        alpha_f = parse_alpha_str(alpha_str)

        cfg = _config_for_cell(config, regime, seed, alpha_f)
        cal_errors = load_cal_errors(cell_dir)
        score_provider = ScoreProvider(cell_dir)

        for q in q_grid:
            # B1 is evaluated first to obtain tau_global for this q.
            b1_result = derive_threshold(
                Baseline.B1, cal_errors,
                n_min=cfg.threshold.n_min, q=q, tau_global=0.0,
                regime=regime, threshold_cfg=cfg.threshold,
            )
            tau_global = float(b1_result.tau_global)

            for baseline in _Q_SENSITIVITY_BASELINES:
                if baseline == Baseline.B1:
                    threshold_result = b1_result
                else:
                    threshold_result = derive_threshold(
                        baseline, cal_errors,
                        n_min=cfg.threshold.n_min, q=q, tau_global=tau_global,
                        regime=regime, threshold_cfg=cfg.threshold,
                    )
                evaluation = evaluate_threshold_result(threshold_result, score_provider, regime, seed, alpha_f)
                rows.append(QSensitivityRow(
                    q=q,
                    regime=regime,
                    seed=seed,
                    alpha=alpha_str,
                    baseline=baseline,
                    cv_fpr=evaluation.cv_fpr,
                    mean_fpr=evaluation.mean_fpr,
                    coverage_ratio=evaluation.coverage_ratio,
                    eligible_count=evaluation.eligible_count,
                    client_count=evaluation.client_count,
                ))

    reference_q = config.threshold.q if config is not None else 0.95
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
    import matplotlib  # local import: Agg backend must be set before any other pyplot call

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    analysis_dir = base_dir / ANALYSIS_DIR
    analysis_dir.mkdir(parents=True, exist_ok=True)

    _write_csv(result, analysis_dir)
    _write_heatmap(result, analysis_dir, plt)


def _write_csv(result: QSensitivityResult, analysis_dir: Path) -> None:
    fieldnames = ["q", "regime", "seed", "alpha", "baseline", "cv_fpr", "mean_fpr",
                  "coverage_ratio", "eligible_count", "client_count"]
    with (analysis_dir / Q_SENSITIVITY_TABLE_CSV).open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in result.rows:
            writer.writerow({
                "q": row.q,
                "regime": row.regime.value,
                "seed": row.seed,
                "alpha": row.alpha,
                "baseline": row.baseline.value,
                "cv_fpr": row.cv_fpr,
                "mean_fpr": row.mean_fpr,
                "coverage_ratio": row.coverage_ratio,
                "eligible_count": row.eligible_count,
                "client_count": row.client_count,
            })


def _write_heatmap(result: QSensitivityResult, analysis_dir: Path, plt) -> None:  # type: ignore[type-arg]
    if not result.rows:
        return

    all_regimes = sorted({r.regime for r in result.rows}, key=lambda r: r.value)
    q_sorted = sorted({r.q for r in result.rows})
    baseline_labels = {Baseline.B1: "B1", Baseline.B2: "B2", Baseline.B4: "B4"}

    n_regimes = len(all_regimes)
    fig, axes = plt.subplots(1, n_regimes, figsize=(3.5 * n_regimes, 3.0), squeeze=False)

    for ax_idx, regime in enumerate(all_regimes):
        ax = axes[0][ax_idx]
        regime_rows = [r for r in result.rows if r.regime == regime]
        baselines_present = sorted({r.baseline for r in regime_rows}, key=lambda b: b.value)

        heat = np.full((len(baselines_present), len(q_sorted)), np.nan)
        for ri, bl in enumerate(baselines_present):
            for qi, q_val in enumerate(q_sorted):
                matching = [r.cv_fpr for r in regime_rows
                            if r.baseline == bl and math.isclose(r.q, q_val)]
                if matching:
                    heat[ri, qi] = float(np.mean([v for v in matching if not math.isnan(v)] or [math.nan]))

        im = ax.imshow(heat, aspect="auto", cmap="viridis", vmin=0)
        ax.set_title(f"Regime {regime.value.upper()}", fontsize=9)
        ax.set_xticks(range(len(q_sorted)))
        ax.set_xticklabels([str(q) for q in q_sorted], fontsize=8)
        ax.set_yticks(range(len(baselines_present)))
        ax.set_yticklabels([baseline_labels.get(bl, bl.value) for bl in baselines_present], fontsize=8)
        ax.set_xlabel("q", fontsize=8)
        ax.set_ylabel("Baseline", fontsize=8)
        fig.colorbar(im, ax=ax, label="Mean CV(FPR)")

    fig.suptitle("q-Sensitivity: Mean CV(FPR) by q and Baseline", fontsize=9)
    fig.tight_layout()
    fig.savefig(analysis_dir / Q_SENSITIVITY_HEATMAP_PNG, dpi=150, bbox_inches="tight")
    plt.close(fig)
