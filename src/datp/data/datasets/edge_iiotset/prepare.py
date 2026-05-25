# SPDX-License-Identifier: Proprietary
"""Edge-IIoTset deterministic preprocessing: raw CSV → Parquet train/cal/test splits.

Reads from data/raw/Edge-IIoTset/ and writes processed Parquet to
data/processed/edge_iiotset/ with per-client subdirectories.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import polars as pl

from datp.core.logging import get_logger
from datp.core.seeds import set_seeds
from datp.data.common.storage import write_artifact
from datp.data.datasets.edge_iiotset.spec import (
    ALL_COLUMNS,
    ATTACK_TYPES,
    CLIENT_ID_COLUMN,
    FEATURE_COLUMNS,
    NORMAL_SENSOR_DIRS,
    RAW_ATTACK_DIR,
    RAW_DATASET_DIR,
    RAW_NORMAL_DIR,
    SPLIT_RATIOS,
    TIMESTAMP_COLUMN,
)
from datp.data.splits import Split, split_path

logger = get_logger(__name__)


def _read_csv_safe(path: Path) -> pd.DataFrame:
    """Read a CSV with known 63-column schema; drops rows with all-NaN features."""
    df = pd.read_csv(path, names=list(ALL_COLUMNS), skiprows=1, low_memory=False)
    # Drop rows where ALL feature columns are NaN.
    feature_mask = df[list(FEATURE_COLUMNS)].notna().any(axis=1)
    return df.loc[feature_mask].reset_index(drop=True)


def _parse_timestamp(df: pd.DataFrame) -> pd.Series:
    """Parse Wireshark-format timestamps; returns datetime64[ns] or NaT on failure."""
    return pd.to_datetime(df[TIMESTAMP_COLUMN], errors="coerce", utc=True)


def _to_float_features(df: pd.DataFrame) -> pd.DataFrame:
    """Convert feature columns to float64, coercing errors to NaN."""
    out = df.copy()
    for col in FEATURE_COLUMNS:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    return out


def _drop_nan_features(df: pd.DataFrame) -> pd.DataFrame:
    """Drop rows where any feature column is NaN."""
    return df.dropna(subset=list(FEATURE_COLUMNS)).reset_index(drop=True)


def _chronological_split(
    df: pd.DataFrame,
    *,
    train_frac: float,
    cal_frac: float,
    seed: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Deterministic chronological split.

    Sorts by timestamp, splits into train / cal / test_benign fractions.
    Returns (train, cal, test_benign).
    """
    ts = _parse_timestamp(df)
    if ts.notna().any():
        df = df.loc[ts.notna()].copy()
        df = df.sort_values(TIMESTAMP_COLUMN).reset_index(drop=True)
    else:
        # Fallback: random split if no parseable timestamps.
        rng = np.random.default_rng(seed)
        df = df.iloc[rng.permutation(len(df))].reset_index(drop=True)

    n = len(df)
    n_train = int(n * train_frac)
    n_cal = int(n * cal_frac)

    train = df.iloc[:n_train]
    cal = df.iloc[n_train : n_train + n_cal]
    test_benign = df.iloc[n_train + n_cal :]

    return train, cal, test_benign


def _to_parquet(df: pd.DataFrame, features_only: bool) -> pl.DataFrame:
    subset = df[list(FEATURE_COLUMNS)] if features_only else df[list(ALL_COLUMNS)]
    return pl.from_pandas(subset).cast({col: pl.Float32 for col in FEATURE_COLUMNS})


def _load_normal_traffic(normal_dir: Path) -> dict[str, pd.DataFrame]:
    """Load and clean normal traffic per sensor; raises if no data loaded."""
    normal_dfs: dict[str, pd.DataFrame] = {}
    for sensor in NORMAL_SENSOR_DIRS:
        sensor_dir = normal_dir / sensor
        csv_files = sorted(sensor_dir.glob("*.csv"))
        if not csv_files:
            logger.warning("No CSV found for normal sensor %s", sensor)
            continue
        dfs = [
            _read_csv_safe(csv_path).assign(**{CLIENT_ID_COLUMN: sensor})
            for csv_path in csv_files
        ]
        combined = pd.concat(dfs, ignore_index=True)
        combined = _to_float_features(combined)
        combined = _drop_nan_features(combined)
        if len(combined) > 0:
            normal_dfs[sensor] = combined
    if not normal_dfs:
        raise RuntimeError("No valid normal traffic data loaded from Edge-IIoTset")
    return normal_dfs


def _load_attack_traffic(
    attack_dir: Path,
    normal_dfs: dict[str, pd.DataFrame],
    seed: int,
) -> pd.DataFrame:
    """Load attack CSVs and assign rows to clients proportionally."""
    attack_dfs: list[pd.DataFrame] = []
    client_ids = sorted(normal_dfs.keys())
    rng = np.random.default_rng(seed)

    for attack_type in ATTACK_TYPES:
        csv_path = attack_dir / f"{attack_type}_attack.csv"
        if not csv_path.is_file():
            logger.warning("Attack CSV not found: %s", csv_path)
            continue
        df = _read_csv_safe(csv_path)
        df = _to_float_features(df)
        df = _drop_nan_features(df)
        if len(df) > 0 and client_ids:
            assignments = rng.choice(client_ids, size=len(df))
            df[CLIENT_ID_COLUMN] = assignments
            attack_dfs.append(df)

    if attack_dfs:
        return pd.concat(attack_dfs, ignore_index=True)
    return pd.DataFrame()


def _write_client_splits(
    normal_dfs: dict[str, pd.DataFrame],
    all_attacks: pd.DataFrame,
    output_root: Path,
    seed: int,
) -> int:
    """Write per-client train/cal/test_benign/test_attack Parquet splits."""
    n_clients = 0
    for sensor in sorted(normal_dfs.keys()):
        normal = normal_dfs[sensor]
        train, cal, test_benign = _chronological_split(
            normal,
            train_frac=SPLIT_RATIOS["train"],
            cal_frac=SPLIT_RATIOS["cal"],
            seed=seed + hash(sensor) % 10000,
        )

        test_attack = (
            all_attacks[all_attacks[CLIENT_ID_COLUMN] == sensor]
            if len(all_attacks) > 0
            else pd.DataFrame(columns=list(ALL_COLUMNS))
        )

        client_dir = output_root / sensor
        client_dir.mkdir(parents=True, exist_ok=True)

        splits = [
            (train, Split.TRAIN),
            (cal, Split.CAL),
            (test_benign, Split.TEST_BENIGN),
            (test_attack, Split.TEST_ATTACK),
        ]
        for df, split in splits:
            write_artifact(
                _to_parquet(df, features_only=True), split_path(client_dir, split)
            )

        n_clients += 1
    return n_clients


def prepare_edge_iiotset(
    raw_root: Path,
    output_root: Path,
    *,
    seed: int,
) -> int:
    """Preprocess Edge-IIoTset raw CSV files into per-client Parquet splits.

    Returns the number of clients produced.
    """
    set_seeds(seed)
    raw_dataset = raw_root / RAW_DATASET_DIR
    output_root.mkdir(parents=True, exist_ok=True)

    normal_dfs = _load_normal_traffic(raw_dataset / RAW_NORMAL_DIR)
    all_attacks = _load_attack_traffic(raw_dataset / RAW_ATTACK_DIR, normal_dfs, seed)
    n_clients = _write_client_splits(normal_dfs, all_attacks, output_root, seed)

    logger.info(
        "Edge-IIoTset preprocessing complete: %d clients written to %s",
        n_clients,
        output_root,
    )
    return n_clients
