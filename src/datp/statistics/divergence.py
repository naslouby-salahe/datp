from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from datp.statistics.constants import (
    EXTREME_PERCENTILE,
    JS_BIN_EPSILON,
    JS_LAPLACE_SMOOTHING,
)


@dataclass(frozen=True, slots=True)
class JSSummary:
    n_compared: int
    n_pairs: int
    n_bins: int
    mean: float | None
    std: float | None
    p50: float | None
    p95: float | None
    max: float | None


def _histogram_distribution(arr: np.ndarray, bin_edges: np.ndarray) -> np.ndarray:
    counts, _ = np.histogram(arr, bins=bin_edges)
    smoothed = counts.astype(np.float64) + JS_LAPLACE_SMOOTHING
    return smoothed / smoothed.sum()


def pairwise_js_divergence(probs: list[np.ndarray]) -> np.ndarray:
    """JSD = 0.5·KL(P‖M) + 0.5·KL(Q‖M) where M = 0.5·(P+Q); returns 1-D array of n*(n-1)/2 values."""
    n = len(probs)
    out: list[float] = []
    for i in range(n):
        for j in range(i + 1, n):
            p = probs[i]
            q = probs[j]
            m = 0.5 * (p + q)
            with np.errstate(divide="ignore", invalid="ignore"):
                kl_pm = float(np.sum(np.where(p > 0, p * np.log(p / m), 0.0)))
                kl_qm = float(np.sum(np.where(q > 0, q * np.log(q / m), 0.0)))
            out.append(0.5 * (kl_pm + kl_qm))
    return np.asarray(out, dtype=np.float64)


def _js_array_to_summary(js: np.ndarray, n_compared: int, n_bins: int) -> JSSummary:
    return JSSummary(
        n_compared=n_compared,
        n_pairs=int(js.size),
        n_bins=n_bins,
        mean=float(js.mean()),
        std=float(js.std(ddof=1)) if js.size > 1 else 0.0,
        p50=float(np.percentile(js, 50)),
        p95=float(np.percentile(js, EXTREME_PERCENTILE)),
        max=float(js.max()),
    )


def pairwise_js_summary(
    arrays: list[np.ndarray],
    *,
    n_bins: int,
) -> JSSummary:
    """Returns None stats when fewer than 2 non-empty arrays are provided."""
    non_empty = [arr for arr in arrays if arr.size > 0]
    n = len(non_empty)
    if n < 2:
        return JSSummary(
            n_compared=n,
            n_pairs=0,
            n_bins=n_bins,
            mean=None,
            std=None,
            p50=None,
            p95=None,
            max=None,
        )

    pooled = np.concatenate(non_empty)
    upper = float(np.percentile(pooled, 99.0))
    lower = float(np.min(pooled))
    if upper <= lower:
        upper = lower + JS_BIN_EPSILON
    bin_edges = np.linspace(lower, upper, n_bins + 1)
    probs = [_histogram_distribution(arr, bin_edges) for arr in non_empty]
    js = pairwise_js_divergence(probs)
    return _js_array_to_summary(js, n, n_bins)


def pairwise_js_from_distributions(
    distributions: list[np.ndarray],
) -> JSSummary:
    """Pairwise JSD from pre-computed probability vectors; returns None stats for fewer than 2."""
    n = len(distributions)
    n_bins = distributions[0].shape[0] if n > 0 else 0
    if n < 2:
        return JSSummary(
            n_compared=n,
            n_pairs=0,
            n_bins=n_bins,
            mean=None,
            std=None,
            p50=None,
            p95=None,
            max=None,
        )

    js = pairwise_js_divergence(distributions)
    return _js_array_to_summary(js, n, n_bins)
