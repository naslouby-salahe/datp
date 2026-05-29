from __future__ import annotations

import math
from collections.abc import Callable
from pathlib import Path

import attrs
import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from datp.thresholding.types import ClientThreshold
from datp.core.enums import (
    Baseline,
    Regime,
)
from datp.core.errors import fmt
from datp.data.regimes.catalog import dataset_for_regime
from datp.evaluation.metric_keys import (
    CONFUSION_FN,
    CONFUSION_FP,
    CONFUSION_TN,
    CONFUSION_TP,
)
from datp.scoring.loading import ScoreProvider
from datp.statistics.constants import CV_DDOF
from datp.statistics.cv import cv

_MODULE = "evaluation.metrics"


@attrs.define(frozen=True, slots=True)
class BinaryMetrics:
    fpr: float
    tpr: float
    tnr: float
    fnr: float
    balanced_accuracy: float
    precision: float
    recall: float
    macro_f1: float


def recompute_binary_metrics(tp: int, fp: int, tn: int, fn: int) -> BinaryMetrics:
    n_benign = fp + tn
    n_attack = tp + fn
    fpr = fp / n_benign if n_benign > 0 else math.nan
    tpr = tp / n_attack if n_attack > 0 else math.nan
    tnr = tn / n_benign if n_benign > 0 else math.nan
    fnr = fn / n_attack if n_attack > 0 else math.nan
    if n_benign > 0 and n_attack > 0:
        balanced_accuracy = (tpr + tnr) / 2.0
        prec0 = tn / (tn + fn) if (tn + fn) > 0 else 0.0
        rec0 = tnr
        f1_0 = 2 * prec0 * rec0 / (prec0 + rec0) if (prec0 + rec0) > 0 else 0.0
        prec1 = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec1 = tpr
        f1_1 = 2 * prec1 * rec1 / (prec1 + rec1) if (prec1 + rec1) > 0 else 0.0
        macro_f1 = (f1_0 + f1_1) / 2.0
    else:
        balanced_accuracy = math.nan
        prec1 = math.nan
        rec1 = tpr
        macro_f1 = math.nan
    return BinaryMetrics(
        fpr=fpr,
        tpr=tpr,
        tnr=tnr,
        fnr=fnr,
        balanced_accuracy=balanced_accuracy,
        precision=prec1,
        recall=rec1,
        macro_f1=macro_f1,
    )


class ClientMetrics(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    client_id: str
    fpr: float
    tpr: float
    tnr: float = math.nan
    fnr: float = math.nan
    precision: float = math.nan
    recall: float = math.nan
    balanced_accuracy: float
    macro_f1: float
    confusion_matrix: dict[str, int]
    n_benign: int = Field(ge=0)
    n_attack: int = Field(ge=0)


@attrs.define(frozen=True, slots=True)
class FprDispersionBundle:
    cv_fpr: float
    mean_fpr: float
    std_fpr: float
    iqr_fpr: float
    worst_client_fpr: float
    worst_client_id: str | None
    eligible_count: int
    client_count: int
    max_min_fpr_gap: float


class EvaluationResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    baseline: Baseline
    regime: Regime
    seed: int
    alpha: float | None
    dataset: str = ""
    per_client: list[ClientMetrics]
    eligible_ids: list[str]
    pending_ids: list[str]
    eval_incomplete_ids: list[str] = Field(default_factory=list)
    coverage_ratio: float
    cv_fpr: float
    mean_fpr: float
    std_fpr: float
    cv_tpr: float
    iqr_fpr: float
    iqr_tpr: float
    max_min_fpr_gap: float = math.nan
    worst_client_fpr: float
    worst_client_id: str | None
    eligible_count: int
    client_count: int
    worst_ba: float
    p10_macro_f1: float


def compute_client_metrics(
    client_id: str,
    scores_benign: np.ndarray,
    scores_attack: np.ndarray,
    threshold: float,
) -> ClientMetrics:
    """Compute per-client binary classification metrics (anomaly rule: score > threshold)."""
    benign = np.asarray(scores_benign, dtype=np.float64)
    attack = np.asarray(scores_attack, dtype=np.float64)
    n_benign = int(benign.size)
    n_attack = int(attack.size)

    fp = int(np.sum(benign > threshold))
    tn = n_benign - fp
    tp = int(np.sum(attack > threshold))
    fn = n_attack - tp

    bm = recompute_binary_metrics(tp, fp, tn, fn)

    return ClientMetrics(
        client_id=client_id,
        fpr=bm.fpr,
        tpr=bm.tpr,
        tnr=bm.tnr,
        fnr=bm.fnr,
        precision=bm.precision,
        recall=bm.recall,
        balanced_accuracy=bm.balanced_accuracy,
        macro_f1=bm.macro_f1,
        confusion_matrix={
            CONFUSION_TP: tp,
            CONFUSION_FP: fp,
            CONFUSION_TN: tn,
            CONFUSION_FN: fn,
        },
        n_benign=n_benign,
        n_attack=n_attack,
    )


@attrs.define(frozen=True, slots=True)
class _AggResult:
    fpr: FprDispersionBundle
    cv_tpr: float
    iqr_tpr: float
    worst_ba: float
    p10_macro_f1: float


def _aggregate_dispersion(
    per_client: list[ClientMetrics],
    eligible_ids: list[str],
    eval_incomplete_ids: list[str],
) -> _AggResult:
    from datp.evaluation.metric_filtering import filter_eligible_metrics

    fm = filter_eligible_metrics(per_client, eligible_ids, eval_incomplete_ids)

    fpr_arr = fm.fpr_eligible
    if np.isnan(fpr_arr).any():
        eligible_set = set(eligible_ids)
        bad_ids = [
            cm.client_id
            for cm in per_client
            if cm.client_id in eligible_set and math.isnan(cm.fpr)
        ]
        raise ValueError(
            fmt(
                _MODULE,
                "Undefined eligible-client FPR cannot enter dispersion metrics",
                "every eligible client has at least one benign test row",
                ", ".join(bad_ids) or "unknown",
            )
        )
    tpr_arr = fm.tpr_eligible
    ba_arr = fm.ba_eligible
    f1_arr = fm.f1_eligible

    cv_fpr = cv(fpr_arr, ddof=CV_DDOF)
    mean_fpr = float(fpr_arr.mean()) if fpr_arr.size > 0 else math.nan
    std_fpr = float(fpr_arr.std(ddof=CV_DDOF)) if fpr_arr.size >= 2 else math.nan
    iqr_fpr = (
        float(np.percentile(fpr_arr, 75) - np.percentile(fpr_arr, 25))
        if fpr_arr.size >= 2
        else math.nan
    )
    if fpr_arr.size > 0:
        worst_idx = int(np.argmax(fpr_arr))
        worst_client_fpr = float(fpr_arr[worst_idx])
        eligible_list = [c for c in per_client if c.client_id in set(eligible_ids)]
        worst_client_id: str | None = (
            eligible_list[worst_idx].client_id
            if worst_idx < len(eligible_list)
            else None
        )
        max_min_fpr_gap = float(fpr_arr.max() - fpr_arr.min())
    else:
        worst_client_fpr = math.nan
        worst_client_id = None
        max_min_fpr_gap = math.nan
    cv_tpr = cv(tpr_arr, ddof=CV_DDOF)
    iqr_tpr = (
        float(np.percentile(tpr_arr, 75) - np.percentile(tpr_arr, 25))
        if tpr_arr.size >= 2
        else math.nan
    )
    worst_ba = float(ba_arr.min()) if ba_arr.size > 0 else math.nan
    p10_macro_f1 = float(np.percentile(f1_arr, 10)) if f1_arr.size > 0 else math.nan

    return _AggResult(
        fpr=FprDispersionBundle(
            cv_fpr=cv_fpr,
            mean_fpr=mean_fpr,
            std_fpr=std_fpr,
            iqr_fpr=iqr_fpr,
            worst_client_fpr=worst_client_fpr,
            worst_client_id=worst_client_id,
            eligible_count=fpr_arr.size,
            client_count=len(per_client),
            max_min_fpr_gap=max_min_fpr_gap,
        ),
        cv_tpr=cv_tpr,
        iqr_tpr=iqr_tpr,
        worst_ba=worst_ba,
        p10_macro_f1=p10_macro_f1,
    )


def build_evaluation_result(
    *,
    baseline: Baseline,
    regime: Regime,
    seed: int,
    alpha: float | None,
    per_client: list[ClientMetrics],
    eligible_ids: list[str],
    pending_ids: list[str],
    eval_incomplete_ids: list[str] | None,
) -> EvaluationResult:
    if not per_client:
        raise ValueError(
            fmt(
                _MODULE,
                "per_client metrics are empty",
                "at least one client",
                "empty list",
            )
        )
    client_ids = [cm.client_id for cm in per_client]
    if len(client_ids) != len(set(client_ids)):
        raise ValueError(
            fmt(
                _MODULE,
                "Duplicate client metrics",
                "unique client_id values",
                str(client_ids),
            )
        )

    known = set(client_ids)
    unknown_eligible = sorted(set(eligible_ids) - known)
    unknown_pending = sorted(set(pending_ids) - known)
    if unknown_eligible or unknown_pending:
        raise ValueError(
            fmt(
                _MODULE,
                "Eligibility references unknown clients",
                "eligible/pending IDs are present in per_client",
                f"eligible={unknown_eligible}, pending={unknown_pending}",
            )
        )
    overlap = sorted(set(eligible_ids) & set(pending_ids))
    if overlap:
        raise ValueError(
            fmt(
                _MODULE,
                "Client has mixed eligibility status",
                "disjoint eligible/pending IDs",
                str(overlap),
            )
        )

    incomplete = [] if eval_incomplete_ids is None else eval_incomplete_ids
    agg = _aggregate_dispersion(per_client, eligible_ids, incomplete)
    return EvaluationResult(
        baseline=baseline,
        regime=regime,
        seed=seed,
        alpha=alpha,
        dataset=dataset_for_regime(regime).value,
        per_client=per_client,
        eligible_ids=eligible_ids,
        pending_ids=pending_ids,
        eval_incomplete_ids=incomplete,
        coverage_ratio=len(eligible_ids) / len(per_client),
        cv_fpr=agg.fpr.cv_fpr,
        mean_fpr=agg.fpr.mean_fpr,
        std_fpr=agg.fpr.std_fpr,
        cv_tpr=agg.cv_tpr,
        iqr_fpr=agg.fpr.iqr_fpr,
        iqr_tpr=agg.iqr_tpr,
        max_min_fpr_gap=agg.fpr.max_min_fpr_gap,
        worst_client_fpr=agg.fpr.worst_client_fpr,
        worst_client_id=agg.fpr.worst_client_id,
        eligible_count=agg.fpr.eligible_count,
        client_count=agg.fpr.client_count,
        worst_ba=agg.worst_ba,
        p10_macro_f1=agg.p10_macro_f1,
    )


def _validate_client_thresholds(client_thresholds: list[ClientThreshold]) -> None:
    if not client_thresholds:
        raise ValueError(
            fmt(
                _MODULE,
                "client_thresholds is empty",
                "at least one entry",
                "empty list",
            )
        )

    client_ids = [ct.client_id for ct in client_thresholds]
    if len(client_ids) != len(set(client_ids)):
        seen: set[str] = set()
        dupes: list[str] = []
        for cid in client_ids:
            if cid in seen:
                dupes.append(cid)
            else:
                seen.add(cid)
        raise ValueError(
            fmt(
                _MODULE,
                "Duplicate client_id values in client_thresholds",
                "unique ids",
                str(dupes),
            )
        )

    strategies = {(type(ct.strategy), ct.strategy.value) for ct in client_thresholds}
    if len(strategies) > 1:
        raise ValueError(
            fmt(
                _MODULE,
                "Mixed threshold strategies in client_thresholds",
                "one strategy",
                str(strategies),
            )
        )


def evaluate_baseline(
    client_thresholds: list[ClientThreshold],
    score_root: Path,
    regime: Regime,
    seed: int,
    alpha: float | None,
    *,
    score_provider: ScoreProvider | None,
) -> EvaluationResult:
    """Evaluate a baseline by loading per-client score artifacts and computing CV(FPR/TPR) over eligible clients only.

    Missing score artifacts always raise FileNotFoundError (no silent fallback).
    """
    _validate_client_thresholds(client_thresholds)

    provider = score_provider
    if provider is None:
        provider = ScoreProvider(score_root)

    per_client: list[ClientMetrics] = []
    eligible_ids: list[str] = []
    pending_ids: list[str] = []
    eval_incomplete_ids: list[str] = []

    for ct in client_thresholds:
        cid = ct.client_id
        scores_benign, scores_attack = provider.load_test_scores(cid)

        per_client.append(
            compute_client_metrics(cid, scores_benign, scores_attack, ct.threshold)
        )
        (pending_ids if ct.calibration_pending else eligible_ids).append(cid)
        if len(scores_attack) == 0:
            eval_incomplete_ids.append(cid)

    strategy = client_thresholds[0].strategy
    if not isinstance(strategy, Baseline):
        raise TypeError("threshold strategy must be a Baseline enum")
    baseline = strategy
    return build_evaluation_result(
        baseline=baseline,
        regime=regime,
        seed=seed,
        alpha=alpha,
        per_client=per_client,
        eligible_ids=eligible_ids,
        pending_ids=pending_ids,
        eval_incomplete_ids=eval_incomplete_ids,
    )


def compute_fpr(benign_errors: np.ndarray, threshold: float) -> float:
    """Fraction of benign reconstruction errors exceeding the threshold."""
    if benign_errors.size == 0:
        return 0.0
    return float(np.mean(benign_errors > threshold))


def compute_empirical_coverage(test_benign: np.ndarray, threshold: float) -> float:
    """Fraction of test_benign scores <= threshold."""
    if test_benign.size == 0:
        return 0.0
    return float(np.mean(test_benign <= threshold))


@attrs.define(frozen=True, slots=True)
class PerAttackFamilyTPR:
    client_id: str
    attack_label: str
    family: str | None
    detected_count: int
    denominator: int
    tpr: float


def compute_per_attack_tpr(
    client_id: str,
    attack_scores: np.ndarray,
    attack_labels: np.ndarray,
    threshold: float,
    family_fn: Callable[[str], str | None],
) -> list[PerAttackFamilyTPR]:
    """Compute per-attack-label TPR; attack_scores and attack_labels must be aligned arrays."""
    scores = np.asarray(attack_scores, dtype=np.float64)
    labels = np.asarray(attack_labels, dtype=object)

    if scores.shape[0] != labels.shape[0]:
        raise ValueError(
            fmt(
                _MODULE,
                "attack_scores and attack_labels length mismatch",
                str(scores.shape[0]),
                str(labels.shape[0]),
            )
        )

    results: list[PerAttackFamilyTPR] = []
    for lbl in np.unique(labels):
        mask = labels == lbl
        lbl_scores = scores[mask]
        detected = int(np.sum(lbl_scores > threshold))
        denom = int(mask.sum())
        tpr = detected / denom if denom > 0 else math.nan
        results.append(
            PerAttackFamilyTPR(
                client_id=client_id,
                attack_label=str(lbl),
                family=family_fn(str(lbl)),
                detected_count=detected,
                denominator=denom,
                tpr=tpr,
            )
        )
    return results
