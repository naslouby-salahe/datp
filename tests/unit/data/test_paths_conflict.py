from __future__ import annotations
from datp.artifacts.names import ArtifactFile

from pathlib import Path

import pytest

from datp.data.catalog import DatasetID, dataset_spec
from datp.data.manifests import PartitionManifest, create_manifest
from datp.data.paths import (
    DEFAULT_BASE_DIR,
    assert_no_root_conflict,
    processed_root,
)


def _write_manifest(target_dir: Path, *, dataset: str, content: bytes) -> Path:
    raw_root = target_dir / "raw_src"
    raw_root.mkdir(parents=True, exist_ok=True)
    raw_file = raw_root / "file.bin"
    raw_file.write_bytes(content)
    target_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = target_dir / ArtifactFile.MANIFEST
    create_manifest(
        dataset=dataset,
        raw_files=[raw_file],
        raw_base_dir=raw_root,
        metadata={"n_devices": 1, "n_features": 39},
        manifest_path=manifest_path,
    )
    return manifest_path


def test_default_base_dir_is_dot() -> None:
    assert DEFAULT_BASE_DIR == Path(".")


def test_no_conflict_when_only_canonical_root_exists(tmp_path: Path) -> None:
    dataset = DatasetID.CICIOT2023
    canonical_dir = processed_root(dataset, base_dir=tmp_path)
    _write_manifest(
        canonical_dir, dataset=dataset_spec(dataset).processed_slug, content=b"abc"
    )
    assert_no_root_conflict(tmp_path, dataset)


def test_no_conflict_when_only_legacy_root_exists(tmp_path: Path) -> None:
    dataset = DatasetID.CICIOT2023
    legacy_dir = processed_root(dataset, base_dir=tmp_path / "data")
    _write_manifest(
        legacy_dir, dataset=dataset_spec(dataset).processed_slug, content=b"abc"
    )
    assert_no_root_conflict(tmp_path, dataset)


def test_no_conflict_when_both_manifests_agree(tmp_path: Path) -> None:
    dataset = DatasetID.CICIOT2023
    slug = dataset_spec(dataset).processed_slug
    canonical_dir = processed_root(dataset, base_dir=tmp_path)
    legacy_dir = processed_root(dataset, base_dir=tmp_path / "data")
    _write_manifest(canonical_dir, dataset=slug, content=b"abc")

    legacy_dir.mkdir(parents=True, exist_ok=True)
    canonical_manifest = PartitionManifest.load(canonical_dir / ArtifactFile.MANIFEST)
    (legacy_dir / ArtifactFile.MANIFEST).write_text(
        canonical_manifest.model_dump_json(indent=2)
    )

    assert_no_root_conflict(tmp_path, dataset)


def test_conflict_raises_on_diverging_file_hashes(tmp_path: Path) -> None:
    dataset = DatasetID.CICIOT2023
    slug = dataset_spec(dataset).processed_slug
    canonical_dir = processed_root(dataset, base_dir=tmp_path)
    legacy_dir = processed_root(dataset, base_dir=tmp_path / "data")
    _write_manifest(canonical_dir, dataset=slug, content=b"canonical-bytes")
    _write_manifest(legacy_dir, dataset=slug, content=b"legacy-bytes")

    with pytest.raises(
        RuntimeError, match=r"\[data\.paths\].*Conflicting processed roots"
    ):
        assert_no_root_conflict(tmp_path, dataset)


def test_no_conflict_when_neither_root_exists(tmp_path: Path) -> None:
    assert_no_root_conflict(tmp_path, DatasetID.CICIOT2023)
