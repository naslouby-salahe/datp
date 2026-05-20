"""B4 — Cluster-mean threshold: k-means on eligible [mean, std, skew, p95] fingerprints; Calibration-Pending clients never enter k-means and receive τ_global."""

from __future__ import annotations

from collections import defaultdict

import numpy as np
from scipy import stats as sp_stats
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

from datp.baselines.common.eligibility import (
    build_threshold_result,
    compute_client_thresholds,
    identify_eligible,
)
from datp.baselines.common.thresholds import arithmetic_mean_threshold
from datp.baselines.common.types import B4ClusterInfo, B4Metadata, ThresholdResult
from datp.core.enums import (
    Baseline,
    Regime,
)
from datp.core.errors import fmt
from datp.core.logging import get_logger

logger = get_logger(__name__)

_MODULE = "baselines.b4"
_MIN_CLUSTER_ELIGIBLE = 2


def compute_fingerprints(
    client_errors: dict[str, np.ndarray],
    eligible: list[str],
    *,
    q: float,
) -> dict[str, np.ndarray]:
    # Calibration-Pending clients must not appear in eligible.
    # Constant/near-constant arrays produce skew=0.0 rather than NaN; single-element arrays also yield std=0.0.
    fingerprints: dict[str, np.ndarray] = {}
    for cid in eligible:
        e = np.asarray(client_errors[cid], dtype=np.float64)
        mean_e = float(np.mean(e))
        # ddof=1 is NaN for n==1; clamp to 0.0
        std_e = float(np.std(e, ddof=1)) if e.size >= 2 else 0.0
        # scipy skew is NaN for constant arrays; map to 0.0
        raw_skew = float(sp_stats.skew(e)) if e.size >= 2 else 0.0
        skew_e = 0.0 if (not np.isfinite(raw_skew)) else raw_skew
        p95_e = float(np.percentile(e, q * 100))
        fingerprints[cid] = np.array([mean_e, std_e, skew_e, p95_e], dtype=np.float64)
    return fingerprints


def _silhouette_scores_by_k(
    x_scaled: np.ndarray,
    k_candidates: list[int],
    random_state: int,
    n_init: int,
) -> dict[str, float]:
    # Each k is fitted once; use this as the single source for both audit metadata and best-k selection.
    scores: dict[str, float] = {}
    for k in k_candidates:
        if k < 2 or k >= x_scaled.shape[0]:
            continue
        km = KMeans(n_clusters=k, random_state=random_state, n_init=int(n_init))  # type: ignore[arg-type]
        labels = km.fit_predict(x_scaled)
        n_labels = len(set(labels))
        if n_labels < 2 or n_labels >= x_scaled.shape[0]:
            continue
        score = float(silhouette_score(x_scaled, labels))
        if not np.isfinite(score):
            continue
        logger.info("B4 silhouette", k=k, score=score)
        scores[str(k)] = score
    return scores


def _select_best_k(scores: dict[str, float]) -> tuple[int, float]:
    # Does NOT refit KMeans; call _silhouette_scores_by_k first.
    if not scores:
        raise ValueError(
            fmt(_MODULE, "No valid silhouette scores", "at least one valid k in [2, K_elig - 1]", "none")
        )
    best_k_str = max(scores, key=lambda k: scores[k])
    return int(best_k_str), scores[best_k_str]


def _validate_k_candidates(k_candidates: list[int]) -> list[int]:
    if not k_candidates:
        raise ValueError(fmt(_MODULE, "k_candidates is empty", "at least one integer k", "empty list"))
    invalid = [k for k in k_candidates if not isinstance(k, int) or k < 2]
    if invalid:
        raise ValueError(fmt(_MODULE, "Invalid k_candidates", "integers >= 2", str(invalid)))
    return sorted(set(k_candidates))


def _validate_fingerprint_matrix(fingerprint_matrix: np.ndarray) -> None:
    if not np.isfinite(fingerprint_matrix).all():
        raise ValueError(fmt(_MODULE, "Invalid fingerprint values", "finite mean/std/skew/p95", "NaN or inf"))
    unique_rows = np.unique(fingerprint_matrix, axis=0)
    if unique_rows.shape[0] < 2:
        raise ValueError(
            fmt(_MODULE, "Degenerate fingerprints — all eligible clients have identical fingerprints",
                "at least 2 distinct eligible fingerprints", str(unique_rows.shape[0]))
        )


def compute(
    client_errors: dict[str, np.ndarray],
    n_min: int,
    tau_global: float,
    regime: Regime,
    q: float,
    random_state: int,
    k_regime_a: int,
    k_candidates: list[int],
    n_init: int,
) -> ThresholdResult:
    # Regime A: K=k_regime_a fixed; Regime B/C: K selected by silhouette.
    # Calibration-Pending clients receive tau_global unconditionally.
    eligible, pending = identify_eligible(client_errors, n_min=n_min)
    valid_k_candidates = _validate_k_candidates(k_candidates)

    if len(eligible) < _MIN_CLUSTER_ELIGIBLE:
        raise ValueError(
            fmt(_MODULE, "Cannot cluster",
                f"at least {_MIN_CLUSTER_ELIGIBLE} eligible clients", str(len(eligible)))
        )

    client_taus = compute_client_thresholds(client_errors, eligible, q=q)

    fingerprints = compute_fingerprints(client_errors, eligible, q=q)

    eligible_ids = sorted(eligible)
    fingerprint_matrix = np.array([fingerprints[cid] for cid in eligible_ids])
    _validate_fingerprint_matrix(fingerprint_matrix)

    scaler = StandardScaler()
    fingerprint_scaled = scaler.fit_transform(fingerprint_matrix)
    if not np.isfinite(fingerprint_scaled).all():
        raise ValueError(fmt(_MODULE, "Invalid scaled fingerprints", "finite values after scaling", "NaN or inf"))
    # Fit KMeans once per k candidate; reuse scores for audit metadata and best-k selection.
    silhouette_scores = _silhouette_scores_by_k(
        fingerprint_scaled,
        k_candidates=valid_k_candidates,
        random_state=random_state,
        n_init=n_init,
    )

    if regime == Regime.A:
        if k_regime_a <= 0:
            k, silhouette = _select_best_k(silhouette_scores)
        else:
            if k_regime_a >= len(eligible):
                raise ValueError(
                    fmt(_MODULE, "Invalid Regime A k", f"2 <= k < eligible_count ({len(eligible)})", str(k_regime_a))
                )
            k = k_regime_a
            silhouette = silhouette_scores.get(str(k))
            if silhouette is None:
                raise ValueError(
                    fmt(_MODULE, "Regime A k has no valid silhouette score", "non-degenerate clustering", str(k))
                )
    elif regime in (Regime.B, Regime.C):
        k, silhouette = _select_best_k(silhouette_scores)
        logger.info(
            "B4 selected K",
            k=k, silhouette=silhouette, regime=regime,
        )
    else:
        raise ValueError(
            fmt(_MODULE, "Invalid regime", "'A', 'B', or 'C'", repr(regime))
        )

    km = KMeans(n_clusters=k, random_state=random_state, n_init=int(n_init))  # type: ignore[arg-type]
    labels = km.fit_predict(fingerprint_scaled)
    final_silhouette = (
        float(silhouette_score(fingerprint_scaled, labels))
        if len(set(labels)) > 1
        else 0.0
    )

    client_cluster: dict[str, int] = dict(zip(eligible_ids, labels.astype(int), strict=True))

    cluster_taus_map: dict[int, list[float]] = defaultdict(list)
    for cid in eligible_ids:
        c = client_cluster[cid]
        cluster_taus_map[c].append(client_taus[cid])

    tau_per_cluster: dict[int, float] = {}
    for c, taus in cluster_taus_map.items():
        tau_per_cluster[c] = arithmetic_mean_threshold(taus)

    eligible_map = {cid: tau_per_cluster[client_cluster[cid]] for cid in eligible_ids}

    cluster_info: dict[str, B4ClusterInfo] = {}
    for c in sorted(tau_per_cluster.keys()):
        members = [cid for cid in eligible_ids if client_cluster[cid] == c]
        cluster_info[f"cluster_{c}"] = B4ClusterInfo(
            tau_cluster=tau_per_cluster[c],
            members=members,
        )

    logger.info(
        "B4 clustering complete",
        k=k,
        cluster_sizes=[len(cluster_taus_map[c]) for c in sorted(cluster_taus_map.keys())],
        silhouette=final_silhouette,
    )

    return build_threshold_result(
        strategy=Baseline.B4,
        tau_global=tau_global,
        eligible_thresholds=eligible_map,
        pending_clients=pending,
        b3_metadata=None,
        b4_metadata=B4Metadata(
            k=k,
            cluster_info=cluster_info,
            silhouette=final_silhouette,
            silhouette_scores=silhouette_scores,
            fingerprints={cid: fingerprints[cid].tolist() for cid in eligible_ids},
        ),
    )

