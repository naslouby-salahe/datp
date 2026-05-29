from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from datp.core.enums import (
    B0NormalizationMode,
    Baseline,
    NormalizationScope,
    Regime,
    ThresholdAggregationMethod,
)

ThresholdStrategyValue = Baseline


class _FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class B3FamilyInfo(_FrozenModel):
    tau_family: float
    eligible_count: int
    members: list[str]
    threshold_variance: float
    singleton: bool


class B3Metadata(_FrozenModel):
    family_info: dict[str, B3FamilyInfo]


class B4ClusterInfo(_FrozenModel):
    tau_cluster: float
    members: list[str]


class B4Metadata(_FrozenModel):
    cluster_info: dict[str, B4ClusterInfo]
    fingerprints: dict[str, list[float]]
    silhouette: float
    silhouette_scores: dict[str, float]
    k: int


class ClientThreshold(_FrozenModel):
    client_id: str
    threshold: float
    calibration_pending: bool
    strategy: ThresholdStrategyValue


class ThresholdResult(_FrozenModel):
    strategy: ThresholdStrategyValue
    tau_global: float
    client_thresholds: list[ClientThreshold]
    eligible_count: int = Field(ge=0)
    pending_count: int = Field(ge=0)
    b3_metadata: B3Metadata | None
    b4_metadata: B4Metadata | None


class ClientEvalResult(_FrozenModel):
    fpr: float
    tpr: float
    balanced_accuracy: float
    macro_f1: float
    confusion_matrix: dict[str, int]
    n_benign: int
    n_attack: int
    benign_count: int | None
    attack_count: int | None
    calibration_pending: bool | None
    evaluation_incomplete: bool | None
    threshold_value: float | None
    threshold_source: str | None


class ClientEvalResultWithAuroc(ClientEvalResult):
    auroc: float
    pr_auc: float


class BaselineResult(_FrozenModel):
    baseline: Baseline
    regime: Regime
    seed: int
    per_client: dict[str, ClientEvalResult]
    n_clients: int
    calibration_pending_clients: list[str]


class B0Result(BaselineResult):
    schema_version: str
    metric_schema_version: str
    threshold_schema_version: str
    run_id: str
    dataset: str
    tau_b0: float
    tau_global: float
    threshold_scope: str
    threshold_strategy_name: str
    q: float
    n_min: int
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
    max_min_fpr_gap: float
    worst_client_fpr: float
    worst_client_id: str | None
    worst_ba: float
    p10_macro_f1: float
    auroc: float | None
    pr_auc: float | None
    aggregate_metrics: dict[str, float | str | None]
    provenance: dict[str, str]
    threshold_mode: ThresholdAggregationMethod
    normalization_scope: NormalizationScope
    normalization_mode: B0NormalizationMode
