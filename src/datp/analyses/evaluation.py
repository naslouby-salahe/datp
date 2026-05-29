"""Shared metric and threshold evaluation helpers for analyses."""

from __future__ import annotations

import math
from collections.abc import Sequence

import numpy as np

from datp.thresholding.thresholds import derive_threshold
from datp.config.models import ThresholdConfig
from datp.core.enums import Baseline, Regime
from datp.evaluation.metrics import (
    ClientEvaluationRecord,
    EvaluationResult,
    build_evaluation_result,
    compute_client_record,
)
from datp.scoring.loading import ScoreProvider
from datp.statistics.constants import CV_DDOF
from datp.statistics.cv import cv as _canonical_cv
from datp.thresholding.types import ClientThreshold, ThresholdResult


def compute_cv(values: np.ndarray) -> float:
    """CV for analyses — delegates to the canonical implementation in statistics.cv."""
    result = _canonical_cv(values, ddof=CV_DDOF)
    # Canonical returns nan for <2 elements or zero-mean; analyses historically returned 0.0
    if math.isnan(result):
        return 0.0
    return result


def derive_tau_global(
    cal_errors: dict[str, np.ndarray],
    *,
    regime: Regime,
    threshold_cfg: ThresholdConfig,
    q: float | None = None,
) -> tuple[float, ThresholdResult]:
    """Derive B1 once and return ``(tau_global, b1_result)``."""
    q_value = threshold_cfg.q if q is None else q
    b1_result = derive_threshold(
        Baseline.B1,
        cal_errors,
        n_min=threshold_cfg.n_min,
        q=q_value,
        tau_global=0.0,
        regime=regime,
        threshold_cfg=threshold_cfg,
    )
    return float(b1_result.tau_global), b1_result


def evaluate_threshold_result(
    threshold_result: ThresholdResult,
    score_provider: ScoreProvider,
    regime: Regime,
    seed: int,
    alpha: float | None,
) -> EvaluationResult:
    clients: list[ClientEvaluationRecord] = []
    eligible_ids: list[str] = []
    pending_ids: list[str] = []
    incomplete_ids: list[str] = []

    for ct in threshold_result.client_thresholds:
        client_id = ct.client_id
        benign, attack = score_provider.load_test_scores(client_id)
        clients.append(compute_client_record(client_id, benign, attack, ct))

        (pending_ids if ct.calibration_pending else eligible_ids).append(client_id)
        if attack.size == 0:
            incomplete_ids.append(client_id)

    return build_evaluation_result(
        baseline=threshold_result.strategy,
        regime=regime,
        seed=seed,
        alpha=alpha,
        clients=tuple(clients),
        eligible_ids=tuple(eligible_ids),
        pending_ids=tuple(pending_ids),
        incomplete_ids=tuple(incomplete_ids),
    )


def evaluate_single_threshold(
    *,
    baseline: Baseline,
    threshold: float,
    score_provider: ScoreProvider,
    client_ids: Sequence[str],
    regime: Regime,
    seed: int,
    alpha: float | None,
) -> EvaluationResult:
    """Evaluate a single global threshold across all clients."""
    clients: list[ClientEvaluationRecord] = []
    eligible_ids: list[str] = []
    incomplete_ids: list[str] = []

    for client_id in client_ids:
        benign, attack = score_provider.load_test_scores(client_id)
        ct = ClientThreshold(
            client_id=client_id,
            threshold=threshold,
            calibration_pending=False,
            strategy=baseline,
        )
        clients.append(compute_client_record(client_id, benign, attack, ct))
        eligible_ids.append(client_id)
        if attack.size == 0:
            incomplete_ids.append(client_id)

    return build_evaluation_result(
        baseline=baseline,
        regime=regime,
        seed=seed,
        alpha=alpha,
        clients=tuple(clients),
        eligible_ids=tuple(eligible_ids),
        pending_ids=(),
        incomplete_ids=tuple(incomplete_ids),
    )
