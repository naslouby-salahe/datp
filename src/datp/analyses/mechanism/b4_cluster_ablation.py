"""GB-06 B4 feature ablation.

Evaluates B4 fingerprint subsets and full 4-feature fingerprint
[mean, std, skew, p95]. Computes clustering per subset, evaluates CV(FPR),
and produces contingency of cluster assignment vs. device family (Regime A).

The full 4-feature fingerprint MUST reproduce canonical B4 results.

Outputs (when write_outputs=True):
  <base_dir>/analysis/b4_ablation_table.csv
  <base_dir>/analysis/b4_ablation_contingency.png
"""

from __future__ import annotations

import math
from collections import defaultdict
from itertools import combinations
from pathlib import Path

import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.preprocessing import StandardScaler

from datp.analyses.cells import (
    iter_analysis_cell_contexts,
    load_verified_safe_cells,
)
from datp.analyses.evaluation import (
    derive_tau_global,
    evaluate_threshold_result,
)
from datp.analyses.io import ensure_analysis_dir, write_analysis_csv
from datp.analyses.plotting import saved_figure
from datp.analyses.runners import analysis_runner
from datp.core.types import AnalysisRowBase, FrozenModel
from datp.validation.constants import SCALAR_METRIC_TOLERANCE
from datp.thresholding.eligibility import identify_eligible
from datp.thresholding.thresholds import arithmetic_mean_threshold, derive_threshold
from datp.thresholding.strategies.b4_cluster import compute_fingerprints
from datp.core.types import ClientThreshold
from datp.config.models import DatpConfig, ThresholdConfig
from datp.core.enums import Baseline, Regime
from datp.data.datasets.nbaiot.spec import DEVICE_FAMILY_MAP
from datp.evaluation.metrics import (
    EvaluationResult,
    evaluate_baseline,
)
from datp.scoring.loading import ScoreProvider

from datp.analyses.constants import B4_ABLATION_CONTINGENCY_PNG, B4_ABLATION_TABLE_CSV
from datp.core.enums import B4_FINGERPRINT_FEATURES

_ALL_FEATURES: tuple[int, ...] = tuple(range(len(B4_FINGERPRINT_FEATURES)))

_SUBSET_LABELS: dict[tuple[int, ...], str] = {
    indices: (
        "full"
        if len(indices) == len(B4_FINGERPRINT_FEATURES)
        else "+".join(B4_FINGERPRINT_FEATURES[i] for i in indices)
    )
    for size in range(1, len(B4_FINGERPRINT_FEATURES) + 1)
    for indices in combinations(range(len(B4_FINGERPRINT_FEATURES)), size)
}


class B4AblationRow(AnalysisRowBase):
    subset: str
    n_features: int
    k: int
    silhouette: float
    ari_vs_family: (
        float  # Adjusted Rand Index vs device family (Regime A only; NaN otherwise)
    )
    cv_fpr: float
    mean_fpr: float
    coverage_ratio: float
    eligible_count: int


class B4AblationResult(FrozenModel):
    rows: list[B4AblationRow]
    verified_safe_cell_count: int
    full_feature_reproduces_b4: bool
    full_vs_canonical_max_deviation: float


def _slice_fingerprints(
    full_fps: dict[str, np.ndarray],
    indices: tuple[int, ...],
) -> dict[str, np.ndarray]:
    idx = np.array(indices)
    return {cid: fp[idx] for cid, fp in full_fps.items()}


def _build_sorted_matrix(
    fingerprints: dict[str, np.ndarray],
    eligible: list[str],
) -> tuple[list[str], np.ndarray]:
    eligible_ids = sorted(eligible)
    matrix = np.array([fingerprints[cid] for cid in eligible_ids])
    return eligible_ids, matrix


def _kmeans_labels(
    matrix: np.ndarray,
    k: int,
    random_state: int,
) -> tuple[np.ndarray, np.ndarray]:
    scaled = StandardScaler().fit_transform(matrix)
    km = KMeans(n_clusters=k, random_state=random_state, n_init=10)  # pyright: ignore[reportArgumentType]  # sklearn stub types n_init as str-only
    labels = km.fit_predict(scaled)
    return scaled, labels


def _per_client_cluster_thresholds(
    fingerprints: dict[str, np.ndarray],
    eligible_ids: list[str],
    labels: np.ndarray,
) -> dict[str, float]:
    cluster_taus: dict[int, list[float]] = defaultdict(list)
    for i, cid in enumerate(eligible_ids):
        cluster_taus[int(labels[i])].append(float(fingerprints[cid][-1]))
    tau_per_cluster = {c: arithmetic_mean_threshold(t) for c, t in cluster_taus.items()}
    return {cid: tau_per_cluster[int(labels[i])] for i, cid in enumerate(eligible_ids)}


def _evaluate_clusters(
    score_provider: ScoreProvider,
    eligible_map: dict[str, float],
    eligible_ids: list[str],
    pending: list[str],
    tau_global: float,
    regime: Regime,
    seed: int,
    alpha: float | None,
) -> EvaluationResult:
    client_thresholds = []
    for cid in eligible_ids + pending:
        tau = eligible_map.get(cid, tau_global)
        client_thresholds.append(
            ClientThreshold(
                client_id=cid,
                threshold=tau,
                calibration_pending=cid not in eligible_map,
                strategy=Baseline.B4,
            )
        )
    return evaluate_baseline(
        client_thresholds=client_thresholds,
        score_root=Path(""),
        regime=regime,
        seed=seed,
        alpha=alpha,
        score_provider=score_provider,
    )


def _silhouette(scaled: np.ndarray, labels: np.ndarray, random_state: int) -> float:
    n_labels = len(set(labels))
    if 1 < n_labels < len(labels):
        return float(silhouette_score(scaled, labels, random_state=random_state))
    return 0.0


def _ari_vs_family(
    eligible_ids: list[str],
    labels: np.ndarray,
    regime: Regime,
) -> float:
    if regime != Regime.A:
        return float("nan")
    family_labels = [DEVICE_FAMILY_MAP.get(cid, cid) for cid in eligible_ids]
    unique_families = sorted(set(family_labels))
    family_int = [unique_families.index(f) for f in family_labels]
    return float(adjusted_rand_score(family_int, labels))


def _canonical_b4_cv_fpr(
    cal_errors: dict[str, np.ndarray],
    score_provider: ScoreProvider,
    tau_global: float,
    regime: Regime,
    seed: int,
    alpha_value: float | None,
    threshold_cfg: ThresholdConfig,
) -> float:
    """Canonical B4 CV(FPR) via derive_threshold over already-loaded cell artifacts."""
    b4_result = derive_threshold(
        Baseline.B4,
        cal_errors,
        n_min=threshold_cfg.n_min,
        q=threshold_cfg.q,
        tau_global=tau_global,
        regime=regime,
        threshold_cfg=threshold_cfg,
        seed=seed,
        alpha=alpha_value,
    )
    evaluation = evaluate_threshold_result(
        b4_result, score_provider, regime, seed, alpha_value
    )
    return float(evaluation.cv_fpr)


def _ablation_row(
    *,
    indices: tuple[int, ...],
    label: str,
    full_fps: dict[str, np.ndarray],
    eligible: list[str],
    pending: list[str],
    tau_global: float,
    random_state: int,
    k: int,
    score_provider: ScoreProvider,
    regime: Regime,
    seed: int,
    alpha_label: str | None,
    alpha_value: float | None,
) -> tuple[B4AblationRow, float]:
    sliced = _slice_fingerprints(full_fps, indices)
    eligible_ids, matrix = _build_sorted_matrix(sliced, eligible)
    scaled, labels = _kmeans_labels(matrix, k, random_state)
    eligible_map = _per_client_cluster_thresholds(sliced, eligible_ids, labels)
    evaluation = _evaluate_clusters(
        score_provider,
        eligible_map,
        eligible_ids,
        pending,
        tau_global,
        regime,
        seed,
        alpha_value,
    )
    sil = _silhouette(scaled, labels, random_state)
    ari = _ari_vs_family(eligible_ids, labels, regime)
    cv_fpr = float(evaluation.cv_fpr)
    row = B4AblationRow(
        subset=label,
        n_features=len(indices),
        regime=regime,
        seed=seed,
        alpha=alpha_label,
        k=k,
        silhouette=sil,
        ari_vs_family=ari,
        cv_fpr=cv_fpr,
        mean_fpr=float(evaluation.mean_fpr),
        coverage_ratio=float(evaluation.coverage_ratio),
        eligible_count=evaluation.eligible_count,
    )
    return row, cv_fpr


def _k_for_regime(regime: Regime, eligible: list[str], k_regime_a: int) -> int:
    if regime == Regime.A:
        return k_regime_a
    # For B/C, ablation uses a fixed K heuristic to avoid re-running silhouette sweeps.
    return max(2, min(5, len(eligible) - 1))


def _write_outputs(result: B4AblationResult, base_dir: Path) -> None:
    write_analysis_csv(base_dir, B4_ABLATION_TABLE_CSV, result.rows, B4AblationRow)
    _write_contingency_plot(
        result, ensure_analysis_dir(base_dir) / B4_ABLATION_CONTINGENCY_PNG
    )


@analysis_runner(writer_func=_write_outputs)
def run_b4_ablation(
    base_dir: Path,
    *,
    config: DatpConfig,
) -> B4AblationResult:
    random_state = config.threshold.b4_random_state
    k_regime_a = config.threshold.b4_k_regime_a

    safe_cells = load_verified_safe_cells(base_dir)

    full_max_dev = 0.0
    rows: list[B4AblationRow] = []

    for ctx in iter_analysis_cell_contexts(safe_cells):
        eligible, pending = identify_eligible(
            ctx.calibration_errors, n_min=config.threshold.n_min
        )
        if len(eligible) < 2:
            continue

        tau_global, _ = derive_tau_global(
            ctx.calibration_errors, regime=ctx.regime, threshold_cfg=config.threshold
        )

        k_val = _k_for_regime(ctx.regime, eligible, k_regime_a)

        canonical_cv = _canonical_b4_cv_fpr(
            ctx.calibration_errors,
            ctx.score_provider,
            tau_global,
            ctx.regime,
            ctx.seed,
            ctx.alpha_value,
            config.threshold,
        )

        full_fps = compute_fingerprints(
            ctx.calibration_errors, eligible, q=config.threshold.q
        )

        for indices, label in _SUBSET_LABELS.items():
            row, cv_fpr = _ablation_row(
                indices=indices,
                label=label,
                full_fps=full_fps,
                eligible=eligible,
                pending=pending,
                tau_global=tau_global,
                random_state=random_state,
                k=k_val,
                score_provider=ctx.score_provider,
                regime=ctx.regime,
                seed=ctx.seed,
                alpha_label=ctx.alpha_label,
                alpha_value=ctx.alpha_value,
            )
            if indices == _ALL_FEATURES:
                full_max_dev = max(full_max_dev, abs(cv_fpr - canonical_cv))
            rows.append(row)

    reproduces = full_max_dev <= SCALAR_METRIC_TOLERANCE

    return B4AblationResult(
        rows=rows,
        verified_safe_cell_count=len(safe_cells),
        full_feature_reproduces_b4=reproduces,
        full_vs_canonical_max_deviation=full_max_dev,
    )


def _write_contingency_plot(result: B4AblationResult, path: Path) -> None:
    regime_a_rows = [r for r in result.rows if r.regime == Regime.A and r.alpha is None]
    if not regime_a_rows:
        return

    subset_aris: dict[str, list[float]] = {}
    for row in regime_a_rows:
        if not math.isnan(row.ari_vs_family):
            subset_aris.setdefault(row.subset, []).append(row.ari_vs_family)
    if not subset_aris:
        return

    labels = sorted(subset_aris.keys(), key=lambda s: len(s.split("+")), reverse=True)
    means = [float(np.mean(subset_aris[label])) for label in labels]
    with saved_figure(path, figsize=(12, 5)) as (fig, ax):
        ax.barh(labels, means, alpha=0.8)
        ax.set_xlabel("Adjusted Rand Index vs Device Family")
        ax.set_title("B4 Feature Ablation - Cluster/Family Contingency (Regime A)")
        ax.axvline(0.0, color="gray", linestyle="--", alpha=0.4)
        ax.grid(True, alpha=0.3, axis="x")
