"""GB-06 B4 feature ablation.

Evaluates B4 fingerprint subsets and full 4‑feature fingerprint
[mean, std, skew, p95].  Computes clustering per subset, evaluates CV(FPR),
and produces contingency of cluster assignment vs. device family (Regime A).

The full 4‑feature fingerprint MUST reproduce canonical B4 results.

Outputs (when write_outputs=True):
  <base_dir>/analysis/b4_ablation_table.csv
  <base_dir>/analysis/b4_ablation_contingency.png
"""

from __future__ import annotations

import csv
import math
from pathlib import Path

import numpy as np
from pydantic import BaseModel, ConfigDict
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score
from sklearn.preprocessing import StandardScaler

from datp.analyses._common import (
    load_cal_errors,
    load_verified_safe_cells,
    parse_alpha_str,
)
from datp.artifacts.directories import ANALYSIS_DIR
from datp.audit.constants import SCALAR_METRIC_TOLERANCE
from datp.baselines.common.thresholds import arithmetic_mean_threshold, derive_threshold
from datp.baselines.main.b4 import compute_fingerprints
from datp.baselines.common.eligibility import identify_eligible
from datp.config.compose import compose_config
from datp.config.models import DatpConfig
from datp.core.enums import Baseline, Regime
from datp.data.datasets.nbaiot.spec import DEVICE_FAMILY_MAP
from datp.evaluation.metrics import (
    ClientMetrics,
    build_evaluation_result,
    compute_client_metrics,
)
from datp.evaluation.score_loading import ScoreProvider

_MODULE = "analyses.b4_ablation"

B4_ABLATION_TABLE_CSV = "b4_ablation_table.csv"
B4_ABLATION_CONTINGENCY_PNG = "b4_ablation_contingency.png"

# Fingerprint feature names — canonical order from b4.py
_FEATURE_NAMES: tuple[str, ...] = ("mean", "std", "skew", "p95")
_ALL_FEATURES: tuple[int, ...] = (0, 1, 2, 3)

# Subset definitions: all singles, all pairs, all triples, full set
_SUBSET_LABELS: dict[tuple[int, ...], str] = {
    (0,): "mean",
    (1,): "std",
    (2,): "skew",
    (3,): "p95",
    (0, 1): "mean+std",
    (0, 2): "mean+skew",
    (0, 3): "mean+p95",
    (1, 2): "std+skew",
    (1, 3): "std+p95",
    (2, 3): "skew+p95",
    (0, 1, 2): "mean+std+skew",
    (0, 1, 3): "mean+std+p95",
    (0, 2, 3): "mean+skew+p95",
    (1, 2, 3): "std+skew+p95",
    (0, 1, 2, 3): "full",
}


class B4AblationRow(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    subset: str
    n_features: int
    regime: Regime
    seed: int
    alpha: str | None
    k: int
    silhouette: float
    ari_vs_family: float  # Adjusted Rand Index vs device family (Regime A only; NaN otherwise)
    cv_fpr: float
    mean_fpr: float
    coverage_ratio: float
    eligible_count: int


class B4AblationResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    rows: list[B4AblationRow]
    verified_safe_cell_count: int
    full_feature_reproduces_b4: bool
    full_vs_canonical_max_deviation: float


# ── Helpers: _load_cell_verdicts, _load_cal_errors, _parse_alpha_str
#    → imported from datp.analyses._common


def _subset_fingerprint(client_errors: dict[str, np.ndarray], eligible: list[str],
                        q: float, indices: tuple[int, ...]) -> dict[str, np.ndarray]:
    """Compute fingerprints restricted to the given feature indices."""
    full = compute_fingerprints(client_errors, eligible, q=q)
    return {cid: fp[np.array(indices)] for cid, fp in full.items()}


def _cluster_and_evaluate(
    fingerprints: dict[str, np.ndarray],
    eligible: list[str],
    pending: list[str],
    tau_global: float,
    random_state: int,
    k: int,
    score_provider: ScoreProvider,
    regime: Regime,
    seed: int,
    alpha: float | None,
) -> tuple[float, float, float, float, float, int]:
    """Cluster fingerprints with KMeans at fixed k and evaluate CV(FPR)."""
    eligible_ids = sorted(eligible)
    matrix = np.array([fingerprints[cid] for cid in eligible_ids])

    scaler = StandardScaler()
    scaled = scaler.fit_transform(matrix)

    km = KMeans(n_clusters=k, random_state=random_state, n_init=10)  # type: ignore[arg-type]
    labels = km.fit_predict(scaled)

    # Compute cluster-mean thresholds
    from collections import defaultdict
    # Per-client local thresholds
    client_taus: dict[str, float] = {}
    for i, cid in enumerate(eligible_ids):
        fp = fingerprints[cid]
        # Use p95 of calibration errors as the local threshold
        client_taus[cid] = float(fp[-1])  # p95 is always the last element

    cluster_taus_map: dict[int, list[float]] = defaultdict(list)
    for i, cid in enumerate(eligible_ids):
        cluster_taus_map[int(labels[i])].append(client_taus[cid])

    tau_per_cluster: dict[int, float] = {}
    for c, taus in cluster_taus_map.items():
        tau_per_cluster[c] = arithmetic_mean_threshold(taus)

    eligible_map = {cid: tau_per_cluster[int(labels[i])] for i, cid in enumerate(eligible_ids)}

    # Evaluate
    per_client: list[ClientMetrics] = []
    all_ids = eligible_ids + pending
    for cid in all_ids:
        benign, attack = score_provider.load_test_scores(cid)
        tau = eligible_map.get(cid, tau_global)
        per_client.append(compute_client_metrics(cid, benign, attack, tau))

    evaluation = build_evaluation_result(
        baseline=Baseline.B4,
        regime=regime,
        seed=seed,
        alpha=alpha,
        per_client=per_client,
        eligible_ids=eligible_ids,
        pending_ids=pending,
        eval_incomplete_ids=[],
    )

    # Silhouette
    from sklearn.metrics import silhouette_score
    n_labels = len(set(labels))
    sil = float(silhouette_score(scaled, labels)) if n_labels > 1 and n_labels < len(labels) else 0.0

    # ARI vs device family (Regime A only)
    ari = float("nan")
    if regime == Regime.A:
        family_labels = [DEVICE_FAMILY_MAP.get(cid, cid) for cid in eligible_ids]
        unique_families = sorted(set(family_labels))
        family_int = [unique_families.index(f) for f in family_labels]
        ari = float(adjusted_rand_score(family_int, labels))

    return (
        float(evaluation.cv_fpr),
        float(evaluation.mean_fpr),
        float(evaluation.coverage_ratio),
        sil,
        ari,
        evaluation.eligible_count,
    )


def _canonical_b4_cv_fpr(
    cell_dir: Path,
    regime: Regime,
    seed: int,
    alpha_f: float | None,
    cfg: DatpConfig,
) -> float:
    """Compute canonical B4 CV(FPR) using derive_threshold."""
    cal_errors = load_cal_errors(cell_dir)
    score_provider = ScoreProvider(cell_dir)

    b1_result = derive_threshold(
        Baseline.B1, cal_errors, n_min=cfg.threshold.n_min, q=cfg.threshold.q,
        tau_global=0.0, regime=regime, threshold_cfg=cfg.threshold,
    )
    tau_global = float(b1_result.tau_global)

    b4_result = derive_threshold(
        Baseline.B4, cal_errors, n_min=cfg.threshold.n_min, q=cfg.threshold.q,
        tau_global=tau_global, regime=regime, threshold_cfg=cfg.threshold,
    )

    per_client: list[ClientMetrics] = []
    for ct in b4_result.client_thresholds:
        benign, attack = score_provider.load_test_scores(ct.client_id)
        per_client.append(compute_client_metrics(ct.client_id, benign, attack, ct.threshold))

    eligible_ids = [ct.client_id for ct in b4_result.client_thresholds if not ct.calibration_pending]
    pending_ids = [ct.client_id for ct in b4_result.client_thresholds if ct.calibration_pending]

    evaluation = build_evaluation_result(
        baseline=Baseline.B4,
        regime=regime,
        seed=seed,
        alpha=alpha_f,
        per_client=per_client,
        eligible_ids=eligible_ids,
        pending_ids=pending_ids,
        eval_incomplete_ids=[],
    )
    return float(evaluation.cv_fpr)


def run_b4_ablation(
    base_dir: Path,
    *,
    config: DatpConfig | None = None,
    write_outputs: bool = False,
) -> B4AblationResult:
    cfg = config or compose_config(regime=Regime.A, baseline=Baseline.B1, seed=0)
    q = cfg.threshold.q
    n_min = cfg.threshold.n_min
    random_state = cfg.threshold.b4_random_state
    k_regime_a = cfg.threshold.b4_k_regime_a

    resolved = base_dir.resolve()
    safe_cells = load_verified_safe_cells(resolved)

    full_max_dev = 0.0
    rows: list[B4AblationRow] = []

    for cell in safe_cells:
        cell_dir = Path(cell["cell_dir"])
        regime = Regime(cell["regime"])
        seed = int(cell["seed"])
        alpha_str: str | None = cell.get("alpha")
        alpha_f = parse_alpha_str(alpha_str)

        cal_errors = load_cal_errors(cell_dir)
        score_provider = ScoreProvider(cell_dir)

        eligible, pending = identify_eligible(cal_errors, n_min=n_min)

        # tau_global for fallback
        b1_result = derive_threshold(
            Baseline.B1, cal_errors, n_min=n_min, q=q, tau_global=0.0,
            regime=regime, threshold_cfg=cfg.threshold,
        )
        tau_global = float(b1_result.tau_global)

        # Determine K for this regime
        if regime == Regime.A:
            k_val = k_regime_a
        else:
            # For B/C, use silhouette — but for ablation we simplify to a fixed K heuristic
            k_val = max(2, min(5, len(eligible) - 1))

        canonical_cv = _canonical_b4_cv_fpr(cell_dir, regime, seed, alpha_f, cfg)

        for indices, label in _SUBSET_LABELS.items():
            if len(eligible) < 2:
                continue

            fps = _subset_fingerprint(cal_errors, eligible, q, indices)
            cv_fpr, mean_fpr, cov_ratio, sil, ari, elig_count = _cluster_and_evaluate(
                fps, eligible, pending, tau_global, random_state, k_val,
                score_provider, regime, seed, alpha_f,
            )

            if indices == _ALL_FEATURES:
                full_max_dev = max(full_max_dev, abs(cv_fpr - canonical_cv))

            rows.append(B4AblationRow(
                subset=label,
                n_features=len(indices),
                regime=regime,
                seed=seed,
                alpha=alpha_str,
                k=k_val,
                silhouette=sil,
                ari_vs_family=ari,
                cv_fpr=cv_fpr,
                mean_fpr=mean_fpr,
                coverage_ratio=cov_ratio,
                eligible_count=elig_count,
            ))

    reproduces = full_max_dev <= SCALAR_METRIC_TOLERANCE

    result = B4AblationResult(
        rows=rows,
        verified_safe_cell_count=len(safe_cells),
        full_feature_reproduces_b4=reproduces,
        full_vs_canonical_max_deviation=full_max_dev,
    )

    if write_outputs:
        _write_outputs(result, resolved)

    return result


def _write_outputs(result: B4AblationResult, base_dir: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    analysis_dir = base_dir / ANALYSIS_DIR
    analysis_dir.mkdir(parents=True, exist_ok=True)

    # CSV
    fieldnames = [
        "subset", "n_features", "regime", "seed", "alpha", "k", "silhouette",
        "ari_vs_family", "cv_fpr", "mean_fpr", "coverage_ratio", "eligible_count",
    ]
    csv_path = analysis_dir / B4_ABLATION_TABLE_CSV
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in result.rows:
            writer.writerow({
                "subset": row.subset,
                "n_features": row.n_features,
                "regime": row.regime.value,
                "seed": row.seed,
                "alpha": row.alpha,
                "k": row.k,
                "silhouette": row.silhouette,
                "ari_vs_family": row.ari_vs_family,
                "cv_fpr": row.cv_fpr,
                "mean_fpr": row.mean_fpr,
                "coverage_ratio": row.coverage_ratio,
                "eligible_count": row.eligible_count,
            })

    # Show ARI bar chart across subsets.
    regime_a_rows = [r for r in result.rows if r.regime == Regime.A and r.alpha is None]
    if regime_a_rows:
        # Aggregate ARI across seeds per subset
        subset_aris: dict[str, list[float]] = {}
        for row in regime_a_rows:
            if not math.isnan(row.ari_vs_family):
                subset_aris.setdefault(row.subset, []).append(row.ari_vs_family)

        if subset_aris:
            fig, ax = plt.subplots(figsize=(12, 5))
            labels = sorted(subset_aris.keys(), key=lambda s: len(s.split("+")), reverse=True)
            means = [float(np.mean(subset_aris[label])) for label in labels]
            ax.barh(labels, means, alpha=0.8)
            ax.set_xlabel("Adjusted Rand Index vs Device Family")
            ax.set_title("B4 Feature Ablation — Cluster/Family Contingency (Regime A)")
            ax.axvline(0.0, color="gray", linestyle="--", alpha=0.4)
            ax.grid(True, alpha=0.3, axis="x")
            fig.tight_layout()
            fig.savefig(analysis_dir / B4_ABLATION_CONTINGENCY_PNG, dpi=150)
            plt.close(fig)
