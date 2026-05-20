from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

import pytest
from rich.logging import RichHandler

from datp.config.models import LoggingConfig
from datp.core.logging import configure_logging, reset_logging


def _make_cfg(
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
    level: str = "DEBUG",
    json_format: bool = False,
    training_progress_interval: int = 10,
) -> LoggingConfig:
    return LoggingConfig(
        level=level,
        json_format=json_format,
        max_bytes=max_bytes,
        backup_count=backup_count,
        training_progress_interval=training_progress_interval,
    )


@pytest.fixture(autouse=True)
def _clean_logging():
    reset_logging()
    yield
    reset_logging()


def test_log_rotation_triggers(tmp_path: Path) -> None:
    max_bytes = 1024
    log_dir = tmp_path / "logs"

    configure_logging(_make_cfg(max_bytes=max_bytes, backup_count=5), log_dir)
    logger = logging.getLogger("test_rotation")

    for i in range(100):
        logger.warning("Synthetic log line %d — padding to force rotation xxxxxx", i)

    for h in logging.getLogger().handlers:
        h.flush()

    main_log = log_dir / "datp.log"
    assert main_log.exists()
    assert main_log.stat().st_size <= max_bytes

    backups = list(log_dir.glob("datp.log.*"))
    assert len(backups) > 0, "Expected at least one backup file after rotation"


def test_default_log_dir_created(tmp_path: Path) -> None:
    log_dir = tmp_path / "nonexistent" / "logs"
    assert not log_dir.is_dir()

    configure_logging(_make_cfg(), log_dir)
    assert log_dir.is_dir()


def test_console_handler_attached(tmp_path: Path) -> None:
    configure_logging(_make_cfg(), tmp_path / "logs")
    root = logging.getLogger()
    assert any(
        isinstance(handler, (RichHandler, logging.StreamHandler))
        for handler in root.handlers
    )


def test_idempotent(tmp_path: Path) -> None:
    cfg = _make_cfg()
    log_dir = tmp_path / "logs"
    configure_logging(cfg, log_dir)
    count_before = len(logging.getLogger().handlers)
    configure_logging(cfg, log_dir)
    assert len(logging.getLogger().handlers) == count_before


def test_rotating_file_handler_present(tmp_path: Path) -> None:
    configure_logging(_make_cfg(), tmp_path / "logs")
    root = logging.getLogger()
    handler_types = [type(h) for h in root.handlers]
    assert RotatingFileHandler in handler_types
