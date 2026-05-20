from __future__ import annotations

from pathlib import Path

from datp.core.enums import Regime
from datp.core.regime import enforce_regime
from datp.data.contracts import PartitionResult
from datp.data.datasets.ciciot2023 import prepare_ciciot


@enforce_regime(Regime.B)
def prepare_regime_b(
    raw_dir: Path,
    output_dir: Path,
    *,
    regime: Regime,
    n_min: int,
    cap: int,
    seed: int,
    attack_reserve_fraction: float,
) -> dict[str, PartitionResult]:
    del regime
    return prepare_ciciot(
        raw_dir=raw_dir,
        output_dir=output_dir,
        n_min=n_min,
        cap=cap,
        seed=seed,
        attack_reserve_fraction=attack_reserve_fraction,
    )
