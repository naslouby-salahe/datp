"""GB-07 JS Divergence vs DATP Benefit.

Computes per-client Jensen-Shannon divergence between each client's calibration
error distribution and the pooled global distribution, then relates divergence
to per-client B1−B2 FPR gain.

Non-causal/descriptive only — weak correlation is reported honestly.

Outputs (when write_outputs=True):
  <base_dir>/analysis/js_divergence_table.csv
  <base_dir>/analysis/js_divergence_scatter.png
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
from pydantic import BaseModel, ConfigDict

from datp.analyses._common import (
    ensure_analysis_dir,
    load_cal_errors,
    load_verified_safe_cells,
)
from datp.baselines.common.thresholds import derive_threshold
from datp.config.compose import compose_analysis_config
from datp.config.models import DatpConfig
from datp.core.enums import Baseline, Regime
from datp.core.errors import fmt
from datp.data.datasets.nbaiot.spec import DEVICE_FAMILY_MAP
from datp.evaluation.score_loading import ScoreProvider
from datp.statistics.constants import JS_BIN_EPSILON, JS_LAPLACE_SMOOTHING
from datp.statistics.spearman import SpearmanResult, spearman_correlation

_MODULE = "analyses.js_divergence_benefit"

JS_DIVERGENCE_TABLE_CSV = "js_divergence_table.csv"
JS_DIVERGENCE_SCATTER_PNG = "js_divergence_scatter.png"


class JSClientRow(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    client_id: str
    js_divergence: float
    fpr_b1: float
    fpr_b2: float
    delta_fpr: float
    seed: int
    device_family: str


class JSDivergenceResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
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
    cell_dir: Path,
    regime: Regime,
    seed: int,
    cfg: DatpConfig,
    js_n_bins: int,
    device_family_map: dict[str, str],
) -> list[JSClientRow]:
    cal_errors = load_cal_errors(cell_dir)
    score_provider = ScoreProvider(cell_dir)

    jsd = _per_client_js(cal_errors, js_n_bins)

    q = cfg.threshold.q
    n_min = cfg.threshold.n_min

    b1_result = derive_threshold(
        Baseline.B1, cal_errors, n_min, q, 0.0, regime, threshold_cfg=cfg.threshold
    )
    b2_result = derive_threshold(
        Baseline.B2, cal_errors, n_min, q, 0.0, regime, threshold_cfg=cfg.threshold
    )

    rows: list[JSClientRow] = []
    for cid in sorted(cal_errors):
        benign, _ = score_provider.load_test_scores(cid)
        if benign.size == 0:
            continue
        b1_tau = next(
            (ct.threshold for ct in b1_result.client_thresholds if ct.client_id == cid),
            0.0,
        )
        b2_tau = next(
            (ct.threshold for ct in b2_result.client_thresholds if ct.client_id == cid),
            0.0,
        )
        fpr_b1 = float(np.mean(benign > b1_tau))
        fpr_b2 = float(np.mean(benign > b2_tau))
        rows.append(
            JSClientRow(
                client_id=cid,
                js_divergence=jsd.get(cid, 0.0),
                fpr_b1=fpr_b1,
                fpr_b2=fpr_b2,
                delta_fpr=fpr_b1 - fpr_b2,
                seed=seed,
                device_family=device_family_map.get(cid, cid),
            )
        )
    return rows


def run_js_divergence(
    base_dir: Path,
    *,
    config: DatpConfig | None = None,
    write_outputs: bool = False,
) -> JSDivergenceResult:
    cells = load_verified_safe_cells(base_dir)
    regime_a_cells = [
        c for c in cells if c.regime == Regime.A and c.alpha in (None, "iid")
    ]
    if not regime_a_cells:
        raise FileNotFoundError(
            fmt(
                _MODULE,
                "No verified Regime A cells found",
                "VERIFIED_REUSE_SAFE cells for regime 'a'",
                "none",
            )
        )

    cfg = config if config is not None else compose_analysis_config()
    js_n_bins = cfg.quality_gates.js_divergence_n_bins

    all_rows: list[JSClientRow] = []
    for cell in regime_a_cells:
        cell_dir = Path(cell.cell_dir)
        seed = cell.seed
        all_rows.extend(
            _compute_cell_rows(
                cell_dir, Regime.A, seed, cfg, js_n_bins, DEVICE_FAMILY_MAP
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
            js_vals, delta_vals, cfg.statistics.significance_alpha
        )
        r_sq = float(spearman.rho**2)
    else:
        spearman = SpearmanResult(
            rho=0.0, p_value=1.0, mechanism_wording="HYPOTHESIS", n=js_vals.size
        )

    result = JSDivergenceResult(
        rows=all_rows,
        spearman_rho=spearman.rho,
        spearman_p_value=spearman.p_value,
        r_squared=r_sq,
        spearman_mechanism_wording=spearman.mechanism_wording,
        n_clients=len({r.client_id for r in all_rows}),
        n_cells=len(regime_a_cells),
    )

    if write_outputs:
        _write_outputs(result, base_dir)

    return result


def _write_outputs(result: JSDivergenceResult, base_dir: Path) -> None:
    out_dir = ensure_analysis_dir(base_dir)

    table_path = out_dir / JS_DIVERGENCE_TABLE_CSV
    with open(table_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            [
                "client_id",
                "js_divergence",
                "fpr_b1",
                "fpr_b2",
                "delta_fpr",
                "seed",
                "device_family",
            ]
        )
        for row in result.rows:
            writer.writerow(
                [
                    row.client_id,
                    row.js_divergence,
                    row.fpr_b1,
                    row.fpr_b2,
                    row.delta_fpr,
                    row.seed,
                    row.device_family,
                ]
            )

    _write_scatter(result, out_dir / JS_DIVERGENCE_SCATTER_PNG)


def _write_scatter(result: JSDivergenceResult, path: Path) -> None:
    from datp.analyses._plotting import plt

    js = np.array([r.js_divergence for r in result.rows])
    delta = np.array([r.delta_fpr for r in result.rows])

    fig, ax = plt.subplots(figsize=(5, 4))
    ax.scatter(js, delta, alpha=0.7, s=40)
    ax.set_xlabel("JS Divergence (client vs pool)")
    ax.set_ylabel("ΔFPR (B1 − B2)")
    ax.set_title(
        f"JS Divergence vs DATP Benefit\nρ={result.spearman_rho:.3f}, p={result.spearman_p_value:.3f} ({result.spearman_mechanism_wording})"
    )
    ax.axhline(y=0, color="gray", linestyle="--", linewidth=0.5)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
