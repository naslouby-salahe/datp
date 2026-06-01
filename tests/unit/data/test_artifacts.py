"""Tests for datp.data.artifacts — write_client_splits and create_empty_feature_frame."""

from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest
from sklearn.preprocessing import StandardScaler

from datp.artifacts.names import ArtifactFile
from datp.data.artifacts import create_empty_feature_frame, write_client_splits
from datp.data.catalog import (
    CapPolicy,
    CapStrategy,
    ClientIdentity,
    DatasetID,
    DatasetSpec,
    SplitPolicy,
)
from datp.data.common.storage import read_artifact
from datp.data.scaling import load_scaler
from datp.data.splits import Split, filename_for_split


def _make_spec(
    *,
    feature_columns: tuple[str, ...] | None = None,
    feature_count: int = 4,
) -> DatasetSpec:
    return DatasetSpec(
        id=DatasetID.NBAIOT,
        display_name="test",
        processed_slug="test",
        feature_count=feature_count,
        feature_columns=feature_columns,
        label_column=None,
        benign_label=None,
        client_identity=ClientIdentity.DEVICE_DIRECTORY,
        raw_root_slug="test",
        split_policy=SplitPolicy(
            name="test",
            calibration_benign_only=True,
            chronological=False,
            contiguous_gaps=False,
            ratios={"train": 0.6, "cal": 0.2},
        ),
        cap_policy=CapPolicy(total=1000, attack_reserve=100, strategy=CapStrategy.RANDOM),
        family_map=None,
        device_ids=(),
        attack_family_dirs=(),
        expected_client_count=None,
    )


def _make_df(columns: list[str], n_rows: int = 10) -> pl.DataFrame:
    return pl.DataFrame(
        {col: [float(i) for i in range(n_rows)] for col in columns}
    )


class TestCreateEmptyFeatureFrame:
    def test_creates_empty_frame_with_correct_columns(self) -> None:
        df = create_empty_feature_frame(["a", "b", "c"])
        assert df.shape == (0, 3)
        assert df.columns == ["a", "b", "c"]

    def test_all_columns_are_float64(self) -> None:
        df = create_empty_feature_frame(["x", "y"])
        for col in df.columns:
            assert df[col].dtype == pl.Float64

    def test_empty_column_list(self) -> None:
        df = create_empty_feature_frame([])
        assert df.shape == (0, 0)

    def test_single_column(self) -> None:
        df = create_empty_feature_frame(["f0"])
        assert df.shape == (0, 1)
        assert df["f0"].dtype == pl.Float64


class TestWriteClientSplits:
    def test_writes_all_splits_to_disk(self, tmp_path: Path) -> None:
        client_dir = tmp_path / "c1"
        spec = _make_spec(feature_columns=("a", "b"))
        splits = {
            Split.TRAIN: _make_df(["a", "b"]),
            Split.CAL: _make_df(["a", "b"]),
            Split.TEST_BENIGN: _make_df(["a", "b"]),
            Split.TEST_ATTACK: _make_df(["a", "b"]),
        }
        write_client_splits(client_dir, splits, spec)

        for split in Split:
            path = client_dir / filename_for_split(split)
            assert path.exists()
            df = read_artifact(path)
            assert df.shape == (10, 2)

    def test_writes_subset_of_splits(self, tmp_path: Path) -> None:
        client_dir = tmp_path / "c1"
        spec = _make_spec(feature_columns=("a", "b"))
        splits = {
            Split.TRAIN: _make_df(["a", "b"]),
            Split.CAL: _make_df(["a", "b"]),
        }
        write_client_splits(client_dir, splits, spec)

        assert (client_dir / filename_for_split(Split.TRAIN)).exists()
        assert (client_dir / filename_for_split(Split.CAL)).exists()
        assert not (client_dir / filename_for_split(Split.TEST_BENIGN)).exists()
        assert not (client_dir / filename_for_split(Split.TEST_ATTACK)).exists()

    def test_saves_scaler_when_provided(self, tmp_path: Path) -> None:
        client_dir = tmp_path / "c1"
        spec = _make_spec(feature_columns=("a", "b"))
        scaler = StandardScaler()
        scaler.fit([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])
        splits = {Split.TRAIN: _make_df(["a", "b"])}

        write_client_splits(client_dir, splits, spec, scaler=scaler)

        scaler_path = client_dir / ArtifactFile.SCALER
        assert scaler_path.exists()
        loaded = load_scaler(scaler_path)
        assert loaded.mean_ is not None
        assert loaded.var_ is not None

    def test_does_not_save_scaler_when_none(self, tmp_path: Path) -> None:
        client_dir = tmp_path / "c1"
        spec = _make_spec(feature_columns=("a", "b"))
        splits = {Split.TRAIN: _make_df(["a", "b"])}

        write_client_splits(client_dir, splits, spec, scaler=None)

        assert not (client_dir / ArtifactFile.SCALER).exists()

    def test_validates_feature_columns_from_spec(self, tmp_path: Path) -> None:
        client_dir = tmp_path / "c1"
        spec = _make_spec(feature_columns=("a", "b", "c"))
        splits = {Split.TRAIN: _make_df(["a", "b", "c"])}

        write_client_splits(client_dir, splits, spec)

        # Should not raise — columns match
        df = read_artifact(client_dir / filename_for_split(Split.TRAIN))
        assert df.columns == ["a", "b", "c"]

    def test_raises_on_feature_column_mismatch(self, tmp_path: Path) -> None:
        client_dir = tmp_path / "c1"
        spec = _make_spec(feature_columns=("a", "b"))
        splits = {Split.TRAIN: _make_df(["a", "b", "c"])}

        with pytest.raises(ValueError, match="schema mismatch"):
            write_client_splits(client_dir, splits, spec)

    def test_validates_feature_count_when_no_feature_columns(self, tmp_path: Path) -> None:
        client_dir = tmp_path / "c1"
        spec = _make_spec(feature_columns=None, feature_count=3)
        splits = {Split.TRAIN: _make_df(["x", "y", "z"])}

        write_client_splits(client_dir, splits, spec)

        # Should not raise — feature count matches
        df = read_artifact(client_dir / filename_for_split(Split.TRAIN))
        assert df.shape == (10, 3)

    def test_raises_on_feature_count_mismatch(self, tmp_path: Path) -> None:
        client_dir = tmp_path / "c1"
        spec = _make_spec(feature_columns=None, feature_count=5)
        splits = {Split.TRAIN: _make_df(["a", "b", "c"])}

        with pytest.raises(ValueError, match="Feature count mismatch"):
            write_client_splits(client_dir, splits, spec)

    def test_creates_parent_directories(self, tmp_path: Path) -> None:
        client_dir = tmp_path / "deep" / "nested" / "c1"
        spec = _make_spec(feature_columns=("a",))
        splits = {Split.TRAIN: _make_df(["a"])}

        write_client_splits(client_dir, splits, spec)

        assert (client_dir / filename_for_split(Split.TRAIN)).exists()

    def test_handles_empty_dataframes(self, tmp_path: Path) -> None:
        client_dir = tmp_path / "c1"
        spec = _make_spec(feature_columns=("a", "b"))
        empty = create_empty_feature_frame(["a", "b"])
        splits = {
            Split.TRAIN: _make_df(["a", "b"]),
            Split.CAL: empty,
            Split.TEST_BENIGN: empty,
            Split.TEST_ATTACK: empty,
        }

        write_client_splits(client_dir, splits, spec)

        cal = read_artifact(client_dir / filename_for_split(Split.CAL))
        assert cal.shape == (0, 2)
        assert cal.columns == ["a", "b"]

    def test_scaler_path_uses_canonical_constant(self, tmp_path: Path) -> None:
        client_dir = tmp_path / "c1"
        spec = _make_spec(feature_columns=("a",))
        scaler = StandardScaler()
        scaler.fit([[1.0]])
        splits = {Split.TRAIN: _make_df(["a"])}

        write_client_splits(client_dir, splits, spec, scaler=scaler)

        # Verify the scaler path uses ArtifactFile.SCALER, not a hardcoded string
        assert (client_dir / "scaler.pkl").exists()
        assert ArtifactFile.SCALER == "scaler.pkl"
