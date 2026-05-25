"""Shared metric and threshold evaluation helpers for analyses."""

from __future__ import annotations

import math
from collections.abc import Sequence

import numpy as np

from datp.baselines.common.thresholds import derive_threshold
from datp.baselines.common.types import ThresholdResult
from datp.config.models import ThresholdConfig
from datp.core.enums import Baseline, Regime
from datp.evaluation.metrics import (
    ClientMetrics,
    EvaluationResult,
    build_evaluation_result,
    compute_client_metrics,
)
from datp.evaluation.score_loading import ScoreProvider

_CV_ZERO_MEAN_TOLERANCE = 1e-12


def compute_cv(values: np.ndarray) -> float:
    if values.size < 2:
        return 0.0
    mean = float(np.mean(values))
    if math.isclose(mean, 0.0, abs_tol=_CV_ZERO_MEAN_TOLERANCE):
        return 0.0
    return float(np.std(values, ddof=1) / mean)


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
    per_client: list[ClientMetrics] = []
    eligible_ids: list[str] = []
    pending_ids: list[str] = []
    eval_incomplete_ids: list[str] = []

    for client_threshold in threshold_result.client_thresholds:
        client_id = client_threshold.client_id
        benign, attack = score_provider.load_test_scores(client_id)
        per_client.append(
            compute_client_metrics(
                client_id, benign, attack, client_threshold.threshold
            )
        )

        (pending_ids if client_threshold.calibration_pending else eligible_ids).append(
            client_id
        )
        if attack.size == 0:
            eval_incomplete_ids.append(client_id)

    return build_evaluation_result(
        baseline=threshold_result.strategy,
        regime=regime,
        seed=seed,
        alpha=alpha,
        per_client=per_client,
        eligible_ids=eligible_ids,
        pending_ids=pending_ids,
        eval_incomplete_ids=eval_incomplete_ids,
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
    per_client: list[ClientMetrics] = []
    eligible_ids: list[str] = []
    eval_incomplete_ids: list[str] = []

    for client_id in client_ids:
        benign, attack = score_provider.load_test_scores(client_id)
        per_client.append(compute_client_metrics(client_id, benign, attack, threshold))
        eligible_ids.append(client_id)
        if attack.size == 0:
            eval_incomplete_ids.append(client_id)

    return build_evaluation_result(
        baseline=baseline,
        regime=regime,
        seed=seed,
        alpha=alpha,
        per_client=per_client,
        eligible_ids=eligible_ids,
        pending_ids=[],
        eval_incomplete_ids=eval_incomplete_ids,
    )
