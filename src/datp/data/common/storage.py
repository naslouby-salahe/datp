"""All intermediate processed datasets use Parquet; CSV is not acceptable."""

from __future__ import annotations

from pathlib import Path

import polars as pl

from datp.artifacts.names import PathToken
from datp.core.errors import fmt


def write_artifact(df: pl.DataFrame, path: Path | str) -> None:
    path = Path(path)
    if path.suffix != PathToken.PARQUET_EXT:
        raise ValueError(
            fmt(
                "data.storage",
                f"Artifact path must use '{PathToken.PARQUET_EXT}' extension.",
                f"path ending in {PathToken.PARQUET_EXT}",
                f"path ending in {path.suffix}",
            )
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(".tmp.parquet")
    df.write_parquet(tmp_path, compression="snappy")
    tmp_path.rename(path)


def read_artifact(path: Path | str) -> pl.DataFrame:
    path = Path(path)
    if path.suffix != PathToken.PARQUET_EXT:
        raise ValueError(
            fmt(
                "data.storage",
                f"Artifact path must use '{PathToken.PARQUET_EXT}' extension.",
                f"path ending in {PathToken.PARQUET_EXT}",
                f"path ending in {path.suffix}",
            )
        )
    return pl.read_parquet(path)


def assert_no_csv_artifacts(directory: Path | str) -> None:
    directory = Path(directory)
    if not directory.exists():
        return
    csv_files = sorted(directory.rglob("*.csv"))
    if csv_files:
        listing = "\n  ".join(str(f) for f in csv_files[:10])
        extra = f"\n  ... and {len(csv_files) - 10} more" if len(csv_files) > 10 else ""
        raise RuntimeError(
            f"[data.storage] CSV files found in {directory} — "
            f"Parquet is the only accepted format.\n  {listing}{extra}"
        )
