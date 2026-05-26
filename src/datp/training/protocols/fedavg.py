# SPDX-License-Identifier: Proprietary
"""FedAvg protocol entry point: train AE via FedAvg and produce score artifacts."""

from __future__ import annotations

from pathlib import Path

from flwr.common import Parameters

from datp.artifacts.paths import ExperimentLocator
from datp.config.models import DatpConfig
from datp.core.errors import fmt
from datp.models.autoencoder import Autoencoder
from datp.training.simulation import TrainingResult, run_fl_simulation
from datp.training.strategies import DatpFedAvg
from datp.training.types import ClientData

_MODULE = "training.protocols.fedavg"


def run_fl_training(
    cfg: DatpConfig,
    client_data: dict[str, ClientData],
    seed: int,
    alpha: float | None = None,
    *,
    base_dir: Path | None = None,
    prepared_dir: Path | None = None,
    output_locator: ExperimentLocator | None = None,
) -> TrainingResult:
    """Train AE via FedAvg and produce score artifacts (main FL entry point)."""
    regime = cfg.regime
    if regime is None:
        raise ValueError(
            fmt(
                _MODULE, "regime must be set in config", "non-null regime", repr(regime)
            )
        )
    if base_dir is None and output_locator is None:
        raise ValueError(
            fmt(
                _MODULE,
                "base_dir or output_locator required",
                "non-null base_dir or output_locator",
                f"base_dir={base_dir}, output_locator={output_locator}",
            )
        )
    _base_dir: Path = base_dir if base_dir is not None else Path(".")

    def _build_strategy(initial_parameters: Parameters, num_clients: int) -> DatpFedAvg:
        return DatpFedAvg.from_config(
            cfg,
            initial_parameters=initial_parameters,
            num_clients=num_clients,
        )

    loc = (
        output_locator
        if output_locator is not None
        else ExperimentLocator.for_main(_base_dir, regime)
    )
    return run_fl_simulation(
        cfg,
        client_data,
        seed,
        alpha,
        model_cls=Autoencoder,
        build_strategy=_build_strategy,
        ckpt_dir=loc.checkpoint(seed, alpha),
        score_base=loc.score(seed, alpha),
        label="FL",
        prepared_dir=prepared_dir,
    )
