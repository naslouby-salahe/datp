# SPDX-License-Identifier: Proprietary
"""FedAvg protocol entry point: train AE via FedAvg and produce score artifacts."""

from __future__ import annotations

from pathlib import Path

from flwr.common import Parameters

from datp.artifacts.layout import ArtifactLayout
from datp.config.models import DatpConfig
from datp.core.errors import fmt
from datp.core.identity import ScoreCellId, TrainingCellId
from datp.modeling.autoencoder import Autoencoder
from datp.federated.simulation import TrainingResult, run_fl_simulation
from datp.federated.strategies import DatpFedAvg
from datp.federated.types import ClientData

_MODULE = "training.protocols.fedavg"


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
    regime = cfg.regime
    if regime is None:
        raise ValueError(
            fmt(
                _MODULE, "regime must be set in config", "non-null regime", repr(regime)
            )
        )
    if base_dir is None and output_layout is None:
        raise ValueError(
            fmt(
                _MODULE,
                "base_dir or output_layout required",
                "non-null base_dir or output_layout",
                f"base_dir={base_dir}, output_layout={output_layout}",
            )
        )
    _base_dir: Path = base_dir if base_dir is not None else Path(".")

    def _build_strategy(initial_parameters: Parameters, num_clients: int) -> DatpFedAvg:
        return DatpFedAvg.from_config(
            cfg,
            initial_parameters=initial_parameters,
            num_clients=num_clients,
        )

    layout = (
        output_layout
        if output_layout is not None
        else ArtifactLayout(base_dir=_base_dir, regime=regime)
    )
    cell = TrainingCellId(regime=regime, seed=seed, alpha=alpha)
    return run_fl_simulation(
        cfg,
        client_data,
        seed,
        alpha,
        model_cls=Autoencoder,
        build_strategy=_build_strategy,
        ckpt_dir=layout.checkpoint_dir(cell),
        score_base=layout.score_cell(ScoreCellId(cell=cell)).score_dir,
        label="FL",
        prepared_dir=prepared_dir,
    )
