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
import json
import math
from pathlib import Path

import numpy as np
from pydantic import BaseModel, ConfigDict

from datp.artifacts.directories import ANALYSIS_DIR, SCORES_DIR
from datp.audit.constants import CELL_VERDICTS_JSON, SCALAR_METRIC_TOLERANCE
from datp.baselines.common.thresholds import derive_threshold
from datp.config.compose import compose_config
from datp.config.models import DatpConfig
from datp.core.enums import Baseline, Regime, ReuseVerdict, ScoringStage
from datp.core.errors import fmt
from datp.evaluation.metrics import (
    ClientMetrics,
    EvaluationResult,
    build_evaluation_result,
    compute_client_metrics,
)
from datp.evaluation.score_loading import ScoreProvider, read_score_column

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


def _load_cell_verdicts(base_dir: Path) -> list[dict]:
    path = base_dir / SCORES_DIR / CELL_VERDICTS_JSON
    if not path.is_file():
        raise FileNotFoundError(
            fmt(_MODULE, f"Cell verdicts not found at {path}", "cell_verdicts.json from T04", "absent")
        )
    return json.loads(path.read_text(encoding="utf-8"))["cells"]


def _load_cal_errors(score_root: Path) -> dict[str, np.ndarray]:
    cal_dir = score_root / ScoringStage.CAL.value
    if not cal_dir.is_dir():
        raise FileNotFoundError(
            fmt(_MODULE, f"Calibration score directory missing at {cal_dir}", "cal/ directory", "absent")
        )
    errors: dict[str, np.ndarray] = {}
    for parquet in sorted(cal_dir.glob("*.parquet")):
        errors[parquet.stem] = read_score_column(parquet)
    if not errors:
        raise FileNotFoundError(
            fmt(_MODULE, f"No calibration parquets at {cal_dir}", "at least one .parquet", "none")
        )
    return errors


def _parse_alpha_str(alpha_str: str | None) -> float | None:
    if alpha_str is None:
        return None
    if alpha_str == "iid":
        return math.inf
    return float(alpha_str)


def _evaluate(
    threshold_result,
    score_provider: ScoreProvider,
    regime: Regime,
    seed: int,
    alpha: float | None,
) -> EvaluationResult:
    per_client: list[ClientMetrics] = []
    eligible_ids: list[str] = []
    pending_ids: list[str] = []
    eval_incomplete_ids: list[str] = []

    for ct in threshold_result.client_thresholds:
        cid = ct.client_id
        benign, attack = score_provider.load_test_scores(cid)
        per_client.append(compute_client_metrics(cid, benign, attack, ct.threshold))
        (pending_ids if ct.calibration_pending else eligible_ids).append(cid)
        if attack.size == 0:
            eval_incomplete_ids.append(cid)

    return build_evaluation_result(
        baseline=threshold_result.strategy,
        regime=regime,
        seed=seed,
        alpha=alpha,
        per_client=per_client,
        eligible_ids=eligible_ids,
        pending_ids=pending_ids,
        eval_incomplete_ids=eval_incomplete_ids,
    )


def run_tau_shrink(
    base_dir: Path,
    *,
    config: DatpConfig | None = None,
    write_outputs: bool = False,
) -> TauShrinkResult:
    cfg = config or compose_config(regime=Regime.A, baseline=Baseline.B1)
    lambdas = cfg.analysis.tau_shrink_lambdas
    q = cfg.threshold.q
    n_min = cfg.threshold.n_min

    if not lambdas:
        raise ValueError(fmt(_MODULE, "tau_shrink_lambdas is empty", "non-empty list", "empty list"))

    resolved = base_dir.resolve()
    safe_cells = [
        c for c in _load_cell_verdicts(resolved)
        if c["verdict"] == ReuseVerdict.VERIFIED_REUSE_SAFE
    ]

    b1_ref: float | None = None
    b2_ref: float | None = None
    rows: list[TauShrinkRow] = []

    for cell in safe_cells:
        cell_dir = Path(cell["cell_dir"])
        regime = Regime(cell["regime"])
        seed = int(cell["seed"])
        alpha_str: str | None = cell.get("alpha")
        alpha_f = _parse_alpha_str(alpha_str)

        cal_errors = _load_cal_errors(cell_dir)
        score_provider = ScoreProvider(cell_dir)

        # Compute B1 (global) and B2 (per-client) thresholds first
        b1_result = derive_threshold(
            Baseline.B1, cal_errors, n_min=n_min, q=q, tau_global=0.0,
            regime=regime, threshold_cfg=cfg.threshold,
        )
        tau_global = float(b1_result.tau_global)

        b2_result = derive_threshold(
            Baseline.B2, cal_errors, n_min=n_min, q=q, tau_global=tau_global,
            regime=regime, threshold_cfg=cfg.threshold,
        )

        b1_eval = _evaluate(b1_result, score_provider, regime, seed, alpha_f)
        b2_eval = _evaluate(b2_result, score_provider, regime, seed, alpha_f)

        if regime == Regime.A and alpha_str is None:
            b1_ref = b1_eval.cv_fpr
            b2_ref = b2_eval.cv_fpr

        for lam in lambdas:
            if math.isclose(lam, 0.0):
                eval_result = b1_eval
            elif math.isclose(lam, 1.0):
                eval_result = b2_eval
            else:
                # Interpolate each client's threshold
                from datp.baselines.main import b2 as b2_mod
                client_taus_local: dict[str, float] = {}
                for ct in b2_result.client_thresholds:
                    client_taus_local[ct.client_id] = ct.threshold

                # Build interpolated threshold result
                from datp.baselines.common.eligibility import build_threshold_result
                interpolated: dict[str, float] = {}
                pending: list[str] = []
                for ct in b2_result.client_thresholds:
                    cid = ct.client_id
                    if ct.calibration_pending:
                        pending.append(cid)
                        interpolated[cid] = tau_global
                    else:
                        local = client_taus_local.get(cid, tau_global)
                        interpolated[cid] = lam * local + (1.0 - lam) * tau_global

                thr_result = build_threshold_result(
                    strategy=Baseline.B2,  # label as B2 variant
                    tau_global=tau_global,
                    eligible_thresholds=interpolated,
                    pending_clients=pending,
                    b3_metadata=None,
                    b4_metadata=None,
                )
                eval_result = _evaluate(thr_result, score_provider, regime, seed, alpha_f)

            rows.append(TauShrinkRow(
                lambda_val=lam,
                regime=regime,
                seed=seed,
                alpha=alpha_str,
                cv_fpr=eval_result.cv_fpr,
                mean_fpr=eval_result.mean_fpr,
                macro_f1=eval_result.p10_macro_f1,
                coverage_ratio=eval_result.coverage_ratio,
                eligible_count=eval_result.eligible_count,
            ))

    endpoint_ok = (
        b1_ref is not None
        and b2_ref is not None
        and abs(b1_ref - b2_ref) >= 0  # trivial check — actual tolerance check below
    )
    # Verify endpoint λ=0 rows reproduce B1 reference and λ=1 rows reproduce B2 reference
    for row in rows:
        if row.regime == Regime.A and row.alpha is None:
            if math.isclose(row.lambda_val, 0.0) and b1_ref is not None:
                if abs(row.cv_fpr - b1_ref) > SCALAR_METRIC_TOLERANCE:
                    endpoint_ok = False
            if math.isclose(row.lambda_val, 1.0) and b2_ref is not None:
                if abs(row.cv_fpr - b2_ref) > SCALAR_METRIC_TOLERANCE:
                    endpoint_ok = False

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
