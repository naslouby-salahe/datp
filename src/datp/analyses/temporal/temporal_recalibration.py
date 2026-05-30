# SPDX-License-Identifier: Proprietary
"""Temporal recalibration probe (T25 / PRE_CODING_PLAN §6.5).

Tests whether per-client thresholds degrade over time and whether one-shot
benign-only recalibration can recover performance. This is a temporal probe,
not a concept-drift solution.

CICIoT2023 path is permanently suppressed: TEMPORAL_REJECTED_NO_TIMESTAMPS.
Edge-IIoTset path uses frame.time for chronological ordering.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from datp.analyses.types import FrozenModel
from datp.core.enums import (
    Baseline,
    TemporalOutcome,
)
from datp.evaluation.metrics import compute_client_record
from datp.thresholding.types import ClientThreshold

from datp.analyses.constants import TEMPORAL_TABLE_CSV

# Recovery classification thresholds (locked per PRE_CODING_PLAN §6.5)
_RECOVERY_HELPS_THRESHOLD: float = 0.10
_RECOVERY_NEUTRAL_THRESHOLD: float = 0.0


class TemporalResultRow(FrozenModel):
    """One row per (client, baseline) in the temporal recalibration table."""

    client_id: str
    baseline: Baseline
    cv_fpr_frozen: float
    cv_fpr_recalibrated: float
    recovery_ratio: float | None
    outcome: TemporalOutcome
    n_early_benign: int
    n_late_benign: int
    n_late_attack: int


@dataclass(slots=True)
class TemporalProbeResult:
    rows: list[TemporalResultRow]
    overall_outcome: TemporalOutcome
    n_clients: int
    n_feasible: int
    n_helps: int
    n_neutral: int
    n_hurts: int


@dataclass(frozen=True, slots=True)
class _TemporalInput:
    """Collapsed input for temporal recalibration evaluation."""

    early_benign: dict[str, np.ndarray]
    late_benign: dict[str, np.ndarray]
    late_attack: dict[str, np.ndarray]
    thresholds_frozen: dict[Baseline, dict[str, float]]
    thresholds_recalibrated: dict[Baseline, dict[str, float]]
    client_ids: list[str]
    n_min: int


def _client_is_covered(
    eb: np.ndarray | None,
    lb: np.ndarray | None,
    n_min: int,
) -> bool:
    """True when both early and late benign windows have sufficient samples."""
    return eb is not None and eb.size >= n_min and lb is not None and lb.size >= n_min


def _client_is_feasible(
    early_benign_errors: np.ndarray | None,
    late_benign_errors: np.ndarray | None,
    late_attack_errors: np.ndarray | None,
    n_min: int,
) -> bool:
    """True when all three score arrays are present with sufficient benign samples."""
    return (
        early_benign_errors is not None
        and late_benign_errors is not None
        and late_attack_errors is not None
        and early_benign_errors.size >= n_min
        and late_benign_errors.size >= n_min
    )


def _check_temporal_feasibility(inp: _TemporalInput) -> TemporalOutcome:
    """Check preconditions for temporal recalibration.

    Returns TEMPORAL_FEASIBLE or a rejection reason.
    """
    if not inp.client_ids:
        return TemporalOutcome.TEMPORAL_INFEASIBLE

    n_covered = sum(
        1
        for cid in inp.client_ids
        if _client_is_covered(
            inp.early_benign.get(cid),
            inp.late_benign.get(cid),
            inp.n_min,
        )
    )

    if n_covered < len(inp.client_ids) * 0.5:
        return TemporalOutcome.TEMPORAL_REJECTED_LOW_COVERAGE

    has_attack = any(
        inp.late_attack.get(cid) is not None and inp.late_attack[cid].size > 0
        for cid in inp.client_ids
    )
    if not has_attack:
        return TemporalOutcome.TEMPORAL_REJECTED_INSUFFICIENT_ATTACKS

    return TemporalOutcome.TEMPORAL_FEASIBLE


def _classify_recovery(recovery_ratio: float) -> TemporalOutcome:
    """Classify recovery ratio per locked thresholds."""
    if recovery_ratio > _RECOVERY_HELPS_THRESHOLD:
        return TemporalOutcome.TEMPORAL_HELPS
    if recovery_ratio >= _RECOVERY_NEUTRAL_THRESHOLD:
        return TemporalOutcome.TEMPORAL_NEUTRAL
    return TemporalOutcome.TEMPORAL_HURTS


def _determine_overall_outcome(
    n_helps: int,
    n_neutral: int,
    n_hurts: int,
) -> TemporalOutcome:
    """Majority vote across all temporal rows."""
    if n_helps >= n_neutral and n_helps >= n_hurts:
        return TemporalOutcome.TEMPORAL_HELPS
    if n_neutral >= n_hurts:
        return TemporalOutcome.TEMPORAL_NEUTRAL
    return TemporalOutcome.TEMPORAL_HURTS


def _evaluate_baseline_row(
    client_id: str,
    baseline: Baseline,
    late_benign: np.ndarray,
    late_attack: np.ndarray,
    tau_frozen: float,
    tau_recal: float,
    n_early_benign: int,
    n_late_attack: int,
) -> tuple[TemporalResultRow, TemporalOutcome]:
    """Compute one (client, baseline) temporal row.

    Returns (row, outcome) for counting.
    """
    frozen_metric = compute_client_record(
        client_id,
        late_benign,
        late_attack,
        ClientThreshold(
            client_id=client_id,
            threshold=tau_frozen,
            calibration_pending=False,
            strategy=Baseline.B2,
        ),
    )
    cv_frozen = (
        frozen_metric.metrics.fpr if not np.isnan(frozen_metric.metrics.fpr) else 0.0
    )

    recal_metric = compute_client_record(
        client_id,
        late_benign,
        late_attack,
        ClientThreshold(
            client_id=client_id,
            threshold=tau_recal,
            calibration_pending=False,
            strategy=Baseline.B2,
        ),
    )
    cv_recal = (
        recal_metric.metrics.fpr if not np.isnan(recal_metric.metrics.fpr) else 0.0
    )

    if cv_frozen > 0:
        recovery_ratio: float | None = (cv_frozen - cv_recal) / cv_frozen
    else:
        recovery_ratio = None

    outcome = (
        _classify_recovery(recovery_ratio)
        if recovery_ratio is not None
        else TemporalOutcome.TEMPORAL_INFEASIBLE
    )

    row = TemporalResultRow(
        client_id=client_id,
        baseline=baseline,
        cv_fpr_frozen=cv_frozen,
        cv_fpr_recalibrated=cv_recal,
        recovery_ratio=recovery_ratio,
        outcome=outcome,
        n_early_benign=n_early_benign,
        n_late_benign=int(late_benign.size),
        n_late_attack=n_late_attack,
    )
    return row, outcome


def _evaluate_feasible_clients(inp: _TemporalInput) -> TemporalProbeResult:
    """Evaluate all temporally feasible clients across B1, B2, B4."""
    rows: list[TemporalResultRow] = []
    counts = {
        TemporalOutcome.TEMPORAL_HELPS: 0,
        TemporalOutcome.TEMPORAL_NEUTRAL: 0,
        TemporalOutcome.TEMPORAL_HURTS: 0,
    }
    n_feasible = 0

    for cid in inp.client_ids:
        early_benign_errors = inp.early_benign.get(cid)
        late_benign_errors = inp.late_benign.get(cid)
        late_attack_errors = inp.late_attack.get(cid)

        if not _client_is_feasible(
            early_benign_errors, late_benign_errors, late_attack_errors, inp.n_min
        ):
            continue
        n_feasible += 1
        if (
            early_benign_errors is None
            or late_benign_errors is None
            or late_attack_errors is None
        ):
            continue

        n_early_benign = int(early_benign_errors.size)
        n_late_attack = int(late_attack_errors.size)

        for baseline in (Baseline.B1, Baseline.B2, Baseline.B4):
            tau_frozen = inp.thresholds_frozen.get(baseline, {}).get(cid)
            tau_recal = inp.thresholds_recalibrated.get(baseline, {}).get(cid)

            if tau_frozen is None or tau_recal is None:
                continue

            row, outcome = _evaluate_baseline_row(
                cid,
                baseline,
                late_benign_errors,
                late_attack_errors,
                tau_frozen,
                tau_recal,
                n_early_benign,
                n_late_attack,
            )
            rows.append(row)
            if outcome in counts:
                counts[outcome] += 1

    return TemporalProbeResult(
        rows=rows,
        overall_outcome=_determine_overall_outcome(
            counts[TemporalOutcome.TEMPORAL_HELPS],
            counts[TemporalOutcome.TEMPORAL_NEUTRAL],
            counts[TemporalOutcome.TEMPORAL_HURTS],
        ),
        n_clients=len(inp.client_ids),
        n_feasible=n_feasible,
        n_helps=counts[TemporalOutcome.TEMPORAL_HELPS],
        n_neutral=counts[TemporalOutcome.TEMPORAL_NEUTRAL],
        n_hurts=counts[TemporalOutcome.TEMPORAL_HURTS],
    )


def evaluate_temporal_recalibration(
    early_benign: dict[str, np.ndarray],
    late_benign: dict[str, np.ndarray],
    late_attack: dict[str, np.ndarray],
    thresholds_frozen: dict[Baseline, dict[str, float]],
    thresholds_recalibrated: dict[Baseline, dict[str, float]],
    client_ids: list[str],
    n_min: int,
) -> TemporalProbeResult:
    """Evaluate frozen vs recalibrated per-client thresholds over a temporal split."""
    inp = _TemporalInput(
        early_benign=early_benign,
        late_benign=late_benign,
        late_attack=late_attack,
        thresholds_frozen=thresholds_frozen,
        thresholds_recalibrated=thresholds_recalibrated,
        client_ids=client_ids,
        n_min=n_min,
    )
    feasibility = _check_temporal_feasibility(inp)
    if feasibility != TemporalOutcome.TEMPORAL_FEASIBLE:
        return TemporalProbeResult(
            rows=[],
            overall_outcome=feasibility,
            n_clients=len(client_ids),
            n_feasible=0,
            n_helps=0,
            n_neutral=0,
            n_hurts=0,
        )
    return _evaluate_feasible_clients(inp)


def write_temporal_table(result: TemporalProbeResult, output_dir: Path) -> None:
    """Write temporal recalibration table as CSV."""
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / TEMPORAL_TABLE_CSV
    fieldnames = list(TemporalResultRow.model_fields)
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in result.rows:
            writer.writerow(row.model_dump(mode="json"))


def compute_recovery_ratio(
    cv_fpr_frozen: float,
    cv_fpr_recalibrated: float,
) -> float | None:
    """Recovery ratio = (frozen − recalibrated) / frozen.

    Positive means recalibration reduced CV(FPR). Returns None when
    frozen CV(FPR) is zero or negative (undefined ratio).
    """
    if cv_fpr_frozen <= 0:
        return None
    return (cv_fpr_frozen - cv_fpr_recalibrated) / cv_fpr_frozen
