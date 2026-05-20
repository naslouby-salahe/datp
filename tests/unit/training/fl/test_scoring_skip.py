from __future__ import annotations

import json
from pathlib import Path

import pytest

from datp.artifacts.constants import SCORING_MANIFEST_FILE, SCORING_SENTINEL
from datp.artifacts.paths import ExperimentLocator
from datp.core.enums import Regime
from datp.training.fl.scoring import validate_scoring_manifest

_SEED = 0


def _score_base(tmp_path: Path) -> Path:
    return ExperimentLocator.for_main(tmp_path, Regime.A).score(_SEED)


def _write_sentinel(score_base: Path) -> None:
    score_base.mkdir(parents=True, exist_ok=True)
    (score_base / SCORING_SENTINEL).write_text("Scoring complete: 2 clients.\n")


def _write_valid_manifest(
    score_base: Path, client_ids: list[str], splits: list[str]
) -> None:
    score_base.mkdir(parents=True, exist_ok=True)
    records = []
    for cid in client_ids:
        for split in splits:
            path = score_base / split / f"{cid}.parquet"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"\x00")  # placeholder
            records.append(
                {
                    "client_id": cid,
                    "split": split,
                    "path": str(path),
                    "row_count": 50,
                    "columns": ["reconstruction_error"],
                    "dtypes": {"reconstruction_error": "Float32"},
                    "score_min": 0.1,
                    "score_max": 1.0,
                    "score_nan_count": 0,
                    "file_hash": "abc123",
                }
            )
    manifest = {
        "schema_version": "1",
        "completion_status": "complete",
        "expected_client_ids": sorted(client_ids),
        "expected_splits": sorted(splits),
        "actual_client_ids": sorted(client_ids),
        "actual_splits": sorted(splits),
        "records": records,
    }
    (score_base / SCORING_MANIFEST_FILE).write_text(
        json.dumps(manifest), encoding="utf-8"
    )


def test_validate_scoring_manifest_passes_with_valid_manifest(tmp_path: Path) -> None:
    sb = _score_base(tmp_path)
    _write_valid_manifest(sb, ["c0", "c1"], ["cal", "test_benign", "test_attack"])
    result = validate_scoring_manifest(sb)
    assert result["completion_status"] == "complete"


def test_sentinel_alone_is_not_sufficient(tmp_path: Path) -> None:
    sb = _score_base(tmp_path)
    _write_sentinel(sb)
    # Manifest not written — sentinel must not be enough
    with pytest.raises(FileNotFoundError, match="Scoring manifest missing"):
        validate_scoring_manifest(sb)


def test_validate_scoring_manifest_fails_when_manifest_missing(tmp_path: Path) -> None:
    sb = _score_base(tmp_path)
    sb.mkdir(parents=True, exist_ok=True)
    with pytest.raises(FileNotFoundError, match="Scoring manifest missing"):
        validate_scoring_manifest(sb)


def test_validate_scoring_manifest_fails_incomplete_status(tmp_path: Path) -> None:
    sb = _score_base(tmp_path)
    sb.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema_version": "1",
        "completion_status": "incomplete",
        "expected_client_ids": ["c0"],
        "expected_splits": ["cal"],
        "records": [],
    }
    (sb / SCORING_MANIFEST_FILE).write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="Scoring manifest incomplete"):
        validate_scoring_manifest(sb)


def test_validate_scoring_manifest_fails_missing_records(tmp_path: Path) -> None:
    sb = _score_base(tmp_path)
    sb.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema_version": "1",
        "completion_status": "complete",
        "expected_client_ids": ["c0"],
        "expected_splits": ["cal"],
        "records": [],  # empty — missing expected (c0, cal)
    }
    (sb / SCORING_MANIFEST_FILE).write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="Scoring manifest incomplete"):
        validate_scoring_manifest(sb)


def test_validate_scoring_manifest_fails_missing_files(tmp_path: Path) -> None:
    sb = _score_base(tmp_path)
    sb.mkdir(parents=True, exist_ok=True)
    ghost_path = sb / "cal" / "c0.parquet"
    manifest = {
        "schema_version": "1",
        "completion_status": "complete",
        "expected_client_ids": ["c0"],
        "expected_splits": ["cal"],
        "actual_client_ids": ["c0"],
        "actual_splits": ["cal"],
        "records": [
            {
                "client_id": "c0",
                "split": "cal",
                "path": str(ghost_path),  # does not exist
                "row_count": 50,
                "columns": ["reconstruction_error"],
                "dtypes": {"reconstruction_error": "Float32"},
                "score_min": 0.1,
                "score_max": 1.0,
                "score_nan_count": 0,
                "file_hash": "abc",
            }
        ],
    }
    (sb / SCORING_MANIFEST_FILE).write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="Scoring manifest incomplete"):
        validate_scoring_manifest(sb)
