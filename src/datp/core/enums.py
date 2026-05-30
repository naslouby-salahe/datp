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
    """Identifies the calibration scope for a threshold.

    Values intentionally mirror Baseline names — each baseline has a canonical
    ThresholdSource. See BASELINE_THRESHOLD_SOURCE mapping for the relationship.
    """

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


# Absorption ratio thresholds — locked per PRE_CODING_PLAN §6.4.
# Do not change without a scientific ticket and drift-enforcer review.
ABSORPTION_STRONG_RETENTION_THRESHOLD: float = 0.75
ABSORPTION_PARTIAL_THRESHOLD: float = 0.25


def classify_absorption(ratio: float) -> AbsorptionClass:
    """Classify absorption ratio into the locked categories."""
    if ratio >= ABSORPTION_STRONG_RETENTION_THRESHOLD:
        return AbsorptionClass.STRONG_RETENTION
    if ratio >= ABSORPTION_PARTIAL_THRESHOLD:
        return AbsorptionClass.PARTIAL
    return AbsorptionClass.NEAR_FULL





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

# Threshold ladder — the four controlled baselines being compared.
# B0 is a centralized reference, not part of the ladder.
# B5 is a local-only ablation, not part of the ladder.
CONTROLLED_BASELINES: tuple[Baseline, ...] = (
    Baseline.B1,
    Baseline.B2,
    Baseline.B3,
    Baseline.B4,
)

# B4 fingerprint feature order: locked per scientific contract.
# Do not reorder without a scientific ticket.
B4_FINGERPRINT_FEATURES: tuple[str, ...] = ("mean", "std", "skew", "p95")


class MetricName(enum.StrEnum):
    FPR = "fpr"
    TPR = "tpr"
    TNR = "tnr"
    FNR = "fnr"
    PRECISION = "precision"
    RECALL = "recall"
    MACRO_F1 = "macro_f1"
    BALANCED_ACCURACY = "balanced_accuracy"
    AUROC = "auroc"
    PR_AUC = "pr_auc"
    CV_FPR = "cv_fpr"
    CV_TPR = "cv_tpr"
    MEAN_FPR = "mean_fpr"
    STD_FPR = "std_fpr"
    IQR_FPR = "iqr_fpr"
    IQR_TPR = "iqr_tpr"
    WORST_CLIENT_FPR = "worst_client_fpr"
    WORST_BA = "worst_ba"
    P10_MACRO_F1 = "p10_macro_f1"
    WORST_CLIENT_TPR = "worst_client_tpr"
    WORST_CLIENT_MACRO_F1 = "worst_client_macro_f1"
    WORST_CLIENT_BALANCED_ACCURACY = "worst_client_balanced_accuracy"


class PayloadKey(enum.StrEnum):
    CLIENT_ID = "client_id"
    PER_CLIENT = "per_client"
    CONFUSION_MATRIX = "confusion_matrix"
    BASELINE = "baseline"
    REGIME = "regime"
    SEED = "seed"
    ALPHA = "alpha"
    COVERAGE_RATIO = "coverage_ratio"


class ConfusionKey(enum.StrEnum):
    TP = "tp"
    FP = "fp"
    TN = "tn"
    FN = "fn"


class ComparatorKind(enum.StrEnum):
    FEDPROX = "fedprox"
    DITTO = "ditto"
    FEDREP_AE = "fedrep_ae"
    FEDPER_AE = "fedper_ae"
    FEDSTATS_BENIGN = "fedstats_benign"
    LARIDI_FAITHFUL = "laridi_faithful"


class RunKind(enum.StrEnum):
    CORE_LADDER = "core_ladder"
    STRESS_TEST = "stress_test"
    CENTRALIZED_REFERENCE = "centralized_reference"
    COMPARATOR = "comparator"


def controlled_baselines_for_regime(regime: Regime) -> tuple[Baseline, ...]:
    """Return controlled threshold-ladder baselines for a regime.

    B3 (family threshold) applies only in Regime A (N-BaIoT device families).
    """
    if regime == Regime.A:
        return CONTROLLED_BASELINES
    return tuple(b for b in CONTROLLED_BASELINES if b != Baseline.B3)


class ConvergenceStatus(enum.StrEnum):
    CONVERGED = "converged"
    NOT_CONVERGED = "not_converged"
    UNKNOWN = "unknown"
    BLOCKED_PENDING_RUN = "BLOCKED_PENDING_RUN"
    MISSING_CHECKPOINT = "MISSING_CHECKPOINT"


class EvidenceRole(enum.StrEnum):
    """Scientific evidence role for a figure or analysis result."""

    DESCRIPTIVE = "descriptive"
    DESCRIPTIVE_WITH_CONFIRMATORY_SIDECAR_DELTA = (
        "descriptive_with_confirmatory_sidecar_delta"
    )
    SECONDARY = "secondary"


class SeedScope(enum.StrEnum):
    """Which seeds a figure or result covers."""

    REPRESENTATIVE_SEED = "representative_seed"
    ALL_SEED = "all_seed"


class FigureName(enum.StrEnum):
    """Canonical identifiers for the four main paper figures."""

    FIGURE_1 = "figure_1"
    FIGURE_2 = "figure_2"
    FIGURE_3 = "figure_3"
    FIGURE_4 = "figure_4"


# Baselines used for statistical comparisons per regime.
# Excludes isolated B0; excludes B3 in Regime A (family threshold, not part of the
# causal B1/B2/B4 ladder comparisons).
STATS_REPORTING_BASELINES: dict[Regime, frozenset[Baseline]] = {
    Regime.A: REGIME_BASELINES[Regime.A] - ISOLATED_BASELINES - {Baseline.B3},
    Regime.B: REGIME_BASELINES[Regime.B] - ISOLATED_BASELINES,
    Regime.C: REGIME_BASELINES[Regime.C] - ISOLATED_BASELINES,
    Regime.D: REGIME_BASELINES[Regime.D] - ISOLATED_BASELINES,
}
