"""GB-05 B-FedStatsBenign comparator.

Benign‑only federated summary‑statistics threshold comparator.

Per‑client summaries from benign calibration errors:
  (n_i, μ_i, σ²_i)

Weighted global mean:
  μ_global = Σ(n_i × μ_i) / Σ(n_i)

Pooled variance (within‑client + between‑client terms):
  within_var = Σ(n_i × σ²_i) / Σ(n_i)
  between_var = Σ(n_i × (μ_i − μ_global)²) / Σ(n_i)
  σ²_global = within_var + between_var
  between_ratio = between_var / σ²_global

Threshold grid:
  τ(k) = μ_global + k · σ_global,   k ∈ [k_min, k_max] step k_step

Operating point selection:
  k* = argmin_k | exceedance(k) − target_exceedance |,  tie‑break: larger k

NO attack labels are used in any computation.

Outputs (when write_outputs=True):
  <base_dir>/analysis/fedstats_benign_table.csv
  <base_dir>/analysis/fedstats_benign_diagnostics.json
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import numpy as np
from pydantic import BaseModel, ConfigDict

from datp.analyses._common import (
    load_cal_errors,
    load_verified_safe_cells,
    parse_alpha_str,
)
from datp.artifacts.directories import ANALYSIS_DIR
from datp.config.compose import compose_config
from datp.config.models import DatpConfig
from datp.core.enums import Baseline, Regime
from datp.core.errors import fmt
from datp.evaluation.metrics import (
    ClientMetrics,
    EvaluationResult,
    build_evaluation_result,
    compute_client_metrics,
)
from datp.evaluation.score_loading import ScoreProvider

_MODULE = "analyses.fedstats_benign"

FEDSTATS_TABLE_CSV = "fedstats_benign_table.csv"
FEDSTATS_DIAGNOSTICS_JSON = "fedstats_benign_diagnostics.json"


class ClientSummary(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    client_id: str
    n: int
    mean: float
    var: float


class FedStatsResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    mu_global: float
    sigma_sq_global: float
    within_var: float
    between_var: float
    between_ratio: float
    k_star: float
    tau_star: float
    achieved_exceedance: float
    abs_deviation_from_target: float
    cv_fpr: float
    mean_fpr: float
    coverage_ratio: float
    eligible_count: int
    client_count: int
    regime: Regime
    seed: int
    alpha: str | None


class FedStatsRunResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    cells: list[FedStatsResult]
    k_min: float
    k_max: float
    k_step: float
    target_exceedance: float
    verified_safe_cell_count: int


# ── Helpers: _load_cell_verdicts, _load_cal_errors, _parse_alpha_str
#    → imported from datp.analyses._common


def _compute_client_summaries(cal_errors: dict[str, np.ndarray]) -> list[ClientSummary]:
    summaries: list[ClientSummary] = []
    for cid, arr in cal_errors.items():
        arr_f64 = np.asarray(arr, dtype=np.float64)
        n = arr_f64.size
        mean = float(np.mean(arr_f64))
        var = float(np.var(arr_f64, ddof=0)) if n >= 2 else 0.0
        summaries.append(ClientSummary(client_id=cid, n=n, mean=mean, var=var))
    return summaries


def _compute_global_stats(summaries: list[ClientSummary]) -> tuple[float, float, float, float, float]:
    total_n = sum(s.n for s in summaries)
    if total_n == 0:
        raise ValueError(fmt(_MODULE, "No calibration samples", "at least one sample", "0 total"))

    mu_global = sum(s.n * s.mean for s in summaries) / total_n

    within_var = sum(s.n * s.var for s in summaries) / total_n
    between_var = sum(s.n * (s.mean - mu_global) ** 2 for s in summaries) / total_n

    sigma_sq_global = within_var + between_var
    between_ratio = between_var / sigma_sq_global if sigma_sq_global > 0 else 0.0

    return mu_global, sigma_sq_global, within_var, between_var, between_ratio


def _select_k_star(
    mu_global: float,
    sigma_global: float,
    k_min: float,
    k_max: float,
    k_step: float,
    target_exceedance: float,
    cal_errors: dict[str, np.ndarray],
) -> tuple[float, float, float]:
    """Select k* = argmin |exceedance(k) - target|, tie-break larger k.

    exceedance(k) = fraction of all calibration errors > τ(k).
    """
    all_errors = np.concatenate([np.asarray(arr, dtype=np.float64) for arr in cal_errors.values()])
    if all_errors.size == 0:
        raise ValueError(fmt(_MODULE, "No calibration errors", "at least one sample", "0"))

    best_k = k_min
    best_dev = float("inf")

    k = k_min
    while k <= k_max + 1e-12:
        tau = mu_global + k * sigma_global
        exceedance = float(np.mean(all_errors > tau))
        dev = abs(exceedance - target_exceedance)
        if dev < best_dev - 1e-15 or (abs(dev - best_dev) < 1e-15 and k > best_k):
            best_dev = dev
            best_k = k
        k += k_step

    tau_star = mu_global + best_k * sigma_global
    achieved = float(np.mean(all_errors > tau_star))
    return best_k, tau_star, achieved


def _evaluate_threshold(
    tau: float,
    score_provider: ScoreProvider,
    client_ids: list[str],
    regime: Regime,
    seed: int,
    alpha: float | None,
) -> EvaluationResult:
    per_client: list[ClientMetrics] = []
    eligible_ids: list[str] = []
    pending_ids: list[str] = []
    eval_incomplete_ids: list[str] = []

    for cid in client_ids:
        benign, attack = score_provider.load_test_scores(cid)
        per_client.append(compute_client_metrics(cid, benign, attack, tau))
        eligible_ids.append(cid)
        if attack.size == 0:
            eval_incomplete_ids.append(cid)

    return build_evaluation_result(
        baseline=Baseline.B1,  # comparator, labelled as B1-style global threshold
        regime=regime,
        seed=seed,
        alpha=alpha,
        per_client=per_client,
        eligible_ids=eligible_ids,
        pending_ids=pending_ids,
        eval_incomplete_ids=eval_incomplete_ids,
    )


def run_fedstats_benign(
    base_dir: Path,
    *,
    config: DatpConfig | None = None,
    write_outputs: bool = False,
) -> FedStatsRunResult:
    cfg = config or compose_config(regime=Regime.A, baseline=Baseline.B1, seed=0)
    k_min = cfg.analysis.fedstats_k_min
    k_max = cfg.analysis.fedstats_k_max
    k_step = cfg.analysis.fedstats_k_step
    target_exceedance = cfg.analysis.fedstats_target_exceedance

    resolved = base_dir.resolve()
    safe_cells = load_verified_safe_cells(resolved)

    results: list[FedStatsResult] = []
    for cell in safe_cells:
        cell_dir = Path(cell["cell_dir"])
        regime = Regime(cell["regime"])
        seed = int(cell["seed"])
        alpha_str: str | None = cell.get("alpha")
        alpha_f = parse_alpha_str(alpha_str)

        cal_errors = load_cal_errors(cell_dir)
        score_provider = ScoreProvider(cell_dir)

        summaries = _compute_client_summaries(cal_errors)
        mu_global, sigma_sq_global, within_var, between_var, between_ratio = _compute_global_stats(summaries)
        sigma_global = math.sqrt(max(sigma_sq_global, 0.0))

        if sigma_global <= 0.0:
            continue  # degenerate — all errors identical

        k_star, tau_star, achieved = _select_k_star(
            mu_global, sigma_global, k_min, k_max, k_step, target_exceedance, cal_errors,
        )

        client_ids = sorted(cal_errors.keys())
        evaluation = _evaluate_threshold(tau_star, score_provider, client_ids, regime, seed, alpha_f)

        results.append(FedStatsResult(
            mu_global=mu_global,
            sigma_sq_global=sigma_sq_global,
            within_var=within_var,
            between_var=between_var,
            between_ratio=between_ratio,
            k_star=k_star,
            tau_star=tau_star,
            achieved_exceedance=achieved,
            abs_deviation_from_target=abs(achieved - target_exceedance),
            cv_fpr=evaluation.cv_fpr,
            mean_fpr=evaluation.mean_fpr,
            coverage_ratio=evaluation.coverage_ratio,
            eligible_count=evaluation.eligible_count,
            client_count=evaluation.client_count,
            regime=regime,
            seed=seed,
            alpha=alpha_str,
        ))

    result = FedStatsRunResult(
        cells=results,
        k_min=k_min,
        k_max=k_max,
        k_step=k_step,
        target_exceedance=target_exceedance,
        verified_safe_cell_count=len(safe_cells),
    )

    if write_outputs:
        _write_outputs(result, resolved)

    return result


def _write_outputs(result: FedStatsRunResult, base_dir: Path) -> None:
    analysis_dir = base_dir / ANALYSIS_DIR
    analysis_dir.mkdir(parents=True, exist_ok=True)

    # CSV
    fieldnames = [
        "regime", "seed", "alpha", "mu_global", "sigma_sq_global", "within_var",
        "between_var", "between_ratio", "k_star", "tau_star", "achieved_exceedance",
        "abs_deviation", "cv_fpr", "mean_fpr", "coverage_ratio", "eligible_count", "client_count",
    ]
    csv_path = analysis_dir / FEDSTATS_TABLE_CSV
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for r in result.cells:
            writer.writerow({
                "regime": r.regime.value,
                "seed": r.seed,
                "alpha": r.alpha,
                "mu_global": r.mu_global,
                "sigma_sq_global": r.sigma_sq_global,
                "within_var": r.within_var,
                "between_var": r.between_var,
                "between_ratio": r.between_ratio,
                "k_star": r.k_star,
                "tau_star": r.tau_star,
                "achieved_exceedance": r.achieved_exceedance,
                "abs_deviation": r.abs_deviation_from_target,
                "cv_fpr": r.cv_fpr,
                "mean_fpr": r.mean_fpr,
                "coverage_ratio": r.coverage_ratio,
                "eligible_count": r.eligible_count,
                "client_count": r.client_count,
            })

    # Diagnostics JSON
    diag = {
        "k_min": result.k_min,
        "k_max": result.k_max,
        "k_step": result.k_step,
        "target_exceedance": result.target_exceedance,
        "verified_safe_cell_count": result.verified_safe_cell_count,
        "regime_a_between_ratios": [
            {"seed": r.seed, "between_ratio": r.between_ratio}
            for r in result.cells if r.regime == Regime.A and r.alpha is None
        ],
    }
    diag_path = analysis_dir / FEDSTATS_DIAGNOSTICS_JSON
    diag_path.write_text(json.dumps(diag, indent=2, default=str), encoding="utf-8")
