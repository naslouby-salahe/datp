from __future__ import annotations

from pathlib import Path

from datp.artifacts.constants import MANIFEST_FILE
from datp.core.enums import Regime
from datp.core.errors import fmt
from datp.core.identity import format_alpha_dir, seed_segment
from datp.data.catalog import DatasetID, dataset_spec
from datp.data.manifests import PartitionManifest
from datp.data.regimes.catalog import dataset_for_regime

PATHS_MODULE = "data.paths"

DEFAULT_BASE_DIR: Path = Path(".")


def data_root(base_dir: str | Path) -> Path:
    return Path(base_dir) / "data"


def raw_root(dataset: DatasetID, base_dir: str | Path) -> Path:
    slug = dataset_spec(dataset).raw_layout.root_slug
    return data_root(base_dir) / "raw" / slug


def processed_root(dataset: DatasetID, base_dir: str | Path) -> Path:
    return data_root(base_dir) / "processed" / dataset_spec(dataset).processed_slug


def assert_no_root_conflict(base_dir: str | Path, dataset: DatasetID) -> None:
    """Raise if `data/processed/<slug>/` and `data/data/processed/<slug>/` both
    hold conflicting manifests for the same dataset.

    Phase 0 (GA-13) lock: the canonical processed root is `data/processed/<slug>/`.
    The legacy `data/data/processed/<slug>/` directory may still exist with extra
    sidecars (e.g., `test_attack_labels.parquet`) and identical splits — that is
    not a conflict. A conflict is two manifests that disagree on dataset name,
    file hashes, or metadata.
    """
    canonical = processed_root(dataset, base_dir=base_dir) / MANIFEST_FILE
    legacy = processed_root(dataset, base_dir=Path(base_dir) / "data") / MANIFEST_FILE
    if not (canonical.exists() and legacy.exists()):
        return

    canonical_manifest = PartitionManifest.load(canonical)
    legacy_manifest = PartitionManifest.load(legacy)

    if _manifests_agree(canonical_manifest, legacy_manifest):
        return

    raise RuntimeError(
        fmt(
            PATHS_MODULE,
            f"Conflicting processed roots for dataset '{dataset_spec(dataset).processed_slug}'",
            f"manifests at {canonical} and {legacy} must agree or one must be removed",
            "manifests disagree on dataset/file_hashes/metadata",
        )
    )


def _manifests_agree(a: PartitionManifest, b: PartitionManifest) -> bool:
    return (
        a.dataset == b.dataset
        and a.file_hashes == b.file_hashes
        and a.metadata.model_dump() == b.metadata.model_dump()
    )


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
