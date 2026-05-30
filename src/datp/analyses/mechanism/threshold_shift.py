"""GB-08 Threshold-Shift vs Delta-FPR/Delta-TPR.

Computes per-client threshold shift (tau_B2 - tau_B1) and relates it to
per-client Delta-FPR = FPR(B1) - FPR(B2) and Delta-TPR = TPR(B2) - TPR(B1).

All Regime A devices are included - no filtering.

Outputs (when write_outputs=True):
  <base_dir>/analysis/threshold_shift_table.csv
  <base_dir>/analysis/threshold_shift_fpr.png
  <base_dir>/analysis/threshold_shift_tpr.png
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from datp.analyses.cells import (
    AnalysisCellContext,
    iter_analysis_cell_contexts,
    load_safe_cells_for_regime,
)
from datp.analyses.evaluation import derive_tau_global
from datp.analyses.io import write_analysis_csv
from datp.analyses.plotting import saved_scatter
from datp.analyses.runners import analysis_runner
from datp.core.types import AnalysisRowBase, FrozenModel
from datp.thresholding.thresholds import derive_threshold
from datp.config.models import DatpConfig, ThresholdConfig
from datp.core.enums import Baseline, Regime
from datp.data.datasets.nbaiot.spec import DEVICE_FAMILY_MAP

from datp.analyses.constants import (
    THRESHOLD_SHIFT_FPR_PNG,
    THRESHOLD_SHIFT_TABLE_CSV,
    THRESHOLD_SHIFT_TPR_PNG,
)

_MODULE = __name__


class ThresholdShiftRow(AnalysisRowBase):
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
    device_family: str


class ThresholdShiftResult(FrozenModel):
    rows: list[ThresholdShiftRow]
    n_clients: int
    n_cells: int


def _build_client_shift_row(
    cid: str,
    tau_b1: float,
    tau_b2: float,
    benign: np.ndarray,
    attack: np.ndarray,
    seed: int,
    regime: Regime,
    alpha: str | None,
) -> ThresholdShiftRow | None:
    if benign.size == 0:
        return None
    fpr_b1 = float(np.mean(benign > tau_b1))
    fpr_b2 = float(np.mean(benign > tau_b2))
    tpr_b1 = float(np.mean(attack > tau_b1)) if attack.size > 0 else 0.0
    tpr_b2 = float(np.mean(attack > tau_b2)) if attack.size > 0 else 0.0
    return ThresholdShiftRow(
        regime=regime,
        alpha=alpha,
        client_id=cid,
        tau_b1=tau_b1,
        tau_b2=tau_b2,
        shift=tau_b2 - tau_b1,
        fpr_b1=fpr_b1,
        fpr_b2=fpr_b2,
        delta_fpr=fpr_b1 - fpr_b2,
        tpr_b1=tpr_b1,
        tpr_b2=tpr_b2,
        delta_tpr=tpr_b2 - tpr_b1,
        seed=seed,
        device_family=DEVICE_FAMILY_MAP.get(cid, cid),
    )


def _threshold_shift_rows_for_cell(
    ctx: AnalysisCellContext,
    threshold_cfg: ThresholdConfig,
) -> list[ThresholdShiftRow]:
    tau_global, b1 = derive_tau_global(
        ctx.calibration_errors, regime=ctx.regime, threshold_cfg=threshold_cfg
    )
    b2 = derive_threshold(
        Baseline.B2,
        ctx.calibration_errors,
        n_min=threshold_cfg.n_min,
        q=threshold_cfg.q,
        tau_global=tau_global,
        regime=ctx.regime,
        threshold_cfg=threshold_cfg,
    )
    b1_map = {ct.client_id: ct.threshold for ct in b1.client_thresholds}
    b2_map = {ct.client_id: ct.threshold for ct in b2.client_thresholds}

    rows: list[ThresholdShiftRow] = []
    for cid in sorted(ctx.calibration_errors):
        if cid not in b1_map or cid not in b2_map:
            continue
        benign, attack = ctx.score_provider.load_test_scores(cid)
        row = _build_client_shift_row(
            cid, b1_map[cid], b2_map[cid], benign, attack, ctx.seed, ctx.regime, ctx.alpha_label
        )
        if row is not None:
            rows.append(row)
    return rows


def _write_outputs(result: ThresholdShiftResult, base_dir: Path) -> None:
    write_analysis_csv(
        base_dir, THRESHOLD_SHIFT_TABLE_CSV, result.rows, ThresholdShiftRow
    )
    _write_shift_scatter(
        result, base_dir, THRESHOLD_SHIFT_FPR_PNG, x_col="shift", y_col="delta_fpr"
    )
    _write_shift_scatter(
        result, base_dir, THRESHOLD_SHIFT_TPR_PNG, x_col="shift", y_col="delta_tpr"
    )


@analysis_runner(writer_func=_write_outputs)
def run_threshold_shift(
    base_dir: Path,
    *,
    config: DatpConfig,
) -> ThresholdShiftResult:
    cells = load_safe_cells_for_regime(
        base_dir,
        Regime.A,
        alpha_values=(None, "iid"),
        caller_module=_MODULE,
    )

    all_rows: list[ThresholdShiftRow] = []
    for ctx in iter_analysis_cell_contexts(cells):
        all_rows.extend(_threshold_shift_rows_for_cell(ctx, config.threshold))

    return ThresholdShiftResult(
        rows=all_rows,
        n_clients=len({r.client_id for r in all_rows}),
        n_cells=len(cells),
    )


def _write_shift_scatter(
    result: ThresholdShiftResult,
    base_dir: Path,
    filename: str,
    *,
    x_col: str,
    y_col: str,
) -> None:
    xs = np.array([getattr(r, x_col) for r in result.rows])
    ys = np.array([getattr(r, y_col) for r in result.rows])
    y_label = y_col.replace("_", " ").title()

    from datp.analyses.io import ensure_analysis_dir

    out_path = ensure_analysis_dir(base_dir) / filename
    with saved_scatter(
        out_path,
        xs,
        ys,
        xlabel="Threshold Shift (τ_B2 − τ_B1)",
        ylabel=y_label,
        title=f"Threshold Shift vs {y_label}",
    ):
        pass
