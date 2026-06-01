from __future__ import annotations

import enum
from pathlib import Path


class Split(enum.StrEnum):
    TRAIN = "train"
    CAL = "cal"
    TEST_BENIGN = "test_benign"
    TEST_ATTACK = "test_attack"


class SplitFilename(enum.StrEnum):
    TRAIN = "train.parquet"
    CAL = "cal.parquet"
    TEST_BENIGN = "test_benign.parquet"
    TEST_ATTACK = "test_attack.parquet"


_SPLIT_FILENAME: dict[Split, SplitFilename] = {
    Split.TRAIN: SplitFilename.TRAIN,
    Split.CAL: SplitFilename.CAL,
    Split.TEST_BENIGN: SplitFilename.TEST_BENIGN,
    Split.TEST_ATTACK: SplitFilename.TEST_ATTACK,
}


def filename_for_split(split: Split) -> SplitFilename:
    return _SPLIT_FILENAME[split]


def split_path(client_dir: Path, split: Split) -> Path:
    return client_dir / filename_for_split(split)


def iter_scoring_splits() -> tuple[Split, ...]:
    return (Split.CAL, Split.TEST_BENIGN, Split.TEST_ATTACK)


def is_scoring_split(split: Split) -> bool:
    return split in iter_scoring_splits()
