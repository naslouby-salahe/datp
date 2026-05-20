from __future__ import annotations

import enum
from pathlib import Path


class Split(enum.StrEnum):
    TRAIN = "train"
    CAL = "cal"
    TEST_BENIGN = "test_benign"
    TEST_ATTACK = "test_attack"


SPLIT_FILENAME: dict[Split, str] = {
    Split.TRAIN: "train.parquet",
    Split.CAL: "cal.parquet",
    Split.TEST_BENIGN: "test_benign.parquet",
    Split.TEST_ATTACK: "test_attack.parquet",
}


def filename_for_split(split: Split) -> str:
    return SPLIT_FILENAME[split]


def split_path(client_dir: Path, split: Split) -> Path:
    return client_dir / filename_for_split(split)


def iter_scoring_splits() -> tuple[Split, ...]:
    return (Split.CAL, Split.TEST_BENIGN, Split.TEST_ATTACK)


def is_scoring_split(split: Split) -> bool:
    return split in iter_scoring_splits()
