"""Per-cell score-manifest verification: schema, manifest, checkpoint hash, client IDs, splits.

Reuses ``datp.data.common.schemas.validate_score_artifact`` for Parquet schema and
``datp.training.fl.scoring.validate_scoring_manifest`` for manifest completion semantics.
Does not recompute metrics (T03) or assign reuse verdicts (T04).
"""

from __future__ import annotations

import enum
import json
import math
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq
from pydantic import BaseModel, ConfigDict, Field

from datp.artifacts.constants import (
    MODEL_CHECKPOINT,
    SCORING_MANIFEST_FILE,
    SCORING_SENTINEL,
)
from datp.artifacts.paths import ExperimentLocator
from datp.audit.constants import (
    SCORE_CELL_VERIFICATION_INDEX_JSON,
    SCORE_CELL_VERIFICATION_JSON,
)
from datp.audit.discovery import ScoreCellLocation, iter_score_cells
from datp.audit.writers import write_json
from datp.core.enums import (
    SCORING_STAGES,
    AuditStatus,
    Regime,
    ScoringStage,
)
from datp.core.identity import alpha_label
from datp.core.provenance import hash_file
from datp.data.catalog import dataset_spec
from datp.data.common.schemas import validate_score_artifact
from datp.data.regimes.catalog import dataset_for_regime
from datp.evaluation.metric_keys import SCORE_COLUMN

_REQUIRED_MANIFEST_FIELDS: tuple[str, ...] = (
    "dataset",
    "regime",
    "seed",
    "alpha",
    "expected_client_ids",
    "model_checkpoint_hash",
    "model_checkpoint_path",
    "expected_splits",
    "actual_client_ids",
    "actual_splits",
    "completion_status",
    "score_column_name",
    "records",
)


class ScoreCheckCode(enum.StrEnum):
    MANIFEST_PRESENT = "manifest_present"
    MANIFEST_PARSEABLE = "manifest_parseable"
    MANIFEST_FIELDS_PRESENT = "manifest_fields_present"
    MANIFEST_COMPLETION_STATUS = "manifest_completion_status"
    SCORING_SENTINEL_PRESENT = "scoring_sentinel_present"
    REGIME_MATCH = "regime_match"
    SEED_MATCH = "seed_match"
    DATASET_MATCH = "dataset_match"
    CLIENT_IDS_MATCH_PARTITION = "client_ids_match_partition"
    EXPECTED_VS_ACTUAL_CLIENTS = "expected_vs_actual_clients"
    EXPECTED_VS_ACTUAL_SPLITS = "expected_vs_actual_splits"
    SPLIT_DIRECTORIES_PRESENT = "split_directories_present"
    PER_CLIENT_SPLIT_FILES_PRESENT = "per_client_split_files_present"
    PARQUET_SCHEMA_VALID = "parquet_schema_valid"
    PARQUET_NON_EMPTY = "parquet_non_empty"
    CHECKPOINT_HASH_FIELD_PRESENT = "checkpoint_hash_field_present"
    CHECKPOINT_FILE_PRESENT = "checkpoint_file_present"
    CHECKPOINT_HASH_MATCHES = "checkpoint_hash_matches"


class ScoreCheckResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    code: ScoreCheckCode
    status: AuditStatus
    detail: str = ""


class ScoreCellVerification(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    cell_dir: str
    regime: Regime
    seed: int
    alpha: str | None
    dataset: str
    expected_client_ids: list[str] = Field(default_factory=list)
    expected_splits: list[str] = Field(default_factory=list)
    checks: list[ScoreCheckResult]
    overall_status: AuditStatus


def _expected_partition_clients(data_root: Path, location: ScoreCellLocation) -> tuple[str, ...] | None:
    """Return the client-id set expected by the partition on disk; None when partition is missing.

    ``data_root`` is the repo root containing ``data/processed/``. For Regime A/B the dataset
    spec is authoritative. For Regime C we read the per-cell partition's per-client
    subdirectories (virtual client_NN ids that depend on seed/alpha).
    """
    from datp.data.paths import prepared_root_for_regime  # noqa: PLC0415

    if location.regime == Regime.C:
        prepared_root = prepared_root_for_regime(
            location.regime, base_dir=data_root, alpha=location.alpha, seed=location.seed,
        )
        if not prepared_root.exists():
            return None
        return tuple(sorted(p.name for p in prepared_root.iterdir() if p.is_dir()))

    spec = dataset_spec(dataset_for_regime(location.regime))
    if spec.device_ids:
        return tuple(sorted(spec.device_ids))

    prepared_root = prepared_root_for_regime(location.regime, base_dir=data_root)
    if not prepared_root.exists():
        return None
    return tuple(sorted(p.name for p in prepared_root.iterdir() if p.is_dir()))


def _read_manifest(path: Path) -> tuple[dict[str, Any] | None, ScoreCheckResult, ScoreCheckResult]:
    if not path.exists():
        present = ScoreCheckResult(
            code=ScoreCheckCode.MANIFEST_PRESENT,
            status=AuditStatus.MISSING,
            detail=f"Scoring manifest absent at {path}",
        )
        parseable = ScoreCheckResult(
            code=ScoreCheckCode.MANIFEST_PARSEABLE,
            status=AuditStatus.MISSING,
            detail="Cannot parse: manifest file is absent",
        )
        return None, present, parseable

    present = ScoreCheckResult(code=ScoreCheckCode.MANIFEST_PRESENT, status=AuditStatus.PASS)
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, present, ScoreCheckResult(
            code=ScoreCheckCode.MANIFEST_PARSEABLE,
            status=AuditStatus.FAIL,
            detail=f"Manifest JSON parse error: {exc}",
        )
    return manifest, present, ScoreCheckResult(
        code=ScoreCheckCode.MANIFEST_PARSEABLE, status=AuditStatus.PASS,
    )


def _check_required_fields(manifest: dict[str, Any]) -> ScoreCheckResult:
    missing = [field for field in _REQUIRED_MANIFEST_FIELDS if field not in manifest]
    if missing:
        return ScoreCheckResult(
            code=ScoreCheckCode.MANIFEST_FIELDS_PRESENT,
            status=AuditStatus.FAIL,
            detail=f"Missing required manifest fields: {missing}",
        )
    return ScoreCheckResult(code=ScoreCheckCode.MANIFEST_FIELDS_PRESENT, status=AuditStatus.PASS)


def _check_completion_status(manifest: dict[str, Any]) -> ScoreCheckResult:
    status = manifest.get("completion_status")
    if status != "complete":
        return ScoreCheckResult(
            code=ScoreCheckCode.MANIFEST_COMPLETION_STATUS,
            status=AuditStatus.FAIL,
            detail=f"completion_status is {status!r}; expected 'complete'",
        )
    return ScoreCheckResult(code=ScoreCheckCode.MANIFEST_COMPLETION_STATUS, status=AuditStatus.PASS)


def _check_sentinel(cell_dir: Path) -> ScoreCheckResult:
    sentinel = cell_dir / SCORING_SENTINEL
    if not sentinel.exists():
        return ScoreCheckResult(
            code=ScoreCheckCode.SCORING_SENTINEL_PRESENT,
            status=AuditStatus.MISSING,
            detail=f"{SCORING_SENTINEL} absent",
        )
    return ScoreCheckResult(code=ScoreCheckCode.SCORING_SENTINEL_PRESENT, status=AuditStatus.PASS)


def _check_regime(manifest: dict[str, Any], location: ScoreCellLocation) -> ScoreCheckResult:
    return _exact_match(
        ScoreCheckCode.REGIME_MATCH,
        actual=manifest.get("regime"),
        expected=location.regime.value,
    )


def _check_seed(manifest: dict[str, Any], location: ScoreCellLocation) -> ScoreCheckResult:
    return _exact_match(
        ScoreCheckCode.SEED_MATCH,
        actual=manifest.get("seed"),
        expected=location.seed,
    )


def _check_dataset(manifest: dict[str, Any], location: ScoreCellLocation) -> ScoreCheckResult:
    expected = dataset_for_regime(location.regime).value
    actual = manifest.get("dataset")
    if actual != expected:
        return ScoreCheckResult(
            code=ScoreCheckCode.DATASET_MATCH,
            status=AuditStatus.FAIL,
            detail=f"dataset {actual!r} does not match expected {expected!r} for {location.regime}",
        )
    return ScoreCheckResult(code=ScoreCheckCode.DATASET_MATCH, status=AuditStatus.PASS)


def _exact_match(code: ScoreCheckCode, *, actual: Any, expected: Any) -> ScoreCheckResult:
    if actual != expected:
        return ScoreCheckResult(
            code=code,
            status=AuditStatus.FAIL,
            detail=f"got {actual!r}, expected {expected!r}",
        )
    return ScoreCheckResult(code=code, status=AuditStatus.PASS)


def _check_clients_match_partition(
    manifest: dict[str, Any],
    expected_partition_clients: tuple[str, ...] | None,
) -> ScoreCheckResult:
    if expected_partition_clients is None:
        return ScoreCheckResult(
            code=ScoreCheckCode.CLIENT_IDS_MATCH_PARTITION,
            status=AuditStatus.MISSING,
            detail="Partition root not found; cannot cross-check client IDs",
        )
    declared = set(map(str, manifest.get("expected_client_ids", [])))
    expected_set = set(expected_partition_clients)
    if declared != expected_set:
        only_manifest = sorted(declared - expected_set)
        only_partition = sorted(expected_set - declared)
        return ScoreCheckResult(
            code=ScoreCheckCode.CLIENT_IDS_MATCH_PARTITION,
            status=AuditStatus.FAIL,
            detail=f"only_in_manifest={only_manifest}, only_in_partition={only_partition}",
        )
    return ScoreCheckResult(code=ScoreCheckCode.CLIENT_IDS_MATCH_PARTITION, status=AuditStatus.PASS)


def _check_expected_vs_actual(
    code: ScoreCheckCode, expected: list[Any], actual: list[Any],
) -> ScoreCheckResult:
    expected_set = set(map(str, expected))
    actual_set = set(map(str, actual))
    if expected_set != actual_set:
        return ScoreCheckResult(
            code=code,
            status=AuditStatus.FAIL,
            detail=f"missing={sorted(expected_set - actual_set)}, extra={sorted(actual_set - expected_set)}",
        )
    return ScoreCheckResult(code=code, status=AuditStatus.PASS)


def _check_split_directories(cell_dir: Path) -> ScoreCheckResult:
    missing = [stage.value for stage in SCORING_STAGES if not (cell_dir / stage.value).is_dir()]
    if missing:
        return ScoreCheckResult(
            code=ScoreCheckCode.SPLIT_DIRECTORIES_PRESENT,
            status=AuditStatus.FAIL,
            detail=f"missing split dirs: {missing}",
        )
    return ScoreCheckResult(code=ScoreCheckCode.SPLIT_DIRECTORIES_PRESENT, status=AuditStatus.PASS)


def _check_per_client_split_files(
    cell_dir: Path, expected_client_ids: list[str],
) -> ScoreCheckResult:
    missing: list[str] = []
    for stage in SCORING_STAGES:
        stage_dir = cell_dir / stage.value
        if not stage_dir.is_dir():
            continue
        for client_id in expected_client_ids:
            parquet = stage_dir / f"{client_id}.parquet"
            if not parquet.is_file():
                missing.append(f"{stage.value}/{client_id}.parquet")
    if missing:
        return ScoreCheckResult(
            code=ScoreCheckCode.PER_CLIENT_SPLIT_FILES_PRESENT,
            status=AuditStatus.FAIL,
            detail=f"missing per-client split files: {missing[:5]}{'…' if len(missing) > 5 else ''}",
        )
    return ScoreCheckResult(code=ScoreCheckCode.PER_CLIENT_SPLIT_FILES_PRESENT, status=AuditStatus.PASS)


def _check_parquet_schema(
    cell_dir: Path, expected_client_ids: list[str],
) -> tuple[ScoreCheckResult, ScoreCheckResult]:
    schema_errors: list[str] = []
    empty: list[str] = []
    for stage in SCORING_STAGES:
        stage_dir = cell_dir / stage.value
        if not stage_dir.is_dir():
            continue
        for client_id in expected_client_ids:
            parquet = stage_dir / f"{client_id}.parquet"
            if not parquet.is_file():
                continue
            try:
                validate_score_artifact(parquet)
            except (ValueError, TypeError) as exc:
                schema_errors.append(f"{stage.value}/{client_id}.parquet: {exc}")
                continue
            try:
                row_count = pq.read_metadata(parquet).num_rows
            except Exception as exc:  # noqa: BLE001
                schema_errors.append(f"{stage.value}/{client_id}.parquet: metadata read failed: {exc}")
                continue
            if row_count == 0 and stage != ScoringStage.TEST_ATTACK:
                empty.append(f"{stage.value}/{client_id}.parquet")
    schema_check = (
        ScoreCheckResult(
            code=ScoreCheckCode.PARQUET_SCHEMA_VALID,
            status=AuditStatus.FAIL,
            detail=f"{len(schema_errors)} schema errors; first: {schema_errors[0]}" if schema_errors else "",
        )
        if schema_errors
        else ScoreCheckResult(code=ScoreCheckCode.PARQUET_SCHEMA_VALID, status=AuditStatus.PASS)
    )
    empty_check = (
        ScoreCheckResult(
            code=ScoreCheckCode.PARQUET_NON_EMPTY,
            status=AuditStatus.FAIL,
            detail=f"empty score files: {empty}",
        )
        if empty
        else ScoreCheckResult(code=ScoreCheckCode.PARQUET_NON_EMPTY, status=AuditStatus.PASS)
    )
    return schema_check, empty_check


def _check_checkpoint(
    base_dir: Path,
    data_root: Path,
    location: ScoreCellLocation,
    manifest: dict[str, Any],
) -> tuple[ScoreCheckResult, ScoreCheckResult, ScoreCheckResult]:
    declared_hash = manifest.get("model_checkpoint_hash")
    declared_path = manifest.get("model_checkpoint_path")

    if not declared_hash or declared_hash == "NOT_PROVIDED":
        hash_field = ScoreCheckResult(
            code=ScoreCheckCode.CHECKPOINT_HASH_FIELD_PRESENT,
            status=AuditStatus.FAIL,
            detail=f"model_checkpoint_hash is {declared_hash!r}",
        )
        file_check = ScoreCheckResult(
            code=ScoreCheckCode.CHECKPOINT_FILE_PRESENT,
            status=AuditStatus.MISSING,
            detail="Skipped: hash field missing",
        )
        match_check = ScoreCheckResult(
            code=ScoreCheckCode.CHECKPOINT_HASH_MATCHES,
            status=AuditStatus.MISSING,
            detail="Skipped: hash field missing",
        )
        return hash_field, file_check, match_check
    hash_field = ScoreCheckResult(
        code=ScoreCheckCode.CHECKPOINT_HASH_FIELD_PRESENT, status=AuditStatus.PASS,
    )

    canonical = ExperimentLocator.for_main(base_dir, location.regime).checkpoint(
        location.seed, location.alpha,
    ) / MODEL_CHECKPOINT
    declared_full = data_root / declared_path if declared_path else canonical

    candidate = canonical if canonical.exists() else declared_full
    if not candidate.exists():
        file_check = ScoreCheckResult(
            code=ScoreCheckCode.CHECKPOINT_FILE_PRESENT,
            status=AuditStatus.MISSING,
            detail=f"Checkpoint not found at canonical {canonical} or declared {declared_full}",
        )
        match_check = ScoreCheckResult(
            code=ScoreCheckCode.CHECKPOINT_HASH_MATCHES,
            status=AuditStatus.MISSING,
            detail="Skipped: checkpoint file missing",
        )
        return hash_field, file_check, match_check

    file_check = ScoreCheckResult(code=ScoreCheckCode.CHECKPOINT_FILE_PRESENT, status=AuditStatus.PASS)
    actual_hash = hash_file(candidate)
    if actual_hash != declared_hash:
        match_check = ScoreCheckResult(
            code=ScoreCheckCode.CHECKPOINT_HASH_MATCHES,
            status=AuditStatus.FAIL,
            detail=f"declared={declared_hash}, actual={actual_hash} (at {candidate})",
        )
    else:
        match_check = ScoreCheckResult(
            code=ScoreCheckCode.CHECKPOINT_HASH_MATCHES, status=AuditStatus.PASS,
        )
    return hash_field, file_check, match_check


def _overall_status(checks: list[ScoreCheckResult]) -> AuditStatus:
    statuses = {c.status for c in checks}
    if AuditStatus.FAIL in statuses:
        return AuditStatus.FAIL
    if AuditStatus.MISSING in statuses:
        return AuditStatus.PARTIAL
    return AuditStatus.PASS


def _alpha_to_text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, float) and math.isinf(value):
        return alpha_label(value)
    if isinstance(value, (int, float)):
        return alpha_label(float(value))
    return str(value)


def verify_score_cell(
    cell_dir: Path, base_dir: Path, *, data_root: Path | None = None,
) -> ScoreCellVerification:
    """Verify one score cell directory and return a structured per-cell report.

    ``base_dir`` is the experiment root (e.g. ``outputs/``); ``cell_dir`` is the cell directory
    under ``<base_dir>/scores/<regime>/seed_N[/alpha_*]/``. ``data_root`` defaults to
    ``base_dir.parent`` (repo root containing ``data/processed/``).
    """
    cell_dir = cell_dir.resolve()
    base_dir = base_dir.resolve()
    resolved_data_root = (data_root or base_dir.parent).resolve()
    rel = cell_dir.relative_to(base_dir / "scores")
    parts = rel.parts
    regime = Regime(parts[0])
    seed_segment = parts[1]
    seed = int(seed_segment.removeprefix("seed_"))
    alpha = (
        None
        if len(parts) <= 2
        else _alpha_from_dir(parts[2])
    )
    location = ScoreCellLocation(regime=regime, seed=seed, alpha=alpha, cell_dir=cell_dir)
    return _verify_at_location(base_dir, resolved_data_root, location)


def _alpha_from_dir(name: str) -> float | None:
    from datp.core.identity import parse_alpha_dir  # noqa: PLC0415

    return parse_alpha_dir(name)


def _verify_at_location(
    base_dir: Path, data_root: Path, location: ScoreCellLocation,
) -> ScoreCellVerification:
    cell_dir = location.cell_dir
    manifest_path = cell_dir / SCORING_MANIFEST_FILE
    checks: list[ScoreCheckResult] = []

    manifest, present, parseable = _read_manifest(manifest_path)
    checks.append(present)
    checks.append(parseable)
    checks.append(_check_sentinel(cell_dir))
    checks.append(_check_split_directories(cell_dir))

    if manifest is None:
        return ScoreCellVerification(
            cell_dir=str(cell_dir),
            regime=location.regime,
            seed=location.seed,
            alpha=alpha_label(location.alpha),
            dataset=dataset_for_regime(location.regime).value,
            expected_client_ids=[],
            expected_splits=[],
            checks=checks,
            overall_status=_overall_status(checks),
        )

    fields_check = _check_required_fields(manifest)
    checks.append(fields_check)
    if fields_check.status != AuditStatus.PASS:
        return ScoreCellVerification(
            cell_dir=str(cell_dir),
            regime=location.regime,
            seed=location.seed,
            alpha=alpha_label(location.alpha),
            dataset=str(manifest.get("dataset", "")),
            expected_client_ids=list(map(str, manifest.get("expected_client_ids", []))),
            expected_splits=list(map(str, manifest.get("expected_splits", []))),
            checks=checks,
            overall_status=_overall_status(checks),
        )

    checks.append(_check_completion_status(manifest))
    checks.append(_check_regime(manifest, location))
    checks.append(_check_seed(manifest, location))
    checks.append(_check_dataset(manifest, location))

    expected_client_ids = list(map(str, manifest["expected_client_ids"]))
    expected_splits = list(map(str, manifest["expected_splits"]))

    checks.append(_check_expected_vs_actual(
        ScoreCheckCode.EXPECTED_VS_ACTUAL_CLIENTS,
        manifest["expected_client_ids"], manifest["actual_client_ids"],
    ))
    checks.append(_check_expected_vs_actual(
        ScoreCheckCode.EXPECTED_VS_ACTUAL_SPLITS,
        manifest["expected_splits"], manifest["actual_splits"],
    ))
    checks.append(_check_clients_match_partition(
        manifest, _expected_partition_clients(data_root, location),
    ))
    checks.append(_check_per_client_split_files(cell_dir, expected_client_ids))

    schema_check, empty_check = _check_parquet_schema(cell_dir, expected_client_ids)
    checks.append(schema_check)
    checks.append(empty_check)

    hash_field, file_check, match_check = _check_checkpoint(base_dir, data_root, location, manifest)
    checks.append(hash_field)
    checks.append(file_check)
    checks.append(match_check)

    return ScoreCellVerification(
        cell_dir=str(cell_dir),
        regime=location.regime,
        seed=location.seed,
        alpha=_alpha_to_text(manifest.get("alpha")),
        dataset=str(manifest["dataset"]),
        expected_client_ids=expected_client_ids,
        expected_splits=expected_splits,
        checks=checks,
        overall_status=_overall_status(checks),
    )


def verify_all_score_cells(
    base_dir: Path,
    *,
    data_root: Path | None = None,
    write_reports: bool = False,
) -> list[ScoreCellVerification]:
    """Verify all discoverable score cells; optionally write a JSON report per cell + an index."""
    resolved_base = base_dir.resolve()
    resolved_data_root = (data_root or resolved_base.parent).resolve()
    results: list[ScoreCellVerification] = []
    for location in iter_score_cells(base_dir):
        report = _verify_at_location(resolved_base, resolved_data_root, location)
        results.append(report)
        if write_reports:
            write_json(
                location.cell_dir / SCORE_CELL_VERIFICATION_JSON,
                report.model_dump(mode="json"),
            )
    if write_reports:
        write_json(
            resolved_base / "scores" / SCORE_CELL_VERIFICATION_INDEX_JSON,
            {"cells": [r.model_dump(mode="json") for r in results]},
        )
    return results


def assert_score_column() -> str:
    """Sanity hook for callers; ensures the verifier uses the canonical score column name."""
    return SCORE_COLUMN
