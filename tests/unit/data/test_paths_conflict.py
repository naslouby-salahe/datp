from __future__ import annotations

import json
from pathlib import Path

import pytest

from datp.artifacts.constants import MANIFEST_FILE
from datp.data.catalog import DatasetID
from datp.data.paths import assert_no_root_conflict


def _create_mock_manifest(path: Path, hashes: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    manifest_data = {
        "dataset": "test_dataset",
        "file_hashes": hashes,
        "metadata": {"n_features": 10, "n_devices": 5},
        "created": "2024-01-01T00:00:00Z",
    }
    path.write_text(json.dumps(manifest_data))


def test_conflict_raises(tmp_path: Path) -> None:
    dataset = DatasetID.NBAIOT
    from datp.data.catalog import dataset_spec
    slug = dataset_spec(dataset).processed_slug

    canonical_root = tmp_path / "data" / "processed" / slug
    nested_root = tmp_path / "data" / "data" / "processed" / slug

    _create_mock_manifest(canonical_root / MANIFEST_FILE, {"file1": "hash1"})
    _create_mock_manifest(nested_root / MANIFEST_FILE, {"file1": "hash2"})

    with pytest.raises(RuntimeError, match="Data root conflict detected"):
        assert_no_root_conflict(tmp_path, dataset)


def test_missing_passes(tmp_path: Path) -> None:
    dataset = DatasetID.NBAIOT
    from datp.data.catalog import dataset_spec
    slug = dataset_spec(dataset).processed_slug

    canonical_root = tmp_path / "data" / "processed" / slug

    _create_mock_manifest(canonical_root / MANIFEST_FILE, {"file1": "hash1"})

    # nested_root doesn't exist, so this should pass
    assert_no_root_conflict(tmp_path, dataset)


def test_compatible_passes(tmp_path: Path) -> None:
    dataset = DatasetID.NBAIOT
    from datp.data.catalog import dataset_spec
    slug = dataset_spec(dataset).processed_slug

    canonical_root = tmp_path / "data" / "processed" / slug
    nested_root = tmp_path / "data" / "data" / "processed" / slug

    _create_mock_manifest(canonical_root / MANIFEST_FILE, {"file1": "hash1"})
    _create_mock_manifest(nested_root / MANIFEST_FILE, {"file1": "hash1"})

    # Hashes are identical, this should pass
    assert_no_root_conflict(tmp_path, dataset)
