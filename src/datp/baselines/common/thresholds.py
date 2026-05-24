from __future__ import annotations

import math
from typing import TYPE_CHECKING

import numpy as np

from datp.baselines.common.types import ThresholdResult
from datp.core.enums import (
    Baseline,
    Regime,
)
from datp.core.errors import fmt
from datp.data.datasets.nbaiot.spec import DEVICE_FAMILY_MAP

if TYPE_CHECKING:
    from datp.config.models import ThresholdConfig

_MODULE = "baselines.thresholds"


def percentile_threshold(errors: np.ndarray, q: float) -> float:
    """Raises ValueError if errors is empty."""
    if errors.size == 0:
        raise ValueError(
            fmt(_MODULE, "Cannot compute percentile", "non-empty array", "empty array")
        )
    return float(np.percentile(errors, q * 100))


def arithmetic_mean_threshold(tau_list: list[float] | np.ndarray) -> float:
    """Simple arithmetic mean (1/K)×Στᵢ; never weighted by sample size (weighting would introduce a second confound).

    Raises ValueError if tau_list is empty.
    """
    arr = np.asarray(tau_list, dtype=np.float64)
    if arr.size == 0:
        raise ValueError(
            fmt(_MODULE, "Cannot compute mean", "non-empty threshold list", "empty list")
        )
    return float(arr.mean())


def conformal_threshold(errors: np.ndarray, alpha: float) -> float:
    """Per‑client split‑conformal threshold.

    k = ceil((n + 1) * (1 − alpha))
    τ = sorted_errors[k − 1]  (0‑indexed)

    If k > n (insufficient samples for the requested alpha), returns max(errors)
    as a conservative fallback.  Raises ValueError if errors is empty.

    Primary anchor: Lu et al. ICML 2023; co‑anchor: Humbert et al. ICML 2023.
    """
    if errors.size == 0:
        raise ValueError(
            fmt(_MODULE, "Cannot compute conformal threshold", "non-empty array", "empty array")
        )
    n = errors.size
    k = int(math.ceil((n + 1) * (1.0 - alpha)))
    if k > n:
        return float(np.max(errors))
    sorted_errors = np.sort(errors)
    return float(sorted_errors[k - 1])


def derive_threshold(
    baseline: Baseline,
    client_errors: dict[str, np.ndarray],
    n_min: int,
    q: float,
    tau_global: float,
    regime: Regime,
    *,
    threshold_cfg: "ThresholdConfig",
) -> ThresholdResult:
    # Local imports avoid circular dependency: b1–b4 depend on arithmetic_mean_threshold.
    from datp.baselines.main import b1 as b1_mod
    from datp.baselines.main import b2 as b2_mod
    from datp.baselines.main import b3 as b3_mod
    from datp.baselines.main import b4 as b4_mod

    if baseline == Baseline.B1:
        return b1_mod.compute(client_errors, n_min, q=q)
    if baseline == Baseline.B2:
        return b2_mod.compute(client_errors, n_min, tau_global, q=q)
    if baseline == Baseline.B3:
        family_map = {cid: DEVICE_FAMILY_MAP[cid] for cid in client_errors}
        return b3_mod.compute(
            client_errors, n_min, tau_global, family_map, q=q, regime=regime,
        )
    if baseline == Baseline.B4:
        mode = threshold_cfg.b4_regime_a_mode
        k_for_a = (
            0  # silhouette selection
            if regime == Regime.A and mode == "silhouette"
            else threshold_cfg.b4_k_regime_a
        )
        return b4_mod.compute(
            client_errors, n_min, tau_global, regime,
            q=q,
            random_state=threshold_cfg.b4_random_state,
            k_regime_a=k_for_a,
            k_candidates=threshold_cfg.b4_k_candidates,
            n_init=threshold_cfg.b4_n_init,
        )

    raise ValueError(
        fmt("thresholds", "Unknown baseline for threshold derivation", "b1/b2/b3/b4", repr(baseline))
    )
