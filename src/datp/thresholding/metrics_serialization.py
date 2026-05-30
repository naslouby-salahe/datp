from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict

from datp.core.types import ThresholdResult
from datp.core.enums import BASELINE_THRESHOLD_SOURCE, THRESHOLD_AGGREGATION_BY_BASELINE
from datp.core.enums import (
    Baseline,
    Regime,
)
from datp.core.provenance import git_commit, source_hash, utc_timestamp
from datp.core.enums import MetricName, RunKind
from datp.data.catalog import DatasetID
from datp.evaluation.metrics import ClientEvaluationRecord, EvaluationResult

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
    run_kind: RunKind
    baseline: Baseline
    regime: Regime
    seed: int
    alpha: float | None
    dataset: DatasetID
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
    baseline = eval_result.baseline
    threshold_scope = THRESHOLD_AGGREGATION_BY_BASELINE[baseline].value
    default_source = BASELINE_THRESHOLD_SOURCE[baseline].value
    run_id = f"{eval_result.regime.value}_{baseline.value}_seed{eval_result.seed}"
    if eval_result.alpha is not None:
        run_id += f"_alpha{eval_result.alpha}"
    aggregate = {
        MetricName.CV_FPR: eval_result.cv_fpr,
        MetricName.MEAN_FPR: eval_result.mean_fpr,
        MetricName.STD_FPR: eval_result.std_fpr,
        MetricName.CV_TPR: eval_result.cv_tpr,
        MetricName.IQR_FPR: eval_result.iqr_fpr,
        MetricName.IQR_TPR: eval_result.iqr_tpr,
        "max_min_fpr_gap": eval_result.max_min_fpr_gap,
        MetricName.WORST_CLIENT_FPR: eval_result.worst_client_fpr,
        "worst_client_id": eval_result.worst_client_id,
        MetricName.WORST_BA: eval_result.worst_ba,
        MetricName.P10_MACRO_F1: eval_result.p10_macro_f1,
    }
    return SweepMetrics(
        schema_version=METRICS_SCHEMA_VERSION,
        metric_schema_version=METRIC_SCHEMA_VERSION,
        threshold_schema_version=THRESHOLD_SCHEMA_VERSION,
        run_id=run_id,
        run_kind=RunKind.CORE_LADDER,
        baseline=eval_result.baseline,
        regime=eval_result.regime,
        seed=eval_result.seed,
        alpha=eval_result.alpha,
        dataset=eval_result.dataset,
        threshold_scope=threshold_scope,
        threshold_strategy_name=threshold_result.run.baseline.value,
        tau_global=threshold_result.tau_global,
        eligible_ids=list(eval_result.eligible_ids),
        pending_ids=list(eval_result.pending_ids),
        eval_incomplete_ids=list(eval_result.incomplete_ids),
        eligible_count=threshold_result.eligible_count,
        pending_count=threshold_result.pending_count,
        eval_incomplete_count=len(eval_result.incomplete_ids),
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
            _to_client_detail(cr, default_source) for cr in eval_result.clients
        ],
    )


def _to_client_detail(
    cr: ClientEvaluationRecord,
    default_source: str,
) -> MetricsClientDetail:
    return MetricsClientDetail(
        client_id=cr.client_id,
        fpr=cr.metrics.fpr,
        tpr=cr.metrics.tpr,
        tnr=cr.metrics.tnr,
        fnr=cr.metrics.fnr,
        precision=cr.metrics.precision,
        recall=cr.metrics.recall,
        balanced_accuracy=cr.metrics.balanced_accuracy,
        macro_f1=cr.metrics.macro_f1,
        confusion_matrix={
            "tp": cr.confusion.tp,
            "fp": cr.confusion.fp,
            "tn": cr.confusion.tn,
            "fn": cr.confusion.fn,
        },
        n_benign=cr.n_benign,
        n_attack=cr.n_attack,
        benign_count=cr.n_benign,
        attack_count=cr.n_attack,
        calibration_pending=cr.threshold.calibration_pending,
        evaluation_incomplete=cr.evaluation_incomplete,
        threshold_value=cr.threshold.threshold,
        threshold_source=(
            "tau_global_fallback"
            if cr.threshold.calibration_pending
            else default_source
        ),
    )
