"""Shared utilities for DATP analysis modules.

Provides cell-verdict loading, score loading, CV helper, and evaluation
orchestration shared across analysis modules.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

from pydantic import BaseModel, ConfigDict

from datp.artifacts.directories import ANALYSIS_DIR, SCORES_DIR
from datp.audit.constants import CELL_VERDICTS_JSON
from datp.audit.enums import ReuseVerdict
from datp.core.enums import Regime, ScoringStage
from datp.core.errors import fmt, fmt_missing
from datp.evaluation.metrics import (
    ClientMetrics,
    EvaluationResult,
    build_evaluation_result,
    compute_client_metrics,
)
from datp.evaluation.score_loading import ScoreProvider, read_score_column

_MODULE = "analyses._common"
_CV_ZERO_MEAN_TOLERANCE = 1e-12


class CellEntry(BaseModel):
    """Typed boundary for cell verdict entries as consumed by analysis modules.

    Contains only the 6 fields analyses need; extra audit-layer fields are ignored.
    """

    model_config = ConfigDict(extra="ignore", frozen=True)
    cell_dir: str
    regime: Regime
    seed: int
    alpha: str | None = None
    dataset: str = ""
    verdict: ReuseVerdict


# ── Cell verdict loading ───────────────────────────────────────────────────


def load_cell_verdicts(base_dir: Path) -> list[CellEntry]:
    """Load and validate cell verdicts JSON; raises FileNotFoundError if absent."""
    path = base_dir / SCORES_DIR / CELL_VERDICTS_JSON
    if not path.is_file():
        raise FileNotFoundError(
            fmt(
                _MODULE,
                f"Cell verdicts not found at {path}",
                "cell_verdicts.json from T04",
                "absent",
            )
        )
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [CellEntry.model_validate(c) for c in raw["cells"]]


def load_verified_safe_cells(base_dir: Path) -> list[CellEntry]:
    """Return only VERIFIED_REUSE_SAFE cell verdict entries."""
    return [
        c
        for c in load_cell_verdicts(base_dir)
        if c.verdict == ReuseVerdict.VERIFIED_REUSE_SAFE
    ]


# ── Score loading ─────────────────────────────────────────────────────────


def load_cal_errors(score_root: Path) -> dict[str, np.ndarray]:
    """Load all calibration-error Parquet files from a score-root/cal/ directory."""
    cal_dir = score_root / ScoringStage.CAL.value
    if not cal_dir.is_dir():
        raise FileNotFoundError(
            fmt(
                _MODULE,
                f"Calibration score directory missing at {cal_dir}",
                "cal/ directory",
                "absent",
            )
        )
    errors: dict[str, np.ndarray] = {}
    for parquet in sorted(cal_dir.glob("*.parquet")):
        errors[parquet.stem] = read_score_column(parquet)
    if not errors:
        raise FileNotFoundError(
            fmt(
                _MODULE,
                f"No calibration parquets at {cal_dir}",
                "at least one .parquet",
                "none",
            )
        )
    return errors


def load_test_benign_errors(score_root: Path) -> dict[str, np.ndarray]:
    """Load test_benign Parquet files from a score-root/test_benign/ directory."""
    tb_dir = score_root / ScoringStage.TEST_BENIGN.value
    if not tb_dir.is_dir():
        raise FileNotFoundError(
            fmt_missing(_MODULE, f"test_benign score directory {tb_dir}")
        )
    errors: dict[str, np.ndarray] = {}
    for parquet in sorted(tb_dir.glob("*.parquet")):
        errors[parquet.stem] = read_score_column(parquet)
    return errors


# ── Analysis output helpers ───────────────────────────────────────────────


def ensure_analysis_dir(base_dir: Path) -> Path:
    """Create and return <base_dir>/analysis/, creating parents as needed."""
    out = base_dir / ANALYSIS_DIR
    out.mkdir(parents=True, exist_ok=True)
    return out


# ── Shared metric helpers ──────────────────────────────────────────────────


def compute_cv(values: np.ndarray) -> float:
    """CV(std(ddof=1)/mean) returning 0.0 for n<2 or mean≈0 (not nan, for safe numeric comparisons)."""
    if values.size < 2:
        return 0.0
    mean = float(np.mean(values))
    if math.isclose(mean, 0.0, abs_tol=_CV_ZERO_MEAN_TOLERANCE):
        return 0.0
    return float(np.std(values, ddof=1) / mean)


# ── Shared evaluation helper ───────────────────────────────────────────────


def evaluate_threshold_result(
    threshold_result,  # ThresholdResult
    score_provider: ScoreProvider,
    regime: Regime,
    seed: int,
    alpha: float | None,
) -> EvaluationResult:
    """Compute per-client metrics from a ThresholdResult + ScoreProvider.

    Tracks eligible, pending, and eval_incomplete client IDs internally.
    """
    per_client: list[ClientMetrics] = []
    eligible_ids: list[str] = []
    pending_ids: list[str] = []
    eval_incomplete_ids: list[str] = []

    for ct in threshold_result.client_thresholds:
        cid = ct.client_id
        benign, attack = score_provider.load_test_scores(cid)
        per_client.append(compute_client_metrics(cid, benign, attack, ct.threshold))
        (pending_ids if ct.calibration_pending else eligible_ids).append(cid)
        if attack.size == 0:
            eval_incomplete_ids.append(cid)

    return build_evaluation_result(
        baseline=threshold_result.strategy,
        regime=regime,
        seed=seed,
        alpha=alpha,
        per_client=per_client,
        eligible_ids=eligible_ids,
        pending_ids=pending_ids,
        eval_incomplete_ids=eval_incomplete_ids,
    )
