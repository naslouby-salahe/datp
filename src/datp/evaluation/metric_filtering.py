"""Calibration-Pending clients are excluded from personalized dispersion metrics."""

from __future__ import annotations

import math

import attrs
import numpy as np

from datp.evaluation.metrics import ClientMetrics


@attrs.define(frozen=True, slots=True)
class FilteredMetrics:
    """fpr_eligible covers all eligible clients; tpr_eligible/ba_eligible/f1_eligible additionally exclude evaluation-incomplete clients."""

    fpr_eligible: np.ndarray
    tpr_eligible: np.ndarray
    ba_eligible: np.ndarray
    f1_eligible: np.ndarray


def filter_eligible_metrics(
    per_client: list[ClientMetrics],
    eligible_ids: list[str],
    eval_incomplete_ids: list[str] | None,
) -> FilteredMetrics:
    eligible_set = set(eligible_ids)
    incomplete_set = set() if eval_incomplete_ids is None else set(eval_incomplete_ids)

    fpr_list: list[float] = []
    tpr_list: list[float] = []
    ba_list: list[float] = []
    f1_list: list[float] = []

    for cm in per_client:
        if cm.client_id not in eligible_set:
            continue
        fpr_list.append(cm.fpr)
        if cm.client_id not in incomplete_set:
            if not math.isnan(cm.tpr):
                tpr_list.append(cm.tpr)
            if not math.isnan(cm.balanced_accuracy):
                ba_list.append(cm.balanced_accuracy)
            if not math.isnan(cm.macro_f1):
                f1_list.append(cm.macro_f1)

    return FilteredMetrics(
        fpr_eligible=np.array(fpr_list, dtype=np.float64),
        tpr_eligible=np.array(tpr_list, dtype=np.float64),
        ba_eligible=np.array(ba_list, dtype=np.float64),
        f1_eligible=np.array(f1_list, dtype=np.float64),
    )
