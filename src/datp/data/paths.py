from __future__ import annotations

from pathlib import Path

from datp.core.enums import Regime
from datp.core.identity import format_alpha_dir, seed_segment
from datp.data.catalog import DatasetID, dataset_spec
from datp.data.regimes.catalog import dataset_for_regime

PATHS_MODULE = "data.paths"

DEFAULT_BASE_DIR: Path = Path(".")


def data_root(base_dir: str | Path) -> Path:
    return Path(base_dir) / "data"


def raw_root(dataset: DatasetID, base_dir: str | Path) -> Path:
    slug = dataset_spec(dataset).raw_root_slug
    return data_root(base_dir) / "raw" / slug


def processed_root(dataset: DatasetID, base_dir: str | Path) -> Path:
    return data_root(base_dir) / "processed" / dataset_spec(dataset).processed_slug





def regime_c_prepared_dir(base_root: Path, alpha: float, seed: int) -> Path:
    return base_root / "regime_c" / format_alpha_dir(alpha) / seed_segment(seed)


def prepared_root_for_regime(
    regime: Regime,
    base_dir: str | Path,
    alpha: float | None = None,
    seed: int | None = None,
) -> Path:
    root = processed_root(dataset_for_regime(regime), base_dir=base_dir)
    if regime != Regime.C:
        return root
    if alpha is None or seed is None:
        raise ValueError(
            f"prepared_root_for_regime: Regime C requires both alpha and seed; "
            f"got alpha={alpha!r}, seed={seed!r}"
        )
    return regime_c_prepared_dir(root, alpha, seed)
