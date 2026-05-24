from __future__ import annotations

from pathlib import Path

from datp.core.enums import Regime
from datp.artifacts.constants import MANIFEST_FILE
from datp.core.errors import fmt
from datp.core.identity import format_alpha_dir, seed_segment
from datp.data.catalog import DatasetID, dataset_spec
from datp.data.manifests import PartitionManifest
from datp.data.regimes.catalog import dataset_for_regime


def data_root(base_dir: str | Path) -> Path:
    return Path(base_dir) / "data"


def raw_root(dataset: DatasetID, base_dir: str | Path) -> Path:
    slug = dataset_spec(dataset).raw_layout.root_slug
    return data_root(base_dir) / "raw" / slug


def processed_root(dataset: DatasetID, base_dir: str | Path) -> Path:
    return data_root(base_dir) / "processed" / dataset_spec(dataset).processed_slug


def regime_c_prepared_dir(base_root: Path, alpha: float, seed: int) -> Path:
    return base_root / "regime_c" / format_alpha_dir(alpha) / seed_segment(seed)


def assert_no_root_conflict(base_dir: str | Path, dataset: DatasetID) -> None:
    """Ensure we do not have conflicting data roots (data/processed/slug vs data/data/processed/slug)."""
    slug = dataset_spec(dataset).processed_slug

    canonical_root = Path(base_dir) / "data" / "processed" / slug
    nested_root = Path(base_dir) / "data" / "data" / "processed" / slug

    canonical_manifest = canonical_root / MANIFEST_FILE
    nested_manifest = nested_root / MANIFEST_FILE

    if canonical_manifest.exists() and nested_manifest.exists():
        try:
            canonical_data = PartitionManifest.load(canonical_manifest)
            nested_data = PartitionManifest.load(nested_manifest)
        except Exception as e:
            # If we fail to read a manifest, we can't definitively check for a conflict,
            # but raising might be better. Let's just let the load() error bubble up.
            raise

        if canonical_data.file_hashes != nested_data.file_hashes:
            raise RuntimeError(
                fmt(
                    "data.paths",
                    "Data root conflict detected",
                    "compatible manifests or only one data root",
                    f"Conflicting manifests in {canonical_root} and {nested_root}"
                )
            )


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
