from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict

from datp.baselines.common.types import ThresholdResult
from datp.core.enums import BASELINE_THRESHOLD_SOURCE, THRESHOLD_AGGREGATION_BY_BASELINE
from datp.core.enums import (
    Baseline,
    Regime,

)
from datp.core.provenance import git_commit, source_hash, utc_timestamp
from datp.evaluation.metrics import EvaluationResult

METRICS_SCHEMA_VERSION = "2"
METRIC_SCHEMA_VERSION = "2"
THRESHOLD_SCHEMA_VERSION = "1"


class MetricsClientDetail(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    client_id: str
    fpr: float
    tpr: float
    tnr: float
    fnr: float
    precision: float
    recall: float
    balanced_accuracy: float
    macro_f1: float
    confusion_matrix: dict[str, int]
    n_benign: int
    n_attack: int
    benign_count: int
    attack_count: int
    calibration_pending: bool
    evaluation_incomplete: bool
    threshold_value: float
    threshold_source: str


class MetricsProvenance(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    config_identity: str
    split_manifest_identity: str
    model_checkpoint_identity: str
    score_artifact_identity: str
    metric_code_version: str
    threshold_code_version: str
    package_version: str
    generated_at_utc: str


class SweepMetrics(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    schema_version: str
    metric_schema_version: str
    threshold_schema_version: str
    run_id: str
    baseline: Baseline
    regime: Regime
    seed: int
    alpha: float | None
    dataset: str
    threshold_scope: str
    threshold_strategy_name: str
    tau_global: float
    eligible_ids: list[str]
    pending_ids: list[str]
    eval_incomplete_ids: list[str]
    eligible_count: int
    pending_count: int
    eval_incomplete_count: int
    client_count: int
    coverage_ratio: float
    cv_fpr: float
    mean_fpr: float
    std_fpr: float
    cv_tpr: float
    iqr_fpr: float
    iqr_tpr: float
    worst_client_fpr: float
    worst_client_id: str | None
    worst_ba: float
    p10_macro_f1: float
    aggregate_metrics: dict[str, float | str | None]
    provenance: MetricsProvenance
    per_client: list[MetricsClientDetail]


def build_metrics_dict(
    eval_result: EvaluationResult,
    threshold_result: ThresholdResult,
    *,
    config_identity: str,
    split_manifest_identity: str,
    model_checkpoint_identity: str,
    score_artifact_identity: str,
) -> SweepMetrics:
    threshold_by_client = {ct.client_id: ct for ct in threshold_result.client_thresholds}
    baseline = eval_result.baseline
    if isinstance(baseline, Baseline):
        threshold_scope = THRESHOLD_AGGREGATION_BY_BASELINE[baseline].value
        default_source = BASELINE_THRESHOLD_SOURCE[baseline].value
    else:
        threshold_scope = str(baseline.value)
        default_source = str(baseline.value)
    run_id = f"{eval_result.regime.value}_{baseline.value}_seed{eval_result.seed}"
    if eval_result.alpha is not None:
        run_id += f"_alpha{eval_result.alpha}"
    aggregate = {
        "cv_fpr": eval_result.cv_fpr,
        "mean_fpr": eval_result.mean_fpr,
        "std_fpr": eval_result.std_fpr,
        "cv_tpr": eval_result.cv_tpr,
        "iqr_fpr": eval_result.iqr_fpr,
        "iqr_tpr": eval_result.iqr_tpr,
        "max_min_fpr_gap": eval_result.max_min_fpr_gap,
        "worst_client_fpr": eval_result.worst_client_fpr,
        "worst_client_id": eval_result.worst_client_id,
        "worst_ba": eval_result.worst_ba,
        "p10_client_macro_f1": eval_result.p10_macro_f1,
    }
    return SweepMetrics(
        schema_version=METRICS_SCHEMA_VERSION,
        metric_schema_version=METRIC_SCHEMA_VERSION,
        threshold_schema_version=THRESHOLD_SCHEMA_VERSION,
        run_id=run_id,
        baseline=eval_result.baseline,
        regime=eval_result.regime,
        seed=eval_result.seed,
        alpha=eval_result.alpha,
        dataset=eval_result.dataset,
        threshold_scope=threshold_scope,
        threshold_strategy_name=threshold_result.strategy.value,
        tau_global=threshold_result.tau_global,
        eligible_ids=eval_result.eligible_ids,
        pending_ids=eval_result.pending_ids,
        eval_incomplete_ids=eval_result.eval_incomplete_ids,
        eligible_count=threshold_result.eligible_count,
        pending_count=threshold_result.pending_count,
        eval_incomplete_count=len(eval_result.eval_incomplete_ids),
        client_count=eval_result.client_count,
        coverage_ratio=eval_result.coverage_ratio,
        cv_fpr=eval_result.cv_fpr,
        mean_fpr=eval_result.mean_fpr,
        std_fpr=eval_result.std_fpr,
        cv_tpr=eval_result.cv_tpr,
        iqr_fpr=eval_result.iqr_fpr,
        iqr_tpr=eval_result.iqr_tpr,
        worst_client_fpr=eval_result.worst_client_fpr,
        worst_client_id=eval_result.worst_client_id,
        worst_ba=eval_result.worst_ba,
        p10_macro_f1=eval_result.p10_macro_f1,
        aggregate_metrics=aggregate,
        provenance=MetricsProvenance(
            config_identity=config_identity,
            split_manifest_identity=split_manifest_identity,
            model_checkpoint_identity=model_checkpoint_identity,
            score_artifact_identity=score_artifact_identity,
            metric_code_version=source_hash([Path(__file__)]),
            threshold_code_version=git_commit(),
            package_version=git_commit(),
            generated_at_utc=utc_timestamp(),
        ),
        per_client=[
            MetricsClientDetail(
                client_id=cm.client_id,
                fpr=cm.fpr,
                tpr=cm.tpr,
                tnr=cm.tnr,
                fnr=cm.fnr,
                precision=cm.precision,
                recall=cm.recall,
                balanced_accuracy=cm.balanced_accuracy,
                macro_f1=cm.macro_f1,
                confusion_matrix=cm.confusion_matrix,
                n_benign=cm.n_benign,
                n_attack=cm.n_attack,
                benign_count=cm.n_benign,
                attack_count=cm.n_attack,
                calibration_pending=threshold_by_client[cm.client_id].calibration_pending,
                evaluation_incomplete=cm.client_id in set(eval_result.eval_incomplete_ids),
                threshold_value=threshold_by_client[cm.client_id].threshold,
                threshold_source=(
                    "tau_global_fallback"
                    if threshold_by_client[cm.client_id].calibration_pending
                    else default_source
                ),
            )
            for cm in eval_result.per_client
        ],
    )
