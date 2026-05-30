# SPDX-License-Identifier: Proprietary
"""Edge-IIoTset deterministic preprocessing: raw CSV → Parquet train/cal/test splits.

Reads from data/raw/Edge-IIoTset/ and writes processed Parquet to
data/processed/edge_iiotset/ with per-client subdirectories.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import polars as pl

from datp.core.logging import get_logger
from datp.core.seeds import set_seeds
from datp.data.artifacts import create_empty_feature_frame, write_client_splits
from datp.data.contracts import PartitionResult
from datp.data.datasets.edge_iiotset.spec import (
    ATTACK_TYPES,
    CLIENT_ID_COLUMN,
    EDGE_IIOTSET_SPEC,
    FEATURE_COLUMNS,
    NORMAL_SENSOR_DIRS,
    RAW_ATTACK_DIR,
    RAW_DATASET_DIR,
    RAW_NORMAL_DIR,
    SPLIT_RATIOS,
    TIMESTAMP_COLUMN,
)
from datp.data.scaling import apply_scaler, fit_scaler
from datp.data.splits import Split

logger = get_logger(__name__)

_MODULE = "data.edge_iiotset"
_N_MIN_DEFAULT = 30


def _read_csv_safe(path: Path) -> pl.DataFrame:
    """Read a CSV; drops rows where all feature columns are null."""
    df = pl.read_csv(path, infer_schema_length=10000, ignore_errors=True)
    available = set(df.columns)
    keep = [
        c
        for c in [TIMESTAMP_COLUMN, CLIENT_ID_COLUMN, *FEATURE_COLUMNS]
        if c in available
    ]
    df = df.select(keep)
    cast_exprs = [
        pl.col(col).cast(pl.Float64, strict=False).alias(col)
        for col in FEATURE_COLUMNS
        if col in available
    ]
    if cast_exprs:
        df = df.with_columns(cast_exprs)
    feature_cols_present = [c for c in FEATURE_COLUMNS if c in available]
    if feature_cols_present:
        any_not_null = pl.any_horizontal(
            pl.col(c).is_not_null() for c in feature_cols_present
        )
        df = df.filter(any_not_null)
    return df


def _drop_null_features(df: pl.DataFrame) -> pl.DataFrame:
    """Drop rows where any feature column is null."""
    feature_cols = [c for c in FEATURE_COLUMNS if c in df.columns]
    if not feature_cols:
        return df
    all_not_null = pl.all_horizontal(pl.col(c).is_not_null() for c in feature_cols)
    return df.filter(all_not_null)


def _chronological_split(
    df: pl.DataFrame,
    *,
    train_frac: float,
    cal_frac: float,
    seed: int,
) -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame]:
    """Deterministic chronological split into train / cal / test_benign."""
    if TIMESTAMP_COLUMN in df.columns:
        ts_valid = df.filter(pl.col(TIMESTAMP_COLUMN).is_not_null())
        if len(ts_valid) > 0:
            df = ts_valid.sort(TIMESTAMP_COLUMN)
        else:
            rng = np.random.default_rng(seed)
            indices = rng.permutation(len(df)).tolist()
            df = df[indices]
    else:
        rng = np.random.default_rng(seed)
        indices = rng.permutation(len(df)).tolist()
        df = df[indices]

    n = len(df)
    n_train = int(n * train_frac)
    n_cal = int(n * cal_frac)

    train = df.slice(0, n_train)
    cal = df.slice(n_train, n_cal)
    test_benign = df.slice(n_train + n_cal, n - n_train - n_cal)

    return train, cal, test_benign


def _load_normal_traffic(normal_dir: Path) -> dict[str, pl.DataFrame]:
    """Load and clean normal traffic per sensor; raises if no data loaded."""
    normal_dfs: dict[str, pl.DataFrame] = {}
    for sensor in NORMAL_SENSOR_DIRS:
        sensor_dir = normal_dir / sensor
        csv_files = sorted(sensor_dir.glob("*.csv"))
        if not csv_files:
            logger.warning("No CSV found for normal sensor %s", sensor)
            continue
        dfs = [_read_csv_safe(csv_path) for csv_path in csv_files]
        combined = pl.concat(dfs, how="diagonal_relaxed")
        combined = _drop_null_features(combined)
        if len(combined) > 0:
            normal_dfs[sensor] = combined
    if not normal_dfs:
        raise RuntimeError("No valid normal traffic data loaded from Edge-IIoTset")
    return normal_dfs


def _load_attack_traffic(
    attack_dir: Path,
    normal_dfs: dict[str, pl.DataFrame],
    seed: int,
) -> pl.DataFrame:
    """Load attack CSVs and assign rows to clients proportionally."""
    attack_dfs: list[pl.DataFrame] = []
    client_ids = sorted(normal_dfs.keys())
    rng = np.random.default_rng(seed)

    for attack_type in ATTACK_TYPES:
        csv_path = attack_dir / f"{attack_type}_attack.csv"
        if not csv_path.is_file():
            logger.warning("Attack CSV not found: %s", csv_path)
            continue
        df = _read_csv_safe(csv_path)
        df = _drop_null_features(df)
        if len(df) > 0 and client_ids:
            assignments = rng.choice(client_ids, size=len(df)).tolist()
            df = df.with_columns(pl.Series(CLIENT_ID_COLUMN, assignments))
            attack_dfs.append(df)

    if attack_dfs:
        return pl.concat(attack_dfs, how="diagonal_relaxed")
    return pl.DataFrame()


def _prepare_client(
    sensor: str,
    normal_df: pl.DataFrame,
    all_attacks: pl.DataFrame,
    output_root: Path,
    seed: int,
    n_min: int,
) -> PartitionResult:
    """Prepare a single client: split, scale, write artifacts."""
    sensor_hash = int(hashlib.md5(sensor.encode("utf-8")).hexdigest(), 16) % 10000
    train, cal, test_benign = _chronological_split(
        normal_df,
        train_frac=SPLIT_RATIOS["train"],
        cal_frac=SPLIT_RATIOS["cal"],
        seed=seed + sensor_hash,
    )

    if len(all_attacks) > 0 and CLIENT_ID_COLUMN in all_attacks.columns:
        test_attack = all_attacks.filter(pl.col(CLIENT_ID_COLUMN) == sensor)
    else:
        test_attack = pl.DataFrame()

    feature_cols = [c for c in FEATURE_COLUMNS if c in train.columns]
    train_feat = train.select(feature_cols)
    cal_feat = cal.select(feature_cols)
    test_benign_feat = test_benign.select(feature_cols)
    test_attack_feat = (
        test_attack.select([c for c in feature_cols if c in test_attack.columns])
        if len(test_attack) > 0
        else create_empty_feature_frame(list(feature_cols))
    )

    scaler = fit_scaler(train_feat)
    train_scaled = apply_scaler(train_feat, scaler)
    cal_scaled = apply_scaler(cal_feat, scaler)
    test_benign_scaled = apply_scaler(test_benign_feat, scaler)
    test_attack_scaled = (
        apply_scaler(test_attack_feat, scaler)
        if len(test_attack_feat) > 0
        else create_empty_feature_frame(list(feature_cols))
    )

    cal_count = len(cal_scaled)
    calibration_pending = cal_count < n_min

    if calibration_pending:
        logger.warning(
            "client flagged as Calibration-Pending",
            client=sensor,
            cal_count=cal_count,
            n_min=n_min,
        )

    client_dir = output_root / sensor
    write_client_splits(
        client_dir=client_dir,
        splits={
            Split.TRAIN: train_scaled,
            Split.CAL: cal_scaled,
            Split.TEST_BENIGN: test_benign_scaled,
            Split.TEST_ATTACK: test_attack_scaled,
        },
        spec=EDGE_IIOTSET_SPEC,
        scaler=scaler,
    )

    return PartitionResult(
        benign_train_count=len(train_scaled),
        benign_cal_count=cal_count,
        test_benign_count=len(test_benign_scaled),
        test_attack_count=len(test_attack_scaled),
        calibration_pending=calibration_pending,
    )


def prepare_edge_iiotset(
    raw_root: Path,
    output_root: Path,
    *,
    seed: int,
    n_min: int = _N_MIN_DEFAULT,
) -> dict[str, PartitionResult]:
    """Preprocess Edge-IIoTset raw CSV files into per-client Parquet splits.

    Returns per-client partition results (same contract as nbaiot/ciciot).
    """
    set_seeds(seed)
    raw_dataset = raw_root / RAW_DATASET_DIR
    output_root.mkdir(parents=True, exist_ok=True)

    normal_dfs = _load_normal_traffic(raw_dataset / RAW_NORMAL_DIR)
    all_attacks = _load_attack_traffic(raw_dataset / RAW_ATTACK_DIR, normal_dfs, seed)

    results: dict[str, PartitionResult] = {}
    for sensor in sorted(normal_dfs.keys()):
        results[sensor] = _prepare_client(
            sensor, normal_dfs[sensor], all_attacks, output_root, seed, n_min
        )

    eligible = sum(1 for v in results.values() if not v.calibration_pending)
    pending = sum(1 for v in results.values() if v.calibration_pending)
    logger.info(
        "Edge-IIoTset preprocessing complete",
        eligible=eligible,
        pending=pending,
        total=len(results),
        output_dir=str(output_root),
    )
    return results
