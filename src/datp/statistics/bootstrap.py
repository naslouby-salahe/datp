from __future__ import annotations

import attrs
import numpy as np


@attrs.define(frozen=True, slots=True)
class BootstrapResult:
    ci_lower: float
    ci_upper: float
    mean_delta: float
    excludes_zero: bool
    n_seeds: int
    n_bootstrap: int


def bootstrap_ci(
    deltas: np.ndarray,
    n_bootstrap: int,
    ci: float,
    seed: int,
) -> BootstrapResult:
    """Percentile-based bootstrap CI on per-seed deltas (e.g. CV(FPR)[B1] − CV(FPR)[B2])."""
    deltas = np.asarray(deltas, dtype=np.float64)
    if deltas.size == 0:
        raise ValueError("bootstrap_ci: deltas array is empty")
    if not np.isfinite(deltas).all():
        bad_count = int(np.sum(~np.isfinite(deltas)))
        raise ValueError(
            f"bootstrap_ci: deltas contains {bad_count} non-finite value(s); "
            "resolve undefined CV(FPR) values before computing bootstrap CI"
        )
    n = len(deltas)
    rng = np.random.default_rng(seed)

    boot_means = np.empty(n_bootstrap, dtype=np.float64)
    for i in range(n_bootstrap):
        sample = rng.choice(deltas, size=n, replace=True)
        boot_means[i] = sample.mean()

    alpha = 1.0 - ci
    ci_lower = float(np.percentile(boot_means, 100 * alpha / 2))
    ci_upper = float(np.percentile(boot_means, 100 * (1 - alpha / 2)))
    mean_delta = float(deltas.mean())
    excludes_zero = (ci_lower > 0.0) or (ci_upper < 0.0)

    return BootstrapResult(
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        mean_delta=mean_delta,
        excludes_zero=excludes_zero,
        n_seeds=n,
        n_bootstrap=n_bootstrap,
    )
