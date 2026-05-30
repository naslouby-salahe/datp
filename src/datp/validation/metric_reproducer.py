"""Per-cell metric reproduction: recompute B1/B2/B3/B4 from stored scores and compare to stored metrics.json.

Reuses canonical threshold computation (``baselines.common.thresholds.derive_threshold``),
canonical metric computation (``evaluation.metrics``), and canonical score loading
(``evaluation.score_loading``). Does not retrain, re-score, or modify any formula.
"""

from __future__ import annotations

import enum
import json
import math
from pathlib import Path
from typing import Any, Mapping

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from datp.artifacts.layout import ArtifactLayout
from datp.artifacts.names import PathToken, ArtifactDir, ArtifactFile
from datp.validation.constants import (
    COVERAGE_RATIO_TOLERANCE,
    RECOMPUTED_METRICS_INDEX_JSON,
    RECOMPUTED_METRICS_JSON,
    SCALAR_METRIC_TOLERANCE,
)
from datp.validation.discovery import ScoreCellLocation, iter_score_cells
from datp.validation.writers import write_json
from datp.thresholding.thresholds import derive_threshold
from datp.core.types import ThresholdResult
from datp.config.compose import compose_config
from datp.config.models import DatpConfig
from datp.validation.enums import AuditStatus
from datp.validation.schemas import ValidationCheck
from datp.core.identity import BaselineRunId, ScoreCellId, TrainingCellId, parse_alpha_dir
from datp.core.enums import (
    Baseline,
    Regime,
    ScoringStage,
    controlled_baselines_for_regime,
)
from datp.core.errors import fmt
from datp.core.enums import ConfusionKey, MetricName
from datp.evaluation.metrics import (
    EvaluationResult,
    evaluate_baseline,
)
from datp.scoring.loading import ScoreProvider

_MODULE = "audit.metric_reproducer"

_SCALAR_METRIC_FIELDS: tuple[str, ...] = (
    MetricName.CV_FPR,
    MetricName.CV_TPR,
    MetricName.MEAN_FPR,
    MetricName.STD_FPR,
    MetricName.IQR_FPR,
    MetricName.IQR_TPR,
    "max_min_fpr_gap",
    MetricName.WORST_CLIENT_FPR,
    MetricName.WORST_BA,
    MetricName.P10_MACRO_F1,
    "tau_global",
)

_CONFUSION_KEYS: tuple[str, ...] = tuple(ConfusionKey)


class MetricCheckCode(enum.StrEnum):
    SCALAR_WITHIN_TOLERANCE = "scalar_within_tolerance"
    COVERAGE_RATIO_WITHIN_TOLERANCE = "coverage_ratio_within_tolerance"
    ELIGIBLE_COUNT_EXACT = "eligible_count_exact"
    PENDING_COUNT_EXACT = "pending_count_exact"
    ELIGIBLE_IDS_EXACT = "eligible_ids_exact"
    PENDING_IDS_EXACT = "pending_ids_exact"
    CLIENT_COUNT_EXACT = "client_count_exact"
    PER_CLIENT_CONFUSION_EXACT = "per_client_confusion_exact"
    PER_CLIENT_THRESHOLDS_WITHIN_TOLERANCE = "per_client_thresholds_within_tolerance"


def _format_check_detail(
    field: str = "",
    expected: Any = None,
    actual: Any = None,
    abs_diff: float | None = None,
    tolerance: float | None = None,
    detail: str = "",
) -> str:
    parts = []
    if field:
        parts.append(f"field={field}")
    if expected is not None:
        parts.append(f"expected={expected}")
    if actual is not None:
        parts.append(f"actual={actual}")
    if abs_diff is not None:
        parts.append(f"diff={abs_diff:.4g}")
    if tolerance is not None:
        parts.append(f"tol={tolerance:.4g}")
    if detail:
        parts.append(detail)
    return ", ".join(parts)


class BaselineReproductionResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    baseline: Baseline
    status: AuditStatus
    metrics_path: str
    recomputed: dict[str, Any]
    stored: dict[str, Any]
    checks: list[ValidationCheck]


class CellReproductionResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, arbitrary_types_allowed=True)
    cell: ScoreCellId
    overall_status: AuditStatus
    baselines: list[BaselineReproductionResult]
    missing_baselines: list[Baseline] = Field(default_factory=list)


def _abs_diff(expected: float | None, actual: float | None) -> float | None:
    if expected is None or actual is None:
        return None
    if (isinstance(expected, float) and math.isnan(expected)) or (
        isinstance(actual, float) and math.isnan(actual)
    ):
        return None
    return abs(float(expected) - float(actual))


def _scalar_check(
    field: str,
    expected: float | None,
    actual: float | None,
    tolerance: float,
    code: MetricCheckCode = MetricCheckCode.SCALAR_WITHIN_TOLERANCE,
) -> ValidationCheck:
    both_nan = (
        expected is not None
        and actual is not None
        and isinstance(expected, float)
        and isinstance(actual, float)
        and math.isnan(expected)
        and math.isnan(actual)
    )
    if both_nan:
        return ValidationCheck(
            code=code,
            status=AuditStatus.PASS,
            detail=_format_check_detail(
                field=field,
                expected=expected,
                actual=actual,
                abs_diff=0.0,
                tolerance=tolerance,
            ),
        )
    if expected is None or actual is None:
        return ValidationCheck(
            code=code,
            status=AuditStatus.MISSING,
            detail=_format_check_detail(
                field=field,
                expected=expected,
                actual=actual,
                tolerance=tolerance,
                detail="expected or actual is None",
            ),
        )
    diff = _abs_diff(expected, actual)
    if diff is None:
        return ValidationCheck(
            code=code,
            status=AuditStatus.MISSING,
            detail=_format_check_detail(
                field=field,
                expected=expected,
                actual=actual,
                tolerance=tolerance,
                detail="NaN encountered on only one side",
            ),
        )
    status = AuditStatus.PASS if diff <= tolerance else AuditStatus.FAIL
    return ValidationCheck(
        code=code,
        status=status,
        detail=_format_check_detail(
            field=field,
            expected=expected,
            actual=actual,
            abs_diff=diff,
            tolerance=tolerance,
        ),
    )


def _exact_match_check(
    code: MetricCheckCode,
    field: str,
    expected: Any,
    actual: Any,
) -> ValidationCheck:
    if expected == actual:
        return ValidationCheck(
            code=code,
            status=AuditStatus.PASS,
            detail=_format_check_detail(field=field, expected=expected, actual=actual),
        )
    return ValidationCheck(
        code=code,
        status=AuditStatus.FAIL,
        detail=_format_check_detail(
            field=field,
            expected=expected,
            actual=actual,
            detail=f"expected={expected!r}, actual={actual!r}",
        ),
    )


def _id_set_check(
    code: MetricCheckCode,
    field: str,
    expected: list[str],
    actual: list[str],
) -> ValidationCheck:
    expected_set = set(expected)
    actual_set = set(actual)
    if expected_set == actual_set:
        return ValidationCheck(
            code=code,
            status=AuditStatus.PASS,
            detail=_format_check_detail(
                field=field, expected=sorted(expected_set), actual=sorted(actual_set)
            ),
        )
    return ValidationCheck(
        code=code,
        status=AuditStatus.FAIL,
        detail=_format_check_detail(
            field=field,
            expected=sorted(expected_set),
            actual=sorted(actual_set),
            detail=(
                f"only_in_expected={sorted(expected_set - actual_set)}, "
                f"only_in_actual={sorted(actual_set - expected_set)}"
            ),
        ),
    )


def _confusion_check(
    expected_per_client: Mapping[str, Mapping[str, int]],
    actual_per_client: Mapping[str, Mapping[str, int]],
) -> ValidationCheck:
    diffs: list[str] = []
    common = sorted(set(expected_per_client) & set(actual_per_client))
    for cid in common:
        for key in _CONFUSION_KEYS:
            exp = int(expected_per_client[cid][key])
            act = int(actual_per_client[cid][key])
            if exp != act:
                diffs.append(f"{cid}.{key}: expected={exp}, actual={act}")
    if diffs:
        return ValidationCheck(
            code=MetricCheckCode.PER_CLIENT_CONFUSION_EXACT,
            status=AuditStatus.FAIL,
            detail=_format_check_detail(
                field="per_client.confusion_matrix",
                detail=f"{len(diffs)} mismatches; first: {diffs[0]}",
            ),
        )
    return ValidationCheck(
        code=MetricCheckCode.PER_CLIENT_CONFUSION_EXACT,
        status=AuditStatus.PASS,
        detail=_format_check_detail(field="per_client.confusion_matrix"),
    )


def _thresholds_check(
    expected_per_client: dict[str, float],
    actual_per_client: dict[str, float],
    tolerance: float,
) -> ValidationCheck:
    diffs: list[tuple[str, float, float, float]] = []
    for cid in sorted(set(expected_per_client) & set(actual_per_client)):
        exp = float(expected_per_client[cid])
        act = float(actual_per_client[cid])
        diff = abs(exp - act)
        if diff > tolerance:
            diffs.append((cid, exp, act, diff))
    if diffs:
        cid, exp, act, diff = diffs[0]
        return ValidationCheck(
            code=MetricCheckCode.PER_CLIENT_THRESHOLDS_WITHIN_TOLERANCE,
            status=AuditStatus.FAIL,
            detail=_format_check_detail(
                field="per_client.threshold_value",
                tolerance=tolerance,
                detail=f"{len(diffs)} threshold mismatches; first: {cid} expected={exp}, actual={act}, diff={diff}",
            ),
        )
    return ValidationCheck(
        code=MetricCheckCode.PER_CLIENT_THRESHOLDS_WITHIN_TOLERANCE,
        status=AuditStatus.PASS,
        detail=_format_check_detail(
            field="per_client.threshold_value", tolerance=tolerance
        ),
    )


def _overall_status(checks: list[ValidationCheck]) -> AuditStatus:
    statuses = {c.status for c in checks}
    if AuditStatus.FAIL in statuses:
        return AuditStatus.FAIL
    if AuditStatus.MISSING in statuses:
        return AuditStatus.PARTIAL
    return AuditStatus.PASS


def _read_metrics_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _normalize_per_client(stored: dict[str, Any]) -> list[dict[str, Any]]:
    per_client = stored["per_client"]
    if isinstance(per_client, dict):
        return [
            dict(values, client_id=client_id)
            for client_id, values in per_client.items()
        ]
    return list(per_client)


def _load_cal_errors(score_root: Path) -> dict[str, np.ndarray]:
    from datp.scoring.loading import read_score_column  # noqa: PLC0415

    cal_dir = score_root / ScoringStage.CAL.value
    if not cal_dir.is_dir():
        raise FileNotFoundError(
            fmt(
                _MODULE,
                f"Calibration score directory missing at {cal_dir}",
                "cal/ directory present",
                "absent",
            )
        )
    errors: dict[str, np.ndarray] = {}
    for parquet in sorted(cal_dir.glob(PathToken.PARQUET_GLOB)):
        errors[parquet.stem] = read_score_column(parquet)
    if not errors:
        raise FileNotFoundError(
            fmt(
                _MODULE,
                f"No calibration parquet files at {cal_dir}",
                "at least one .parquet",
                "none",
            )
        )
    return errors


def _evaluate(
    threshold_result: ThresholdResult,
    score_provider: ScoreProvider,
    regime: Regime,
    seed: int,
    alpha: float | None,
) -> tuple[EvaluationResult, dict[str, float]]:
    evaluation = evaluate_baseline(
        threshold_result.client_thresholds,
        Path(""),
        regime,
        seed,
        alpha,
        score_provider=score_provider,
    )
    client_thresholds = {ct.client_id: float(ct.threshold) for ct in threshold_result.client_thresholds}
    return evaluation, client_thresholds


def _compute_b1_tau_global(
    cal_errors: dict[str, np.ndarray],
    cfg: DatpConfig,
    regime: Regime,
) -> float:
    b1_result = derive_threshold(
        Baseline.B1,
        cal_errors,
        n_min=cfg.threshold.n_min,
        q=cfg.threshold.q,
        tau_global=0.0,
        regime=regime,
        threshold_cfg=cfg.threshold,
    )
    return float(b1_result.tau_global)


def _stored_per_client_map(stored: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["client_id"]: row for row in _normalize_per_client(stored)}


def _stored_scalar(stored: dict[str, Any], field: str) -> Any:
    """Read a scalar metric from top-level keys, falling back to ``aggregate_metrics``.

    Some legacy fields (e.g. ``max_min_fpr_gap``) live only inside ``aggregate_metrics``.
    """
    if stored.get(field) is not None:
        return stored[field]
    aggregate = stored.get("aggregate_metrics") or {}
    return aggregate.get(field)


def _build_baseline_checks(
    *,
    stored: dict[str, Any],
    evaluation: EvaluationResult,
    threshold_result: ThresholdResult,
    client_thresholds_actual: dict[str, float],
) -> list[ValidationCheck]:
    checks: list[ValidationCheck] = []

    actual_scalars = {
        MetricName.CV_FPR: evaluation.cv_fpr,
        MetricName.CV_TPR: evaluation.cv_tpr,
        MetricName.MEAN_FPR: evaluation.mean_fpr,
        MetricName.STD_FPR: evaluation.std_fpr,
        MetricName.IQR_FPR: evaluation.iqr_fpr,
        MetricName.IQR_TPR: evaluation.iqr_tpr,
        "max_min_fpr_gap": evaluation.max_min_fpr_gap,
        MetricName.WORST_CLIENT_FPR: evaluation.worst_client_fpr,
        MetricName.WORST_BA: evaluation.worst_ba,
        MetricName.P10_MACRO_F1: evaluation.p10_macro_f1,
        "tau_global": float(threshold_result.tau_global),
    }
    for field in _SCALAR_METRIC_FIELDS:
        checks.append(
            _scalar_check(
                field=field,
                expected=_stored_scalar(stored, field),
                actual=actual_scalars[field],
                tolerance=SCALAR_METRIC_TOLERANCE,
            )
        )

    checks.append(
        _scalar_check(
            field="coverage_ratio",
            expected=_stored_scalar(stored, "coverage_ratio"),
            actual=evaluation.coverage_ratio,
            tolerance=COVERAGE_RATIO_TOLERANCE,
            code=MetricCheckCode.COVERAGE_RATIO_WITHIN_TOLERANCE,
        )
    )

    checks.append(
        _exact_match_check(
            MetricCheckCode.ELIGIBLE_COUNT_EXACT,
            "eligible_count",
            int(stored["eligible_count"]),
            int(evaluation.eligible_count),
        )
    )
    checks.append(
        _exact_match_check(
            MetricCheckCode.PENDING_COUNT_EXACT,
            "pending_count",
            int(stored["pending_count"]),
            int(len(evaluation.pending_ids)),
        )
    )
    checks.append(
        _exact_match_check(
            MetricCheckCode.CLIENT_COUNT_EXACT,
            "client_count",
            int(stored["client_count"]),
            int(evaluation.client_count),
        )
    )
    checks.append(
        _id_set_check(
            MetricCheckCode.ELIGIBLE_IDS_EXACT,
            "eligible_ids",
            list(map(str, stored["eligible_ids"])),
            list(map(str, evaluation.eligible_ids)),
        )
    )
    checks.append(
        _id_set_check(
            MetricCheckCode.PENDING_IDS_EXACT,
            "pending_ids",
            list(map(str, stored["pending_ids"])),
            list(map(str, evaluation.pending_ids)),
        )
    )

    stored_per_client = _stored_per_client_map(stored)
    actual_per_client = {cr.client_id: cr for cr in evaluation.clients}

    expected_confusion = {
        cid: {k: int(row["confusion_matrix"][k]) for k in _CONFUSION_KEYS}
        for cid, row in stored_per_client.items()
        if "confusion_matrix" in row
    }
    actual_confusion = {
        cid: {
            ConfusionKey.TP.value: cr.confusion.tp,
            ConfusionKey.FP.value: cr.confusion.fp,
            ConfusionKey.TN.value: cr.confusion.tn,
            ConfusionKey.FN.value: cr.confusion.fn,
        }
        for cid, cr in actual_per_client.items()
    }
    checks.append(_confusion_check(expected_confusion, actual_confusion))

    expected_thresholds = {
        cid: float(row["threshold_value"])
        for cid, row in stored_per_client.items()
        if row.get("threshold_value") is not None
    }
    checks.append(
        _thresholds_check(
            expected_thresholds,
            client_thresholds_actual,
            SCALAR_METRIC_TOLERANCE,
        )
    )

    return checks


def _serialize_recomputed(
    evaluation: EvaluationResult,
    threshold_result: ThresholdResult,
    client_thresholds: dict[str, float],
) -> dict[str, Any]:
    return {
        "baseline": evaluation.baseline.value,
        "regime": evaluation.regime.value,
        "seed": evaluation.seed,
        "alpha": evaluation.alpha,
        "dataset": evaluation.dataset,
        "tau_global": float(threshold_result.tau_global),
        "coverage_ratio": evaluation.coverage_ratio,
        MetricName.CV_FPR: evaluation.cv_fpr,
        MetricName.CV_TPR: evaluation.cv_tpr,
        MetricName.MEAN_FPR: evaluation.mean_fpr,
        MetricName.STD_FPR: evaluation.std_fpr,
        MetricName.IQR_FPR: evaluation.iqr_fpr,
        MetricName.IQR_TPR: evaluation.iqr_tpr,
        "max_min_fpr_gap": evaluation.max_min_fpr_gap,
        MetricName.WORST_CLIENT_FPR: evaluation.worst_client_fpr,
        "worst_client_id": evaluation.worst_client_id,
        MetricName.WORST_BA: evaluation.worst_ba,
        MetricName.P10_MACRO_F1: evaluation.p10_macro_f1,
        "client_count": evaluation.client_count,
        "eligible_count": evaluation.eligible_count,
        "pending_count": len(evaluation.pending_ids),
        "eligible_ids": sorted(evaluation.eligible_ids),
        "pending_ids": sorted(evaluation.pending_ids),
        "per_client": {
            cr.client_id: {
                "fpr": cr.metrics.fpr,
                "tpr": cr.metrics.tpr,
                "balanced_accuracy": cr.metrics.balanced_accuracy,
                "macro_f1": cr.metrics.macro_f1,
                "n_benign": cr.n_benign,
                "n_attack": cr.n_attack,
                "confusion_matrix": {
                    ConfusionKey.TP.value: cr.confusion.tp,
                    ConfusionKey.FP.value: cr.confusion.fp,
                    ConfusionKey.TN.value: cr.confusion.tn,
                    ConfusionKey.FN.value: cr.confusion.fn,
                },
                "threshold_value": client_thresholds[cr.client_id],
            }
            for cr in evaluation.clients
        },
    }


def _select_stored_summary(stored: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "baseline",
        "regime",
        "seed",
        "alpha",
        "dataset",
        "tau_global",
        "coverage_ratio",
        MetricName.CV_FPR,
        MetricName.CV_TPR,
        MetricName.MEAN_FPR,
        MetricName.STD_FPR,
        MetricName.IQR_FPR,
        MetricName.IQR_TPR,
        "max_min_fpr_gap",
        MetricName.WORST_CLIENT_FPR,
        "worst_client_id",
        MetricName.WORST_BA,
        MetricName.P10_MACRO_F1,
        "client_count",
        "eligible_count",
        "pending_count",
        "eligible_ids",
        "pending_ids",
    )
    return {k: stored.get(k) for k in keys}


def reproduce_cell_metrics(
    cell_dir: Path,
    base_dir: Path,
    *,
    config: DatpConfig | None = None,
) -> CellReproductionResult:
    """Reproduce metrics for every baseline result that exists for the given score cell.

    ``cell_dir`` is the score cell directory ``<base_dir>/scores/<regime>/seed_N[/alpha_*]/``.
    ``base_dir`` is the experiment root (containing ``scores/`` and ``results/``).
    ``config`` overrides the composed runtime config (used in tests). When None, the canonical
    config is composed via Hydra using the cell's regime/seed/alpha.

    Raises FileNotFoundError when no baseline metrics.json exist for the cell.
    """
    cell_dir = cell_dir.resolve()
    base_dir = base_dir.resolve()
    location = _parse_cell_location(base_dir, cell_dir)
    regime = location.regime
    seed = location.seed
    alpha = location.alpha

    layout = ArtifactLayout(base_dir=base_dir, regime=regime)
    cell = TrainingCellId(regime=regime, seed=seed, alpha=alpha)
    score_root = layout.score_cell(ScoreCellId(cell=cell)).score_dir
    cal_errors = _load_cal_errors(score_root)
    score_provider = ScoreProvider(score_root)

    cfg = config or compose_config(
        regime=regime,
        baseline=Baseline.B1,
        seed=seed,
        alpha=alpha,
    )
    tau_global_b1 = _compute_b1_tau_global(cal_errors, cfg, regime)

    baseline_results: list[BaselineReproductionResult] = []
    missing_baselines: list[Baseline] = []
    candidate_baselines = controlled_baselines_for_regime(regime)

    for baseline in candidate_baselines:
        run = BaselineRunId(cell=cell, baseline=baseline)
        metrics_path = (
            layout.baseline_run(run).result_dir / ArtifactFile.METRICS
        )
        if not metrics_path.exists():
            missing_baselines.append(baseline)
            continue
        stored = _read_metrics_json(metrics_path)
        threshold_result = derive_threshold(
            baseline,
            cal_errors,
            n_min=cfg.threshold.n_min,
            q=cfg.threshold.q,
            tau_global=tau_global_b1,
            regime=regime,
            threshold_cfg=cfg.threshold,
        )
        evaluation, client_thresholds = _evaluate(
            threshold_result,
            score_provider,
            regime,
            seed,
            alpha,
        )
        checks = _build_baseline_checks(
            stored=stored,
            evaluation=evaluation,
            threshold_result=threshold_result,
            client_thresholds_actual=client_thresholds,
        )
        baseline_results.append(
            BaselineReproductionResult(
                baseline=baseline,
                status=_overall_status(checks),
                metrics_path=str(metrics_path),
                recomputed=_serialize_recomputed(
                    evaluation, threshold_result, client_thresholds
                ),
                stored=_select_stored_summary(stored),
                checks=checks,
            )
        )

    overall = _aggregate_overall(
        [br.status for br in baseline_results], missing_baselines
    )
    return CellReproductionResult(
        cell=ScoreCellId(cell=TrainingCellId(regime=regime, seed=seed, alpha=alpha)),
        overall_status=overall,
        baselines=baseline_results,
        missing_baselines=missing_baselines,
    )


def _aggregate_overall(
    statuses: list[AuditStatus],
    missing_baselines: list[Baseline],
) -> AuditStatus:
    if AuditStatus.FAIL in statuses:
        return AuditStatus.FAIL
    if (
        missing_baselines
        or AuditStatus.MISSING in statuses
        or AuditStatus.PARTIAL in statuses
    ):
        return AuditStatus.PARTIAL
    if not statuses:
        return AuditStatus.MISSING
    return AuditStatus.PASS


def _parse_cell_location(base_dir: Path, cell_dir: Path) -> ScoreCellLocation:
    rel = cell_dir.relative_to(base_dir / ArtifactDir.SCORES)
    parts = rel.parts
    regime = Regime(parts[0])
    if not parts[1].startswith(PathToken.SEED_PREFIX):
        raise ValueError(
            fmt(
                _MODULE,
                "Expected seed segment",
                f"prefix {PathToken.SEED_PREFIX!r}",
                repr(parts[1]),
            )
        )
    seed = int(parts[1].removeprefix(PathToken.SEED_PREFIX))
    alpha = parse_alpha_dir(parts[2]) if len(parts) > 2 else None
    return ScoreCellLocation(regime=regime, seed=seed, alpha=alpha, cell_dir=cell_dir)


def reproduce_all_cells(
    base_dir: Path,
    *,
    config: DatpConfig | None = None,
    write_reports: bool = False,
) -> list[CellReproductionResult]:
    """Reproduce metrics for every discoverable score cell under ``base_dir/scores/``."""
    base_dir = base_dir.resolve()
    results: list[CellReproductionResult] = []
    for location in iter_score_cells(base_dir):
        result = reproduce_cell_metrics(location.cell_dir, base_dir, config=config)
        results.append(result)
        if write_reports:
            write_json(
                location.cell_dir / RECOMPUTED_METRICS_JSON,
                result.model_dump(mode="json"),
            )
    if write_reports:
        write_json(
            base_dir / ArtifactDir.SCORES / RECOMPUTED_METRICS_INDEX_JSON,
            {"cells": [r.model_dump(mode="json") for r in results]},
        )
    return results
