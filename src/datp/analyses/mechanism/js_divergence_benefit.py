"""GB-07 JS Divergence vs DATP Benefit.

Computes per-client Jensen-Shannon divergence between each client's calibration
error distribution and the pooled global distribution, then relates divergence
to per-client B1-B2 FPR gain.

Non-causal/descriptive only - weak correlation is reported honestly.

Outputs (when write_outputs=True):
  <base_dir>/analysis/js_divergence_table.csv
  <base_dir>/analysis/js_divergence_scatter.png
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from datp.analyses.cells import (
    AnalysisCellContext,
    iter_analysis_cell_contexts,
    load_safe_cells_for_regime,
)
from datp.analyses.evaluation import derive_tau_global
from datp.analyses.io import ensure_analysis_dir, write_analysis_csv
from datp.analyses.plotting import saved_figure
from datp.analyses.runners import analysis_runner
from datp.analyses.types import FrozenModel
from datp.thresholding.thresholds import derive_threshold
from datp.config.models import DatpConfig
from datp.core.enums import Baseline, Regime
from datp.data.datasets.nbaiot.spec import DEVICE_FAMILY_MAP
from datp.statistics.constants import JS_BIN_EPSILON, JS_LAPLACE_SMOOTHING
from datp.statistics.spearman import SpearmanResult, spearman_correlation

from datp.analyses.constants import JS_DIVERGENCE_SCATTER_PNG, JS_DIVERGENCE_TABLE_CSV

_MODULE = __name__


class JSClientRow(FrozenModel):
    client_id: str
    js_divergence: float
    fpr_b1: float
    fpr_b2: float
    delta_fpr: float
    seed: int
    device_family: str


class JSDivergenceResult(FrozenModel):
    rows: list[JSClientRow]
    spearman_rho: float
    spearman_p_value: float
    r_squared: float
    spearman_mechanism_wording: str
    n_clients: int
    n_cells: int


def _per_client_js(
    client_errors: dict[str, np.ndarray],
    js_n_bins: int,
) -> dict[str, float]:
    """Compute JS(P_client || P_pooled) for each client."""
    pooled = np.concatenate(list(client_errors.values()))
    upper = float(np.percentile(pooled, 99.0))
    lower = float(np.min(pooled))
    if upper <= lower:
        upper = lower + JS_BIN_EPSILON
    bin_edges = np.linspace(lower, upper, js_n_bins + 1)

    def _to_prob(arr: np.ndarray) -> np.ndarray:
        counts, _ = np.histogram(arr, bins=bin_edges)
        smoothed = counts.astype(np.float64) + JS_LAPLACE_SMOOTHING
        return smoothed / smoothed.sum()

    pooled_prob = _to_prob(pooled)

    def _jsd(p: np.ndarray, m: np.ndarray, q: np.ndarray) -> float:
        with np.errstate(divide="ignore", invalid="ignore"):
            kl_pm = float(np.sum(np.where(p > 0, p * np.log(p / m), 0.0)))
            kl_qm = float(np.sum(np.where(q > 0, q * np.log(q / m), 0.0)))
        return 0.5 * (kl_pm + kl_qm)

    jsd: dict[str, float] = {}
    for cid, arr in client_errors.items():
        client_prob = _to_prob(arr)
        mid = 0.5 * (client_prob + pooled_prob)
        jsd[cid] = _jsd(client_prob, mid, pooled_prob)
    return jsd


def _compute_cell_rows(
    ctx: AnalysisCellContext,
    cfg: DatpConfig,
    js_n_bins: int,
    device_family_map: dict[str, str],
) -> list[JSClientRow]:
    jsd = _per_client_js(ctx.calibration_errors, js_n_bins)

    tau_global, b1_result = derive_tau_global(
        ctx.calibration_errors, regime=ctx.regime, threshold_cfg=cfg.threshold
    )
    b2_result = derive_threshold(
        Baseline.B2,
        ctx.calibration_errors,
        n_min=cfg.threshold.n_min,
        q=cfg.threshold.q,
        tau_global=tau_global,
        regime=ctx.regime,
        threshold_cfg=cfg.threshold,
    )

    b1_map = {ct.client_id: ct.threshold for ct in b1_result.client_thresholds}
    b2_map = {ct.client_id: ct.threshold for ct in b2_result.client_thresholds}

    rows: list[JSClientRow] = []
    for cid in sorted(ctx.calibration_errors):
        benign, _ = ctx.score_provider.load_test_scores(cid)
        if benign.size == 0:
            continue
        fpr_b1 = float(np.mean(benign > b1_map.get(cid, 0.0)))
        fpr_b2 = float(np.mean(benign > b2_map.get(cid, 0.0)))
        rows.append(
            JSClientRow(
                client_id=cid,
                js_divergence=jsd.get(cid, 0.0),
                fpr_b1=fpr_b1,
                fpr_b2=fpr_b2,
                delta_fpr=fpr_b1 - fpr_b2,
                seed=ctx.seed,
                device_family=device_family_map.get(cid, cid),
            )
        )
    return rows


def _write_outputs(result: JSDivergenceResult, base_dir: Path) -> None:
    write_analysis_csv(base_dir, JS_DIVERGENCE_TABLE_CSV, result.rows, JSClientRow)
    _write_scatter(result, base_dir)


@analysis_runner(writer_func=_write_outputs)
def run_js_divergence(
    base_dir: Path,
    *,
    config: DatpConfig,
) -> JSDivergenceResult:
    cells = load_safe_cells_for_regime(
        base_dir,
        Regime.A,
        alpha_values=(None, "iid"),
        caller_module=_MODULE,
    )

    js_n_bins = config.quality_gates.js_divergence_n_bins

    all_rows: list[JSClientRow] = []
    for ctx in iter_analysis_cell_contexts(cells):
        all_rows.extend(
            _compute_cell_rows(
                ctx,
                config,
                js_n_bins,
                DEVICE_FAMILY_MAP,
            )
        )

    js_vals = np.array([r.js_divergence for r in all_rows], dtype=np.float64)
    delta_vals = np.array([r.delta_fpr for r in all_rows], dtype=np.float64)

    spearman: SpearmanResult
    r_sq = 0.0
    if (
        js_vals.size >= 3
        and np.std(js_vals) > JS_LAPLACE_SMOOTHING
        and np.std(delta_vals) > JS_LAPLACE_SMOOTHING
    ):
        spearman = spearman_correlation(
            js_vals, delta_vals, config.statistics.significance_alpha
        )
        r_sq = float(spearman.rho**2)
    else:
        spearman = SpearmanResult(
            rho=0.0, p_value=1.0, mechanism_wording="HYPOTHESIS", n=js_vals.size
        )

    return JSDivergenceResult(
        rows=all_rows,
        spearman_rho=spearman.rho,
        spearman_p_value=spearman.p_value,
        r_squared=r_sq,
        spearman_mechanism_wording=spearman.mechanism_wording,
        n_clients=len({r.client_id for r in all_rows}),
        n_cells=len(cells),
    )


def _write_scatter(result: JSDivergenceResult, base_dir: Path) -> None:
    js = np.array([r.js_divergence for r in result.rows])
    delta = np.array([r.delta_fpr for r in result.rows])

    out_path = ensure_analysis_dir(base_dir) / JS_DIVERGENCE_SCATTER_PNG
    with saved_figure(out_path, figsize=(5, 4)) as (fig, ax):
        ax.scatter(js, delta, alpha=0.7, s=40)
        ax.set_xlabel("JS Divergence (client vs pool)")
        ax.set_ylabel("Delta FPR (B1 - B2)")
        ax.set_title(
            f"JS Divergence vs DATP Benefit\n"
            f"rho={result.spearman_rho:.3f}, "
            f"p={result.spearman_p_value:.3f} ({result.spearman_mechanism_wording})"
        )
        ax.axhline(y=0, color="gray", linestyle="--", linewidth=0.5)
