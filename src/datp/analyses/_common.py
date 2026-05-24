"""Shared utilities for DATP analysis modules.

All analysis modules (calibration_sweep, q_sensitivity, tau_shrink, b4_ablation,
b2_conf, fedstats_benign) import loaders and helpers from here to avoid
duplication of cell-verdict loading, calibration-error loading, alpha-string
parsing, and evaluation orchestration.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

from datp.artifacts.directories import SCORES_DIR
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


# ── Cell verdict loading ───────────────────────────────────────────────────


def load_cell_verdicts(base_dir: Path) -> list[dict]:
    """Load cell verdicts JSON; raises FileNotFoundError if absent."""
    path = base_dir / SCORES_DIR / CELL_VERDICTS_JSON
    if not path.is_file():
        raise FileNotFoundError(
            fmt(_MODULE, f"Cell verdicts not found at {path}", "cell_verdicts.json from T04", "absent")
        )
    return json.loads(path.read_text(encoding="utf-8"))["cells"]


def load_verified_safe_cells(base_dir: Path) -> list[dict]:
    """Return only VERIFIED_REUSE_SAFE cell verdict entries."""
    return [c for c in load_cell_verdicts(base_dir) if c["verdict"] == ReuseVerdict.VERIFIED_REUSE_SAFE]


# ── Score loading ─────────────────────────────────────────────────────────


def load_cal_errors(score_root: Path) -> dict[str, np.ndarray]:
    """Load all calibration-error Parquet files from a score-root/cal/ directory."""
    cal_dir = score_root / ScoringStage.CAL.value
    if not cal_dir.is_dir():
        raise FileNotFoundError(
            fmt(_MODULE, f"Calibration score directory missing at {cal_dir}", "cal/ directory", "absent")
        )
    errors: dict[str, np.ndarray] = {}
    for parquet in sorted(cal_dir.glob("*.parquet")):
        errors[parquet.stem] = read_score_column(parquet)
    if not errors:
        raise FileNotFoundError(
            fmt(_MODULE, f"No calibration parquets at {cal_dir}", "at least one .parquet", "none")
        )
    return errors


def load_test_benign_errors(score_root: Path) -> dict[str, np.ndarray]:
    """Load test_benign Parquet files from a score-root/test_benign/ directory.

    Returns empty dict if directory is missing (not all regimes/stages
    guarantee test_benign scores on disk).
    """
    tb_dir = score_root / ScoringStage.TEST_BENIGN.value
    if not tb_dir.is_dir():
        raise FileNotFoundError(
            fmt_missing(_MODULE, f"test_benign score directory {tb_dir}")
        )
    errors: dict[str, np.ndarray] = {}
    for parquet in sorted(tb_dir.glob("*.parquet")):
        errors[parquet.stem] = read_score_column(parquet)
    return errors


# ── Alpha parsing ──────────────────────────────────────────────────────────


def parse_alpha_str(alpha_str: str | None) -> float | None:
    """Convert stored alpha label back to float. 'iid' → math.inf; None → None."""
    if alpha_str is None:
        return None
    if alpha_str == "iid":
        return math.inf
    return float(alpha_str)


# ── Shared metric helpers ──────────────────────────────────────────────────


def compute_fpr(benign_errors: np.ndarray, threshold: float) -> float:
    """Fraction of benign reconstruction errors exceeding the threshold."""
    if benign_errors.size == 0:
        return 0.0
    return float(np.mean(benign_errors > threshold))


def compute_cv(values: np.ndarray) -> float:
    """Coefficient of variation (std(ddof=1) / mean); 0 for n<2 or mean≈0."""
    if values.size < 2:
        return 0.0
    mean = float(np.mean(values))
    if math.isclose(mean, 0.0, abs_tol=1e-12):
        return 0.0
    return float(np.std(values, ddof=1) / mean)


def compute_empirical_coverage(test_benign: np.ndarray, threshold: float) -> float:
    """Fraction of test_benign scores ≤ threshold."""
    if test_benign.size == 0:
        return 0.0
    return float(np.mean(test_benign <= threshold))


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
