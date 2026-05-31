"""Single canonical CV implementation; any parallel ddof-variant is a reproducibility bug."""

from __future__ import annotations

import math

import numpy as np


def cv(arr: np.ndarray, ddof: int = 1) -> float:
    """Coefficient of variation: ``std(arr, ddof=ddof) / mean(arr)``.

    Uses sample standard deviation (ddof=1) by default.
    Returns ``math.nan`` if mean is zero or fewer than 2 elements.
    """
    a = np.asarray(arr, dtype=np.float64)
    if a.size < 2:
        return math.nan
    m = float(a.mean())
    if abs(m) < 1e-15:
        return math.nan
    return float(a.std(ddof=ddof) / m)
