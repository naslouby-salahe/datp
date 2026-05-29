from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict

from datp.core.enums import (
    B0NormalizationMode,
    Baseline,
    NormalizationScope,
    Regime,
    ThresholdAggregationMethod,
)

ThresholdStrategyValue = Baseline


@dataclass(frozen=True, slots=True)
class B3FamilyInfo:
    tau_family: float
    eligible_count: int
    members: tuple[str, ...]
    threshold_variance: float
    singleton: bool


@dataclass(frozen=True, slots=True)
class B3Metadata:
    family_info: dict[str, B3FamilyInfo]


@dataclass(frozen=True, slots=True)
class B4ClusterInfo:
    tau_cluster: float
    members: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class B4Metadata:
    cluster_info: dict[str, B4ClusterInfo]
    fingerprints: dict[str, tuple[float, ...]]
    silhouette: float
    silhouette_scores: dict[str, float]
    k: int


@dataclass(frozen=True, slots=True)
class ClientThreshold:
    client_id: str
    threshold: float
    calibration_pending: bool
    strategy: ThresholdStrategyValue


@dataclass(frozen=True, slots=True)
class ThresholdResult:
    strategy: ThresholdStrategyValue
    tau_global: float
    client_thresholds: tuple[ClientThreshold, ...]
    eligible_count: int
    pending_count: int
    b3_metadata: B3Metadata | None
    b4_metadata: B4Metadata | None


class _FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


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
