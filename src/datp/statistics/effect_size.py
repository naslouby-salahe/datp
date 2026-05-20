from __future__ import annotations

import attrs
import numpy as np

from datp.statistics.constants import (
    CLIFFS_DELTA_MEDIUM,
    CLIFFS_DELTA_NEGLIGIBLE,
    CLIFFS_DELTA_SMALL,
)
from datp.statistics.enums import EffectMagnitude


@attrs.define(frozen=True, slots=True)
class CliffsDeltaResult:
    delta: float
    magnitude: EffectMagnitude


def cliffs_delta(x: np.ndarray, y: np.ndarray) -> CliffsDeltaResult:
    """Cliff's delta: (count(x>y) - count(x<y)) / (n_x * n_y)."""
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)

    n_x = len(x)
    n_y = len(y)

    more = 0
    less = 0
    for xi in x:
        for yj in y:
            if xi > yj:
                more += 1
            elif xi < yj:
                less += 1

    delta = (more - less) / (n_x * n_y)

    abs_d = abs(delta)
    if abs_d < CLIFFS_DELTA_NEGLIGIBLE:
        magnitude = EffectMagnitude.NEGLIGIBLE
    elif abs_d < CLIFFS_DELTA_SMALL:
        magnitude = EffectMagnitude.SMALL
    elif abs_d < CLIFFS_DELTA_MEDIUM:
        magnitude = EffectMagnitude.MEDIUM
    else:
        magnitude = EffectMagnitude.LARGE

    return CliffsDeltaResult(delta=float(delta), magnitude=magnitude)
