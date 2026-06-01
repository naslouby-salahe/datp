from __future__ import annotations

# Raw data under data/raw/ is NEVER modified; fixtures write only to tmp_path.

from pathlib import Path

import pandas as pd
import pytest

import numpy as np

from datp.data.datasets.nbaiot import DEVICE_DIRS as NBAIOT_DEVICES
from datp.data.datasets.edge_iiotset.spec import (
    ATTACK_TYPES as EDGE_ATTACK_TYPES,
    CLIENT_ID_COLUMN as EDGE_CLIENT_ID_COLUMN,
    FEATURE_COLUMNS as EDGE_FEATURE_COLUMNS,
    NORMAL_SENSOR_DIRS as EDGE_IIOTSET_SENSORS,
    RAW_ATTACK_DIR as EDGE_RAW_ATTACK_DIR,
    RAW_DATASET_DIR as EDGE_RAW_DATASET_DIR,
    RAW_NORMAL_DIR as EDGE_RAW_NORMAL_DIR,
    TIMESTAMP_COLUMN as EDGE_TIMESTAMP_COLUMN,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_NBAIOT_RAW = _REPO_ROOT / "data" / "raw" / "N-BaIoT"
_CICIOT_RAW = _REPO_ROOT / "data" / "raw" / "CIC_IOT_Dataset2023"

# Use 2 sensors for speed; need at least 2 for multi-client FL.
# Synthetic data is used because real Edge-IIoTset traffic is sparse: only
# ~0.01% of rows have all 58 features non-null, making tiny real subsets empty
# after the strict null filter in prepare_edge_iiotset.
_EDGE_TINY_SENSORS = EDGE_IIOTSET_SENSORS[:2]
_EDGE_BENIGN_ROWS = 500
_EDGE_ATTACK_ROWS = 100
_CSV_GLOB = "*.csv"

CICIOT_MERGED_FILES = ["Merged01.csv", "Merged02.csv"]

NBAIOT_BENIGN_ROWS = 200
NBAIOT_ATTACK_ROWS = 50
CICIOT_ROWS = 5000


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "e2e: end-to-end pipeline test")


@pytest.fixture(scope="session")
def nbaiot_tiny_raw(tmp_path_factory: pytest.TempPathFactory) -> Path:
    if not _NBAIOT_RAW.is_dir():
        pytest.skip("N-BaIoT raw data not available at data/raw/N-BaIoT")

    tmp_raw = tmp_path_factory.mktemp("nbaiot_raw")

    for device in NBAIOT_DEVICES:
        device_src = _NBAIOT_RAW / device
        if not device_src.is_dir():
            pytest.skip(f"N-BaIoT device directory not found: {device_src}")

        device_dst = tmp_raw / device
        device_dst.mkdir(parents=True)

        benign_src = device_src / "benign_traffic.csv"
        benign_df = pd.read_csv(benign_src, nrows=NBAIOT_BENIGN_ROWS)
        benign_df.to_csv(device_dst / "benign_traffic.csv", index=False)

        for attack_family in ("gafgyt_attacks", "mirai_attacks"):
            family_src = device_src / attack_family
            if not family_src.is_dir():
                continue
            family_dst = device_dst / attack_family
            family_dst.mkdir(parents=True)

            attack_csvs = sorted(family_src.glob(_CSV_GLOB))
            if attack_csvs:
                attack_df = pd.read_csv(attack_csvs[0], nrows=NBAIOT_ATTACK_ROWS)
                attack_df.to_csv(family_dst / attack_csvs[0].name, index=False)

    return tmp_raw


@pytest.fixture(scope="session")
def edge_iiotset_tiny_raw(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Synthetic Edge-IIoTset raw fixture with all features populated.

    Real data is too sparse for tiny subsets (only ~0.01% of rows survive the
    strict null filter), so synthetic data is generated with all feature columns
    filled. This tests the full preprocessing-to-FL pipeline without needing
    the large real dataset.
    """
    tmp_raw = tmp_path_factory.mktemp("edge_iiotset_raw")
    dataset_dst = tmp_raw / EDGE_RAW_DATASET_DIR
    attack_dst = dataset_dst / EDGE_RAW_ATTACK_DIR
    attack_dst.mkdir(parents=True)

    rng = np.random.default_rng(42)
    cols = list(EDGE_FEATURE_COLUMNS)

    for sensor in _EDGE_TINY_SENSORS:
        sensor_dst = dataset_dst / EDGE_RAW_NORMAL_DIR / sensor
        sensor_dst.mkdir(parents=True)
        benign = pd.DataFrame(
            rng.standard_normal((_EDGE_BENIGN_ROWS, len(cols))), columns=cols  # type: ignore[arg-type]
        )
        benign[EDGE_TIMESTAMP_COLUMN] = np.arange(_EDGE_BENIGN_ROWS) * 10
        benign[EDGE_CLIENT_ID_COLUMN] = sensor
        benign.to_csv(sensor_dst / f"{sensor}_normal.csv", index=False)

    for atk_type in EDGE_ATTACK_TYPES[:3]:
        atk = pd.DataFrame(
            rng.standard_normal((_EDGE_ATTACK_ROWS, len(cols))), columns=cols  # type: ignore[arg-type]
        )
        atk[EDGE_TIMESTAMP_COLUMN] = np.arange(_EDGE_ATTACK_ROWS) * 10
        atk.to_csv(attack_dst / f"{atk_type}_attack.csv", index=False)

    return tmp_raw


@pytest.fixture(scope="session")
def ciciot_tiny_raw(tmp_path_factory: pytest.TempPathFactory) -> Path:
    if not _CICIOT_RAW.is_dir():
        pytest.skip("CICIoT2023 raw data not available at data/raw/CIC_IOT_Dataset2023")

    tmp_raw = tmp_path_factory.mktemp("ciciot_raw")
    merged_dst = tmp_raw / "CSV" / "MERGED_CSV"
    merged_dst.mkdir(parents=True)

    merged_src = _CICIOT_RAW / "CSV" / "MERGED_CSV"
    for fname in CICIOT_MERGED_FILES:
        src = merged_src / fname
        if not src.exists():
            pytest.skip(f"CICIoT2023 merged file not found: {src}")
        df = pd.read_csv(src, nrows=CICIOT_ROWS)
        df.to_csv(merged_dst / fname, index=False)

    return tmp_raw
