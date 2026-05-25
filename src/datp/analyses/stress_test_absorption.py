# SPDX-License-Identifier: Proprietary
"""GE-03/GE-04/GE-05 Stress-Test Threshold Grid and Absorption Reporting.

Applies B1/B2/B4 thresholds to stress-test scores (FedProx, FedRep-AE).
Computes absorption ratios and classifies retention per PRE_CODING_PLAN §6.4.

Reads scores — never retrains.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import NamedTuple

import numpy as np

from pydantic import BaseModel, ConfigDict

from datp.analyses._common import load_cal_errors
from datp.baselines.common.thresholds import derive_threshold
from datp.baselines.common.types import ThresholdResult
from datp.config.models import ThresholdConfig
from datp.core.enums import (
    AbsorptionClass,
    Baseline,
    Regime,
    ScoringStage,
    classify_absorption,
)
from datp.evaluation.metrics import (
    ClientMetrics,
    compute_client_metrics,
)
from datp.evaluation.score_loading import ScoreProvider
from datp.statistics.cv import cv as compute_cv_statistic

_MODULE = "analyses.stress_test_absorption"

# ── Output filenames ──────────────────────────────────────────────────────
ABSORPTION_TABLE_CSV = "stress_test_absorption.csv"
ABSORPTION_TABLE_JSON = "stress_test_absorption.json"

_CV_DDOF = 1


class CvFprResult(NamedTuple):
    """Result of _compute_cv_fpr."""

    cv_fpr: float
    mean_fpr: float
    eligible_count: int
    client_count: int
    coverage: float


class BaselineCvStats(NamedTuple):
    cv_fpr: float
    mean_fpr: float
    eligible_count: int
    client_count: int
    coverage: float


class AbsorptionDetails(NamedTuple):
    ratio: float | None
    category: AbsorptionClass | None
    delta_stress: float | None
    delta_fedavg: float | None


class FedAvgReference(NamedTuple):
    cv_fpr_b1: float | None
    cv_fpr_b2: float | None


class AbsorptionRowInputs(NamedTuple):
    stats: BaselineCvStats
    details: AbsorptionDetails
    fedavg: FedAvgReference


class StressTestKind:
    """Stress-test variant labels — never added to Baseline enum."""

    FEDPROX = "fedprox"
    FEDREP = "fedrep"


class StressTestCell(NamedTuple):
    """Identifies a stress-test score directory."""

    kind: str
    mu: float | None
    seed: int
    score_dir: Path


class StressEvaluationContext(NamedTuple):
    cell: StressTestCell
    threshold_cfg: ThresholdConfig
    regime: Regime
    score_provider: ScoreProvider
    client_cal_errors: dict[str, np.ndarray]
    client_ids: list[str]


class AbsorptionRow(BaseModel):
    """One row in the stress-test × threshold absorption table."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    stress_test: str
    mu: float | None
    seed: int
    regime: Regime
    threshold_baseline: Baseline
    cv_fpr: float
    mean_fpr: float
    eligible_count: int
    client_count: int
    coverage_ratio: float
    absorption_ratio: float | None
    absorption_class: AbsorptionClass | None
    cv_fpr_fedavg_b1: float | None
    cv_fpr_fedavg_b2: float | None
    delta_stress: float | None
    delta_fedavg: float | None


class AbsorptionTable(BaseModel):
    """Full absorption analysis result."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    rows: list[AbsorptionRow]
    n_stress_tests: int
    n_seeds: int
    n_thresholds: int


# ── Threshold application ─────────────────────────────────────────────────


def _derive_threshold_for_stress(
    baseline: Baseline,
    client_cal_errors: dict[str, np.ndarray],
    threshold_cfg: ThresholdConfig,
    regime: Regime,
) -> ThresholdResult:
    """Apply canonical threshold derivation to stress-test calibration errors.

    Returns a ThresholdResult keyed by client_id.
    """
    # Compute tau_global: pooled percentile over all cal errors.
    all_errors = np.concatenate(list(client_cal_errors.values()))
    tau_global = float(np.percentile(all_errors, threshold_cfg.q * 100))

    result = derive_threshold(
        baseline=baseline,
        client_errors=client_cal_errors,
        n_min=threshold_cfg.n_min,
        q=threshold_cfg.q,
        tau_global=tau_global,
        regime=regime,
        threshold_cfg=threshold_cfg,
    )
    return result


def _compute_cv_fpr(
    client_metrics: list[ClientMetrics],
    eligible_ids: list[str],
) -> CvFprResult:
    """Compute CV(FPR) and companion stats from eligible-client metrics."""
    eligible_set = set(eligible_ids)
    fprs = [
        cm.fpr
        for cm in client_metrics
        if cm.client_id in eligible_set and not np.isnan(cm.fpr)
    ]
    if not fprs:
        return CvFprResult(
            cv_fpr=0.0,
            mean_fpr=float("nan"),
            eligible_count=0,
            client_count=len(client_metrics),
            coverage=0.0,
        )

    fpr_arr = np.array(fprs, dtype=np.float64)
    cv_val = compute_cv_statistic(fpr_arr, ddof=_CV_DDOF)
    mean_val = float(fpr_arr.mean())
    n_eligible = len(fprs)
    n_total = len(client_metrics)
    coverage = n_eligible / n_total if n_total > 0 else 0.0
    return CvFprResult(
        cv_fpr=float(cv_val) if not np.isnan(cv_val) else 0.0,
        mean_fpr=mean_val,
        eligible_count=n_eligible,
        client_count=n_total,
        coverage=coverage,
    )


# ── Absorption ratio computation ──────────────────────────────────────────


def compute_absorption_ratio(
    delta_stress: float,
    delta_fedavg: float,
) -> tuple[float | None, AbsorptionClass | None]:
    """Compute absorption ratio = Δ_stress / Δ_FedAvg and classify.

    Returns (None, None) when Δ_FedAvg is zero or negative
    (B1→B2 gain not present in FedAvg — absorption undefined).
    """
    if delta_fedavg <= 0:
        return None, None
    ratio = delta_stress / delta_fedavg
    return ratio, classify_absorption(ratio)


def _evaluate_threshold_baseline(
    baseline: Baseline,
    context: StressEvaluationContext,
) -> BaselineCvStats:
    threshold_result = _derive_threshold_for_stress(
        baseline, context.client_cal_errors, context.threshold_cfg, context.regime
    )
    thresholds = {
        ct.client_id: float(ct.threshold) for ct in threshold_result.client_thresholds
    }
    eligible_ids = [
        ct.client_id
        for ct in threshold_result.client_thresholds
        if not ct.calibration_pending
    ]
    metrics = [
        compute_client_metrics(
            cid,
            context.score_provider.load(cid, _TEST_BENIGN_STAGE),
            context.score_provider.load(cid, _TEST_ATTACK_STAGE),
            thresholds[cid],
        )
        for cid in context.client_ids
    ]
    result = _compute_cv_fpr(metrics, eligible_ids)
    return BaselineCvStats(*result)


def _absorption_row(
    *,
    context: StressEvaluationContext,
    baseline: Baseline,
    inputs: AbsorptionRowInputs,
) -> AbsorptionRow:
    return AbsorptionRow(
        stress_test=context.cell.kind,
        mu=context.cell.mu,
        seed=context.cell.seed,
        regime=context.regime,
        threshold_baseline=baseline,
        cv_fpr=inputs.stats.cv_fpr,
        mean_fpr=inputs.stats.mean_fpr,
        eligible_count=inputs.stats.eligible_count,
        client_count=inputs.stats.client_count,
        coverage_ratio=inputs.stats.coverage,
        absorption_ratio=inputs.details.ratio,
        absorption_class=inputs.details.category,
        cv_fpr_fedavg_b1=inputs.fedavg.cv_fpr_b1,
        cv_fpr_fedavg_b2=inputs.fedavg.cv_fpr_b2,
        delta_stress=inputs.details.delta_stress,
        delta_fedavg=inputs.details.delta_fedavg,
    )


def _compute_absorption_details(
    stats_by_baseline: dict[Baseline, BaselineCvStats],
    fedavg: FedAvgReference,
) -> AbsorptionDetails:
    delta_stress = (
        stats_by_baseline[Baseline.B1].cv_fpr - stats_by_baseline[Baseline.B2].cv_fpr
    )
    if fedavg.cv_fpr_b1 is None or fedavg.cv_fpr_b2 is None:
        return AbsorptionDetails(None, None, delta_stress, None)

    delta_fedavg = fedavg.cv_fpr_b1 - fedavg.cv_fpr_b2
    if delta_fedavg <= 0:
        return AbsorptionDetails(None, None, delta_stress, delta_fedavg)

    ratio, category = compute_absorption_ratio(delta_stress, delta_fedavg)
    return AbsorptionDetails(ratio, category, delta_stress, delta_fedavg)


def _build_absorption_rows(
    stats_by_baseline: dict[Baseline, BaselineCvStats],
    context: StressEvaluationContext,
    details: AbsorptionDetails,
    fedavg: FedAvgReference,
) -> list[AbsorptionRow]:
    reference_details = AbsorptionDetails(None, None, None, None)
    empty_fedavg = FedAvgReference(None, None)
    return [
        _absorption_row(
            context=context,
            baseline=Baseline.B1,
            inputs=AbsorptionRowInputs(stats_by_baseline[Baseline.B1], details, fedavg),
        ),
        _absorption_row(
            context=context,
            baseline=Baseline.B2,
            inputs=AbsorptionRowInputs(stats_by_baseline[Baseline.B2], details, fedavg),
        ),
        _absorption_row(
            context=context,
            baseline=Baseline.B4,
            inputs=AbsorptionRowInputs(
                stats_by_baseline[Baseline.B4],
                reference_details,
                empty_fedavg,
            ),
        ),
    ]


# ── Main evaluation ───────────────────────────────────────────────────────


def evaluate_stress_test_cell(
    cell: StressTestCell,
    threshold_cfg: ThresholdConfig,
    regime: Regime,
    *,
    fedavg_cv_fpr_b1: float | None = None,
    fedavg_cv_fpr_b2: float | None = None,
) -> list[AbsorptionRow]:
    """Evaluate one stress-test cell across B1/B2/B4 thresholds.

    Returns one AbsorptionRow per (threshold_baseline) combination.
    Absorption ratio is computed for B1 and B2 only (B4 is for reference).
    """
    score_provider = ScoreProvider(cell.score_dir)
    client_cal_errors = load_cal_errors(cell.score_dir)
    client_ids = sorted(client_cal_errors.keys())

    if not client_ids:
        return []

    context = StressEvaluationContext(
        cell=cell,
        threshold_cfg=threshold_cfg,
        regime=regime,
        score_provider=score_provider,
        client_cal_errors=client_cal_errors,
        client_ids=client_ids,
    )
    stats_by_baseline = {
        baseline: _evaluate_threshold_baseline(baseline, context)
        for baseline in (Baseline.B1, Baseline.B2, Baseline.B4)
    }
    fedavg = FedAvgReference(fedavg_cv_fpr_b1, fedavg_cv_fpr_b2)
    details = _compute_absorption_details(stats_by_baseline, fedavg)
    return _build_absorption_rows(stats_by_baseline, context, details, fedavg)


# ── Scoring stage constants ───────────────────────────────────────────────
_TEST_BENIGN_STAGE = ScoringStage.TEST_BENIGN
_TEST_ATTACK_STAGE = ScoringStage.TEST_ATTACK


# ── Table export ──────────────────────────────────────────────────────────


def write_absorption_table(
    table: AbsorptionTable,
    output_dir: Path,
) -> None:
    """Write absorption table as CSV and JSON."""
    output_dir.mkdir(parents=True, exist_ok=True)

    csv_path = output_dir / ABSORPTION_TABLE_CSV
    with csv_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "stress_test",
                "mu",
                "seed",
                "regime",
                "threshold_baseline",
                "cv_fpr",
                "mean_fpr",
                "eligible_count",
                "client_count",
                "coverage_ratio",
                "absorption_ratio",
                "absorption_class",
                "cv_fpr_fedavg_b1",
                "cv_fpr_fedavg_b2",
                "delta_stress",
                "delta_fedavg",
            ]
        )
        for row in table.rows:
            writer.writerow(
                [
                    row.stress_test,
                    row.mu if row.mu is not None else "",
                    row.seed,
                    row.regime.value,
                    row.threshold_baseline.value,
                    row.cv_fpr,
                    row.mean_fpr,
                    row.eligible_count,
                    row.client_count,
                    row.coverage_ratio,
                    row.absorption_ratio if row.absorption_ratio is not None else "",
                    row.absorption_class.value
                    if row.absorption_class is not None
                    else "",
                    row.cv_fpr_fedavg_b1 if row.cv_fpr_fedavg_b1 is not None else "",
                    row.cv_fpr_fedavg_b2 if row.cv_fpr_fedavg_b2 is not None else "",
                    row.delta_stress if row.delta_stress is not None else "",
                    row.delta_fedavg if row.delta_fedavg is not None else "",
                ]
            )

    json_path = output_dir / ABSORPTION_TABLE_JSON
    json_path.write_text(
        table.model_dump_json(indent=2),
        encoding="utf-8",
    )
