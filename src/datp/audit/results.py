from __future__ import annotations

import dataclasses
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from datp.artifacts.constants import (
    MANIFEST_FILE,
    MODEL_CHECKPOINT,
)
from datp.artifacts.paths import ExperimentLocator
from datp.audit.constants import (
    AUDIT_SCHEMA_VERSION,
    AUDIT_SUMMARY_MD,
    B4_CLUSTER_STABILITY_CSV,
    BASELINE_INVARIANTS_JSON,
    CICIOT_HOMOGENEITY_AUDIT_CSV,
    CLUSTER_ASSIGNMENTS_CSV,
    CONVERGENCE_AUDIT_CSV,
    DATASET_PARTITION_AUDIT_JSON,
    FPR_COMPANION_METRICS_CSV,
    METRIC_DENOMINATOR_AUDIT_CSV,
    METRIC_RECOMPUTATION_AUDIT_CSV,
    PER_ATTACK_METRICS_CSV,
    PER_CLIENT_METRICS_CSV,
    RECONSTRUCTION_ERROR_SUMMARY_CSV,
    REGIME_C_ALPHA_AUDIT_CSV,
    REGIME_C_SEVERITY_TREND_CSV,
    RUN_MANIFEST_CSV,
    SEED_DELTAS_CSV,
    THRESHOLD_VALUES_CSV,
    WARNINGS_MD,
    WORST_CLIENT_TRACKING_CSV,
)
from datp.audit.convergence import convergence_payload as _convergence_payload
from datp.audit.datasets import (
    build_ciciot_protocol,
    build_nbaiot_per_device,
    build_regime_c_alpha_audit,
    chronological_flags_for,
    compute_b4_cluster_stability,
    compute_ciciot_homogeneity,
    compute_regime_c_severity_trend,
    confound_summary_for,
)
from datp.audit.discovery import completed_metric_paths as _completed_metric_paths
from datp.audit.discovery import parse_metric_path as _parse_metric_path
from datp.audit.enums import (
    WORST_CLIENT_DIRECTIONS,
    AttackMetricStatus,
    AuditSeverity,
    ConvergenceStatus,
    DenominatorStatus,
    HomogeneityVerdict,
    WorstDirection,
)
from datp.audit.invariants import build_invariant_results
from datp.audit.schemas import (
    B4ClusterStabilityRecord,
    BaselineInvariantResult,
    CICIoTHomogeneityRecord,
    ClientMetricRecord,
    ClusterAssignmentRecord,
    ConvergenceAuditRecord,
    DatasetPartitionAudit,
    FPRCompanionRecord,
    MetricDenominatorAuditRecord,
    MetricRecomputationRecord,
    NBaIoTDeviceCounts,
    PerAttackMetricRecord,
    ReconstructionErrorSummaryRecord,
    RegimeCAlphaAuditRecord,
    RegimeCSeverityTrendRecord,
    RunManifestRecord,
    SeedDeltaRecord,
    ThresholdRecord,
    WarningRecord,
    WorstClientRecord,
)
from datp.audit.writers import write_csv as _write_csv
from datp.audit.writers import write_json as _write_json
from datp.baselines.main import b1, b2, b3, b4
from datp.config.models import DatpConfig
from datp.core.enums import (
    BASELINE_THRESHOLD_SOURCE,
    THRESHOLD_AGGREGATION_BY_BASELINE,
    AuditStatus,
    Baseline,
    NormalizationScope,
    Regime,
    ScoringStage,
    ThresholdAggregationMethod,
    ThresholdSource,
    WarningCode,
)
from datp.core.identity import RunIdentity, alpha_label
from datp.core.provenance import (
    array_hash,
    hash_file,
    hash_jsonable,
    source_hash,
    utc_timestamp,
)
from datp.core.provenance import (
    git_commit as current_git_commit,
)
from datp.data.datasets.nbaiot.spec import NBAIOT_SPEC
from datp.data.paths import prepared_root_for_regime
from datp.data.regimes.catalog import dataset_for_regime
from datp.evaluation.metric_keys import (
    CLIENT_ID_KEY,
    CONFUSION_KEYS,
    CONFUSION_MATRIX_KEY,
    MetricName,
)
from datp.evaluation.artifact_validation import validate_metrics_payload
from datp.evaluation.metrics import compute_per_attack_tpr, recompute_binary_metrics
from datp.evaluation.ranking import compute_binary_ranking_metrics
from datp.evaluation.score_loading import read_score_column as _read_scores

_CONTROLLED = (Baseline.B1, Baseline.B2, Baseline.B3, Baseline.B4)
_BINARY_ATTACK_LABEL = "binary_attack"
_BLOCKED_COMMAND = "datp sweep --resume"


def _load_client_attack_labels(regime: Regime, client_id: str, prepared_data_root: Path) -> "np.ndarray | None":
    if regime != Regime.B:
        return None
    from datp.data.datasets.ciciot2023.spec import LABEL_COLUMN, TEST_ATTACK_LABELS_ARTIFACT  # noqa: PLC0415
    labels_path = prepared_data_root / client_id / TEST_ATTACK_LABELS_ARTIFACT
    if not labels_path.exists():
        return None
    import polars as pl  # noqa: PLC0415
    series = pl.read_parquet(labels_path)[LABEL_COLUMN]
    if series.is_empty():
        return np.empty(0, dtype=object)
    return series.to_numpy().astype(object)
@dataclasses.dataclass(frozen=True)
class _CellPanel:

    cv_fpr: float | None = None
    cv_tpr: float | None = None
    macro_f1_mean: float | None = None
    macro_f1_p10: float | None = None
    auroc_mean: float | None = None
    pr_auc_mean: float | None = None
    mean_fpr: float | None = None
    std_fpr: float | None = None
    iqr_fpr: float | None = None
    worst_client_fpr: float | None = None
    worst_client_tpr: float | None = None
    worst_client_macro_f1: float | None = None
    worst_client_balanced_accuracy: float | None = None
    convergence_round: int | None = None
    tau_global: float | None = None
    coverage_ratio: str | None = None


def _lookup_threshold_agg(baseline: Baseline) -> ThresholdAggregationMethod:
    try:
        return THRESHOLD_AGGREGATION_BY_BASELINE[baseline]
    except KeyError:
        return ThresholdAggregationMethod.PER_CLIENT_PERCENTILE


def _lookup_dataset(regime: Regime) -> str:
    return dataset_for_regime(regime).value


def _score_root(base_dir: Path, regime: Regime, seed: int, alpha: float | None) -> Path:
    return ExperimentLocator.for_main(base_dir, regime).score(seed, alpha)


def _checkpoint_path(base_dir: Path, regime: Regime, seed: int, alpha: float | None) -> Path:
    return ExperimentLocator.for_main(base_dir, regime).checkpoint(seed, alpha) / MODEL_CHECKPOINT


def _partition_manifest_path(regime: Regime, seed: int, alpha: float | None, base_dir: Path, data_root: Path | None = None) -> Path:
    _data_root = data_root if data_root is not None else base_dir
    return prepared_root_for_regime(regime, base_dir=_data_root, alpha=alpha, seed=seed) / MANIFEST_FILE


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _manifest_payload(path: Path) -> dict[str, Any]:
    return _load_json(path) if path.exists() else {}


def _split_hash(manifest_path: Path) -> str:
    payload = _manifest_payload(manifest_path)
    return hash_jsonable(payload)


def _feature_hash(feature_count: int | None) -> str:
    if feature_count is None:
        return "NOT_PROVIDED"
    return hash_jsonable({"feature_count": feature_count})


def _finite_mean(values: list[float]) -> float | None:
    arr = np.asarray(values, dtype=np.float64)
    arr = arr[np.isfinite(arr)]
    return float(arr.mean()) if arr.size else None


def _finite_array(values: list[float]) -> np.ndarray:
    arr = np.asarray(values, dtype=np.float64)
    return arr[np.isfinite(arr)]


def _percentile_or_none(values: list[float], q: float) -> float | None:
    arr = _finite_array(values)
    return float(np.percentile(arr, q)) if arr.size else None


def _std_or_none(values: list[float]) -> float | None:
    arr = _finite_array(values)
    return float(np.std(arr, ddof=1)) if arr.size > 1 else None


def _iqr_or_none(values: list[float]) -> float | None:
    arr = _finite_array(values)
    if arr.size == 0:
        return None
    return float(np.percentile(arr, 75) - np.percentile(arr, 25))


def _argworst(
    pairs: list[tuple[str, float]],
    direction: WorstDirection,
) -> tuple[str | None, float | None]:
    finite = [(cid, float(v)) for cid, v in pairs if math.isfinite(float(v))]
    if not finite:
        return None, None
    if direction == WorstDirection.MAX_IS_WORST:
        cid, value = max(finite, key=lambda item: item[1])
    else:
        cid, value = min(finite, key=lambda item: item[1])
    return cid, float(value)



def _safe_diff(a: float | None, b: float | None) -> float | None:
    if a is None or b is None or not math.isfinite(a) or not math.isfinite(b):
        return None
    return float(a - b)


_FLAT_CV_TPR_EPSILON = 1e-6
_WORST_CLIENT_STABLE_MIN_SEEDS = 3


def _emit_worst_client_stability_warnings(
    worst_client_records: list[WorstClientRecord],
    warnings: list[WarningRecord],
) -> None:
    """Warn when the same client is worst across seeds, indicating a likely encoder-quality limitation."""
    grouped: dict[tuple[Regime, str | None, Baseline, MetricName], list[tuple[int, str | None]]] = defaultdict(list)
    for record in worst_client_records:
        if record.worst_client_id is None:
            continue
        grouped[(record.regime, record.alpha, record.baseline, record.metric)].append(
            (record.seed, record.worst_client_id)
        )
    for (regime, alpha_text, baseline, metric), entries in sorted(grouped.items()):
        if len(entries) < _WORST_CLIENT_STABLE_MIN_SEEDS:
            continue
        ids = sorted({str(cid) for _, cid in entries})
        if len(ids) == 1:
            warnings.append(WarningRecord(
                severity=AuditSeverity.WARNING,
                code=WarningCode.WORST_CLIENT_STABLE.value,
                message=(
                    f"{regime}/{baseline}/alpha={alpha_text} worst client on {metric} is "
                    f"{ids[0]} across all {len(entries)} seeds; treat as encoder-quality "
                    "limitation, not threshold-strategy effect."
                ),
            ))
        else:
            warnings.append(WarningRecord(
                severity=AuditSeverity.INFO,
                code=WarningCode.WORST_CLIENT_VARIES.value,
                message=(
                    f"{regime}/{baseline}/alpha={alpha_text} worst client on {metric} "
                    f"varies across {len(entries)} seeds: {ids}."
                ),
            ))


def _emit_ciciot_homogeneity_warnings(
    homogeneity_records: list[CICIoTHomogeneityRecord],
    warnings: list[WarningRecord],
    *,
    homogeneity_threshold: float,
) -> None:
    for record in homogeneity_records:
        cell = f"regime={record.regime}/seed={record.seed}/baseline={record.baseline}"
        if record.homogeneity_verdict == HomogeneityVerdict.HOMOGENEOUS:
            warnings.append(WarningRecord(
                severity=AuditSeverity.INFO,
                code=WarningCode.CICIOT_HOMOGENEITY_VERIFIED.value,
                message=(
                    f"{cell} pairwise JS mean "
                    f"{record.pairwise_js_mean:.4g} < {homogeneity_threshold}; "
                    "reported claims may describe CICIoT2023 clients as homogeneous."
                ),
            ))
        elif record.homogeneity_verdict == HomogeneityVerdict.HETEROGENEOUS:
            warnings.append(WarningRecord(
                severity=AuditSeverity.WARNING,
                code=WarningCode.CICIOT_NOT_HOMOGENEOUS.value,
                message=(
                    f"{cell} pairwise JS mean "
                    f"{record.pairwise_js_mean:.4g} \u2265 {homogeneity_threshold}; "
                    "reported claims must not describe CICIoT2023 clients as homogeneous."
                ),
            ))
        else:
            warnings.append(WarningRecord(
                severity=AuditSeverity.BLOCKED_PENDING_RUN,
                code=WarningCode.CICIOT_HOMOGENEITY_INCOMPLETE.value,
                message=f"{cell} pairwise homogeneity could not be computed (insufficient client data).",
                exact_command=_BLOCKED_COMMAND,
            ))


def _emit_flat_cv_tpr_warnings(
    cell_panel: dict[tuple[Regime, int, str | None, Baseline], _CellPanel],
    warnings: list[WarningRecord],
) -> None:
    by_cell: dict[tuple[Regime, int, str | None], list[float]] = defaultdict(list)
    for (regime, seed, alpha_text, _baseline), panel in cell_panel.items():
        if panel.cv_tpr is not None:
            by_cell[(regime, seed, alpha_text)].append(float(panel.cv_tpr))
    for key, values in by_cell.items():
        if len(values) < 2:
            continue
        spread = max(values) - min(values)
        if spread < _FLAT_CV_TPR_EPSILON:
            regime, seed, alpha_text = key
            warnings.append(WarningRecord(
                severity=AuditSeverity.WARNING,
                code=WarningCode.FLAT_CV_TPR_SUSPICIOUS.value,
                message=(
                    f"{regime}_seed{seed}_alpha{alpha_text} CV(TPR) is identical across "
                    f"{len(values)} baselines (spread {spread:.2e}); investigate denominator, "
                    "NaN fill, or zero-attack-client aggregation."
                ),
            ))


def _check_b2_utility_tradeoff(
    regime: Regime, seed: int, alpha_text: str | None,
    b1: _CellPanel, b2: _CellPanel, warnings: list[WarningRecord],
) -> None:
    if b1.cv_fpr is None or b2.cv_fpr is None or b2.cv_fpr >= b1.cv_fpr:
        return
    worsened = [
        short
        for short, attr in ((MetricName.MACRO_F1.value, "macro_f1_mean"), (MetricName.PR_AUC.value, "pr_auc_mean"), (MetricName.AUROC.value, "auroc_mean"), (MetricName.CV_TPR.value, MetricName.CV_TPR.value))
        if getattr(b1, attr) is not None and getattr(b2, attr) is not None
        and float(getattr(b2, attr)) < float(getattr(b1, attr))
    ]
    if worsened:
        warnings.append(WarningRecord(
            severity=AuditSeverity.WARNING, code=WarningCode.B2_UTILITY_TRADEOFF.value,
            message=f"{regime}_seed{seed}_alpha{alpha_text} B2 improves CV(FPR) but worsens {', '.join(worsened)} relative to B1.",
        ))



def _build_seed_deltas(
    cell_panel: dict[tuple[Regime, int, str | None, Baseline], _CellPanel],
    warnings: list[WarningRecord],
) -> list[SeedDeltaRecord]:
    # Side effect: emits B2_UTILITY_TRADEOFF warnings.
    out: list[SeedDeltaRecord] = []
    for regime, seed, alpha_text in sorted({(r, s, a) for r, s, a, _ in cell_panel}):
        b1_key = (regime, seed, alpha_text, Baseline.B1)
        b2_key = (regime, seed, alpha_text, Baseline.B2)
        b4_key = (regime, seed, alpha_text, Baseline.B4)
        b1 = cell_panel[b1_key] if b1_key in cell_panel else _CellPanel()
        b2 = cell_panel[b2_key] if b2_key in cell_panel else _CellPanel()
        b4 = cell_panel[b4_key] if b4_key in cell_panel else _CellPanel()
        out.append(SeedDeltaRecord(
            regime=regime,
            alpha=alpha_text,
            seed=seed,
            b1_cv_fpr=b1.cv_fpr,
            b2_cv_fpr=b2.cv_fpr,
            b4_cv_fpr=b4.cv_fpr,
            b1_cv_tpr=b1.cv_tpr,
            b2_cv_tpr=b2.cv_tpr,
            b4_cv_tpr=b4.cv_tpr,
            b1_macro_f1_mean=b1.macro_f1_mean,
            b2_macro_f1_mean=b2.macro_f1_mean,
            b4_macro_f1_mean=b4.macro_f1_mean,
            b1_macro_f1_p10=b1.macro_f1_p10,
            b2_macro_f1_p10=b2.macro_f1_p10,
            b4_macro_f1_p10=b4.macro_f1_p10,
            b1_auroc_mean=b1.auroc_mean,
            b2_auroc_mean=b2.auroc_mean,
            b4_auroc_mean=b4.auroc_mean,
            b1_pr_auc_mean=b1.pr_auc_mean,
            b2_pr_auc_mean=b2.pr_auc_mean,
            b4_pr_auc_mean=b4.pr_auc_mean,
            b1_mean_fpr=b1.mean_fpr,
            b2_mean_fpr=b2.mean_fpr,
            b4_mean_fpr=b4.mean_fpr,
            b1_std_fpr=b1.std_fpr,
            b2_std_fpr=b2.std_fpr,
            b4_std_fpr=b4.std_fpr,
            b1_iqr_fpr=b1.iqr_fpr,
            b2_iqr_fpr=b2.iqr_fpr,
            b4_iqr_fpr=b4.iqr_fpr,
            b1_worst_client_fpr=b1.worst_client_fpr,
            b2_worst_client_fpr=b2.worst_client_fpr,
            b4_worst_client_fpr=b4.worst_client_fpr,
            b1_worst_client_tpr=b1.worst_client_tpr,
            b2_worst_client_tpr=b2.worst_client_tpr,
            b4_worst_client_tpr=b4.worst_client_tpr,
            b1_worst_client_macro_f1=b1.worst_client_macro_f1,
            b2_worst_client_macro_f1=b2.worst_client_macro_f1,
            b4_worst_client_macro_f1=b4.worst_client_macro_f1,
            b1_worst_client_balanced_accuracy=b1.worst_client_balanced_accuracy,
            b2_worst_client_balanced_accuracy=b2.worst_client_balanced_accuracy,
            b4_worst_client_balanced_accuracy=b4.worst_client_balanced_accuracy,
            delta_cv_fpr_b1_minus_b2=_safe_diff(b1.cv_fpr, b2.cv_fpr),
            delta_cv_fpr_b1_minus_b4=_safe_diff(b1.cv_fpr, b4.cv_fpr),
            delta_cv_tpr_b1_minus_b2=_safe_diff(b1.cv_tpr, b2.cv_tpr),
            delta_cv_tpr_b1_minus_b4=_safe_diff(b1.cv_tpr, b4.cv_tpr),
            delta_macro_f1_b1_minus_b2=_safe_diff(b1.macro_f1_mean, b2.macro_f1_mean),
            delta_macro_f1_b1_minus_b4=_safe_diff(b1.macro_f1_mean, b4.macro_f1_mean),
            delta_pr_auc_b1_minus_b2=_safe_diff(b1.pr_auc_mean, b2.pr_auc_mean),
            delta_pr_auc_b1_minus_b4=_safe_diff(b1.pr_auc_mean, b4.pr_auc_mean),
            delta_auroc_b1_minus_b2=_safe_diff(b1.auroc_mean, b2.auroc_mean),
            delta_auroc_b1_minus_b4=_safe_diff(b1.auroc_mean, b4.auroc_mean),
            b1_convergence_round=b1.convergence_round,
            b2_convergence_round=b2.convergence_round,
            b4_convergence_round=b4.convergence_round,
            b1_tau_global=b1.tau_global,
            b2_tau_global=b2.tau_global,
            b4_tau_global=b4.tau_global,
            coverage_ratio=str(b1.coverage_ratio or b2.coverage_ratio or b4.coverage_ratio or "0/0"),
            status=AuditStatus.PASS if (b1.cv_fpr is not None and b2.cv_fpr is not None) else AuditStatus.BLOCKED_PENDING_RUN,
        ))

        _check_b2_utility_tradeoff(regime, seed, alpha_text, b1, b2, warnings)
    return out


def _binary_auc_fields(row: dict[str, Any], benign: np.ndarray | None, attack: np.ndarray | None) -> tuple[float | None, float | None]:
    if MetricName.AUROC.value in row or MetricName.PR_AUC.value in row:
        return (
            None if row.get(MetricName.AUROC.value) is None else float(row[MetricName.AUROC.value]),
            None if row.get(MetricName.PR_AUC.value) is None else float(row[MetricName.PR_AUC.value]),
        )
    if benign is None or attack is None:
        return None, None
    ranking = compute_binary_ranking_metrics(benign, attack)
    return ranking.auroc, ranking.pr_auc


def _recon_summary(
    *,
    run_id: str | None,
    baseline: Baseline | None,
    seed: int,
    regime: Regime,
    alpha: str | None,
    client_id: str,
    stage: ScoringStage,
    arr: np.ndarray,
    overlap: float | None = None,
) -> ReconstructionErrorSummaryRecord:
    return ReconstructionErrorSummaryRecord(
        run_id=run_id,
        baseline=baseline,
        seed=seed,
        regime=regime,
        alpha=alpha,
        client_id=client_id,
        stage=stage,
        count=int(arr.size),
        mean=float(np.mean(arr)) if arr.size else None,
        std=float(np.std(arr, ddof=1)) if arr.size > 1 else None,
        min=float(np.min(arr)) if arr.size else None,
        p50=float(np.percentile(arr, 50)) if arr.size else None,
        p95=float(np.percentile(arr, 95)) if arr.size else None,
        max=float(np.max(arr)) if arr.size else None,
        benign_attack_overlap=overlap,
        array_hash=array_hash(arr),
    )


def _overlap_rate(benign: np.ndarray, attack: np.ndarray) -> float | None:
    if benign.size == 0 or attack.size == 0:
        return None
    benign_p95 = float(np.percentile(benign, 95))
    return float(np.mean(attack <= benign_p95))


def _score_stage_files(score_root: Path, stage: ScoringStage) -> list[Path]:
    stage_dir = score_root / stage.value
    return sorted(stage_dir.glob("*.parquet")) if stage_dir.exists() else []


def _load_cal_errors(score_root: Path) -> dict[str, np.ndarray]:
    return {path.stem: _read_scores(path) for path in _score_stage_files(score_root, ScoringStage.CAL)}


def _threshold_result(
    baseline: Baseline,
    regime: Regime,
    cal_errors: dict[str, np.ndarray],
    tau_global: float,
    *,
    cfg: DatpConfig,
):
    n_min = cfg.threshold.n_min
    q = cfg.threshold.q
    if baseline == Baseline.B1:
        return b1.compute(cal_errors, n_min=n_min, q=q)
    if baseline == Baseline.B2:
        return b2.compute(cal_errors, n_min=n_min, tau_global=tau_global, q=q)
    if baseline == Baseline.B3:
        return b3.compute(
            cal_errors,
            n_min=n_min,
            tau_global=tau_global,
            family_map=NBAIOT_SPEC.family_map,
            q=q,
            regime=regime,
        )
    if baseline == Baseline.B4:
        return b4.compute(
            cal_errors,
            n_min=n_min,
            tau_global=tau_global,
            regime=regime,
            q=q,
            random_state=cfg.threshold.b4_random_state,
            k_regime_a=cfg.threshold.b4_k_regime_a,
            k_candidates=list(cfg.threshold.b4_k_candidates),
            n_init=cfg.threshold.b4_n_init,
        )
    return None


def _build_partition_audit(
    *,
    regime: Regime,
    alpha_text: str | None,
    seed: int,
    partition_path: Path,
    partition_payload: dict[str, Any],
    metadata: dict[str, Any],
    feature_count: int | None,
    split_hash: str,
) -> DatasetPartitionAudit:
    dataset_name = str(partition_payload["dataset"])
    file_hash_keys: list[str] = list(partition_payload["file_hashes"].keys())

    nbaiot_per_device: list[NBaIoTDeviceCounts] = []
    if regime in (Regime.A, Regime.C):
        processed_root = partition_path.parent
        nbaiot_per_device = build_nbaiot_per_device(processed_root, file_hash_keys)

    ciciot_protocol = build_ciciot_protocol() if regime == Regime.B else None
    chrono_ok, gap_ok = chronological_flags_for(regime, partition_payload)

    return DatasetPartitionAudit(
        dataset=dataset_name,
        regime=regime,
        alpha=alpha_text,
        seed=seed if regime == Regime.C else None,
        manifest_path=str(partition_path),
        manifest_hash=hash_file(partition_path),
        split_hash=split_hash,
        feature_count=feature_count,
        client_count=metadata["n_clients"] if "n_clients" in metadata else metadata["n_devices"],
        nbaiot_per_device=nbaiot_per_device,
        ciciot_protocol=ciciot_protocol,
        confound_summary=confound_summary_for(regime),
        chronological_split_verified=chrono_ok,
        contiguous_gap_verified=gap_ok,
    )


def _metric_counts(metrics: dict[str, Any]) -> tuple[int | None, int | None, int | None]:
    per_client = _normalized_per_client(metrics)
    cal = None
    test = sum(int(row["n_benign"]) + int(row["n_attack"]) for row in per_client)
    return None, cal, test


def _normalized_per_client(metrics: dict[str, Any]) -> list[dict[str, Any]]:
    per_client = metrics["per_client"]
    if isinstance(per_client, dict):
        return [dict(values, client_id=client_id) for client_id, values in per_client.items()]
    return list(per_client)


@dataclasses.dataclass
class _AuditAccumulator:

    manifest_records: list[RunManifestRecord] = dataclasses.field(default_factory=list)
    client_records: list[ClientMetricRecord] = dataclasses.field(default_factory=list)
    attack_records: list[PerAttackMetricRecord] = dataclasses.field(default_factory=list)
    threshold_records: list[ThresholdRecord] = dataclasses.field(default_factory=list)
    recon_records: list[ReconstructionErrorSummaryRecord] = dataclasses.field(default_factory=list)
    denominator_records: list[MetricDenominatorAuditRecord] = dataclasses.field(default_factory=list)
    convergence_records: list[ConvergenceAuditRecord] = dataclasses.field(default_factory=list)
    cluster_records: list[ClusterAssignmentRecord] = dataclasses.field(default_factory=list)
    companion_records: list[FPRCompanionRecord] = dataclasses.field(default_factory=list)
    worst_client_records: list[WorstClientRecord] = dataclasses.field(default_factory=list)
    homogeneity_records: list[CICIoTHomogeneityRecord] = dataclasses.field(default_factory=list)
    regime_c_alpha_records: list[RegimeCAlphaAuditRecord] = dataclasses.field(default_factory=list)
    partition_audits: dict[str, DatasetPartitionAudit] = dataclasses.field(default_factory=dict)
    invariant_inputs: dict[tuple[Regime, int, str | None], dict[Baseline, dict[str, str]]] = dataclasses.field(
        default_factory=lambda: defaultdict(dict)
    )
    score_hashes_by_cell: dict[tuple[Regime, int, str | None], dict[Baseline, dict[tuple[str, str], str]]] = dataclasses.field(
        default_factory=lambda: defaultdict(dict)
    )
    recomputation_records: list[MetricRecomputationRecord] = dataclasses.field(default_factory=list)
    cell_panel: dict[tuple[Regime, int, str | None, Baseline], _CellPanel] = dataclasses.field(default_factory=dict)
    warnings: list[WarningRecord] = dataclasses.field(default_factory=list)
    missing_confusion_warned: set[str] = dataclasses.field(default_factory=set)


def _process_run(
    metrics_path: Path,
    base_dir: Path,
    acc: _AuditAccumulator,
    *,
    git_commit: str,
    timestamp: str,
    scoring_hash: str,
    threshold_hash: str,
    metrics_hash: str,
    cfg: DatpConfig,
    data_root: Path | None = None,
) -> None:
    regime, baseline, seed, alpha = _parse_metric_path(base_dir, metrics_path)
    alpha_text = alpha_label(alpha)
    run_id = RunIdentity(regime=regime, baseline=baseline, seed=seed, alpha=alpha).audit_id()
    metrics = _load_json(metrics_path)
    schema_failures = validate_metrics_payload(metrics, module="audit.results")
    if schema_failures:
        for failure in schema_failures:
            acc.warnings.append(WarningRecord(
                severity=AuditSeverity.FAIL,
                code=WarningCode.SCHEMA_VERSION_MISMATCH.value,
                message=f"{metrics_path}: {failure}",
            ))
        return
    _data_root = data_root if data_root is not None else base_dir
    score_root = _score_root(base_dir, regime, seed, alpha)
    checkpoint = _checkpoint_path(base_dir, regime, seed, alpha)
    partition_path = _partition_manifest_path(regime, seed, alpha, base_dir, data_root=_data_root)
    partition_payload = _manifest_payload(partition_path)
    metadata = partition_payload.get("metadata", {})
    feature_count = metadata["n_features"] if "n_features" in metadata else None
    normalized_clients = _normalized_per_client(metrics)
    client_count = int(metrics["client_count"])
    split_hash = _split_hash(partition_path)
    model_hash = hash_file(checkpoint)
    training_hash = hash_file(metrics_path.parent / "resolved_config.yaml")
    preprocessing_hash = hash_file(partition_path)
    train_count, calibration_count, test_count = _metric_counts(metrics)
    convergence_round, convergence_value, convergence_status, curve_path = _convergence_payload(checkpoint)
    invariant_key = (regime, seed, alpha_text)

    if partition_path.exists():
        acc.partition_audits[f"{regime}:{seed}:{alpha_text}"] = _build_partition_audit(
            regime=regime,
            alpha_text=alpha_text,
            seed=seed,
            partition_path=partition_path,
            partition_payload=partition_payload,
            metadata=metadata,
            feature_count=feature_count,
            split_hash=split_hash,
        )
    else:
        acc.warnings.append(WarningRecord(
            severity=AuditSeverity.BLOCKED_PENDING_RUN,
            code=WarningCode.MISSING_PARTITION_MANIFEST.value,
            message=f"Partition manifest is missing for {run_id}: {partition_path}",
            exact_command="datp diagnostic --regime a --seed 0",
        ))

    cal_errors: dict[str, np.ndarray] = {}
    test_benign_scores: dict[str, np.ndarray] = {}
    test_attack_scores: dict[str, np.ndarray] = {}
    threshold_result = None
    if baseline in _CONTROLLED:
        try:
            cal_errors = _load_cal_errors(score_root)
            test_benign_scores = {p.stem: _read_scores(p) for p in _score_stage_files(score_root, ScoringStage.TEST_BENIGN)}
            test_attack_scores = {p.stem: _read_scores(p) for p in _score_stage_files(score_root, ScoringStage.TEST_ATTACK)}
            threshold_result = _threshold_result(baseline, regime, cal_errors, float(metrics["tau_global"]), cfg=cfg)
        except Exception as exc:
            acc.warnings.append(WarningRecord(
                severity=AuditSeverity.FAIL,
                code=WarningCode.THRESHOLD_RECONSTRUCTION_FAILED.value,
                message=f"Could not reconstruct threshold assignments for {run_id}: {exc}",
            ))

    if threshold_result is not None:
        local_taus = {
            cid: float(np.percentile(errors, cfg.threshold.q * 100))
            for cid, errors in cal_errors.items()
            if errors.size >= cfg.threshold.n_min
        }
        for ct in sorted(threshold_result.client_thresholds, key=lambda item: item.client_id):
            acc.threshold_records.append(ThresholdRecord(
                run_id=run_id, seed=seed, regime=regime, baseline=baseline, alpha=alpha_text,
                client_id=ct.client_id,
                threshold_value=float(ct.threshold),
                threshold_source=ThresholdSource.TAU_GLOBAL_FALLBACK if ct.calibration_pending else BASELINE_THRESHOLD_SOURCE[baseline],
                calibration_pending=ct.calibration_pending,
                tau_global=float(threshold_result.tau_global),
                threshold_aggregation_method=_lookup_threshold_agg(baseline),
                local_tau_i=local_taus.get(ct.client_id),
            ))
        if baseline == Baseline.B4 and threshold_result.b4_metadata:
            for cluster_id, info in threshold_result.b4_metadata.cluster_info.items():
                for client_id in info.members:
                    fp = (
                        threshold_result.b4_metadata.fingerprints[client_id]
                        if client_id in threshold_result.b4_metadata.fingerprints
                        else []
                    )
                    acc.cluster_records.append(ClusterAssignmentRecord(
                        run_id=run_id, seed=seed, regime=regime, alpha=alpha_text,
                        client_id=client_id, cluster_id=cluster_id,
                        threshold_value=float(info.tau_cluster),
                        fingerprint_mean=float(fp[0]) if len(fp) > 0 else None,
                        fingerprint_std=float(fp[1]) if len(fp) > 1 else None,
                        fingerprint_skew=float(fp[2]) if len(fp) > 2 else None,
                        fingerprint_p95=float(fp[3]) if len(fp) > 3 else None,
                        k_selected=threshold_result.b4_metadata.k,
                        silhouette=threshold_result.b4_metadata.silhouette,
                        silhouette_scores=threshold_result.b4_metadata.silhouette_scores,
                    ))
        if baseline == Baseline.B3 and threshold_result.b3_metadata:
            for family, info in threshold_result.b3_metadata.family_info.items():
                if info.threshold_variance > cfg.quality_gates.b3_dispersion_threshold:
                    acc.warnings.append(WarningRecord(
                        severity=AuditSeverity.WARNING,
                        code=WarningCode.B3_TAXONOMY_TOO_COARSE.value,
                        message=f"{run_id} family {family} has high within-family threshold dispersion.",
                    ))
        if baseline == Baseline.B1:
            pooled = float(np.percentile(np.concatenate(list(cal_errors.values())), cfg.threshold.q * 100))
            if not math.isclose(float(threshold_result.tau_global), pooled):
                acc.warnings.append(WarningRecord(
                    severity=AuditSeverity.INFO,
                    code=WarningCode.B1_NOT_POOLED_PERCENTILE.value,
                    message=f"{run_id} tau_global is the arithmetic mean of eligible local tau_i values.",
                    exact_command=None,
                ))

    if baseline == Baseline.B0:
        tau_key = "tau_b0" if "tau_b0" in metrics else "tau_global"
        tau = float(metrics[tau_key])
        pending_ids = set(metrics["pending_ids"])
        for row in normalized_clients:
            acc.threshold_records.append(ThresholdRecord(
                run_id=run_id, seed=seed, regime=regime, baseline=baseline, alpha=alpha_text,
                client_id=str(row[CLIENT_ID_KEY]),
                threshold_value=tau,
                threshold_source=ThresholdSource.B0_POOLED,
                calibration_pending=str(row[CLIENT_ID_KEY]) in pending_ids,
                tau_global=tau,
                threshold_aggregation_method=_lookup_threshold_agg(Baseline.B0),
                local_tau_i=None,
            ))

    eligible_count = int(metrics["eligible_count"])
    coverage_ratio = f"{eligible_count}/{client_count}" if client_count else "0/0"
    incomplete = {str(cid) for cid in metrics["eval_incomplete_ids"]}
    eligible_ids = {str(cid) for cid in metrics["eligible_ids"]}
    pending_ids = {str(cid) for cid in metrics["pending_ids"]}
    pending_count = int(metrics["pending_count"])

    _client_thresholds: dict[str, float] = {}
    if threshold_result is not None:
        for _ct in threshold_result.client_thresholds:
            _client_thresholds[_ct.client_id] = float(_ct.threshold)

    for row in normalized_clients:
        cm = row[CONFUSION_MATRIX_KEY] if CONFUSION_MATRIX_KEY in row else {}
        tp, fp, tn, fn = (
            int(cm[k]) if k in cm else 0
            for k in CONFUSION_KEYS
        )
        client_id = str(row[CLIENT_ID_KEY])
        n_benign = int(row["n_benign"])
        n_attack = int(row["n_attack"])
        fpr_den, tpr_den = fp + tn, tp + fn
        eval_incomplete = client_id in incomplete or n_attack == 0
        has_confusion = bool(cm)
        if not has_confusion and run_id not in acc.missing_confusion_warned:
            acc.missing_confusion_warned.add(run_id)
            acc.warnings.append(WarningRecord(
                severity=AuditSeverity.BLOCKED_PENDING_RUN,
                code=WarningCode.MISSING_CONFUSION_MATRIX.value,
                message=f"Per-client confusion matrices are missing for {run_id}; denominator gates cannot be verified.",
                exact_command=_BLOCKED_COMMAND,
            ))
        fpr_ok = has_confusion and fpr_den == n_benign and n_benign > 0 and math.isfinite(float(row[MetricName.FPR.value]))
        tpr_ok = has_confusion and tpr_den == n_attack and n_attack > 0 and math.isfinite(float(row[MetricName.TPR.value]))
        if not has_confusion:
            fpr_status = tpr_status = macro_f1_status = DenominatorStatus.BLOCKED_PENDING_RUN
        elif eval_incomplete:
            fpr_status = DenominatorStatus.PASS if fpr_ok else DenominatorStatus.FAIL
            tpr_status = macro_f1_status = DenominatorStatus.EXCLUDED_EVALUATION_INCOMPLETE
        else:
            fpr_status = DenominatorStatus.PASS if fpr_ok else DenominatorStatus.FAIL
            tpr_status = DenominatorStatus.PASS if tpr_ok else DenominatorStatus.FAIL
            macro_f1_status = DenominatorStatus.PASS
        acc.denominator_records.append(MetricDenominatorAuditRecord(
            run_id=run_id, seed=seed, regime=regime, baseline=baseline, alpha=alpha_text,
            client_id=client_id,
            fpr_denominator=fpr_den, fpr_denominator_expected=n_benign, fpr_status=fpr_status,
            tpr_denominator=tpr_den, tpr_denominator_expected=n_attack, tpr_status=tpr_status,
            macro_f1_status=macro_f1_status,
        ))
        if has_confusion:
            _append_recomputation_records(
                acc, run_id=run_id, seed=seed, regime=regime, baseline=baseline, alpha=alpha_text,
                client_id=client_id, row=row, tp=tp, fp=fp, tn=tn, fn=fn,
                n_benign=n_benign, n_attack=n_attack,
            )
        auroc, pr_auc = _binary_auc_fields(row, test_benign_scores.get(client_id), test_attack_scores.get(client_id))
        acc.client_records.append(ClientMetricRecord(
            run_id=run_id, seed=seed, regime=regime, baseline=baseline, alpha=alpha_text,
            client_id=client_id,
            fpr=float(row[MetricName.FPR.value]), tpr=float(row[MetricName.TPR.value]),
            balanced_accuracy=float(row[MetricName.BALANCED_ACCURACY.value]), macro_f1=float(row[MetricName.MACRO_F1.value]),
            auroc=auroc, pr_auc=pr_auc,
            n_benign=n_benign, n_attack=n_attack, tp=tp, fp=fp, tn=tn, fn=fn,
            eligible=client_id in eligible_ids,
            calibration_pending=client_id in pending_ids,
            evaluation_incomplete=eval_incomplete,
            coverage_ratio=coverage_ratio,
        ))
        acc.attack_records.append(PerAttackMetricRecord(
            run_id=run_id, seed=seed, regime=regime, baseline=baseline, alpha=alpha_text,
            client_id=client_id, attack_label=_BINARY_ATTACK_LABEL,
            status=AttackMetricStatus.EXCLUDED_EVALUATION_INCOMPLETE if eval_incomplete else AttackMetricStatus.PASS,
            tpr=None if eval_incomplete else float(row[MetricName.TPR.value]),
            detected_count=None if eval_incomplete else tp,
            denominator=None if eval_incomplete else n_attack,
        ))
        # Per-attack-family records (Regime B / CICIoT2023 only).
        if not eval_incomplete:
            raw_attack_scores = test_attack_scores.get(client_id)
            attack_labels = _load_client_attack_labels(regime, client_id, prepared_root_for_regime(regime, base_dir=_data_root, seed=seed, alpha=alpha))
            if raw_attack_scores is not None and attack_labels is not None and attack_labels.size > 0:
                from datp.data.datasets.ciciot2023.spec import attack_family as _attack_family  # noqa: PLC0415
                threshold_val = _client_thresholds[client_id]
                for pat in compute_per_attack_tpr(client_id, raw_attack_scores, attack_labels, threshold_val, _attack_family):
                    pat_status = (
                        AttackMetricStatus.FAIL if pat.family is None else AttackMetricStatus.PASS
                    )
                    acc.attack_records.append(PerAttackMetricRecord(
                        run_id=run_id, seed=seed, regime=regime, baseline=baseline, alpha=alpha_text,
                        client_id=pat.client_id, attack_label=pat.attack_label,
                        status=pat_status,
                        tpr=pat.tpr if math.isfinite(pat.tpr) else None,
                        detected_count=pat.detected_count,
                        denominator=pat.denominator,
                    ))

    eligible_pairs_fpr = [(str(r[CLIENT_ID_KEY]), float(r[MetricName.FPR.value])) for r in normalized_clients if r[CLIENT_ID_KEY] in eligible_ids]
    eligible_pairs_tpr = [
        (str(r[CLIENT_ID_KEY]), float(r[MetricName.TPR.value]))
        for r in normalized_clients
        if r[CLIENT_ID_KEY] in eligible_ids and int(r["n_attack"]) > 0 and str(r[CLIENT_ID_KEY]) not in incomplete
    ]
    eligible_pairs_macro_f1 = [(str(r[CLIENT_ID_KEY]), float(r[MetricName.MACRO_F1.value])) for r in normalized_clients if r[CLIENT_ID_KEY] in eligible_ids]
    eligible_pairs_ba = [(str(r[CLIENT_ID_KEY]), float(r[MetricName.BALANCED_ACCURACY.value])) for r in normalized_clients if r[CLIENT_ID_KEY] in eligible_ids]

    eligible_fpr_values = [v for _, v in eligible_pairs_fpr]
    eligible_macro_f1_values = [v for _, v in eligible_pairs_macro_f1]
    worst_fpr_id, worst_fpr_value = _argworst(eligible_pairs_fpr, WORST_CLIENT_DIRECTIONS[MetricName.FPR])
    worst_tpr_id, worst_tpr_value = _argworst(eligible_pairs_tpr, WORST_CLIENT_DIRECTIONS[MetricName.TPR])
    worst_f1_id, worst_f1_value = _argworst(eligible_pairs_macro_f1, WORST_CLIENT_DIRECTIONS[MetricName.MACRO_F1])
    worst_ba_id, worst_ba_value = _argworst(eligible_pairs_ba, WORST_CLIENT_DIRECTIONS[MetricName.BALANCED_ACCURACY])

    cv_fpr_value = float(metrics[MetricName.CV_FPR.value])
    cv_fpr_record_value = cv_fpr_value if math.isfinite(cv_fpr_value) else None
    if math.isfinite(cv_fpr_value):
        mean_fpr_raw = metrics.get(MetricName.MEAN_FPR.value)
        std_fpr_raw = metrics.get(MetricName.STD_FPR.value)
        if mean_fpr_raw is None or std_fpr_raw is None:
            acc.warnings.append(WarningRecord(
                severity=AuditSeverity.FAIL,
                code=WarningCode.NAKED_CV_FPR.value,
                message=(
                    f"{run_id} contains cv_fpr={cv_fpr_value:.4g} without companion fields "
                    f"mean_fpr/std_fpr. Re-run datp sweep to regenerate metrics artifacts."
                ),
                exact_command=_BLOCKED_COMMAND,
            ))
    mean_fpr_value = _finite_mean(eligible_fpr_values)
    std_fpr_value = _std_or_none(eligible_fpr_values)
    iqr_fpr_value = _iqr_or_none(eligible_fpr_values)
    macro_f1_p10_value = _percentile_or_none(eligible_macro_f1_values, 10.0)

    acc.companion_records.append(FPRCompanionRecord(
        run_id=run_id, seed=seed, regime=regime, baseline=baseline, alpha=alpha_text,
        cv_fpr=cv_fpr_record_value, mean_fpr=mean_fpr_value, std_fpr=std_fpr_value,
        iqr_fpr=iqr_fpr_value, worst_client_fpr=worst_fpr_value,
        eligible_count=len(eligible_ids), client_count=client_count, coverage_ratio=coverage_ratio,
    ))
    for metric_name, (cid, value, pool) in {
        MetricName.FPR: (worst_fpr_id, worst_fpr_value, len(eligible_pairs_fpr)),
        MetricName.TPR: (worst_tpr_id, worst_tpr_value, len(eligible_pairs_tpr)),
        MetricName.MACRO_F1: (worst_f1_id, worst_f1_value, len(eligible_pairs_macro_f1)),
        MetricName.BALANCED_ACCURACY: (worst_ba_id, worst_ba_value, len(eligible_pairs_ba)),
    }.items():
        acc.worst_client_records.append(WorstClientRecord(
            run_id=run_id, seed=seed, regime=regime, baseline=baseline, alpha=alpha_text,
            metric=metric_name, direction=WORST_CLIENT_DIRECTIONS[metric_name],
            worst_client_id=cid, worst_value=value, eligible_pool_size=pool,
        ))

    cv_tpr_raw = metrics.get(MetricName.CV_TPR.value)
    cv_tpr_value = float(cv_tpr_raw) if cv_tpr_raw is not None and math.isfinite(float(cv_tpr_raw)) else None
    acc.cell_panel[(regime, seed, alpha_text, baseline)] = _CellPanel(
        cv_fpr=cv_fpr_record_value, cv_tpr=cv_tpr_value,
        mean_fpr=mean_fpr_value, std_fpr=std_fpr_value, iqr_fpr=iqr_fpr_value,
        worst_client_fpr=worst_fpr_value, worst_client_tpr=worst_tpr_value,
        worst_client_macro_f1=worst_f1_value, worst_client_balanced_accuracy=worst_ba_value,
        macro_f1_mean=_finite_mean([float(r[MetricName.MACRO_F1.value]) for r in normalized_clients]),
        macro_f1_p10=macro_f1_p10_value,
        auroc_mean=_finite_mean([float(r[MetricName.AUROC.value]) for r in normalized_clients if r.get(MetricName.AUROC.value) is not None]),
        pr_auc_mean=_finite_mean([float(r[MetricName.PR_AUC.value]) for r in normalized_clients if r.get(MetricName.PR_AUC.value) is not None]),
        convergence_round=convergence_round,
        tau_global=float(metrics["tau_global"]) if metrics.get("tau_global") is not None else None,
        coverage_ratio=coverage_ratio,
    )

    acc.manifest_records.append(RunManifestRecord(
        run_id=run_id, timestamp=timestamp, git_commit_hash=git_commit,
        seed=seed, dataset=_lookup_dataset(regime), regime=regime, baseline=baseline, alpha=alpha_text,
        client_count=client_count, split_hash=split_hash, model_hash=model_hash, encoder_hash=model_hash,
        training_config_hash=training_hash, preprocessing_config_hash=preprocessing_hash,
        scoring_code_hash=scoring_hash, threshold_code_hash=threshold_hash, metrics_code_hash=metrics_hash,
        artifact_schema_version=AUDIT_SCHEMA_VERSION,
        convergence_round=convergence_round, convergence_criterion_value=convergence_value,
        convergence_status=convergence_status, eligible_clients=eligible_count,
        calibration_pending_clients=pending_count, evaluation_incomplete_clients=len(incomplete),
        feature_count=feature_count, feature_list_hash=_feature_hash(feature_count),
        threshold_aggregation_method=_lookup_threshold_agg(baseline),
        normalization_scope=NormalizationScope(metrics["normalization_scope"]) if metrics.get("normalization_scope") else None,
        train_count=train_count, calibration_count=calibration_count, test_count=test_count,
    ))
    acc.invariant_inputs[invariant_key][baseline] = {
        "split_hash": split_hash, "model_hash": model_hash, "encoder_hash": model_hash,
        "scoring_code_hash": scoring_hash, "metrics_code_hash": metrics_hash,
    }

    if baseline == Baseline.B0:
        b0_auroc = float(metrics[MetricName.AUROC.value]) if metrics.get(MetricName.AUROC.value) is not None else math.nan
        b0_pr_auc = float(metrics[MetricName.PR_AUC.value]) if metrics.get(MetricName.PR_AUC.value) is not None else math.nan
        norm_mode = metrics["normalization_mode"]
        if not math.isfinite(b0_auroc) or not math.isfinite(b0_pr_auc):
            acc.warnings.append(WarningRecord(
                severity=AuditSeverity.BLOCKED_PENDING_RUN,
                code=WarningCode.B0_SANITY_PR_AUC_PENDING.value,
                message=f"{run_id} B0 sanity gate is incomplete because AUROC or PR-AUC is missing (normalization_mode={norm_mode}).",
                exact_command="datp sweep --regime=a --resume",
            ))
        elif b0_auroc < cfg.quality_gates.b0_sanity_min:
            code = WarningCode.B0_SANITY_LOW_AUROC.value if norm_mode == "pooled_zscore" else WarningCode.B0_WEAK_AUC_BLOCKS_PAPER.value
            acc.warnings.append(WarningRecord(
                severity=AuditSeverity.FAIL,
                code=code,
                message=f"{run_id} B0 AUROC={b0_auroc:.4g} below threshold (normalization_mode={norm_mode}).",
                exact_command="make audit-results",
            ))
        elif b0_pr_auc < cfg.quality_gates.b0_sanity_min:
            code = WarningCode.B0_SANITY_LOW_PR_AUC.value if norm_mode == "pooled_zscore" else WarningCode.B0_WEAK_AUC_BLOCKS_PAPER.value
            acc.warnings.append(WarningRecord(
                severity=AuditSeverity.FAIL,
                code=code,
                message=f"{run_id} B0 PR-AUC={b0_pr_auc:.4g} below threshold (normalization_mode={norm_mode}).",
                exact_command="make audit-results",
            ))

    acc.convergence_records.append(ConvergenceAuditRecord(
        regime=regime, seed=seed, alpha=alpha_text, checkpoint_path=str(checkpoint),
        convergence_round=convergence_round, convergence_criterion_value=convergence_value,
        convergence_status=convergence_status, curve_path=curve_path,
    ))

    if baseline in _CONTROLLED and score_root.exists():
        cell_hashes: dict[tuple[str, str], str] = {}
        for stage in ScoringStage:
            for score_path in _score_stage_files(score_root, stage):
                arr = _read_scores(score_path)
                cell_hashes[(stage.value, score_path.stem)] = array_hash(arr)
                if baseline == Baseline.B1:
                    acc.recon_records.append(_recon_summary(
                        run_id=run_id, baseline=baseline, seed=seed, regime=regime, alpha=alpha_text,
                        client_id=score_path.stem, stage=stage, arr=arr,
                    ))
        acc.score_hashes_by_cell[invariant_key][baseline] = cell_hashes

    if baseline == Baseline.B1 and score_root.exists() and regime == Regime.B and cal_errors:
        payload = compute_ciciot_homogeneity(cal_errors, n_bins=cfg.quality_gates.js_divergence_n_bins, threshold=cfg.quality_gates.ciciot_homogeneity_threshold)
        acc.homogeneity_records.append(CICIoTHomogeneityRecord(
            regime=regime, seed=seed, alpha=alpha_text, baseline=baseline,
            n_clients_compared=payload.n_clients_compared, n_pairs=payload.n_pairs,
            n_bins=payload.n_bins, pairwise_js_mean=payload.pairwise_js_mean,
            pairwise_js_std=payload.pairwise_js_std, pairwise_js_p50=payload.pairwise_js_p50,
            pairwise_js_p95=payload.pairwise_js_p95, pairwise_js_max=payload.pairwise_js_max,
            fingerprint_method="benign_recon_error_histogram",
            homogeneity_verdict=payload.verdict,
        ))


_RECOMPUTATION_EPSILON = 1e-9
_RECOMPUTE_METRICS = (
    MetricName.FPR,
    MetricName.TPR,
    MetricName.BALANCED_ACCURACY,
    MetricName.MACRO_F1,
)


def _append_recomputation_records(
    acc: _AuditAccumulator,
    *,
    run_id: str,
    seed: int,
    regime: Regime,
    baseline: Baseline,
    alpha: str | None,
    client_id: str,
    row: "dict[str, Any]",
    tp: int,
    fp: int,
    tn: int,
    fn: int,
    n_benign: int,
    n_attack: int,
) -> None:
    bm = recompute_binary_metrics(tp, fp, tn, fn)
    recomputed: dict[MetricName, float] = {
        MetricName.FPR: bm.fpr,
        MetricName.TPR: bm.tpr,
        MetricName.BALANCED_ACCURACY: bm.balanced_accuracy,
        MetricName.MACRO_F1: bm.macro_f1,
    }
    for metric in _RECOMPUTE_METRICS:
        attack_dependent = metric in (MetricName.TPR, MetricName.BALANCED_ACCURACY, MetricName.MACRO_F1)
        if attack_dependent and n_attack == 0:
            acc.recomputation_records.append(MetricRecomputationRecord(
                run_id=run_id, seed=seed, regime=regime, baseline=baseline, alpha=alpha,
                client_id=client_id, metric=metric,
                saved_value=None, recomputed_value=None, abs_diff=None,
                status=DenominatorStatus.EXCLUDED_EVALUATION_INCOMPLETE,
            ))
            continue
        if metric == MetricName.FPR and n_benign == 0:
            acc.recomputation_records.append(MetricRecomputationRecord(
                run_id=run_id, seed=seed, regime=regime, baseline=baseline, alpha=alpha,
                client_id=client_id, metric=metric,
                saved_value=None, recomputed_value=None, abs_diff=None,
                status=DenominatorStatus.EXCLUDED_EVALUATION_INCOMPLETE,
            ))
            continue
        saved_raw = row.get(metric.value)
        saved = float(saved_raw) if saved_raw is not None else None
        recomp = recomputed[metric]
        if saved is not None and math.isfinite(saved) and math.isfinite(recomp):
            diff = abs(saved - recomp)
            record_status = DenominatorStatus.PASS if diff <= _RECOMPUTATION_EPSILON else DenominatorStatus.FAIL
        elif saved is None or (saved is not None and not math.isfinite(saved) and not math.isfinite(recomp)):
            diff = None
            record_status = DenominatorStatus.PASS
        else:
            diff = None
            record_status = DenominatorStatus.FAIL
        acc.recomputation_records.append(MetricRecomputationRecord(
            run_id=run_id, seed=seed, regime=regime, baseline=baseline, alpha=alpha,
            client_id=client_id, metric=metric,
            saved_value=saved,
            recomputed_value=recomp if math.isfinite(recomp) else None,
            abs_diff=diff,
            status=record_status,
        ))


def _emit_structural_warnings(acc: _AuditAccumulator, seed_deltas: list[SeedDeltaRecord]) -> None:
    if any(row.convergence_status == ConvergenceStatus.BLOCKED_PENDING_RUN for row in acc.convergence_records):
        acc.warnings.append(WarningRecord(
            severity=AuditSeverity.BLOCKED_PENDING_RUN, code=WarningCode.MISSING_CONVERGENCE_CURVES.value,
            message="Existing checkpoints do not include convergence curves or FedAvg-weighted benign validation loss per round.",
            exact_command=_BLOCKED_COMMAND,
        ))
    if not any(row.regime == Regime.A and row.status == AuditStatus.PASS for row in seed_deltas):
        acc.warnings.append(WarningRecord(
            severity=AuditSeverity.BLOCKED_PENDING_RUN, code=WarningCode.PRIMARY_DELTA_INCOMPLETE.value,
            message="Regime A B1-vs-B2 seed delta table is incomplete.", exact_command=_BLOCKED_COMMAND,
        ))
    if not acc.cluster_records:
        acc.warnings.append(WarningRecord(
            severity=AuditSeverity.BLOCKED_PENDING_RUN, code=WarningCode.B4_CLUSTER_DIAGNOSTICS_INCOMPLETE.value,
            message="No B4 cluster assignment diagnostics were generated from completed artifacts.",
            exact_command=_BLOCKED_COMMAND,
        ))
    if not any(row.baseline == Baseline.B0 for row in acc.manifest_records):
        acc.warnings.append(WarningRecord(
            severity=AuditSeverity.BLOCKED_PENDING_RUN, code=WarningCode.B0_NORMALIZATION_DIAGNOSTIC_BLOCKED.value,
            message="Centralized pooled-normalization vs per-device-normalization diagnostic cannot run because B0 artifacts are missing.",
            exact_command="datp sweep --regime=a --resume",
        ))
    acc.warnings.append(WarningRecord(
        severity=AuditSeverity.BLOCKED_PENDING_RUN, code=WarningCode.FIXED_OPERATING_POINT_METRICS_PENDING.value,
        message="FPR at fixed TPR and TPR at fixed FPR require persisted score arrays and operating-point configuration for every completed baseline cell.",
        exact_command="make audit-results",
    ))


def _enrich_regime_c_records_with_cv(
    records: list[RegimeCAlphaAuditRecord],
    cell_panel: dict[tuple[Regime, int, str | None, Baseline], _CellPanel],
) -> list[RegimeCAlphaAuditRecord]:
    enriched: list[RegimeCAlphaAuditRecord] = []
    for rec in records:
        alpha_text: str | None = rec.alpha if rec.alpha not in ("iid", "inf") else None
        if rec.alpha in ("iid", "inf"):
            alpha_text = "iid"
        b1_key = (Regime.C, rec.seed, alpha_text, Baseline.B1)
        b2_key = (Regime.C, rec.seed, alpha_text, Baseline.B2)
        b4_key = (Regime.C, rec.seed, alpha_text, Baseline.B4)
        b1_panel = cell_panel[b1_key] if b1_key in cell_panel else None
        b2_panel = cell_panel[b2_key] if b2_key in cell_panel else None
        b4_panel = cell_panel[b4_key] if b4_key in cell_panel else None
        b1_cv = b1_panel.cv_fpr if b1_panel is not None else None
        b2_cv = b2_panel.cv_fpr if b2_panel is not None else None
        b4_cv = b4_panel.cv_fpr if b4_panel is not None else None
        enriched.append(rec.model_copy(update={
            "b1_cv_fpr": b1_cv,
            "b2_cv_fpr": b2_cv,
            "b4_cv_fpr": b4_cv,
            "delta_b1_b2": _safe_diff(b1_cv, b2_cv),
            "delta_b1_b4": _safe_diff(b1_cv, b4_cv),
            "eligible_only_cv_fpr": b1_cv,
        }))
    return enriched


def _b4_stability_from_cluster_records(
    cluster_records: list[ClusterAssignmentRecord],
) -> list[B4ClusterStabilityRecord]:
    from collections import defaultdict as _dd
    by_regime_alpha: dict[tuple[Regime, str | None], dict[int, dict[str, int]]] = _dd(lambda: _dd(dict))
    for rec in cluster_records:
        try:
            cluster_int = int(rec.cluster_id.split("_")[-1]) if "_" in rec.cluster_id else int(rec.cluster_id)
        except (ValueError, IndexError):
            cluster_int = hash(rec.cluster_id)
        by_regime_alpha[(rec.regime, rec.alpha)][rec.seed][rec.client_id] = cluster_int

    stability: list[B4ClusterStabilityRecord] = []
    for (regime, alpha), by_seed in by_regime_alpha.items():
        stability.extend(compute_b4_cluster_stability(dict(by_seed), regime, alpha))
    return stability


def run_results_audit(base_dir: Path, audit_dir: Path, cfg: DatpConfig, data_root: Path | None = None) -> dict[str, Path]:
    base_dir = Path(base_dir)
    audit_dir = Path(audit_dir)
    audit_dir.mkdir(parents=True, exist_ok=True)

    git_commit = current_git_commit()
    timestamp = utc_timestamp()
    scoring_hash = source_hash([Path("src/datp/training/fl/scoring.py"), Path("src/datp/baselines/common/scoring.py")])
    threshold_hash = source_hash([
        Path("src/datp/baselines/main/b1.py"), Path("src/datp/baselines/main/b2.py"),
        Path("src/datp/baselines/main/b3.py"), Path("src/datp/baselines/main/b4.py"),
        Path("src/datp/baselines/common/thresholds.py"),
    ])
    metrics_hash = source_hash([Path("src/datp/evaluation/metrics.py"), Path("src/datp/evaluation/confusion.py")])

    acc = _AuditAccumulator()
    metric_paths = _completed_metric_paths(base_dir)
    if not metric_paths:
        acc.warnings.append(WarningRecord(
            severity=AuditSeverity.BLOCKED_PENDING_RUN,
            code=WarningCode.NO_COMPLETED_RESULTS.value,
            message="No completed metrics.json artifacts were found.",
            exact_command=_BLOCKED_COMMAND,
        ))

    for metrics_path in metric_paths:
        _process_run(
            metrics_path, base_dir, acc,
            git_commit=git_commit, timestamp=timestamp,
            scoring_hash=scoring_hash, threshold_hash=threshold_hash, metrics_hash=metrics_hash,
            cfg=cfg,
            data_root=data_root,
        )

    _seen_regime_c: set[tuple[str, int]] = set()
    for metrics_path in metric_paths:
        regime, _, seed, alpha = _parse_metric_path(base_dir, metrics_path)
        if regime != Regime.C or alpha is None or (str(alpha), seed) in _seen_regime_c:
            continue
        _seen_regime_c.add((str(alpha), seed))
        _data_root_c = data_root if data_root is not None else base_dir
        prepared = prepared_root_for_regime(Regime.C, base_dir=_data_root_c, alpha=alpha, seed=seed)
        record = build_regime_c_alpha_audit(prepared, alpha, seed)
        if record is not None:
            acc.regime_c_alpha_records.append(record)
        else:
            acc.warnings.append(WarningRecord(
                severity=AuditSeverity.BLOCKED_PENDING_RUN,
                code=WarningCode.REGIME_C_ALPHA_AUDIT_MISSING.value,
                message=(
                    f"Regime C alpha={alpha_label(alpha)} seed={seed} prepared manifest is "
                    "missing; JS divergence and device-mixture proportions cannot be audited."
                ),
                exact_command=_BLOCKED_COMMAND,
            ))

    acc.regime_c_alpha_records = _enrich_regime_c_records_with_cv(
        acc.regime_c_alpha_records, acc.cell_panel
    )

    severity_trend_records: list[RegimeCSeverityTrendRecord] = compute_regime_c_severity_trend(
        acc.regime_c_alpha_records,
        significance_alpha=float(cfg.statistics.significance_alpha),
    )

    b4_stability_records: list[B4ClusterStabilityRecord] = _b4_stability_from_cluster_records(
        acc.cluster_records
    )

    invariant_results = build_invariant_results(acc.invariant_inputs, acc.score_hashes_by_cell, _CONTROLLED)

    seed_deltas = _build_seed_deltas(acc.cell_panel, acc.warnings)

    _emit_structural_warnings(acc, seed_deltas)
    _emit_worst_client_stability_warnings(acc.worst_client_records, acc.warnings)
    _emit_flat_cv_tpr_warnings(acc.cell_panel, acc.warnings)
    _emit_ciciot_homogeneity_warnings(
        acc.homogeneity_records, acc.warnings,
        homogeneity_threshold=cfg.quality_gates.ciciot_homogeneity_threshold,
    )

    _write_csv(audit_dir / RUN_MANIFEST_CSV, acc.manifest_records)
    _write_csv(audit_dir / FPR_COMPANION_METRICS_CSV, acc.companion_records)
    _write_csv(audit_dir / WORST_CLIENT_TRACKING_CSV, acc.worst_client_records)
    _write_csv(audit_dir / CICIOT_HOMOGENEITY_AUDIT_CSV, acc.homogeneity_records)
    _write_csv(audit_dir / REGIME_C_ALPHA_AUDIT_CSV, acc.regime_c_alpha_records)
    _write_csv(audit_dir / REGIME_C_SEVERITY_TREND_CSV, severity_trend_records)
    _write_csv(audit_dir / B4_CLUSTER_STABILITY_CSV, b4_stability_records)
    _write_csv(audit_dir / SEED_DELTAS_CSV, seed_deltas)
    _write_csv(audit_dir / PER_CLIENT_METRICS_CSV, acc.client_records)
    _write_csv(audit_dir / PER_ATTACK_METRICS_CSV, acc.attack_records)
    _write_csv(audit_dir / THRESHOLD_VALUES_CSV, acc.threshold_records)
    _write_csv(audit_dir / RECONSTRUCTION_ERROR_SUMMARY_CSV, acc.recon_records)
    _write_csv(audit_dir / CLUSTER_ASSIGNMENTS_CSV, acc.cluster_records)
    _write_csv(audit_dir / CONVERGENCE_AUDIT_CSV, acc.convergence_records)
    _write_csv(audit_dir / METRIC_DENOMINATOR_AUDIT_CSV, acc.denominator_records)
    _write_csv(audit_dir / METRIC_RECOMPUTATION_AUDIT_CSV, acc.recomputation_records)
    _write_json(audit_dir / BASELINE_INVARIANTS_JSON, [row.model_dump(mode="json") for row in invariant_results])
    _write_json(audit_dir / DATASET_PARTITION_AUDIT_JSON, {
        "schema_version": AUDIT_SCHEMA_VERSION,
        "partitions": [row.model_dump(mode="json") for row in acc.partition_audits.values()],
    })
    _write_warnings(audit_dir / WARNINGS_MD, acc.warnings)
    _write_summary(audit_dir / AUDIT_SUMMARY_MD, acc.manifest_records, invariant_results, acc.warnings)

    return {
        "baseline_invariants": audit_dir / BASELINE_INVARIANTS_JSON,
        "run_manifest": audit_dir / RUN_MANIFEST_CSV,
        "seed_deltas": audit_dir / SEED_DELTAS_CSV,
        "per_client_metrics": audit_dir / PER_CLIENT_METRICS_CSV,
        "per_attack_metrics": audit_dir / PER_ATTACK_METRICS_CSV,
        "threshold_values": audit_dir / THRESHOLD_VALUES_CSV,
        "reconstruction_error_summary": audit_dir / RECONSTRUCTION_ERROR_SUMMARY_CSV,
        "cluster_assignments": audit_dir / CLUSTER_ASSIGNMENTS_CSV,
        "dataset_partition_audit": audit_dir / DATASET_PARTITION_AUDIT_JSON,
        "convergence_audit": audit_dir / CONVERGENCE_AUDIT_CSV,
        "metric_denominator_audit": audit_dir / METRIC_DENOMINATOR_AUDIT_CSV,
        "metric_recomputation_audit": audit_dir / METRIC_RECOMPUTATION_AUDIT_CSV,
        "fpr_companion_metrics": audit_dir / FPR_COMPANION_METRICS_CSV,
        "worst_client_tracking": audit_dir / WORST_CLIENT_TRACKING_CSV,
        "regime_c_alpha_audit": audit_dir / REGIME_C_ALPHA_AUDIT_CSV,
        "regime_c_severity_trend": audit_dir / REGIME_C_SEVERITY_TREND_CSV,
        "b4_cluster_stability": audit_dir / B4_CLUSTER_STABILITY_CSV,
        "warnings": audit_dir / WARNINGS_MD,
        "audit_summary": audit_dir / AUDIT_SUMMARY_MD,
    }


def _write_warnings(path: Path, warnings: list[WarningRecord]) -> None:
    lines = ["# DATP Results Audit Warnings", ""]
    if not warnings:
        lines.append("No warnings.")
    for warning in warnings:
        lines.append(f"- **{warning.severity} `{warning.code}`**: {warning.message}")
        if warning.exact_command:
            lines.append(f"  Command: `{warning.exact_command}`")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_summary(
    path: Path,
    manifest_records: list[RunManifestRecord],
    invariant_results: list[BaselineInvariantResult],
    warnings: list[WarningRecord],
) -> None:
    pass_count = sum(row.status == AuditStatus.PASS for row in invariant_results)
    blocked_count = sum(row.status == AuditStatus.BLOCKED_PENDING_RUN for row in invariant_results)
    fail_count = sum(row.status == AuditStatus.FAIL for row in invariant_results)
    lines = [
        "# DATP Results Audit Summary",
        "",
        f"- Completed runs audited: {len(manifest_records)}",
        f"- B1-B4 invariant PASS cells: {pass_count}",
        f"- B1-B4 invariant BLOCKED_PENDING_RUN cells: {blocked_count}",
        f"- B1-B4 invariant FAIL cells: {fail_count}",
        f"- Warning records: {len(warnings)}",
        "",
        "B0 is a centralized reference comparator; B1\u2013B4 share the trained encoder and scores. Threshold attribution claims are valid only after the B1\u2013B4 invariant passes for the same (regime, seed, alpha) cell.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
