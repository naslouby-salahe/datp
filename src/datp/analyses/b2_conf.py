"""GB-04 B2-conf conformal threshold variant.

Per‑client split‑conformal threshold:
    k = ceil((n + 1) * (1 − alpha)),   alpha = 1 − q (from config)
    τ_i = sorted_errors[k − 1]  (0‑indexed)
If k > n (insufficient calibration samples) → use max(errors) conservative.
Calibration‑Pending clients (n_cal < n_min) receive τ_global as fallback.

Reports empirical benign coverage on held‑out test_benign and CV(FPR).
Does NOT claim guaranteed attack detection — the guarantee is limited to
marginal benign‑distribution coverage (FPR control under exchangeability).

Outputs (when write_outputs=True):
  <base_dir>/analysis/b2_conf_table.csv
  <base_dir>/analysis/b2_conf_coverage.png
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import numpy as np
from pydantic import BaseModel, ConfigDict

from datp.artifacts.directories import ANALYSIS_DIR, SCORES_DIR
from datp.audit.constants import CELL_VERDICTS_JSON, SCALAR_METRIC_TOLERANCE
from datp.baselines.common.thresholds import conformal_threshold, derive_threshold
from datp.config.compose import compose_config
from datp.config.models import DatpConfig
from datp.core.enums import Baseline, Regime, ReuseVerdict, ScoringStage
from datp.core.errors import fmt
from datp.evaluation.metrics import (
    ClientMetrics,
    EvaluationResult,
    build_evaluation_result,
    compute_client_metrics,
)
from datp.evaluation.score_loading import ScoreProvider, read_score_column

_MODULE = "analyses.b2_conf"

B2_CONF_TABLE_CSV = "b2_conf_table.csv"
B2_CONF_COVERAGE_PNG = "b2_conf_coverage.png"


class B2ConfRow(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    regime: Regime
    seed: int
    alpha: str | None
    client_id: str
    tau_conformal: float
    tau_b2: float
    empirical_coverage: float
    n_cal: int
    calibration_pending: bool
    cv_fpr: float | None  # aggregate per cell — None for per‑client rows


class B2ConfResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    rows: list[B2ConfRow]
    alpha_conformal: float
    verified_safe_cell_count: int


def _load_cell_verdicts(base_dir: Path) -> list[dict]:
    path = base_dir / SCORES_DIR / CELL_VERDICTS_JSON
    if not path.is_file():
        raise FileNotFoundError(
            fmt(_MODULE, f"Cell verdicts not found at {path}", "cell_verdicts.json from T04", "absent")
        )
    return json.loads(path.read_text(encoding="utf-8"))["cells"]


def _load_cal_errors(score_root: Path) -> dict[str, np.ndarray]:
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


def _parse_alpha_str(alpha_str: str | None) -> float | None:
    if alpha_str is None:
        return None
    if alpha_str == "iid":
        return math.inf
    return float(alpha_str)


def _empirical_coverage(test_benign: np.ndarray, threshold: float) -> float:
    """Fraction of test_benign scores ≤ threshold."""
    if test_benign.size == 0:
        return 0.0
    return float(np.mean(test_benign <= threshold))


def _fpr(benign_errors: np.ndarray, threshold: float) -> float:
    if benign_errors.size == 0:
        return 0.0
    return float(np.mean(benign_errors > threshold))


def _cv(values: np.ndarray) -> float:
    if values.size < 2:
        return 0.0
    mean = float(np.mean(values))
    if mean == 0.0:
        return 0.0
    return float(np.std(values, ddof=1) / mean)


def run_b2_conf(
    base_dir: Path,
    *,
    config: DatpConfig | None = None,
    write_outputs: bool = False,
) -> B2ConfResult:
    cfg = config or compose_config(regime=Regime.A, baseline=Baseline.B1)
    q = cfg.threshold.q
    n_min = cfg.threshold.n_min
    alpha_conformal = 1.0 - q  # alpha = 1 − q from config

    if not (0.0 < alpha_conformal < 1.0):
        raise ValueError(
            fmt(_MODULE, f"Invalid alpha_conformal={alpha_conformal} from q={q}", "0 < alpha < 1", str(alpha_conformal))
        )

    resolved = base_dir.resolve()
    safe_cells = [
        c for c in _load_cell_verdicts(resolved)
        if c["verdict"] == ReuseVerdict.VERIFIED_REUSE_SAFE
    ]

    rows: list[B2ConfRow] = []
    for cell in safe_cells:
        cell_dir = Path(cell["cell_dir"])
        regime = Regime(cell["regime"])
        seed = int(cell["seed"])
        alpha_str: str | None = cell.get("alpha")
        alpha_f = _parse_alpha_str(alpha_str)

        cal_errors = _load_cal_errors(cell_dir)
        score_provider = ScoreProvider(cell_dir)

        # Get tau_global for Calibration-Pending fallback
        b1_result = derive_threshold(
            Baseline.B1, cal_errors, n_min=n_min, q=q, tau_global=0.0,
            regime=regime, threshold_cfg=cfg.threshold,
        )
        tau_global = float(b1_result.tau_global)

        # Compute B2 for comparison
        b2_result = derive_threshold(
            Baseline.B2, cal_errors, n_min=n_min, q=q, tau_global=tau_global,
            regime=regime, threshold_cfg=cfg.threshold,
        )
        b2_taus: dict[str, float] = {
            ct.client_id: ct.threshold for ct in b2_result.client_thresholds
        }

        # Build per-client conformal thresholds
        cell_fprs: list[float] = []
        for ct in b2_result.client_thresholds:
            cid = ct.client_id
            cal_arr = cal_errors.get(cid, np.array([]))
            n_cal = cal_arr.size
            calibration_pending = ct.calibration_pending

            if calibration_pending or n_cal == 0:
                tau_conf = tau_global
            else:
                tau_conf = conformal_threshold(cal_arr, alpha_conformal)

            tb_arr = score_provider.load(cid, ScoringStage.TEST_BENIGN)
            coverage = _empirical_coverage(tb_arr, tau_conf) if tb_arr.size > 0 else 0.0
            fpr_val = _fpr(tb_arr, tau_conf) if tb_arr.size > 0 else 0.0
            cell_fprs.append(fpr_val)

            rows.append(B2ConfRow(
                regime=regime,
                seed=seed,
                alpha=alpha_str,
                client_id=cid,
                tau_conformal=tau_conf,
                tau_b2=b2_taus.get(cid, tau_global),
                empirical_coverage=coverage,
                n_cal=n_cal,
                calibration_pending=calibration_pending,
                cv_fpr=None,
            ))

    result = B2ConfResult(
        rows=rows,
        alpha_conformal=alpha_conformal,
        verified_safe_cell_count=len(safe_cells),
    )

    if write_outputs:
        _write_outputs(result, resolved)

    return result


def _write_outputs(result: B2ConfResult, base_dir: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    analysis_dir = base_dir / ANALYSIS_DIR
    analysis_dir.mkdir(parents=True, exist_ok=True)

    # CSV
    fieldnames = [
        "regime", "seed", "alpha", "client_id", "tau_conformal", "tau_b2",
        "empirical_coverage", "n_cal", "calibration_pending",
    ]
    csv_path = analysis_dir / B2_CONF_TABLE_CSV
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in result.rows:
            writer.writerow({
                "regime": row.regime.value,
                "seed": row.seed,
                "alpha": row.alpha,
                "client_id": row.client_id,
                "tau_conformal": row.tau_conformal,
                "tau_b2": row.tau_b2,
                "empirical_coverage": row.empirical_coverage,
                "n_cal": row.n_cal,
                "calibration_pending": row.calibration_pending,
            })

    # Coverage histogram figure
    regime_a_rows = [r for r in result.rows if r.regime == Regime.A and r.alpha is None and not r.calibration_pending]
    if not regime_a_rows:
        return
    coverages = [r.empirical_coverage for r in regime_a_rows]
    target = 1.0 - result.alpha_conformal

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(coverages, bins=30, alpha=0.7, edgecolor="black")
    ax.axvline(target, color="red", linestyle="--", linewidth=2, label=f"Target (1−α)={target:.3f}")
    ax.set_xlabel("Empirical benign coverage")
    ax.set_ylabel("Client count")
    ax.set_title("B2-conf Empirical Benign Coverage — Regime A")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(analysis_dir / B2_CONF_COVERAGE_PNG, dpi=150)
    plt.close(fig)
