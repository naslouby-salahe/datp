"""GB-12 Per-Client CDF / Failure-Mode Analysis.

Overlays benign/attack empirical CDFs with B1/B2/B4 threshold lines per client.
Identifies failure modes (high FPR, low TPR) and produces CDF grid figure
and failure-mode table.

All 9 Regime A devices included — no filtering.
Regime A only.

Outputs (when write_outputs=True):
  <base_dir>/analysis/per_client_cdf_grid.png
  <base_dir>/analysis/per_client_failure_modes.csv
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import NamedTuple

import numpy as np
from pydantic import BaseModel, ConfigDict

from datp.analyses._common import (
    ensure_analysis_dir,
    load_cal_errors,
    load_verified_safe_cells,
)
from datp.baselines.common.thresholds import derive_threshold
from datp.config.compose import compose_analysis_config
from datp.config.models import DatpConfig
from datp.core.enums import Baseline, Regime
from datp.core.errors import fmt
from datp.data.datasets.nbaiot.spec import DEVICE_FAMILY_MAP
from datp.evaluation.score_loading import ScoreProvider

_MODULE = "analyses.per_client_cdf"

PER_CLIENT_CDF_GRID_PNG = "per_client_cdf_grid.png"
PER_CLIENT_FAILURE_MODES_CSV = "per_client_failure_modes.csv"

_FPR_HIGH_THRESHOLD = 0.10
_TPR_LOW_THRESHOLD = 0.90


class FailureModeRow(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    device: str
    device_family: str
    seed: int
    b1_fpr: float
    b2_fpr: float
    b4_fpr: float
    b1_tpr: float
    b2_tpr: float
    b4_tpr: float
    b1_tau: float
    b2_tau: float
    b4_tau: float
    failure_mode: str


class PerClientCDFResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    rows: list[FailureModeRow]
    n_devices: int
    n_cells: int


class ThresholdSet(NamedTuple):
    b1: float
    b2: float
    b4: float


class ClientScoreSet(NamedTuple):
    benign: np.ndarray
    attack: np.ndarray


class FailureModeInput(NamedTuple):
    client_id: str
    seed: int
    scores: ClientScoreSet
    thresholds: ThresholdSet


def _threshold_by_client(threshold_result) -> dict[str, float]:
    return {ct.client_id: ct.threshold for ct in threshold_result.client_thresholds}


def _empirical_cdf(
    values: np.ndarray, n_points: int = 500
) -> tuple[np.ndarray, np.ndarray]:
    vals = np.sort(values)
    cdf = np.linspace(0, 1, len(vals))
    if n_points > 0 and len(vals) > n_points:
        idx = np.linspace(0, len(vals) - 1, n_points, dtype=int)
        return vals[idx], cdf[idx]
    return vals, cdf


def _classify_failure(
    b1_fpr: float, b1_tpr: float, b2_fpr: float, b2_tpr: float
) -> str:
    modes: list[str] = []
    if b1_fpr > _FPR_HIGH_THRESHOLD:
        modes.append("HIGH_FPR_B1")
    if b1_tpr < _TPR_LOW_THRESHOLD:
        modes.append("LOW_TPR_B1")
    if b2_fpr > _FPR_HIGH_THRESHOLD:
        modes.append("HIGH_FPR_B2")
    if b2_tpr < _TPR_LOW_THRESHOLD:
        modes.append("LOW_TPR_B2")
    if not modes:
        modes.append("NORMAL")
    return "|".join(modes)


def _derive_regime_a_thresholds(
    cal_errors: dict[str, np.ndarray],
    cfg: DatpConfig,
) -> dict[Baseline, dict[str, float]]:
    return {
        baseline: _threshold_by_client(
            derive_threshold(
                baseline,
                cal_errors,
                cfg.threshold.n_min,
                cfg.threshold.q,
                0.0,
                Regime.A,
                threshold_cfg=cfg.threshold,
            )
        )
        for baseline in (Baseline.B1, Baseline.B2, Baseline.B4)
    }


def _client_thresholds(
    thresholds: dict[Baseline, dict[str, float]],
    client_id: str,
) -> ThresholdSet | None:
    if any(client_id not in thresholds[baseline] for baseline in thresholds):
        return None
    return ThresholdSet(
        b1=thresholds[Baseline.B1][client_id],
        b2=thresholds[Baseline.B2][client_id],
        b4=thresholds[Baseline.B4][client_id],
    )


def _tpr(scores: np.ndarray, threshold: float) -> float:
    return float(np.mean(scores > threshold)) if scores.size > 0 else 0.0


def _failure_mode_row(
    failure_input: FailureModeInput,
) -> FailureModeRow:
    client_id = failure_input.client_id
    thresholds = failure_input.thresholds
    scores = failure_input.scores
    b1_fpr = float(np.mean(scores.benign > thresholds.b1))
    b2_fpr = float(np.mean(scores.benign > thresholds.b2))
    b4_fpr = float(np.mean(scores.benign > thresholds.b4))
    b1_tpr = _tpr(scores.attack, thresholds.b1)
    b2_tpr = _tpr(scores.attack, thresholds.b2)
    b4_tpr = _tpr(scores.attack, thresholds.b4)
    return FailureModeRow(
        device=client_id,
        device_family=DEVICE_FAMILY_MAP.get(client_id, client_id),
        seed=failure_input.seed,
        b1_fpr=b1_fpr,
        b2_fpr=b2_fpr,
        b4_fpr=b4_fpr,
        b1_tpr=b1_tpr,
        b2_tpr=b2_tpr,
        b4_tpr=b4_tpr,
        b1_tau=thresholds.b1,
        b2_tau=thresholds.b2,
        b4_tau=thresholds.b4,
        failure_mode=_classify_failure(b1_fpr, b1_tpr, b2_fpr, b2_tpr),
    )


def _collect_cell_rows(cell, cfg: DatpConfig) -> tuple[list[FailureModeRow], dict]:
    cell_dir = Path(cell.cell_dir)
    cal_errors = load_cal_errors(cell_dir)
    thresholds_by_client = _derive_regime_a_thresholds(cal_errors, cfg)
    score_provider = ScoreProvider(cell_dir)

    rows: list[FailureModeRow] = []
    cdf_data: dict[tuple[str, int], dict] = {}
    for cid in sorted(cal_errors):
        benign, attack = score_provider.load_test_scores(cid)
        if benign.size == 0:
            continue
        thresholds = _client_thresholds(thresholds_by_client, cid)
        if thresholds is None:
            continue
        rows.append(
            _failure_mode_row(
                FailureModeInput(
                    client_id=cid,
                    seed=cell.seed,
                    scores=ClientScoreSet(benign, attack),
                    thresholds=thresholds,
                )
            )
        )
        cdf_data[(cid, cell.seed)] = {
            "benign": benign,
            "attack": attack,
            "b1_tau": thresholds.b1,
            "b2_tau": thresholds.b2,
            "b4_tau": thresholds.b4,
        }
    return rows, cdf_data


def run_per_client_cdf(
    base_dir: Path,
    *,
    config: DatpConfig | None = None,
    write_outputs: bool = False,
) -> PerClientCDFResult:
    cells = load_verified_safe_cells(base_dir)
    regime_a_cells = [
        c for c in cells if c.regime == Regime.A and c.alpha in (None, "iid")
    ]
    if not regime_a_cells:
        raise FileNotFoundError(
            fmt(
                _MODULE,
                "No verified Regime A cells",
                "VERIFIED_REUSE_SAFE cells for regime 'a'",
                "none",
            )
        )

    cfg = config if config is not None else compose_analysis_config()

    all_rows: list[FailureModeRow] = []
    cdf_data: dict[tuple[str, int], dict] = {}

    for cell in regime_a_cells:
        rows, cell_cdf_data = _collect_cell_rows(cell, cfg)
        all_rows.extend(rows)
        cdf_data.update(cell_cdf_data)

    result = PerClientCDFResult(
        rows=all_rows,
        n_devices=len({r.device for r in all_rows}),
        n_cells=len(regime_a_cells),
    )

    if write_outputs:
        _write_outputs(result, cdf_data, base_dir)

    return result


def _write_outputs(result: PerClientCDFResult, cdf_data: dict, base_dir: Path) -> None:
    out_dir = ensure_analysis_dir(base_dir)

    table_path = out_dir / PER_CLIENT_FAILURE_MODES_CSV
    with open(table_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            [
                "device",
                "device_family",
                "seed",
                "b1_fpr",
                "b2_fpr",
                "b4_fpr",
                "b1_tpr",
                "b2_tpr",
                "b4_tpr",
                "b1_tau",
                "b2_tau",
                "b4_tau",
                "failure_mode",
            ]
        )
        for row in result.rows:
            writer.writerow(
                [
                    row.device,
                    row.device_family,
                    row.seed,
                    row.b1_fpr,
                    row.b2_fpr,
                    row.b4_fpr,
                    row.b1_tpr,
                    row.b2_tpr,
                    row.b4_tpr,
                    row.b1_tau,
                    row.b2_tau,
                    row.b4_tau,
                    row.failure_mode,
                ]
            )

    _write_cdf_grid(result, cdf_data, out_dir / PER_CLIENT_CDF_GRID_PNG)


def _flatten_axes(axes, *, n_rows: int, n_cols: int):
    if n_rows > 1:
        return axes.flatten()
    if n_cols == 1:
        return [axes]
    return axes


def _write_cdf_grid(result: PerClientCDFResult, cdf_data: dict, path: Path) -> None:
    from datp.analyses._plotting import plt

    devices = sorted({r.device for r in result.rows})
    n_devs = len(devices)
    n_cols = 3
    n_rows = (n_devs + n_cols - 1) // n_cols

    fig, axes = plt.subplots(n_rows, n_cols, figsize=(n_cols * 5, n_rows * 4))
    axes_flat = _flatten_axes(axes, n_rows=n_rows, n_cols=n_cols)

    for idx, device in enumerate(devices):
        ax = axes_flat[idx]
        device_data = [(k, v) for k, v in cdf_data.items() if k[0] == device]
        if not device_data:
            ax.set_title(f"{device}\n(no data)")
            continue

        (_, _), data = device_data[0]

        ben_x, ben_y = _empirical_cdf(data["benign"])
        att_x, att_y = _empirical_cdf(data["attack"])

        ax.plot(ben_x, ben_y, "b-", linewidth=1.5, alpha=0.8, label="Benign")
        ax.plot(att_x, att_y, "r-", linewidth=1.5, alpha=0.8, label="Attack")

        ax.axvline(
            data["b1_tau"],
            color="#1f77b4",
            linestyle="--",
            linewidth=1,
            alpha=0.7,
            label="B1",
        )
        ax.axvline(
            data["b2_tau"],
            color="#ff7f0e",
            linestyle="--",
            linewidth=1,
            alpha=0.7,
            label="B2",
        )
        ax.axvline(
            data["b4_tau"],
            color="#d62728",
            linestyle=":",
            linewidth=1,
            alpha=0.7,
            label="B4",
        )

        device_rows = [r for r in result.rows if r.device == device]
        fm = device_rows[0].failure_mode if device_rows else "NORMAL"
        ax.set_title(f"{device}\n{fm}", fontsize=9)
        ax.set_xlabel("Reconstruction Error")
        ax.set_ylabel("CDF")

    for idx in range(len(devices), len(axes_flat)):
        axes_flat[idx].set_visible(False)

    handles, labels = axes_flat[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=5, fontsize=8)
    fig.suptitle("Per-Client CDFs with B1/B2/B4 Thresholds", fontsize=12)
    fig.tight_layout(rect=(0, 0.08, 1, 0.95))
    fig.savefig(path, dpi=150)
    plt.close(fig)
