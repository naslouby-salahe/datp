"""Calibration-Pending clients are excluded from personalized dispersion metrics."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from datp.evaluation.metrics import ClientEvaluationRecord


@dataclass(frozen=True, slots=True)
class FilteredMetrics:
    """fpr_eligible covers all eligible clients; tpr_eligible/ba_eligible/f1_eligible additionally exclude evaluation-incomplete clients."""

    fpr_eligible: np.ndarray
    tpr_eligible: np.ndarray
    ba_eligible: np.ndarray
    f1_eligible: np.ndarray


def filter_eligible_metrics(
    clients: tuple[ClientEvaluationRecord, ...] | list[ClientEvaluationRecord],
    eligible_ids: tuple[str, ...] | list[str],
    incomplete_ids: tuple[str, ...] | list[str] | None,
) -> FilteredMetrics:
    eligible_set = set(eligible_ids)
    incomplete_set = set() if incomplete_ids is None else set(incomplete_ids)

    fpr_list: list[float] = []
    tpr_list: list[float] = []
    ba_list: list[float] = []
    f1_list: list[float] = []

    for cr in clients:
        if cr.client_id not in eligible_set:
            continue
        fpr_list.append(cr.metrics.fpr)
        if cr.client_id not in incomplete_set:
            if not math.isnan(cr.metrics.tpr):
                tpr_list.append(cr.metrics.tpr)
            if not math.isnan(cr.metrics.balanced_accuracy):
                ba_list.append(cr.metrics.balanced_accuracy)
            if not math.isnan(cr.metrics.macro_f1):
                f1_list.append(cr.metrics.macro_f1)

    return FilteredMetrics(
        fpr_eligible=np.array(fpr_list, dtype=np.float64),
        tpr_eligible=np.array(tpr_list, dtype=np.float64),
        ba_eligible=np.array(ba_list, dtype=np.float64),
        f1_eligible=np.array(f1_list, dtype=np.float64),
    )
