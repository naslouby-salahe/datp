from __future__ import annotations

# Raw data under data/raw/ is NEVER modified; fixtures write only to tmp_path.

from pathlib import Path

import pandas as pd
import pytest

from datp.data.datasets.nbaiot import DEVICE_DIRS as NBAIOT_DEVICES

_REPO_ROOT = Path(__file__).resolve().parents[2]
_NBAIOT_RAW = _REPO_ROOT / "data" / "raw" / "N-BaIoT"
_CICIOT_RAW = _REPO_ROOT / "data" / "raw" / "CIC_IOT_Dataset2023"

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

            attack_csvs = sorted(family_src.glob("*.csv"))
            if attack_csvs:
                attack_df = pd.read_csv(attack_csvs[0], nrows=NBAIOT_ATTACK_ROWS)
                attack_df.to_csv(family_dst / attack_csvs[0].name, index=False)

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
