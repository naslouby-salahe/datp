"""GB-10 B3 Preservation.

Reproduces Regime A B3 (family-mean threshold) from stored scores,
verifies against stored reference, and produces a journal-facing artifact.

B3 uses DEVICE_FAMILY_MAP for family grouping and arithmetic mean
within each family. Regime A only.

Outputs (when write_outputs=True):
  <base_dir>/analysis/b3_preservation.csv
"""

from __future__ import annotations

import csv
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from datp.analyses._common import evaluate_threshold_result, load_cal_errors, load_verified_safe_cells
from datp.artifacts.constants import METRICS_FILE
from datp.artifacts.directories import ANALYSIS_DIR
from datp.artifacts.paths import ExperimentLocator
from datp.audit.constants import SCALAR_METRIC_TOLERANCE
from datp.baselines.common.thresholds import derive_threshold
from datp.config.compose import compose_config
from datp.config.models import DatpConfig
from datp.core.enums import Baseline, Regime
from datp.core.errors import fmt
from datp.evaluation.score_loading import ScoreProvider

_MODULE = "analyses.b3_preservation"

B3_PRESERVATION_CSV = "b3_preservation.csv"


class B3Row(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    seed: int
    cv_fpr: float
    mean_fpr: float
    coverage_ratio: float
    eligible_count: int
    client_count: int
    within_tolerance: bool


class B3PreservationResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    rows: list[B3Row]
    all_within_tolerance: bool


def _load_stored_b3_metric(base_dir: Path, seed: int) -> dict | None:
    result_dir = ExperimentLocator.for_main(base_dir, Regime.A).result(Baseline.B3, seed)
    metrics_file = result_dir / METRICS_FILE
    if not metrics_file.is_file():
        return None
    import json
    return json.loads(metrics_file.read_text(encoding="utf-8"))


def run_b3_preservation(
    base_dir: Path,
    *,
    config: DatpConfig | None = None,
    write_outputs: bool = False,
) -> B3PreservationResult:
    cells = load_verified_safe_cells(base_dir)
    regime_a_cells = [
        c for c in cells
        if c["regime"] == Regime.A.value and c.get("alpha") in (None, "iid")
    ]
    if not regime_a_cells:
        raise FileNotFoundError(
            fmt(_MODULE, "No verified Regime A cells", "VERIFIED_REUSE_SAFE cells for regime 'a'", "none")
        )

    cfg = config if config is not None else compose_config(regime=Regime.A, baseline=Baseline.B3, seed=0)
    q = cfg.threshold.q
    n_min = cfg.threshold.n_min

    rows: list[B3Row] = []
    for cell in regime_a_cells:
        cell_dir = Path(cell["cell_dir"])
        seed = int(cell["seed"])
        cal_errors = load_cal_errors(cell_dir)


        score_provider = ScoreProvider(cell_dir)
        b3_result = derive_threshold(Baseline.B3, cal_errors, n_min, q, 0.0, Regime.A, threshold_cfg=cfg.threshold)
        evaluation = evaluate_threshold_result(b3_result, score_provider, Regime.A, seed, None)

        cv_fpr = float(evaluation.cv_fpr)
        mean_fpr = float(evaluation.mean_fpr)
        coverage = float(evaluation.coverage_ratio)

        within_tol = True
        stored = _load_stored_b3_metric(base_dir, seed)
        if stored is not None:
            stored_cv = float(stored.get("cv_fpr", cv_fpr))
            within_tol = abs(cv_fpr - stored_cv) <= SCALAR_METRIC_TOLERANCE

        rows.append(B3Row(
            seed=seed,
            cv_fpr=cv_fpr,
            mean_fpr=mean_fpr,
            coverage_ratio=coverage,
            eligible_count=evaluation.eligible_count,
            client_count=len(evaluation.per_client),
            within_tolerance=within_tol,
        ))

    all_ok = all(r.within_tolerance for r in rows)

    result = B3PreservationResult(
        rows=rows,
        all_within_tolerance=all_ok,
    )

    if write_outputs:
        _write_outputs(result, base_dir)

    return result


def _write_outputs(result: B3PreservationResult, base_dir: Path) -> None:
    out_dir = base_dir / ANALYSIS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    path = out_dir / B3_PRESERVATION_CSV
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["seed", "cv_fpr", "mean_fpr", "coverage_ratio", "eligible_count", "client_count", "within_tolerance"])
        for row in result.rows:
            writer.writerow([row.seed, row.cv_fpr, row.mean_fpr, row.coverage_ratio, row.eligible_count, row.client_count, row.within_tolerance])
