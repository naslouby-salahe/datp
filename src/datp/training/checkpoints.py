# SPDX-License-Identifier: Proprietary
"""Checkpoint persistence: atomic writes for model state and convergence artifacts."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import torch
import torch.nn as nn

from datp.artifacts.constants import (
    CONVERGENCE_CURVE_FILE,
    CONVERGENCE_SUMMARY_FILE,
    MODEL_CHECKPOINT,
)
from datp.audit.enums import ConvergenceStatus
from datp.core.logging import get_logger

logger = get_logger(__name__)


def save_checkpoint(model: nn.Module, ckpt_dir: Path) -> Path:
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    ckpt_file = ckpt_dir / MODEL_CHECKPOINT

    tmp_file = ckpt_file.with_suffix(".pt.tmp")
    torch.save(model.state_dict(), tmp_file)
    tmp_file.rename(ckpt_file)

    logger.info("checkpoint saved", path=str(ckpt_file))
    return ckpt_file


def save_convergence_artifacts(
    ckpt_dir: Path,
    loss_history: list[float],
    converged_round: int | None,
    criterion_value: float | None,
    *,
    rounds_initial: int,
    rounds_max: int,
    relative_threshold: float,
    window: int,
) -> None:
    curve_path = ckpt_dir / CONVERGENCE_CURVE_FILE
    summary_path = ckpt_dir / CONVERGENCE_SUMMARY_FILE
    rows = [
        {"round": index, "fedavg_weighted_benign_val_loss": loss}
        for index, loss in enumerate(loss_history, start=1)
    ]
    pd.DataFrame(rows).to_csv(curve_path, index=False)
    summary_path.write_text(
        json.dumps(
            {
                "rounds_initial": rounds_initial,
                "rounds_max": rounds_max,
                "relative_threshold": relative_threshold,
                "window": window,
                "actual_rounds_run": len(loss_history),
                "convergence_round": converged_round,
                "convergence_criterion_value": criterion_value,
                "convergence_status": ConvergenceStatus.CONVERGED
                if converged_round is not None
                else ConvergenceStatus.NOT_CONVERGED,
                "weighted_validation_loss_per_round": loss_history,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
