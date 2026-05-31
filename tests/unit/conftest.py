"""Shared test utilities for unit tests."""

from __future__ import annotations

from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from datp.scoring.schema import SCORE_COLUMN


def _write_score_artifact(path: Path, values: list[float]) -> None:
    """Write a minimal score .parquet artifact for testing."""
    path.parent.mkdir(parents=True, exist_ok=True)
    table = pa.table({SCORE_COLUMN: pa.array(values, type=pa.float32())})
    pq.write_table(table, path)
