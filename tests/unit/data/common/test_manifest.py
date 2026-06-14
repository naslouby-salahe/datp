from __future__ import annotations

import json
from pathlib import Path

import pytest

from datp.data.catalog import DatasetID
from datp.data.manifests import (
    ManifestMetadata,
    PartitionManifest,
    compute_manifest_hashes,
    create_manifest,
)


class TestManifestMetadata:
    def test_requires_n_devices_or_n_clients(self) -> None:
        with pytest.raises(ValueError, match="missing client count"):
            ManifestMetadata(n_features=10)

    def test_accepts_n_devices(self) -> None:
        m = ManifestMetadata(n_features=10, n_devices=9)
        assert m.n_devices == 9

    def test_accepts_n_clients(self) -> None:
        m = ManifestMetadata(n_features=10, n_clients=5)
        assert m.n_clients == 5

    def test_optional_fields_default_none(self) -> None:
        m = ManifestMetadata(n_features=115, n_devices=9)
        assert m.cap is None
        assert m.dataset_display_name is None


class TestComputeManifestHashes:
    def test_returns_relative_paths_as_keys(self, tmp_path: Path) -> None:
        f = tmp_path / "sub" / "file.csv"
        f.parent.mkdir()
        f.write_bytes(b"abc")
        hashes = compute_manifest_hashes([f], base_dir=tmp_path)
        assert "sub/file.csv" in hashes

    def test_hash_is_hex_string(self, tmp_path: Path) -> None:
        f = tmp_path / "data.csv"
        f.write_bytes(b"content")
        hashes = compute_manifest_hashes([f], base_dir=tmp_path)
        h = list(hashes.values())[0]
        int(h, 16)  # raises ValueError if not hex

    def test_sorted_by_path(self, tmp_path: Path) -> None:
        paths = []
        for name in ("z.csv", "a.csv", "m.csv"):
            p = tmp_path / name
            p.write_bytes(name.encode())
            paths.append(p)
        hashes = compute_manifest_hashes(paths, base_dir=tmp_path)
        assert list(hashes.keys()) == sorted(hashes.keys())


class TestPartitionManifest:
    def _make_manifest(self, tmp_path: Path) -> PartitionManifest:
        raw = tmp_path / "raw.csv"
        raw.write_bytes(b"data")
        return PartitionManifest(
            dataset=DatasetID.NBAIOT,
            file_hashes={"raw.csv": "deadbeef"},
            metadata=ManifestMetadata(n_features=115, n_devices=9),
            created="2026-01-01T00:00:00Z",
        )

    def test_empty_file_hashes_rejected(self) -> None:
        with pytest.raises(ValueError, match="file_hashes is empty"):
            PartitionManifest(
                dataset=DatasetID.NBAIOT,
                file_hashes={},
                metadata=ManifestMetadata(n_features=115, n_devices=9),
                created="2026-01-01T00:00:00Z",
            )

    def test_write_and_load_roundtrip(self, tmp_path: Path) -> None:
        manifest = self._make_manifest(tmp_path)
        path = tmp_path / "manifest.json"
        manifest.write(path)
        loaded = PartitionManifest.load(path)
        assert loaded.dataset == manifest.dataset
        assert loaded.file_hashes == manifest.file_hashes
        assert loaded.metadata.n_features == manifest.metadata.n_features

    def test_load_missing_raises(self, tmp_path: Path) -> None:
        with pytest.raises(RuntimeError, match="missing"):
            PartitionManifest.load(tmp_path / "nonexistent.json")

    def test_load_malformed_raises(self, tmp_path: Path) -> None:
        path = tmp_path / "bad.json"
        path.write_text("{not valid json")
        with pytest.raises(RuntimeError, match="Malformed"):
            PartitionManifest.load(path)

    def test_write_creates_parent_dirs(self, tmp_path: Path) -> None:
        manifest = self._make_manifest(tmp_path)
        deep = tmp_path / "a" / "b" / "c" / "manifest.json"
        manifest.write(deep)
        assert deep.exists()

    def test_verify_hashes_passes_on_match(self, tmp_path: Path) -> None:
        raw = tmp_path / "raw" / "data.csv"
        raw.parent.mkdir()
        raw.write_bytes(b"content")
        hashes = compute_manifest_hashes([raw], base_dir=tmp_path / "raw")
        m = PartitionManifest(
            dataset=DatasetID.NBAIOT,
            file_hashes=hashes,
            metadata=ManifestMetadata(n_features=10, n_devices=2),
            created="2026-01-01T00:00:00Z",
        )
        m.verify_hashes(tmp_path / "raw")

    def test_verify_hashes_fails_on_missing_file(self, tmp_path: Path) -> None:
        m = PartitionManifest(
            dataset=DatasetID.NBAIOT,
            file_hashes={"missing.csv": "abc123"},
            metadata=ManifestMetadata(n_features=10, n_devices=2),
            created="2026-01-01T00:00:00Z",
        )
        with pytest.raises(RuntimeError, match="missing"):
            m.verify_hashes(tmp_path)

    def test_verify_hashes_fails_on_mismatch(self, tmp_path: Path) -> None:
        raw = tmp_path / "data.csv"
        raw.write_bytes(b"content")
        m = PartitionManifest(
            dataset=DatasetID.NBAIOT,
            file_hashes={"data.csv": "00000000"},
            metadata=ManifestMetadata(n_features=10, n_devices=2),
            created="2026-01-01T00:00:00Z",
        )
        with pytest.raises(RuntimeError, match="mismatch"):
            m.verify_hashes(tmp_path)


class TestCreateManifest:
    def test_writes_manifest_file(self, tmp_path: Path) -> None:
        raw = tmp_path / "raw" / "file.csv"
        raw.parent.mkdir()
        raw.write_bytes(b"data")
        manifest_path = tmp_path / "manifest.json"
        result = create_manifest(
            dataset=DatasetID.NBAIOT,
            raw_files=[raw],
            raw_base_dir=tmp_path / "raw",
            metadata=ManifestMetadata(n_features=115, n_devices=9),
            manifest_path=manifest_path,
        )
        assert manifest_path.exists()
        assert result.dataset == DatasetID.NBAIOT
        assert len(result.file_hashes) == 1

    def test_manifest_is_valid_json(self, tmp_path: Path) -> None:
        raw = tmp_path / "a.csv"
        raw.write_bytes(b"x")
        manifest_path = tmp_path / "m.json"
        create_manifest(
            dataset=DatasetID.NBAIOT,
            raw_files=[raw],
            raw_base_dir=tmp_path,
            metadata=ManifestMetadata(n_features=115, n_devices=9),
            manifest_path=manifest_path,
        )
        parsed = json.loads(manifest_path.read_text())
        assert "file_hashes" in parsed
        assert "dataset" in parsed
