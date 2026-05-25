from __future__ import annotations

from datp.core.enums import Regime
from datp.data.catalog import DatasetID, DatasetSpec, dataset_spec

REGIME_DATASET: dict[Regime, DatasetID] = {
    Regime.A: DatasetID.NBAIOT,
    Regime.B: DatasetID.CICIOT2023,
    Regime.C: DatasetID.NBAIOT,
    Regime.D: DatasetID.EDGE_IIOTSET,
}


def dataset_for_regime(regime: Regime) -> DatasetID:
    return REGIME_DATASET[regime]


def spec_for_regime(regime: Regime) -> DatasetSpec:
    return dataset_spec(dataset_for_regime(regime))


def is_dirichlet_regime(regime: Regime) -> bool:
    return regime == Regime.C


def requires_alpha(regime: Regime) -> bool:
    return is_dirichlet_regime(regime)
