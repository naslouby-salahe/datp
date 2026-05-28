"""GB-05 B-FedStatsBenign comparator.

Benign-only federated summary-statistics threshold comparator.

Per-client summaries from benign calibration errors:
  (n_i, mu_i, sigma_sq_i)

Weighted global mean:
  mu_global = sum(n_i * mu_i) / sum(n_i)

Pooled variance (within-client + between-client terms):
  within_var = sum(n_i * sigma_sq_i) / sum(n_i)
  between_var = sum(n_i * (mu_i - mu_global)^2) / sum(n_i)
  sigma_sq_global = within_var + between_var
  between_ratio = between_var / sigma_sq_global

Threshold grid:
  tau(k) = mu_global + k * sigma_global,   k in [k_min, k_max] step k_step

Operating point selection:
  k_star = argmin_k | exceedance(k) - target_exceedance |,  tie-break: larger k

NO attack labels are used in any computation.

Outputs (when write_outputs=True):
  <base_dir>/analysis/fedstats_benign_table.csv
  <base_dir>/analysis/fedstats_benign_diagnostics.json
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np

from datp.analyses.cells import (
    iter_analysis_cell_contexts,
    load_verified_safe_cells,
)
from datp.analyses.evaluation import evaluate_single_threshold
from datp.analyses.io import (
    write_analysis_csv,
    write_analysis_json,
)
from datp.analyses.runners import analysis_runner
from datp.analyses.types import FrozenModel
from datp.config.models import DatpConfig
from datp.core.enums import Baseline, Regime
from datp.core.errors import fmt

_MODULE = __name__

FEDSTATS_TABLE_CSV = "fedstats_benign_table.csv"
FEDSTATS_DIAGNOSTICS_JSON = "fedstats_benign_diagnostics.json"


class ClientSummary(FrozenModel):
    client_id: str
    n: int
    mean: float
    var: float


class FedStatsResult(FrozenModel):
    regime: Regime
    seed: int
    alpha: str | None
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


class FedStatsRunResult(FrozenModel):
    cells: list[FedStatsResult]
    k_min: float
    k_max: float
    k_step: float
    target_exceedance: float
    verified_safe_cell_count: int


def _compute_client_summaries(cal_errors: dict[str, np.ndarray]) -> list[ClientSummary]:
    summaries: list[ClientSummary] = []
    for cid, client_errors in cal_errors.items():
        errors_f64 = np.asarray(client_errors, dtype=np.float64)
        n = errors_f64.size
        mean = float(np.mean(errors_f64))
        var = float(np.var(errors_f64, ddof=0)) if n >= 2 else 0.0
        summaries.append(ClientSummary(client_id=cid, n=n, mean=mean, var=var))
    return summaries


def _compute_global_stats(
    summaries: list[ClientSummary],
) -> tuple[float, float, float, float, float]:
    total_n = sum(s.n for s in summaries)
    if total_n == 0:
        raise ValueError(
            fmt(_MODULE, "No calibration samples", "at least one sample", "0 total")
        )

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
    """k_star = argmin |exceedance(k) - target|, tie-break larger k.

    exceedance(k) = fraction of all calibration errors > tau(k).
    """
    all_errors = np.concatenate(
        [np.asarray(arr, dtype=np.float64) for arr in cal_errors.values()]
    )
    if all_errors.size == 0:
        raise ValueError(
            fmt(_MODULE, "No calibration errors", "at least one sample", "0")
        )

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


def _write_outputs(result: FedStatsRunResult, base_dir: Path) -> None:
    write_analysis_csv(base_dir, FEDSTATS_TABLE_CSV, result.cells, FedStatsResult)
    write_analysis_json(
        base_dir,
        FEDSTATS_DIAGNOSTICS_JSON,
        {
            "k_min": result.k_min,
            "k_max": result.k_max,
            "k_step": result.k_step,
            "target_exceedance": result.target_exceedance,
            "verified_safe_cell_count": result.verified_safe_cell_count,
            "regime_a_between_ratios": [
                {"seed": r.seed, "between_ratio": r.between_ratio}
                for r in result.cells
                if r.regime == Regime.A and r.alpha is None
            ],
        },
    )


@analysis_runner(writer_func=_write_outputs)
def run_fedstats_benign(
    base_dir: Path,
    *,
    config: DatpConfig,
) -> FedStatsRunResult:
    k_min = config.analysis.fedstats_k_min
    k_max = config.analysis.fedstats_k_max
    k_step = config.analysis.fedstats_k_step
    target_exceedance = config.analysis.fedstats_target_exceedance

    safe_cells = load_verified_safe_cells(base_dir)

    results: list[FedStatsResult] = []
    for ctx in iter_analysis_cell_contexts(safe_cells):
        summaries = _compute_client_summaries(ctx.calibration_errors)
        mu_global, sigma_sq_global, within_var, between_var, between_ratio = (
            _compute_global_stats(summaries)
        )
        sigma_global = math.sqrt(max(sigma_sq_global, 0.0))

        if sigma_global <= 0.0:
            continue

        k_star, tau_star, achieved = _select_k_star(
            mu_global,
            sigma_global,
            k_min,
            k_max,
            k_step,
            target_exceedance,
            ctx.calibration_errors,
        )

        client_ids = sorted(ctx.calibration_errors.keys())
        evaluation = evaluate_single_threshold(
            baseline=Baseline.B1,
            threshold=tau_star,
            score_provider=ctx.score_provider,
            client_ids=client_ids,
            regime=ctx.regime,
            seed=ctx.seed,
            alpha=ctx.alpha_value,
        )

        results.append(
            FedStatsResult(
                regime=ctx.regime,
                seed=ctx.seed,
                alpha=ctx.alpha_label,
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
            )
        )

    return FedStatsRunResult(
        cells=results,
        k_min=k_min,
        k_max=k_max,
        k_step=k_step,
        target_exceedance=target_exceedance,
        verified_safe_cell_count=len(safe_cells),
    )
