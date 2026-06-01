from __future__ import annotations

import math
from pathlib import Path

import polars as pl

from datp.artifacts.names import ArtifactFile
from datp.core.errors import fmt, fmt_missing
from datp.core.logging import get_logger
from datp.data.artifacts import create_empty_feature_frame, write_client_splits
from datp.data.contracts import PartitionResult, SplitIndices
from datp.data.datasets.nbaiot.spec import (
    ATTACK_FAMILY_DIRS,
    BENIGN_TRAFFIC_FILE,
    CSV_GLOB,
    DEVICE_DIRS,
    FEATURE_COUNT,
    GAP1_KEY,
    GAP2_KEY,
    NBAIOT_SPEC,
    SPLIT_RATIOS,
)
from datp.data.manifests import ManifestMetadata, create_manifest
from datp.data.scaling import apply_scaler, fit_scaler
from datp.data.splits import Split

logger = get_logger(__name__)

_MODULE = "datp.data.datasets.nbaiot"


def _raw_nbaiot_files(raw_dir: Path) -> list[Path]:
    files: list[Path] = []
    for device_id in DEVICE_DIRS:
        device_dir = raw_dir / device_id
        files.append(device_dir / BENIGN_TRAFFIC_FILE)
        for attack_family_dir in ATTACK_FAMILY_DIRS:
            files.extend(sorted((device_dir / attack_family_dir).glob(CSV_GLOB)))
    return [path for path in files if path.exists()]


def _compute_split_indices(n: int) -> SplitIndices:
    n_train = math.floor(n * SPLIT_RATIOS[Split.TRAIN])
    n_gap1 = math.floor(n * SPLIT_RATIOS[GAP1_KEY])
    n_cal = math.floor(n * SPLIT_RATIOS[Split.CAL])
    n_gap2 = math.floor(n * SPLIT_RATIOS[GAP2_KEY])

    train_end = n_train
    gap1_end = train_end + n_gap1
    cal_end = gap1_end + n_cal
    gap2_end = cal_end + n_gap2

    result = SplitIndices(
        train=(0, train_end),
        gap1=(train_end, gap1_end),
        cal=(gap1_end, cal_end),
        gap2=(cal_end, gap2_end),
        test_benign=(gap2_end, n),
    )

    if result.gap1[0] != result.train[1]:
        raise ValueError(
            fmt(_MODULE, "Gap1 alignment error", "gap1 following train", "gap")
        )
    if result.cal[0] != result.gap1[1]:
        raise ValueError(
            fmt(_MODULE, "Cal alignment error", "cal following gap1", "gap")
        )
    if result.gap2[0] != result.cal[1]:
        raise ValueError(
            fmt(_MODULE, "Gap2 alignment error", "gap2 following cal", "gap")
        )
    if result.test_benign[0] != result.gap2[1]:
        raise ValueError(
            fmt(_MODULE, "Test alignment error", "test following gap2", "gap")
        )
    return result


def _load_attack_csvs(device_dir: Path) -> tuple[pl.DataFrame, list[str]]:
    attack_frames: list[pl.DataFrame] = []
    attack_classes: list[str] = []

    for attack_family_dir in ATTACK_FAMILY_DIRS:
        family_path = device_dir / attack_family_dir
        if not family_path.is_dir():
            continue
        for csv_file in sorted(family_path.glob(CSV_GLOB)):
            df = pl.read_csv(csv_file)
            attack_frames.append(df)
            attack_classes.append(
                f"{attack_family_dir.replace('_attacks', '')}_{csv_file.stem}"
            )

    if attack_frames:
        return pl.concat(attack_frames), sorted(set(attack_classes))
    return pl.DataFrame(), []


def _prepare_device(
    device_id: str,
    raw_dir: Path,
    output_dir: Path,
    n_min: int,
    seed: int,
    *,
    balanced_test: bool,
) -> PartitionResult:

    device_raw = raw_dir / device_id
    device_out = output_dir / device_id

    benign_csv = device_raw / BENIGN_TRAFFIC_FILE
    if not benign_csv.exists():
        raise FileNotFoundError(fmt_missing(_MODULE, str(benign_csv)))
    benign_df = pl.read_csv(benign_csv)
    feature_cols = benign_df.columns
    n_benign = len(benign_df)
    logger.info(
        "device loaded",
        device=device_id,
        n_benign=n_benign,
        n_features=len(feature_cols),
    )

    attack_df_raw, attack_classes = _load_attack_csvs(device_raw)

    splits = _compute_split_indices(n_benign)
    train_df = benign_df.slice(splits.train[0], splits.train[1] - splits.train[0])
    cal_df = benign_df.slice(splits.cal[0], splits.cal[1] - splits.cal[0])
    test_benign_df = benign_df.slice(
        splits.test_benign[0], splits.test_benign[1] - splits.test_benign[0]
    )

    cal_count = len(cal_df)
    calibration_pending = cal_count < n_min
    if calibration_pending:
        logger.warning(
            "device flagged as Calibration-Pending",
            device=device_id,
            cal_count=cal_count,
            n_min=n_min,
        )
    else:
        logger.info(
            "device eligible", device=device_id, cal_count=cal_count, n_min=n_min
        )

    scaler = fit_scaler(train_df)

    train_scaled = apply_scaler(train_df, scaler)
    cal_scaled = apply_scaler(cal_df, scaler)
    test_benign_scaled = apply_scaler(test_benign_df, scaler)

    if len(attack_df_raw) > 0:
        test_attack_scaled = apply_scaler(attack_df_raw, scaler)
    else:
        test_attack_scaled = create_empty_feature_frame(feature_cols)

    if balanced_test and len(test_attack_scaled) > 0:
        n_attack = len(test_attack_scaled)
        if len(test_benign_scaled) > n_attack:
            test_benign_scaled = test_benign_scaled.sample(
                n=n_attack, seed=seed, with_replacement=False
            )
            logger.info(
                "balanced-test sensitivity: subsampled benign test to match attack count",
                device=device_id,
                n=n_attack,
            )

    write_client_splits(
        client_dir=device_out,
        splits={
            Split.TRAIN: train_scaled,
            Split.CAL: cal_scaled,
            Split.TEST_BENIGN: test_benign_scaled,
            Split.TEST_ATTACK: test_attack_scaled,
        },
        spec=NBAIOT_SPEC,
        scaler=scaler,
    )

    logger.info(
        "device prepared",
        device=device_id,
        train=len(train_scaled),
        cal=len(cal_scaled),
        test_benign=len(test_benign_scaled),
        test_attack=len(test_attack_scaled),
        attacks=attack_classes,
    )

    return PartitionResult(
        benign_train_count=len(train_scaled),
        benign_cal_count=cal_count,
        test_benign_count=len(test_benign_scaled),
        test_attack_count=len(test_attack_scaled),
        attack_classes=attack_classes,
        calibration_pending=calibration_pending,
        split_indices=splits,
    )


def prepare_nbaiot(
    raw_dir: Path,
    output_dir: Path,
    n_min: int,
    seed: int,
    *,
    balanced_test: bool,
) -> dict[str, PartitionResult]:
    raw_dir = Path(raw_dir)
    output_dir = Path(output_dir)

    if not raw_dir.is_dir():
        raise FileNotFoundError(
            fmt_missing(_MODULE, f"Raw N-BaIoT directory {raw_dir}")
        )

    results: dict[str, PartitionResult] = {}
    for device_id in DEVICE_DIRS:
        results[device_id] = _prepare_device(
            device_id, raw_dir, output_dir, n_min, seed, balanced_test=balanced_test
        )

    eligible = sum(1 for v in results.values() if not v.calibration_pending)
    pending = sum(1 for v in results.values() if v.calibration_pending)
    logger.info(
        "N-BaIoT preparation complete",
        eligible=eligible,
        pending=pending,
        total=len(results),
    )

    create_manifest(
        dataset=NBAIOT_SPEC.id,
        raw_files=_raw_nbaiot_files(raw_dir),
        raw_base_dir=raw_dir,
        metadata=ManifestMetadata(
            n_devices=len(results),
            n_features=FEATURE_COUNT,
            dataset_display_name=NBAIOT_SPEC.display_name,
            split_indices={
                dev: {
                    Split.TRAIN.value: list(result.split_indices.train),
                    GAP1_KEY: list(result.split_indices.gap1),
                    Split.CAL.value: list(result.split_indices.cal),
                    GAP2_KEY: list(result.split_indices.gap2),
                    Split.TEST_BENIGN.value: list(result.split_indices.test_benign),
                }
                for dev, result in results.items()
                if result.split_indices is not None
            },
        ),
        manifest_path=output_dir / ArtifactFile.MANIFEST,
    )

    return results
