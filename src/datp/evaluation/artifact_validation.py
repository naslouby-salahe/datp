from __future__ import annotations

from collections.abc import Mapping
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


def validate_metrics_payload(payload: Mapping[str, Any], *, module: str) -> list[str]:
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
    if missing:
        return [f"[{module}] MISSING metrics fields: {', '.join(sorted(missing))}"]

    errors: list[str] = []
    if isinstance(provenance, Mapping):
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
    ids = {str(cid) for cid in payload["eligible_ids"]}
    pending = {str(cid) for cid in payload["pending_ids"]}
    incomplete = {str(cid) for cid in payload["eval_incomplete_ids"]}
    if ids & pending:
        errors.append(
            f"[{module}] FAIL eligible_ids overlap pending_ids: {sorted(ids & pending)}"
        )
    rows = client_rows(payload)
    row_ids = {cid for cid, _ in rows}
    if ids - row_ids or pending - row_ids or incomplete - row_ids:
        errors.append(
            f"[{module}] FAIL eligibility ids not present in per_client: "
            f"eligible={sorted(ids - row_ids)}, pending={sorted(pending - row_ids)}, "
            f"eval_incomplete={sorted(incomplete - row_ids)}"
        )
    for cid, row in rows:
        missing_client = [field for field in REQUIRED_CLIENT_FIELDS if field not in row]
        cm = row.get("confusion_matrix")
        if not isinstance(cm, Mapping):
            missing_client.append("confusion_matrix.tp/fp/tn/fn")
        else:
            missing_client.extend(
                f"confusion_matrix.{key}"
                for key in ("tp", "fp", "tn", "fn")
                if key not in cm
            )
        if missing_client:
            errors.append(
                f"[{module}] MISSING per-client fields for {cid}: {', '.join(sorted(missing_client))}"
            )
        if cid in pending and row.get("calibration_pending") is not True:
            errors.append(
                f"[{module}] FAIL pending client {cid} missing calibration_pending=true"
            )
        if cid in incomplete and row.get("evaluation_incomplete") is not True:
            errors.append(
                f"[{module}] FAIL eval-incomplete client {cid} missing evaluation_incomplete=true"
            )
    return errors
