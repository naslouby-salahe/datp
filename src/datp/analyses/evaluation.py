"""Shared metric and threshold evaluation helpers for analyses."""

from __future__ import annotations

import math
from collections.abc import Sequence

import numpy as np

from datp.thresholding.thresholds import derive_threshold
from datp.config.models import ThresholdConfig
from datp.core.enums import Baseline, Regime
from datp.evaluation.metrics import (
    EvaluationResult,
    evaluate_baseline,
)
from datp.scoring.loading import ScoreProvider
from datp.statistics.constants import CV_DDOF
from datp.statistics.cv import cv as _canonical_cv
from datp.core.types import ClientThreshold, ThresholdResult


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
    seed: int = 0,
    alpha: float | None = None,
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
        seed=seed,
        alpha=alpha,
    )
    return float(b1_result.tau_global), b1_result


def evaluate_threshold_result(
    threshold_result: ThresholdResult,
    score_provider: ScoreProvider,
    regime: Regime,
    seed: int,
    alpha: float | None,
) -> EvaluationResult:
    from pathlib import Path
    return evaluate_baseline(
        client_thresholds=threshold_result.client_thresholds,
        score_root=Path(""),
        regime=regime,
        seed=seed,
        alpha=alpha,
        score_provider=score_provider,
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
    from pathlib import Path
    client_thresholds = [
        ClientThreshold(
            client_id=client_id,
            threshold=threshold,
            calibration_pending=False,
            strategy=baseline,
        )
        for client_id in client_ids
    ]
    return evaluate_baseline(
        client_thresholds=client_thresholds,
        score_root=Path(""),
        regime=regime,
        seed=seed,
        alpha=alpha,
        score_provider=score_provider,
    )
