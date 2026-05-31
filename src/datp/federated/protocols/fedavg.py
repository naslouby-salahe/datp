# SPDX-License-Identifier: Proprietary
"""FedAvg protocol entry point: train AE via FedAvg and produce score artifacts."""

from __future__ import annotations

from typing import TYPE_CHECKING

from datp.artifacts.layout import ArtifactLayout
from datp.core.errors import fmt
from datp.core.identity import ScoreCellId, TrainingCellId
from datp.federated.simulation import run_fl_simulation, validate_regime
from datp.modeling.autoencoder import Autoencoder

if TYPE_CHECKING:
    from pathlib import Path

    from datp.config.models import DatpConfig
    from datp.federated.simulation import TrainingResult
    from datp.federated.types import ClientData

_MODULE = "federated.protocols.fedavg"


def run_fl_training(
    cfg: DatpConfig,
    client_data: dict[str, ClientData],
    seed: int,
    alpha: float | None = None,
    *,
    base_dir: Path | None = None,
    prepared_dir: Path | None = None,
    output_layout: ArtifactLayout | None = None,
) -> TrainingResult:
    """Train AE via FedAvg and produce score artifacts (main FL entry point)."""
    regime = validate_regime(cfg)
    if output_layout is not None:
        layout = output_layout
    elif base_dir is not None:
        layout = ArtifactLayout(base_dir=base_dir, regime=regime)
    else:
        raise ValueError(
            fmt(
                _MODULE,
                "base_dir or output_layout required",
                "non-null base_dir or output_layout",
                f"base_dir={base_dir}, output_layout={output_layout}",
            )
        )

    cell = TrainingCellId(regime=regime, seed=seed, alpha=alpha)
    return run_fl_simulation(
        cfg,
        client_data,
        seed,
        alpha,
        model_cls=Autoencoder,
        ckpt_dir=layout.checkpoint_dir(cell),
        score_base=layout.score_cell(ScoreCellId(cell=cell)).score_dir,
        label="FL",
        prepared_dir=prepared_dir,
    )
