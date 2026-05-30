from __future__ import annotations

from pathlib import Path

from datp.core.enums import Regime
from datp.core.regime import enforce_regime
from datp.data.contracts import PartitionResult
from datp.data.datasets.edge_iiotset.prepare import prepare_edge_iiotset


@enforce_regime(Regime.D)
def prepare_regime_d(
    raw_dir: Path,
    output_dir: Path,
    *,
    regime: Regime,
    n_min: int,
    seed: int,
    balanced_test: bool,
) -> dict[str, PartitionResult]:
    del regime
    del balanced_test  # Edge-IIoTset uses chronological split, balanced_test may not be natively supported or used.
    
    return prepare_edge_iiotset(
        raw_root=raw_dir,
        output_root=output_dir,
        n_min=n_min,
        seed=seed,
    )
