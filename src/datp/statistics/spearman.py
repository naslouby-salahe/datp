"""Spearman ρ between JS divergence and per-client FPR; gates mechanism wording on ρ > 0 and p < 0.05."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy.stats import spearmanr as _scipy_spearmanr


@dataclass(frozen=True, slots=True)
class SpearmanResult:
    rho: float
    p_value: float
    mechanism_wording: str
    n: int


def spearman_correlation(
    divergences: np.ndarray,
    fpr_values: np.ndarray,
    significance_alpha: float,
) -> SpearmanResult:
    divergences = np.asarray(divergences, dtype=np.float64)
    fpr_values = np.asarray(fpr_values, dtype=np.float64)

    result: Any = _scipy_spearmanr(divergences, fpr_values)
    rho = float(result.statistic)
    p = float(result.pvalue)

    if rho > 0 and p < significance_alpha:
        mechanism_wording = "EMPIRICAL"
    else:
        mechanism_wording = "HYPOTHESIS"

    return SpearmanResult(
        rho=rho,
        p_value=p,
        mechanism_wording=mechanism_wording,
        n=len(divergences),
    )
