from __future__ import annotations

import logging

import pytest
from lightning_utilities.core import rank_zero as lightning_rank_zero

from datp.baselines.common.training import (
    _quiet_lightning_console_logging,
    _should_log_epoch_progress,
)


@pytest.mark.parametrize(
    ("completed_epochs", "max_epochs", "expected"),
    [
        (1, 200, True),
        (2, 200, False),
        (10, 200, True),
        (19, 200, False),
        (20, 200, True),
        (37, 37, True),
    ],
)
def test_should_log_epoch_progress_cadence(
    completed_epochs: int,
    max_epochs: int,
    expected: bool,
) -> None:
    assert (
        _should_log_epoch_progress(completed_epochs, max_epochs, interval=10)
        is expected
    )


def test_quiet_lightning_console_logging_sets_rank_zero_warning_level() -> None:
    lightning_rank_zero.log.setLevel(logging.INFO)

    _quiet_lightning_console_logging()

    assert lightning_rank_zero.log.level == logging.WARNING
