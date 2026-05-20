from __future__ import annotations

from pathlib import Path

from datp.core.enums import Regime
from datp.core.regime import enforce_regime
from datp.data.contracts import PartitionResult
from datp.data.datasets.nbaiot import prepare_nbaiot


@enforce_regime(Regime.A)
def prepare_regime_a(
    raw_dir: Path,
    output_dir: Path,
    *,
    regime: Regime,
    n_min: int,
    seed: int,
    balanced_test: bool,
) -> dict[str, PartitionResult]:
    del regime
    return prepare_nbaiot(
        raw_dir=raw_dir,
        output_dir=output_dir,
        n_min=n_min,
        seed=seed,
        balanced_test=balanced_test,
    )
