"""GB-11 Regime C Severity Analysis.

Analyzes CV(FPR) gap (B1 − B2) over α values in Regime C.
Documents how heterogeneity severity (controlled by Dirichlet α)
relates to the B1−B2 threshold personalization gap.

Missing α/IID cells are documented with explicit suppression notes.
No Regime C retraining.

Outputs (when write_outputs=True):
  <base_dir>/analysis/regime_c_severity_table.csv
  <base_dir>/analysis/regime_c_severity_trend.png
  <base_dir>/analysis/regime_c_severity_suppression.json (if missing cells)
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
from pydantic import BaseModel, ConfigDict

from datp.analyses._common import (
    ensure_analysis_dir,
    evaluate_threshold_result,
    load_cal_errors,
    load_verified_safe_cells,
)
from datp.core.identity import alpha_from_label
from datp.baselines.common.thresholds import derive_threshold
from datp.config.compose import compose_analysis_config
from datp.config.models import DatpConfig
from datp.core.enums import Baseline, Regime
from datp.core.errors import fmt
from datp.evaluation.score_loading import ScoreProvider

_MODULE = "analyses.regime_c_severity"

REGIME_C_SEVERITY_TABLE_CSV = "regime_c_severity_table.csv"
REGIME_C_SEVERITY_TREND_PNG = "regime_c_severity_trend.png"
REGIME_C_SEVERITY_SUPPRESSION_JSON = "regime_c_severity_suppression.json"


class SeverityRow(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    alpha: str
    seed: int
    b1_cv_fpr: float
    b2_cv_fpr: float
    gap: float
    eligible_count: int


class SeverityResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    rows: list[SeverityRow]
    alpha_summary: list[dict]  # alpha, mean_gap, std_gap, n_seeds
    missing_alphas: list[str]
    suppressed: bool


def _alpha_key(alpha_label: str) -> float:
    if alpha_label == "iid":
        return float("inf")
    return float(alpha_label)


def run_regime_c_severity(
    base_dir: Path,
    *,
    config: DatpConfig | None = None,
    write_outputs: bool = False,
) -> SeverityResult:
    cells = load_verified_safe_cells(base_dir)
    regime_c_cells = [c for c in cells if c.regime == Regime.C]
    if not regime_c_cells:
        raise FileNotFoundError(
            fmt(
                _MODULE,
                "No verified Regime C cells",
                "VERIFIED_REUSE_SAFE cells for regime 'c'",
                "none",
            )
        )

    found_alphas = {c.alpha for c in regime_c_cells}

    cfg = config if config is not None else compose_analysis_config()
    q = cfg.threshold.q
    n_min = cfg.threshold.n_min

    expected_alphas: list[float | str] = [
        float(a) if a != float("inf") else "iid" for a in cfg.experiment.regime_c_alphas
    ]
    missing = sorted(
        [
            str(a)
            for a in expected_alphas
            if str(a) not in found_alphas and a not in found_alphas
        ],
        key=lambda x: 0 if x == "iid" else float(x),
    )

    rows: list[SeverityRow] = []
    for cell in regime_c_cells:
        cell_dir = Path(cell.cell_dir)
        seed = cell.seed
        alpha_label = cell.alpha or "iid"
        cal_errors = load_cal_errors(cell_dir)
        score_provider = ScoreProvider(cell_dir)

        b1 = derive_threshold(
            Baseline.B1,
            cal_errors,
            n_min,
            q,
            0.0,
            Regime.C,
            threshold_cfg=cfg.threshold,
        )
        b2 = derive_threshold(
            Baseline.B2,
            cal_errors,
            n_min,
            q,
            0.0,
            Regime.C,
            threshold_cfg=cfg.threshold,
        )

        alpha_f = None if alpha_label == "iid" else alpha_from_label(alpha_label)
        b1_eval = evaluate_threshold_result(b1, score_provider, Regime.C, seed, alpha_f)
        b2_eval = evaluate_threshold_result(b2, score_provider, Regime.C, seed, alpha_f)

        rows.append(
            SeverityRow(
                alpha=str(alpha_label),
                seed=seed,
                b1_cv_fpr=float(b1_eval.cv_fpr),
                b2_cv_fpr=float(b2_eval.cv_fpr),
                gap=float(b1_eval.cv_fpr - b2_eval.cv_fpr),
                eligible_count=b1_eval.eligible_count,
            )
        )

    alpha_summary: list[dict] = []
    for alpha_label in sorted({r.alpha for r in rows}, key=_alpha_key):
        alpha_rows = [r for r in rows if r.alpha == alpha_label]
        gaps = np.array([r.gap for r in alpha_rows])
        alpha_summary.append(
            {
                "alpha": alpha_label,
                "mean_gap": float(gaps.mean()),
                "std_gap": float(gaps.std(ddof=1)) if gaps.size > 1 else 0.0,
                "n_seeds": len(alpha_rows),
            }
        )

    result = SeverityResult(
        rows=rows,
        alpha_summary=alpha_summary,
        missing_alphas=missing,
        suppressed=len(missing) > 0,
    )

    if write_outputs:
        _write_outputs(result, base_dir)

    return result


def _write_outputs(result: SeverityResult, base_dir: Path) -> None:
    out_dir = ensure_analysis_dir(base_dir)

    table_path = out_dir / REGIME_C_SEVERITY_TABLE_CSV
    with open(table_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            ["alpha", "seed", "b1_cv_fpr", "b2_cv_fpr", "gap", "eligible_count"]
        )
        for row in result.rows:
            writer.writerow(
                [
                    row.alpha,
                    row.seed,
                    row.b1_cv_fpr,
                    row.b2_cv_fpr,
                    row.gap,
                    row.eligible_count,
                ]
            )

    if result.suppressed:
        suppression_path = out_dir / REGIME_C_SEVERITY_SUPPRESSION_JSON
        suppression_path.write_text(
            json.dumps(
                {
                    "note": "Some expected Regime C alpha values are missing from verified cells.",
                    "missing_alphas": result.missing_alphas,
                    "action": "These cells were not included in the analysis. Re-run T02/T04 to verify completeness.",
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    _write_trend(result, out_dir / REGIME_C_SEVERITY_TREND_PNG)


def _write_trend(result: SeverityResult, path: Path) -> None:
    if not result.alpha_summary:
        return
    from datp.analyses._plotting import plt

    alphas = [s["alpha"] for s in result.alpha_summary]
    means = [s["mean_gap"] for s in result.alpha_summary]
    stds = [s["std_gap"] for s in result.alpha_summary]

    x_pos = range(len(alphas))
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.errorbar(x_pos, means, yerr=stds, fmt="o-", capsize=4)
    ax.set_xticks(x_pos)
    ax.set_xticklabels(alphas)
    ax.set_xlabel("Dirichlet α")
    ax.set_ylabel("B1−B2 CV(FPR) Gap")
    ax.set_title("Regime C: Heterogeneity Severity vs DATP Benefit")
    ax.axhline(y=0, color="gray", linestyle="--", linewidth=0.5)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
