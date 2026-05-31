"""GB-10 B3 Preservation.

Reproduces Regime A B3 (family-mean threshold) from stored scores,
verifies against stored reference, and produces a journal-facing artifact.

B3 uses DEVICE_FAMILY_MAP for family grouping and arithmetic mean
within each family. Regime A only.

Outputs (when write_outputs=True):
  <base_dir>/analysis/b3_preservation.csv
"""

from __future__ import annotations

import json
from pathlib import Path

from datp.analyses.cells import (
    iter_analysis_cell_contexts,
    load_safe_cells_for_regime,
)
from datp.analyses.evaluation import (
    derive_tau_global,
    evaluate_threshold_result,
)
from datp.analyses.io import write_analysis_csv
from datp.analyses.runners import analysis_runner
from datp.analyses.constants import B3_PRESERVATION_TABLE_CSV
from datp.core.types import AnalysisRowBase, FrozenModel
from datp.artifacts.layout import ArtifactLayout
from datp.artifacts.names import ArtifactFile
from datp.validation.constants import SCALAR_METRIC_TOLERANCE
from datp.thresholding.thresholds import derive_threshold
from datp.config.models import DatpConfig
from datp.core.enums import Baseline, MetricName, Regime
from datp.core.identity import BaselineRunId, IID_ALPHA_LABEL, TrainingCellId

_MODULE = __name__


class B3Row(AnalysisRowBase):
    cv_fpr: float
    mean_fpr: float
    coverage_ratio: float
    eligible_count: int
    client_count: int
    within_tolerance: bool


class B3PreservationResult(FrozenModel):
    rows: list[B3Row]
    all_within_tolerance: bool


def _load_stored_b3_metric(base_dir: Path, seed: int) -> dict[str, object] | None:
    run = BaselineRunId(
        cell=TrainingCellId(regime=Regime.A, seed=seed, alpha=None),
        baseline=Baseline.B3,
    )
    result_dir = ArtifactLayout(base_dir=base_dir, regime=Regime.A).baseline_run(
        run
    ).result_dir
    metrics_file = result_dir / ArtifactFile.METRICS
    if not metrics_file.is_file():
        return None
    return json.loads(metrics_file.read_text(encoding="utf-8"))


@analysis_runner(
    writer_func=lambda result, base_dir: write_analysis_csv(
        base_dir, B3_PRESERVATION_TABLE_CSV, result.rows, B3Row
    )
)
def run_b3_preservation(
    base_dir: Path,
    *,
    config: DatpConfig,
) -> B3PreservationResult:
    cells = load_safe_cells_for_regime(
        base_dir, Regime.A, alpha_values=(None, IID_ALPHA_LABEL), caller_module=_MODULE
    )

    rows: list[B3Row] = []
    for ctx in iter_analysis_cell_contexts(cells):
        seed = ctx.seed

        tau_global, _b1 = derive_tau_global(
            ctx.calibration_errors,
            regime=Regime.A,
            threshold_cfg=config.threshold,
            seed=ctx.seed,
            alpha=ctx.alpha_value,
        )

        b3_result = derive_threshold(
            Baseline.B3,
            ctx.calibration_errors,
            n_min=config.threshold.n_min,
            q=config.threshold.q,
            tau_global=tau_global,
            regime=Regime.A,
            threshold_cfg=config.threshold,
            seed=ctx.seed,
            alpha=ctx.alpha_value,
        )
        evaluation = evaluate_threshold_result(
            b3_result, ctx.score_provider, Regime.A, seed, None
        )

        cv_fpr = float(evaluation.cv_fpr)
        mean_fpr = float(evaluation.mean_fpr)
        coverage = float(evaluation.coverage_ratio)

        within_tol = True
        stored = _load_stored_b3_metric(base_dir, seed)
        if stored is not None:
            raw = stored.get(MetricName.CV_FPR.value, cv_fpr)
            stored_cv = float(raw) if isinstance(raw, (int, float)) else cv_fpr
            within_tol = abs(cv_fpr - stored_cv) <= SCALAR_METRIC_TOLERANCE

        rows.append(
            B3Row(
                regime=Regime.A,
                alpha=ctx.alpha_label,
                seed=seed,
                cv_fpr=cv_fpr,
                mean_fpr=mean_fpr,
                coverage_ratio=coverage,
                eligible_count=evaluation.eligible_count,
                client_count=len(evaluation.clients),
                within_tolerance=within_tol,
            )
        )

    return B3PreservationResult(
        rows=rows,
        all_within_tolerance=all(r.within_tolerance for r in rows),
    )
