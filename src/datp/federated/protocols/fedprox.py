# SPDX-License-Identifier: Proprietary
"""FedProx stress-test: client with proximal term + runner.

FedProx is a locked aggregation-side stress test, not a core baseline.
It is never added to the Baseline enum.
µ=0.0 must match FedAvg within tolerance.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import torch

from flwr.common import Parameters

from datp.artifacts.directories import SCORES_DIR
from datp.config.models import DatpConfig
from datp.core.identity import format_alpha_dir
from datp.modeling.autoencoder import Autoencoder
from datp.federated.clients import DatpClient
from datp.federated.local_training import train_local
from datp.federated.parameters import get_parameters, set_parameters
from datp.federated.simulation import SimClientConfig, TrainingResult, run_fl_simulation
from datp.federated.strategies import DatpFedAvg
from datp.federated.types import ClientData


class DatpFedProxClient(DatpClient):
    """FedProx client: adds proximal term (µ/2)||w - w_global||² to local loss."""

    def __init__(
        self,
        cid: str,
        model: Autoencoder,
        train_data: torch.Tensor,
        val_data: torch.Tensor,
        cfg: DatpConfig,
        mu: float,
    ) -> None:
        super().__init__(cid, model, train_data, val_data, cfg)
        self._mu = mu

    def fit(
        self,
        parameters: list[np.ndarray],
        config: dict[str, Any],  # noqa: ARG002
    ) -> tuple[list[np.ndarray], int, dict[str, Any]]:
        set_parameters(self.model, parameters)
        self.model.train()

        global_params = [p.detach().clone() for p in self.model.parameters()]

        last_loss = train_local(
            self.model,
            self.train_data,
            epochs=self._local_epochs,
            batch_size=self._batch_size,
            lr=self._lr,
            mu=self._mu,
            global_params=global_params,
        )

        return (
            get_parameters(self.model),
            len(self.train_data),
            {"train_loss": last_loss},
        )


def run_fedprox_training(
    cfg: DatpConfig,
    client_data: dict[str, ClientData] | None,
    seed: int,
    mu: float,
    *,
    alpha: float | None = None,
    base_dir: Path,
    prepared_dir: Path | None = None,
) -> TrainingResult:
    """Run FedProx training with proximal term coefficient mu for one seed."""
    from datp.core.errors import fmt as _fmt

    regime = cfg.regime
    if regime is None:
        raise ValueError(
            _fmt(
                "training.protocols.fedprox",
                "regime must be set in config",
                "non-null regime",
                repr(regime),
            )
        )

    def _build_strategy(initial_parameters: Parameters, num_clients: int) -> DatpFedAvg:
        return DatpFedAvg.from_config(
            cfg, initial_parameters=initial_parameters, num_clients=num_clients
        )

    ckpt_base = base_dir / "fedprox" / regime.value / f"mu_{mu:g}"
    if alpha is not None:
        ckpt_base = ckpt_base / format_alpha_dir(alpha)
    ckpt_dir = ckpt_base / f"seed_{seed}"
    score_base = ckpt_dir / SCORES_DIR

    return run_fl_simulation(
        cfg,
        client_data,
        seed,
        alpha,
        model_cls=Autoencoder,
        build_strategy=_build_strategy,
        ckpt_dir=ckpt_dir,
        score_base=score_base,
        label=f"FedProx(mu={mu:g})",
        prepared_dir=prepared_dir,
        client_config=SimClientConfig(
            client_cls=DatpFedProxClient,
            client_extra_kwargs={"mu": mu},
        ),
    )
