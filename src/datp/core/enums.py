from __future__ import annotations

import enum


class Baseline(enum.StrEnum):
    B0 = "b0"
    B1 = "b1"
    B2 = "b2"
    B3 = "b3"
    B4 = "b4"


class Regime(enum.StrEnum):
    A = "a"
    B = "b"
    C = "c"
    D = "d"


class FeasibilityOutcome(enum.StrEnum):
    """Dataset/preprocessing feasibility outcomes per PRE_CODING_PLAN §5.5."""

    EDGE_FEASIBLE_DEVICE_CLIENTS = "edge_feasible_device_clients"
    EDGE_FEASIBLE_GROUP_CLIENTS_ONLY = "edge_feasible_group_clients_only"
    EDGE_REJECTED_NO_METADATA = "edge_rejected_no_metadata"
    EDGE_REJECTED_INSUFFICIENT_CLIENTS = "edge_rejected_insufficient_clients"
    EDGE_BLOCKED_DATA_UNAVAILABLE = "edge_blocked_data_unavailable"


class TemporalOutcome(enum.StrEnum):
    """Temporal recalibration probe outcomes per PRE_CODING_PLAN §6.5."""

    TEMPORAL_FEASIBLE = "temporal_feasible"
    TEMPORAL_HELPS = "temporal_helps"
    TEMPORAL_NEUTRAL = "temporal_neutral"
    TEMPORAL_HURTS = "temporal_hurts"
    TEMPORAL_INFEASIBLE = "temporal_infeasible"
    TEMPORAL_REJECTED_NO_TIMESTAMP = "temporal_rejected_no_timestamp"
    TEMPORAL_REJECTED_LOW_COVERAGE = "temporal_rejected_low_coverage"
    TEMPORAL_REJECTED_INSUFFICIENT_ATTACKS = "temporal_rejected_insufficient_attacks"
    TEMPORAL_REJECTED_NONCHRONOLOGICAL = "temporal_rejected_nonchronological"


class ClientStatus(enum.StrEnum):
    ELIGIBLE = "eligible"
    CALIBRATION_PENDING = "calibration_pending"


class ThresholdAggregationMethod(enum.StrEnum):
    ELIGIBLE_CLIENT_ARITHMETIC_MEAN = "eligible_client_arithmetic_mean"
    PER_CLIENT_PERCENTILE = "per_client_percentile"
    ELIGIBLE_FAMILY_ARITHMETIC_MEAN = "eligible_family_arithmetic_mean"
    ELIGIBLE_CLUSTER_ARITHMETIC_MEAN = "eligible_cluster_arithmetic_mean"
    POOLED_PERCENTILE = "pooled_percentile"


class ThresholdSource(enum.StrEnum):
    B0_POOLED = "pooled_percentile"
    B1_SHARED = "b1"
    B2_PER_CLIENT = "b2"
    B3_FAMILY = "b3"
    B4_CLUSTER = "b4"
    TAU_GLOBAL_FALLBACK = "tau_global_fallback"


class NormalizationScope(enum.StrEnum):
    GLOBAL = "global"
    PER_CLIENT = "per_client"
    PER_CLIENT_ZSCORE = "per_client_zscore"
    POOLED_ZSCORE = "pooled_zscore"


class PipelineStage(enum.StrEnum):
    PREPARE = "prepare"
    TRAIN = "train"
    SCORE = "score"
    THRESHOLD = "threshold"
    EVALUATE = "evaluate"
    REPORT = "report"


class B0NormalizationMode(enum.StrEnum):
    PER_CLIENT_PREPARED = "per_client_prepared"
    POOLED_ZSCORE = "pooled_zscore"


class BaselineRole(enum.StrEnum):
    CONTROLLED_THRESHOLD = "controlled_threshold"
    CENTRALIZED_REFERENCE = "centralized_reference"


class ScoringStage(enum.StrEnum):
    CAL = "cal"
    TEST_BENIGN = "test_benign"
    TEST_ATTACK = "test_attack"

    @classmethod
    def all(cls) -> tuple["ScoringStage", ...]:
        return tuple(cls)


SCORING_STAGES: tuple[ScoringStage, ...] = ScoringStage.all()


class AbsorptionClass(enum.StrEnum):
    """Absorption ratio classification per PRE_CODING_PLAN §6.4.

    Ratio = Δ_personalized / Δ_FedAvg where each Δ = CV(FPR)[B1] − CV(FPR)[B2].
    """

    STRONG_RETENTION = "strong_retention"
    PARTIAL = "partial"
    NEAR_FULL = "near_full"


# Absorption ratio thresholds (locked per PRE_CODING_PLAN §6.4).
ABSORPTION_STRONG_RETENTION_THRESHOLD: float = 0.75
ABSORPTION_PARTIAL_THRESHOLD: float = 0.25


def classify_absorption(ratio: float) -> AbsorptionClass:
    """Classify absorption ratio into the locked categories."""
    if ratio >= ABSORPTION_STRONG_RETENTION_THRESHOLD:
        return AbsorptionClass.STRONG_RETENTION
    if ratio >= ABSORPTION_PARTIAL_THRESHOLD:
        return AbsorptionClass.PARTIAL
    return AbsorptionClass.NEAR_FULL


class ArtifactKind(enum.StrEnum):
    MODEL_CHECKPOINT = "model_checkpoint"
    SCORE = "score"
    METRICS = "metrics"
    MANIFEST = "manifest"
    SCALER = "scaler"
    PARTITION = "partition"
    AUDIT = "audit"
    FIGURE = "figure"
    TABLE = "table"


# Derived maps — do not duplicate in other modules; import from here.

REGIME_BASELINES: dict[Regime, frozenset[Baseline]] = {
    Regime.A: frozenset(
        {Baseline.B0, Baseline.B1, Baseline.B2, Baseline.B3, Baseline.B4}
    ),
    Regime.B: frozenset({Baseline.B0, Baseline.B1, Baseline.B2, Baseline.B4}),
    Regime.C: frozenset({Baseline.B1, Baseline.B2, Baseline.B4}),
    Regime.D: frozenset({Baseline.B0, Baseline.B1, Baseline.B2, Baseline.B4}),
}

MAIN_BODY_BASELINES: frozenset[Baseline] = frozenset(
    {
        Baseline.B0,
        Baseline.B1,
        Baseline.B2,
        Baseline.B3,
        Baseline.B4,
    }
)

ISOLATED_BASELINES: frozenset[Baseline] = frozenset({Baseline.B0})

THRESHOLD_AGGREGATION_BY_BASELINE: dict[Baseline, ThresholdAggregationMethod] = {
    Baseline.B0: ThresholdAggregationMethod.POOLED_PERCENTILE,
    Baseline.B1: ThresholdAggregationMethod.ELIGIBLE_CLIENT_ARITHMETIC_MEAN,
    Baseline.B2: ThresholdAggregationMethod.PER_CLIENT_PERCENTILE,
    Baseline.B3: ThresholdAggregationMethod.ELIGIBLE_FAMILY_ARITHMETIC_MEAN,
    Baseline.B4: ThresholdAggregationMethod.ELIGIBLE_CLUSTER_ARITHMETIC_MEAN,
}

BASELINE_THRESHOLD_SOURCE: dict[Baseline, ThresholdSource] = {
    Baseline.B0: ThresholdSource.B0_POOLED,
    Baseline.B1: ThresholdSource.B1_SHARED,
    Baseline.B2: ThresholdSource.B2_PER_CLIENT,
    Baseline.B3: ThresholdSource.B3_FAMILY,
    Baseline.B4: ThresholdSource.B4_CLUSTER,
}

BASELINE_ROLE: dict[Baseline, BaselineRole] = {
    Baseline.B0: BaselineRole.CENTRALIZED_REFERENCE,
    Baseline.B1: BaselineRole.CONTROLLED_THRESHOLD,
    Baseline.B2: BaselineRole.CONTROLLED_THRESHOLD,
    Baseline.B3: BaselineRole.CONTROLLED_THRESHOLD,
    Baseline.B4: BaselineRole.CONTROLLED_THRESHOLD,
}
