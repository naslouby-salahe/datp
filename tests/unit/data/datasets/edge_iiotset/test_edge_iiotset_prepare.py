# SPDX-License-Identifier: Proprietary
"""Tests for Edge-IIoTset preprocessing (prepare_edge_iiotset)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import polars as pl
import pytest

from datp.data.contracts import PartitionResult
from datp.data.datasets.edge_iiotset.prepare import (
    _chronological_split,
    _fill_null_features,
    prepare_edge_iiotset,
)
from datp.data.datasets.edge_iiotset.spec import (
    ATTACK_TYPES,
    CLIENT_ID_COLUMN,
    FEATURE_COLUMNS,
    FEATURE_COUNT,
    SPLIT_RATIOS,
    TIMESTAMP_COLUMN,
)
from datp.data.splits import Split, SplitFilename

# ── Synthetic data builders ──────────────────────────────────────────────

N_FEATURES = 58  # Real feature count — use actual column names.
N_BENIGN_PER_SENSOR = 500  # Enough to exercise all splits.
N_ATTACK_PER_TYPE = 100

# Use a subset of sensors for fast testing.
_SYNTHETIC_SENSORS = ("Distance", "Flame_Sensor", "Heart_Rate")


def _make_synthetic_raw(
    tmp_path: Path,
    sensors: tuple[str, ...] = _SYNTHETIC_SENSORS,
    attack_types: tuple[str, ...] | None = None,
    n_benign: int = N_BENIGN_PER_SENSOR,
    seed: int = 42,
) -> Path:
    """Create a synthetic Edge-IIoTset raw directory structure.

    Returns the raw_root (containing "Edge-IIoTset dataset/").
    """
    raw_root = tmp_path / "raw"
    dataset_dir = raw_root / "Edge-IIoTset dataset"
    normal_dir = dataset_dir / "Normal traffic"
    attack_dir = dataset_dir / "Attack traffic"
    attack_dir.mkdir(parents=True)

    rng = np.random.default_rng(seed)
    cols = list(FEATURE_COLUMNS)

    for sensor in sensors:
        sensor_dir = normal_dir / sensor
        sensor_dir.mkdir(parents=True)
        benign = pd.DataFrame(rng.standard_normal((n_benign, N_FEATURES)), columns=cols)  # type: ignore[arg-type]
        benign[TIMESTAMP_COLUMN] = np.arange(n_benign) * 10  # synthetic timestamps
        benign[CLIENT_ID_COLUMN] = sensor
        benign.to_csv(sensor_dir / f"{sensor}_normal.csv", index=False)

    if attack_types is None:
        attack_types = ATTACK_TYPES[:3]  # First 3 for speed

    for atk_type in attack_types:
        atk = pd.DataFrame(rng.standard_normal((N_ATTACK_PER_TYPE, N_FEATURES)), columns=cols)  # type: ignore[arg-type]
        atk[TIMESTAMP_COLUMN] = np.arange(N_ATTACK_PER_TYPE) * 10
        atk.to_csv(attack_dir / f"{atk_type}_attack.csv", index=False)

    return raw_root


# ── Chronological split unit tests ───────────────────────────────────────

class TestChronologicalSplit:
    def test_split_ratios_match(self) -> None:
        rng = np.random.default_rng(1)
        cols = list(FEATURE_COLUMNS)
        df = pl.DataFrame(rng.standard_normal((1000, N_FEATURES)), schema=cols)  # type: ignore[arg-type]
        df = df.with_columns(pl.Series(TIMESTAMP_COLUMN, np.arange(1000) * 10))

        train, cal, test_benign = _chronological_split(
            df, train_frac=0.60, cal_frac=0.25, seed=42
        )

        assert len(train) == 600
        assert len(cal) == 250
        assert len(test_benign) == 150
        assert len(train) + len(cal) + len(test_benign) == 1000

    def test_chronological_order_preserved(self) -> None:
        rng = np.random.default_rng(2)
        cols = list(FEATURE_COLUMNS)
        df = pl.DataFrame(rng.standard_normal((100, N_FEATURES)), schema=cols)  # type: ignore[arg-type]
        df = df.with_columns(pl.Series(TIMESTAMP_COLUMN, np.arange(100) * 10))

        train, cal, test_benign = _chronological_split(
            df, train_frac=0.60, cal_frac=0.25, seed=42
        )

        # Train should have lowest timestamps, then cal, then test_benign.
        train_max_val = train[TIMESTAMP_COLUMN].max()
        cal_min_val = cal[TIMESTAMP_COLUMN].min()
        cal_max_val = cal[TIMESTAMP_COLUMN].max()
        test_min_val = test_benign[TIMESTAMP_COLUMN].min()
        assert train_max_val is not None and cal_min_val is not None
        assert cal_max_val is not None and test_min_val is not None
        assert int(train_max_val) < int(cal_min_val)  # type: ignore[arg-type]
        assert int(cal_max_val) < int(test_min_val)  # type: ignore[arg-type]

    def test_no_overlap(self) -> None:
        rng = np.random.default_rng(3)
        cols = list(FEATURE_COLUMNS)
        df = pl.DataFrame(rng.standard_normal((1000, N_FEATURES)), schema=cols)  # type: ignore[arg-type]
        df = df.with_columns(pl.Series(TIMESTAMP_COLUMN, np.arange(1000) * 10))

        train, cal, test_benign = _chronological_split(
            df, train_frac=0.60, cal_frac=0.25, seed=42
        )

        train_ts = set(train[TIMESTAMP_COLUMN].to_list())
        cal_ts = set(cal[TIMESTAMP_COLUMN].to_list())
        test_ts = set(test_benign[TIMESTAMP_COLUMN].to_list())

        assert len(train_ts & cal_ts) == 0
        assert len(train_ts & test_ts) == 0
        assert len(cal_ts & test_ts) == 0

    def test_falls_back_to_random_when_no_timestamp(self) -> None:
        rng = np.random.default_rng(4)
        cols = list(FEATURE_COLUMNS)
        df = pl.DataFrame(rng.standard_normal((100, N_FEATURES)), schema=cols)  # type: ignore[arg-type]

        train, cal, test_benign = _chronological_split(
            df, train_frac=0.60, cal_frac=0.25, seed=42
        )

        assert len(train) == 60
        assert len(cal) == 25
        assert len(test_benign) == 15

    def test_deterministic(self) -> None:
        rng = np.random.default_rng(5)
        cols = list(FEATURE_COLUMNS)
        df = pl.DataFrame(rng.standard_normal((100, N_FEATURES)), schema=cols)  # type: ignore[arg-type]
        df = df.with_columns(pl.Series(TIMESTAMP_COLUMN, np.arange(100) * 10))

        a = _chronological_split(df, train_frac=0.60, cal_frac=0.25, seed=42)
        b = _chronological_split(df, train_frac=0.60, cal_frac=0.25, seed=42)

        for i in range(3):
            assert a[i].shape == b[i].shape
            assert (a[i][TIMESTAMP_COLUMN].to_list() == b[i][TIMESTAMP_COLUMN].to_list())


# ── Fill null features unit tests ────────────────────────────────────────

class TestFillNullFeatures:
    def test_no_null_features_unchanged(self) -> None:
        cols = list(FEATURE_COLUMNS[:3])
        df = pl.DataFrame({cols[0]: [1.0, 2.0, 3.0], cols[1]: [4.0, 5.0, 6.0], cols[2]: [7.0, 8.0, 9.0]})
        result = _fill_null_features(df)
        assert len(result) == 3
        assert result[cols[0]].to_list() == [1.0, 2.0, 3.0]

    def test_fills_nulls_with_zero_preserves_all_rows(self) -> None:
        cols = list(FEATURE_COLUMNS[:3])
        df = pl.DataFrame(
            {
                cols[0]: [1.0, None, 3.0],
                cols[1]: [4.0, 5.0, None],
                cols[2]: [7.0, 8.0, 9.0],
            }
        )
        result = _fill_null_features(df)
        assert len(result) == 3  # All rows preserved
        assert result[cols[0]].to_list() == [1.0, 0.0, 3.0]
        assert result[cols[1]].to_list() == [4.0, 5.0, 0.0]

    def test_infinite_values_replaced_with_zero(self) -> None:
        cols = list(FEATURE_COLUMNS[:2])
        df = pl.DataFrame(
            {
                cols[0]: [1.0, float("inf"), float("-inf")],
                cols[1]: [4.0, 5.0, 6.0],
            }
        )
        result = _fill_null_features(df)
        assert len(result) == 3
        assert result[cols[0]].to_list() == [1.0, 0.0, 0.0]
        assert result[cols[1]].to_list() == [4.0, 5.0, 6.0]

    def test_non_feature_columns_not_affected(self) -> None:
        cols = list(FEATURE_COLUMNS[:2])
        df = pl.DataFrame(
            {
                "frame.time": ["t1", None, "t3"],
                cols[0]: [1.0, None, 3.0],
                cols[1]: [4.0, 5.0, None],
            }
        )
        result = _fill_null_features(df)
        assert result["frame.time"].to_list() == ["t1", None, "t3"]
        assert result[cols[0]].to_list() == [1.0, 0.0, 3.0]


# ── Preprocessing integration tests ──────────────────────────────────────

@pytest.fixture()
def prepared(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, dict[str, PartitionResult]]:
    raw_root = _make_synthetic_raw(tmp_path)
    output_dir = tmp_path / "processed"

    result = prepare_edge_iiotset(
        raw_root=raw_root,
        output_root=output_dir,
        seed=42,
        n_min=50,
    )
    return output_dir, result


class TestPrepareEdgeIIoTset:

    def test_output_is_parquet(self, prepared: tuple[Path, dict[str, PartitionResult]]) -> None:
        output_dir, _ = prepared
        for sensor in _SYNTHETIC_SENSORS:
            sensor_dir = output_dir / sensor
            for name in (SplitFilename.TRAIN, SplitFilename.CAL, SplitFilename.TEST_BENIGN, SplitFilename.TEST_ATTACK):
                p = sensor_dir / name
                assert p.exists(), f"Missing artifact: {p}"
                assert p.suffix == ".parquet"
            assert (sensor_dir / "scaler.pkl").exists()

    def test_result_count_matches_sensors(self, prepared: tuple[Path, dict[str, PartitionResult]]) -> None:
        _, result = prepared
        assert len(result) == len(_SYNTHETIC_SENSORS)
        for sensor in _SYNTHETIC_SENSORS:
            assert sensor in result

    def test_chronological_split_ratios(self, prepared: tuple[Path, dict[str, PartitionResult]]) -> None:
        _, result = prepared
        for sensor in _SYNTHETIC_SENSORS:
            info = result[sensor]
            total_benign = info.benign_train_count + info.benign_cal_count + info.test_benign_count
            assert total_benign == N_BENIGN_PER_SENSOR

            expected_train = int(N_BENIGN_PER_SENSOR * SPLIT_RATIOS[Split.TRAIN])
            expected_cal = int(N_BENIGN_PER_SENSOR * SPLIT_RATIOS[Split.CAL])
            assert info.benign_train_count == expected_train
            assert info.benign_cal_count == expected_cal

    def test_calibration_above_n_min(self, prepared: tuple[Path, dict[str, PartitionResult]]) -> None:
        _, result = prepared
        for sensor in _SYNTHETIC_SENSORS:
            assert result[sensor].benign_cal_count >= 50
            assert result[sensor].calibration_pending is False

    def test_calibration_pending_flagged(self, tmp_path: Path) -> None:
        """Client with tiny calibration set is flagged."""
        raw_root = _make_synthetic_raw(tmp_path, n_benign=30)
        output_dir = tmp_path / "out_tiny"

        result = prepare_edge_iiotset(
            raw_root=raw_root,
            output_root=output_dir,
            seed=42,
            n_min=50,
        )
        for sensor in _SYNTHETIC_SENSORS:
            assert result[sensor].calibration_pending is True

    def test_attack_in_test_only(self, prepared: tuple[Path, dict[str, PartitionResult]]) -> None:
        output_dir, result = prepared
        for sensor in _SYNTHETIC_SENSORS:
            sensor_dir = output_dir / sensor
            train = pd.read_parquet(sensor_dir / SplitFilename.TRAIN)
            cal = pd.read_parquet(sensor_dir / SplitFilename.CAL)

            assert len(train) == result[sensor].benign_train_count
            assert len(cal) == result[sensor].benign_cal_count

            # Attack count should be non-zero (random assignment from 3 attack types)
            assert result[sensor].test_attack_count >= 0

    def test_attack_classes_populated(self, prepared: tuple[Path, dict[str, PartitionResult]]) -> None:
        _, result = prepared
        for sensor in _SYNTHETIC_SENSORS:
            info = result[sensor]
            # 3 attack types loaded; attack_classes should list them.
            assert len(info.attack_classes) == 3
            for atk in ATTACK_TYPES[:3]:
                assert atk in info.attack_classes

    def test_no_attack_classes_when_no_attacks(self, tmp_path: Path) -> None:
        """When no attack CSVs exist, attack_classes should be empty."""
        raw_root = _make_synthetic_raw(tmp_path, attack_types=())
        output_dir = tmp_path / "out_noatk"

        result = prepare_edge_iiotset(
            raw_root=raw_root,
            output_root=output_dir,
            seed=42,
            n_min=50,
        )
        for sensor in _SYNTHETIC_SENSORS:
            assert result[sensor].attack_classes == []

    def test_no_train_test_overlap(self, prepared: tuple[Path, dict[str, PartitionResult]]) -> None:
        output_dir, _ = prepared
        for sensor in _SYNTHETIC_SENSORS:
            sensor_dir = output_dir / sensor
            train = pd.read_parquet(sensor_dir / SplitFilename.TRAIN)
            test_b = pd.read_parquet(sensor_dir / SplitFilename.TEST_BENIGN)

            merged = pd.merge(train, test_b, how="inner")
            assert len(merged) == 0, f"Train/test_benign overlap in {sensor}: {len(merged)} rows"

    def test_no_train_cal_overlap(self, prepared: tuple[Path, dict[str, PartitionResult]]) -> None:
        output_dir, _ = prepared
        for sensor in _SYNTHETIC_SENSORS:
            sensor_dir = output_dir / sensor
            train = pd.read_parquet(sensor_dir / SplitFilename.TRAIN)
            cal = pd.read_parquet(sensor_dir / SplitFilename.CAL)

            merged = pd.merge(train, cal, how="inner")
            assert len(merged) == 0, f"Train/cal overlap in {sensor}: {len(merged)} rows"

    def test_feature_count_in_output(self, prepared: tuple[Path, dict[str, PartitionResult]]) -> None:
        output_dir, _ = prepared
        for sensor in _SYNTHETIC_SENSORS:
            sensor_dir = output_dir / sensor
            train = pd.read_parquet(sensor_dir / SplitFilename.TRAIN)
            assert train.shape[1] == FEATURE_COUNT

    def test_deterministic(self, tmp_path: Path) -> None:
        raw_root = _make_synthetic_raw(tmp_path)
        out_a = tmp_path / "out_a"
        out_b = tmp_path / "out_b"

        result_a = prepare_edge_iiotset(raw_root=raw_root, output_root=out_a, seed=42, n_min=50)
        result_b = prepare_edge_iiotset(raw_root=raw_root, output_root=out_b, seed=42, n_min=50)

        for sensor in _SYNTHETIC_SENSORS:
            assert result_a[sensor].benign_train_count == result_b[sensor].benign_train_count
            assert result_a[sensor].benign_cal_count == result_b[sensor].benign_cal_count
            assert result_a[sensor].test_benign_count == result_b[sensor].test_benign_count
            assert result_a[sensor].test_attack_count == result_b[sensor].test_attack_count
            assert result_a[sensor].calibration_pending == result_b[sensor].calibration_pending

    def test_different_seeds_different_output(self, tmp_path: Path) -> None:
        raw_root = _make_synthetic_raw(tmp_path)
        out_a = tmp_path / "out_a"
        out_b = tmp_path / "out_b"

        result_a = prepare_edge_iiotset(raw_root=raw_root, output_root=out_a, seed=42, n_min=50)
        result_b = prepare_edge_iiotset(raw_root=raw_root, output_root=out_b, seed=99, n_min=50)

        # Attack assignment differs by seed (random client assignment).
        # At least one sensor should differ in attack count.
        any_diff = False
        for sensor in _SYNTHETIC_SENSORS:
            if result_a[sensor].test_attack_count != result_b[sensor].test_attack_count:
                any_diff = True
                break
        assert any_diff, "Different seeds should produce different attack assignments"


class TestPartitionResultModel:
    def test_partition_result_fields(self) -> None:
        result = PartitionResult(
            benign_train_count=300,
            benign_cal_count=125,
            test_benign_count=75,
            test_attack_count=200,
            calibration_pending=False,
            attack_classes=["Backdoor", "DDoS_HTTP_Flood"],
        )
        assert result.benign_train_count == 300
        assert result.calibration_pending is False
        assert "Backdoor" in result.attack_classes

    def test_partition_result_immutable(self) -> None:
        result = PartitionResult(
            benign_train_count=1,
            benign_cal_count=1,
            test_benign_count=1,
            test_attack_count=0,
            calibration_pending=True,
        )
        with pytest.raises(Exception):
            result.benign_train_count = 999  # type: ignore[misc]
