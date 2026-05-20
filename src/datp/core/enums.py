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


class DemotionDecision(enum.StrEnum):
    DEMOTED = "demoted"
    RETAINED = "retained"


class AuditStatus(enum.StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    MISSING = "MISSING"
    PARTIAL = "PARTIAL"
    BLOCKED_PENDING_RUN = "BLOCKED_PENDING_RUN"
    WARNING = "WARNING"


class BaselineRole(enum.StrEnum):
    CONTROLLED_THRESHOLD = "controlled_threshold"
    CENTRALIZED_REFERENCE = "centralized_reference"


class B0NormalizationMode(enum.StrEnum):
    PER_CLIENT_PREPARED = "per_client_prepared"
    POOLED_ZSCORE = "pooled_zscore"


class WarningCode(enum.StrEnum):
    B0_AUROC_BELOW_THRESHOLD = "B0_AUROC_BELOW_THRESHOLD"
    B0_NORMALIZATION_DIAGNOSTIC_BLOCKED = "B0_NORMALIZATION_DIAGNOSTIC_BLOCKED"
    B0_SANITY_LOW_AUROC = "B0_SANITY_LOW_AUROC"
    B0_SANITY_LOW_PR_AUC = "B0_SANITY_LOW_PR_AUC"
    B0_SANITY_PR_AUC_PENDING = "B0_SANITY_PR_AUC_PENDING"
    B0_WEAK_AUC_BLOCKS_PAPER = "B0_WEAK_AUC_BLOCKS_PAPER"
    B1_NOT_POOLED_PERCENTILE = "B1_NOT_POOLED_PERCENTILE"
    B1_MEAN_NOT_POOLED_PERCENTILE = "B1_MEAN_NOT_POOLED_PERCENTILE"
    B2_UTILITY_TRADEOFF = "B2_UTILITY_TRADEOFF"
    B3_TAXONOMY_TOO_COARSE = "B3_TAXONOMY_TOO_COARSE"
    B4_CLUSTER_DIAGNOSTICS_INCOMPLETE = "B4_CLUSTER_DIAGNOSTICS_INCOMPLETE"
    B4_SINGLE_CLUSTER = "B4_SINGLE_CLUSTER"
    CAL_PENDING_HIGH_FRACTION = "CAL_PENDING_HIGH_FRACTION"
    CICIOT_HOMOGENEITY_BLOCKED = "CICIOT_HOMOGENEITY_BLOCKED"
    CICIOT_HOMOGENEITY_INCOMPLETE = "CICIOT_HOMOGENEITY_INCOMPLETE"
    CICIOT_HOMOGENEITY_VERIFIED = "CICIOT_HOMOGENEITY_VERIFIED"
    CICIOT_HETEROGENEITY_DETECTED = "CICIOT_HETEROGENEITY_DETECTED"
    CICIOT_NOT_HOMOGENEOUS = "CICIOT_NOT_HOMOGENEOUS"
    CLUSTER_THRESHOLD_RECONSTRUCTION_FAILED = "CLUSTER_THRESHOLD_RECONSTRUCTION_FAILED"
    CONVERGENCE_NOT_REACHED = "CONVERGENCE_NOT_REACHED"
    COVERAGE_BELOW_THRESHOLD = "COVERAGE_BELOW_THRESHOLD"
    FIXED_OPERATING_POINT_METRICS_PENDING = "FIXED_OPERATING_POINT_METRICS_PENDING"
    FLAT_CV_TPR_SUSPICIOUS = "FLAT_CV_TPR_SUSPICIOUS"
    MISSING_CONVERGENCE_CURVES = "MISSING_CONVERGENCE_CURVES"
    MISSING_CONFUSION_MATRICES = "MISSING_CONFUSION_MATRICES"
    MISSING_CONFUSION_MATRIX = "MISSING_CONFUSION_MATRIX"
    MISSING_PARTITION_MANIFEST = "MISSING_PARTITION_MANIFEST"
    MISSING_RUN = "MISSING_RUN"
    MISSING_SCORE_ARTIFACTS = "MISSING_SCORE_ARTIFACTS"
    METRIC_DENOMINATOR_MISMATCH = "METRIC_DENOMINATOR_MISMATCH"
    NAKED_CV_FPR = "NAKED_CV_FPR"
    PRIMARY_DELTA_INCOMPLETE = "PRIMARY_DELTA_INCOMPLETE"
    NO_COMPLETED_RESULTS = "NO_COMPLETED_RESULTS"
    REGIME_C_ALPHA_AUDIT_MISSING = "REGIME_C_ALPHA_AUDIT_MISSING"
    REGIME_C_PREPARED_MANIFEST_MISSING = "REGIME_C_PREPARED_MANIFEST_MISSING"
    SCHEMA_VERSION_MISMATCH = "SCHEMA_VERSION_MISMATCH"
    STABLE_WORST_CLIENT = "STABLE_WORST_CLIENT"
    THRESHOLD_RECONSTRUCTION_FAILED = "THRESHOLD_RECONSTRUCTION_FAILED"
    WORST_CLIENT_STABLE = "WORST_CLIENT_STABLE"
    WORST_CLIENT_VARIES = "WORST_CLIENT_VARIES"


class ScoringStage(enum.StrEnum):
    CAL = "cal"
    TEST_BENIGN = "test_benign"
    TEST_ATTACK = "test_attack"

    @classmethod
    def all(cls) -> tuple["ScoringStage", ...]:
        return tuple(cls)


SCORING_STAGES: tuple[ScoringStage, ...] = ScoringStage.all()


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
    Regime.A: frozenset({Baseline.B0, Baseline.B1, Baseline.B2, Baseline.B3, Baseline.B4}),
    Regime.B: frozenset({Baseline.B0, Baseline.B1, Baseline.B2, Baseline.B4}),
    Regime.C: frozenset({Baseline.B1, Baseline.B2, Baseline.B4}),
}

MAIN_BODY_BASELINES: frozenset[Baseline] = frozenset({
    Baseline.B0, Baseline.B1, Baseline.B2, Baseline.B3, Baseline.B4,
})

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
