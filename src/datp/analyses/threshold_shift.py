"""GB-08 Threshold-Shift vs Delta-FPR/Delta-TPR.

Computes per-client threshold shift (τ_B2 − τ_B1) and relates it to
per-client ΔFPR = FPR(B1) − FPR(B2) and ΔTPR = TPR(B2) − TPR(B1).

All Regime A devices are included — no filtering.

Outputs (when write_outputs=True):
  <base_dir>/analysis/threshold_shift_table.csv
  <base_dir>/analysis/threshold_shift_fpr.png
  <base_dir>/analysis/threshold_shift_tpr.png
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
from pydantic import BaseModel, ConfigDict

from datp.analyses._common import load_cal_errors, load_verified_safe_cells
from datp.artifacts.directories import ANALYSIS_DIR
from datp.baselines.common.thresholds import derive_threshold
from datp.config.compose import compose_config
from datp.config.models import DatpConfig
from datp.core.enums import Baseline, Regime
from datp.core.errors import fmt
from datp.data.datasets.nbaiot.spec import DEVICE_FAMILY_MAP
from datp.evaluation.score_loading import ScoreProvider

_MODULE = "analyses.threshold_shift"

THRESHOLD_SHIFT_TABLE_CSV = "threshold_shift_table.csv"
THRESHOLD_SHIFT_FPR_PNG = "threshold_shift_fpr.png"
THRESHOLD_SHIFT_TPR_PNG = "threshold_shift_tpr.png"


class ThresholdShiftRow(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    client_id: str
    tau_b1: float
    tau_b2: float
    shift: float
    fpr_b1: float
    fpr_b2: float
    delta_fpr: float
    tpr_b1: float
    tpr_b2: float
    delta_tpr: float
    seed: int
    device_family: str


class ThresholdShiftResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    rows: list[ThresholdShiftRow]
    n_clients: int
    n_cells: int


def run_threshold_shift(
    base_dir: Path,
    *,
    config: DatpConfig | None = None,
    write_outputs: bool = False,
) -> ThresholdShiftResult:
    cells = load_verified_safe_cells(base_dir)
    regime_a_cells = [
        c for c in cells
        if c["regime"] == Regime.A.value and c.get("alpha") in (None, "iid")
    ]
    if not regime_a_cells:
        raise FileNotFoundError(
            fmt(_MODULE, "No verified Regime A cells found", "VERIFIED_REUSE_SAFE cells for regime 'a'", "none")
        )

    cfg = config if config is not None else compose_config(regime=Regime.A, baseline=Baseline.B1, seed=0)
    q = cfg.threshold.q
    n_min = cfg.threshold.n_min

    all_rows: list[ThresholdShiftRow] = []
    for cell in regime_a_cells:
        cell_dir = Path(cell["cell_dir"])
        seed = int(cell["seed"])
        cal_errors = load_cal_errors(cell_dir)
        score_provider = ScoreProvider(cell_dir)

        b1 = derive_threshold(Baseline.B1, cal_errors, n_min, q, 0.0, Regime.A, threshold_cfg=cfg.threshold)
        b2 = derive_threshold(Baseline.B2, cal_errors, n_min, q, 0.0, Regime.A, threshold_cfg=cfg.threshold)

        for cid in sorted(cal_errors):
            b1_ct = next((ct for ct in b1.client_thresholds if ct.client_id == cid), None)
            b2_ct = next((ct for ct in b2.client_thresholds if ct.client_id == cid), None)
            if b1_ct is None or b2_ct is None:
                continue

            benign, attack = score_provider.load_test_scores(cid)
            if benign.size == 0:
                continue

            fpr_b1 = float(np.mean(benign > b1_ct.threshold))
            fpr_b2 = float(np.mean(benign > b2_ct.threshold))
            tpr_b1 = float(np.mean(attack > b1_ct.threshold)) if attack.size > 0 else 0.0
            tpr_b2 = float(np.mean(attack > b2_ct.threshold)) if attack.size > 0 else 0.0

            all_rows.append(ThresholdShiftRow(
                client_id=cid,
                tau_b1=b1_ct.threshold,
                tau_b2=b2_ct.threshold,
                shift=b2_ct.threshold - b1_ct.threshold,
                fpr_b1=fpr_b1,
                fpr_b2=fpr_b2,
                delta_fpr=fpr_b1 - fpr_b2,
                tpr_b1=tpr_b1,
                tpr_b2=tpr_b2,
                delta_tpr=tpr_b2 - tpr_b1,
                seed=seed,
                device_family=DEVICE_FAMILY_MAP.get(cid, cid),
            ))

    result = ThresholdShiftResult(
        rows=all_rows,
        n_clients=len(set(r.client_id for r in all_rows)),
        n_cells=len(regime_a_cells),
    )

    if write_outputs:
        _write_outputs(result, base_dir)

    return result


def _write_outputs(result: ThresholdShiftResult, base_dir: Path) -> None:
    out_dir = base_dir / ANALYSIS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    table_path = out_dir / THRESHOLD_SHIFT_TABLE_CSV
    with open(table_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow([
            "client_id", "tau_b1", "tau_b2", "shift", "fpr_b1", "fpr_b2",
            "delta_fpr", "tpr_b1", "tpr_b2", "delta_tpr", "seed", "device_family",
        ])
        for row in result.rows:
            writer.writerow([
                row.client_id, row.tau_b1, row.tau_b2, row.shift,
                row.fpr_b1, row.fpr_b2, row.delta_fpr,
                row.tpr_b1, row.tpr_b2, row.delta_tpr,
                row.seed, row.device_family,
            ])

    _write_scatter(result, out_dir / THRESHOLD_SHIFT_FPR_PNG, x_col="shift", y_col="delta_fpr")
    _write_scatter(result, out_dir / THRESHOLD_SHIFT_TPR_PNG, x_col="shift", y_col="delta_tpr")


def _write_scatter(result: ThresholdShiftResult, path: Path, *, x_col: str, y_col: str) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    xs = np.array([getattr(r, x_col) for r in result.rows])
    ys = np.array([getattr(r, y_col) for r in result.rows])

    fig, ax = plt.subplots(figsize=(5, 4))
    ax.scatter(xs, ys, alpha=0.7, s=40)
    ax.set_xlabel("Threshold Shift (τ_B2 − τ_B1)")
    ax.set_ylabel(y_col.replace("_", " ").title())
    ax.set_title(f"Threshold Shift vs {y_col.replace('_', ' ').title()}")
    ax.axhline(y=0, color="gray", linestyle="--", linewidth=0.5)
    ax.axvline(x=0, color="gray", linestyle="--", linewidth=0.5)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
