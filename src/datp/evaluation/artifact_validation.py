from __future__ import annotations

from collections.abc import Mapping
from typing import NamedTuple
from typing import Any

REQUIRED_METRICS_FIELDS = (
    "schema_version",
    "metric_schema_version",
    "threshold_schema_version",
    "run_id",
    "dataset",
    "regime",
    "baseline",
    "seed",
    "threshold_scope",
    "threshold_strategy_name",
    "client_count",
    "eligible_count",
    "pending_count",
    "eval_incomplete_count",
    "coverage_ratio",
    "eligible_ids",
    "pending_ids",
    "eval_incomplete_ids",
    "per_client",
    "aggregate_metrics",
    "provenance",
)

REQUIRED_CLIENT_FIELDS = (
    "confusion_matrix",
    "n_benign",
    "n_attack",
    "benign_count",
    "attack_count",
    "calibration_pending",
    "evaluation_incomplete",
    "threshold_value",
    "threshold_source",
)

REQUIRED_PROVENANCE_FIELDS = (
    "config_identity",
    "split_manifest_identity",
    "model_checkpoint_identity",
    "score_artifact_identity",
    "metric_code_version",
    "threshold_code_version",
    "package_version",
    "generated_at_utc",
)


def client_rows(payload: Mapping[str, Any]) -> list[tuple[str, Mapping[str, Any]]]:
    raw = payload["per_client"]
    if isinstance(raw, Mapping):
        return [(str(cid), row) for cid, row in raw.items()]
    return [(str(row["client_id"]), row) for row in raw]


_VAGUE_PROVENANCE = {"UNKNOWN", "unknown"}

# MISSING_* prefix means the hash could not be resolved at serialization time.
_HASH_IDENTITY_FIELDS = frozenset(
    {
        "config_identity",
        "split_manifest_identity",
        "model_checkpoint_identity",
        "score_artifact_identity",
    }
)


class ValidationIds(NamedTuple):
    eligible: set[str]
    pending: set[str]
    incomplete: set[str]
    row: set[str]


class ClientRowContext(NamedTuple):
    pending_ids: set[str]
    incomplete_ids: set[str]
    module: str


def _missing_payload_fields(payload: Mapping[str, Any]) -> list[str]:
    missing = [field for field in REQUIRED_METRICS_FIELDS if field not in payload]
    provenance = payload.get("provenance")
    if isinstance(provenance, Mapping):
        missing.extend(
            f"provenance.{field}"
            for field in REQUIRED_PROVENANCE_FIELDS
            if field not in provenance
        )
    else:
        missing.append("provenance.*")
    return missing


def _missing_payload_error(missing: list[str], *, module: str) -> str:
    return f"[{module}] MISSING metrics fields: {', '.join(sorted(missing))}"


def _payload_validation_ids(
    payload: Mapping[str, Any],
    row_ids: set[str],
) -> ValidationIds:
    return ValidationIds(
        eligible={str(cid) for cid in payload["eligible_ids"]},
        pending={str(cid) for cid in payload["pending_ids"]},
        incomplete={str(cid) for cid in payload["eval_incomplete_ids"]},
        row=row_ids,
    )


def _client_row_context(
    validation_ids: ValidationIds,
    *,
    module: str,
) -> ClientRowContext:
    return ClientRowContext(validation_ids.pending, validation_ids.incomplete, module)


def _validate_provenance(provenance: Mapping[str, Any], *, module: str) -> list[str]:
    errors: list[str] = []
    vague = [
        field
        for field in REQUIRED_PROVENANCE_FIELDS
        if str(provenance[field]) in _VAGUE_PROVENANCE
    ]
    if vague:
        errors.append(
            f"[{module}] FAIL vague UNKNOWN provenance fields: {', '.join(sorted(vague))}"
        )
    unresolved = [
        field
        for field in _HASH_IDENTITY_FIELDS
        if str(provenance[field]).startswith("MISSING_")
    ]
    if unresolved:
        errors.append(
            f"[{module}] FAIL unresolved required provenance (MISSING_*) in: {', '.join(sorted(unresolved))}"
        )
    return errors


def _missing_row_ids(ids: ValidationIds) -> bool:
    return bool(
        ids.eligible - ids.row or ids.pending - ids.row or ids.incomplete - ids.row
    )


def _validate_membership_ids(ids: ValidationIds, *, module: str) -> list[str]:
    errors: list[str] = []
    if ids.eligible & ids.pending:
        errors.append(
            f"[{module}] FAIL eligible_ids overlap pending_ids: {sorted(ids.eligible & ids.pending)}"
        )
    if _missing_row_ids(ids):
        errors.append(
            f"[{module}] FAIL eligibility ids not present in per_client: "
            f"eligible={sorted(ids.eligible - ids.row)}, pending={sorted(ids.pending - ids.row)}, "
            f"eval_incomplete={sorted(ids.incomplete - ids.row)}"
        )
    return errors


def _missing_client_fields(row: Mapping[str, Any]) -> list[str]:
    missing = [field for field in REQUIRED_CLIENT_FIELDS if field not in row]
    cm = row.get("confusion_matrix")
    if not isinstance(cm, Mapping):
        missing.append("confusion_matrix.tp/fp/tn/fn")
        return missing
    missing.extend(
        f"confusion_matrix.{key}" for key in ("tp", "fp", "tn", "fn") if key not in cm
    )
    return missing


def _validate_client_row(
    cid: str,
    row: Mapping[str, Any],
    *,
    context: ClientRowContext,
) -> list[str]:
    errors: list[str] = []
    missing_client = _missing_client_fields(row)
    if missing_client:
        errors.append(
            f"[{context.module}] MISSING per-client fields for {cid}: {', '.join(sorted(missing_client))}"
        )
    if cid in context.pending_ids and row.get("calibration_pending") is not True:
        errors.append(
            f"[{context.module}] FAIL pending client {cid} missing calibration_pending=true"
        )
    if cid in context.incomplete_ids and row.get("evaluation_incomplete") is not True:
        errors.append(
            f"[{context.module}] FAIL eval-incomplete client {cid} missing evaluation_incomplete=true"
        )
    return errors


def validate_metrics_payload(payload: Mapping[str, Any], *, module: str) -> list[str]:
    missing = _missing_payload_fields(payload)
    provenance = payload.get("provenance")
    if missing:
        return [_missing_payload_error(missing, module=module)]

    errors: list[str] = []
    if isinstance(provenance, Mapping):
        errors.extend(_validate_provenance(provenance, module=module))
    rows = client_rows(payload)
    row_ids = {cid for cid, _ in rows}
    validation_ids = _payload_validation_ids(payload, row_ids)
    errors.extend(_validate_membership_ids(validation_ids, module=module))
    row_context = _client_row_context(validation_ids, module=module)
    for cid, row in rows:
        errors.extend(
            _validate_client_row(
                cid,
                row,
                context=row_context,
            )
        )
    return errors
