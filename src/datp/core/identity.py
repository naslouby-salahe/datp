from __future__ import annotations

import math
import time

import attrs

from datp.artifacts.run_formatting import (
    ALPHA_IID,
    ALPHA_PREFIX,
    SEED_PREFIX,
)
from datp.core.enums import (
    Baseline,
    Regime,
)


def alpha_label(alpha: float | None) -> str | None:
    if alpha is None:
        return None
    if math.isinf(alpha):
        return "iid"
    return f"{alpha:g}"


def alpha_from_label(label: str | None) -> float | None:
    """Convert serialized alpha label back to float. 'iid' → math.inf; None → None."""
    if label is None:
        return None
    if label == "iid":
        return math.inf
    return float(label)


def format_alpha_dir(alpha: float) -> str:
    label = alpha_label(alpha)
    if label == "iid":
        return ALPHA_IID
    return f"{ALPHA_PREFIX}{label}"


def parse_alpha_dir(name: str) -> float | None:
    if not name.startswith(ALPHA_PREFIX):
        return None
    if name == ALPHA_IID:
        return math.inf
    return float(name.removeprefix(ALPHA_PREFIX))


def seed_segment(seed: int) -> str:
    return f"{SEED_PREFIX}{seed}"


def make_run_id(regime: Regime, seed: int, alpha: float | None = None) -> str:
    ts_ms = int(time.time() * 1000)
    parts = [regime.value, f"seed{seed}"]
    label = alpha_label(alpha)
    if label is not None:
        parts.append(f"alpha{label}")
    parts.append(str(ts_ms))
    return "_".join(parts)


@attrs.define(frozen=True, slots=True)
class ExperimentKey:
    """Shared training identity for one FL encoder and score-artifact cell."""

    regime: Regime
    seed: int
    alpha: float | None = None

    def __attrs_post_init__(self) -> None:
        if not isinstance(self.regime, Regime):
            raise TypeError(
                f"ExperimentKey.regime must be Regime, got {type(self.regime)!r}"
            )

    def label(self) -> str:
        parts = [f"regime={self.regime}", f"seed={self.seed}"]
        label = alpha_label(self.alpha)
        if label is not None:
            parts.append(f"alpha={label}")
        return " ".join(parts)


@attrs.define(frozen=True, slots=True)
class RunIdentity:
    regime: Regime
    baseline: Baseline
    seed: int
    alpha: float | None = None

    def __attrs_post_init__(self) -> None:
        if not isinstance(self.regime, Regime):
            raise TypeError(
                f"RunIdentity.regime must be Regime, got {type(self.regime)!r}"
            )
        if not isinstance(self.baseline, Baseline):
            raise TypeError(
                f"RunIdentity.baseline must be Baseline, got {type(self.baseline)!r}"
            )

    def audit_id(self) -> str:
        suffix = f"_alpha{alpha_label(self.alpha)}" if self.alpha is not None else ""
        return f"{self.regime}_{self.baseline}_seed{self.seed}{suffix}"

    def shared_training_key(self) -> tuple[Regime, int, float | None]:
        return (self.regime, self.seed, self.alpha)

    def label(self) -> str:
        parts = [
            f"regime={self.regime}",
            f"baseline={self.baseline}",
            f"seed={self.seed}",
        ]
        label = alpha_label(self.alpha)
        if label is not None:
            parts.append(f"alpha={label}")
        return " ".join(parts)

    def tracking_name(self) -> str:
        suffix = f"_alpha{alpha_label(self.alpha)}" if self.alpha is not None else ""
        return f"{self.regime.value}_{self.baseline.value}_seed{self.seed}{suffix}"
