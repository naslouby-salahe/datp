# SPDX-License-Identifier: Proprietary
"""FedProx stress-test runner: trains with proximal term across µ grid.

FedProx is a locked stress test — it is never added to the Baseline enum.
µ=0.0 must match FedAvg within tolerance.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import torch
from flwr.client import Client
from flwr.common import Context, ndarrays_to_parameters
from flwr.server import ServerConfig
from flwr.simulation import start_simulation

from datp.artifacts.constants import MODEL_CHECKPOINT
from datp.baselines.common.data_loading import (
    ALL_SPLITS,
    load_client_data,
    load_single_client_training_data,
)
from datp.config.models import DatpConfig
from datp.core.device import get_device
from datp.core.seeds import set_seeds
from datp.core.logging import get_logger
from datp.data.regimes.catalog import dataset_for_regime
from datp.models.autoencoder import Autoencoder
from datp.training.fl.client import get_parameters, set_parameters
from datp.training.fl.convergence import ConvergenceMonitor
from datp.training.fl.fedprox import DatpFedProxClient
from datp.training.fl.scoring import ClientData, score_clients
from datp.training.fl.strategy import DatpFedAvg

logger = get_logger(__name__)


@dataclass(slots=True)
class FedProxResult:
    mu: float
    seed: int
    converged_round: int | None
    total_rounds: int
    checkpoint_dir: Path
    score_dir: Path
    loss_history: list[float] = field(default_factory=list)


def _build_model(cfg: DatpConfig) -> Autoencoder:
    return Autoencoder(
        input_dim=cfg.model.input_dim,
        hidden_dims=cfg.model.encoder_dims,
        activation=cfg.model.activation,
        use_bn=cfg.model.use_bn,
    )


def _make_client_fn(
    client_data: dict[str, ClientData],
    client_ids: list[str],
    cfg: DatpConfig,
    device: torch.device,
    mu: float,
    prepared_dir: Path | None,
) -> Callable[[Context], Client]:
    if prepared_dir is not None:
        client_dir_map = {
            d.name: d
            for d in (
                sorted(
                    d
                    for d in prepared_dir.iterdir()
                    if d.is_dir()
                )
            )
        }

        def client_fn(context: Context) -> Client:
            idx = int(context.node_config["partition-id"])
            client_id = client_ids[idx]
            train_t, cal_t = load_single_client_training_data(
                client_dir_map[client_id], device
            )
            model = _build_model(cfg)
            model.to(device)
            return DatpFedProxClient(
                cid=client_id,
                model=model,
                train_data=train_t,
                val_data=cal_t,
                cfg=cfg,
                mu=mu,
            ).to_client()

        return client_fn

    def client_fn(context: Context) -> Client:
        idx = int(context.node_config["partition-id"])
        client_id = client_ids[idx]
        splits = client_data[client_id]
        model = _build_model(cfg)
        model.to(device)
        return DatpFedProxClient(
            cid=client_id,
            model=model,
            train_data=splits.train.to(device, non_blocking=True),
            val_data=splits.val.to(device, non_blocking=True),
            cfg=cfg,
            mu=mu,
        ).to_client()

    return client_fn


def run_fedprox_training(
    cfg: DatpConfig,
    client_data: dict[str, ClientData],
    seed: int,
    mu: float,
    *,
    base_dir: Path,
    prepared_dir: Path | None = None,
) -> FedProxResult:
    """Run FedProx training with proximal term coefficient mu for one seed."""
    from datp import configure_runtime_env
    from datp.training.fl.resources import (
        derive_max_concurrent,
        ensure_ray_memory_threshold,
        get_available_ram_gb,
    )

    import math
    import os
    import ray

    regime = cfg.regime
    if regime is None:
        raise ValueError("regime must be set in config")

    device = get_device()
    set_seeds(seed)

    rounds_max = cfg.federation.convergence.rounds_max
    client_ids = sorted(client_data.keys())
    num_clients = len(client_ids)

    if num_clients == 0:
        raise ValueError("No clients provided")

    model = _build_model(cfg)
    model.to(device)
    initial_params = get_parameters(model)
    initial_parameters = ndarrays_to_parameters(initial_params)

    monitor = ConvergenceMonitor.from_config(cfg)
    strategy = DatpFedAvg(
        convergence_monitor=monitor,
        round_timeout_s=cfg.federation.convergence.round_timeout_s,
        fraction_fit=1.0,
        fraction_evaluate=1.0,
        min_fit_clients=num_clients,
        min_evaluate_clients=num_clients,
        min_available_clients=num_clients,
        initial_parameters=initial_parameters,
    )

    ckpt_dir = base_dir / "fedprox" / f"mu_{mu:g}" / f"seed_{seed}"
    ckpt_dir.mkdir(parents=True, exist_ok=True)

    configure_runtime_env()
    ensure_ray_memory_threshold(cfg.runtime.ray_memory_threshold)

    available_ram_gb = get_available_ram_gb()
    if cfg.machine.max_concurrent_override is not None:
        max_concurrent = cfg.machine.max_concurrent_override
    else:
        max_concurrent = derive_max_concurrent(
            available_ram_gb,
            per_client_ram_gb=cfg.machine.per_client_ram_gb,
            reserve_gb=cfg.machine.reserve_ram_gb,
        )
    cpu_count = os.cpu_count()
    if cpu_count is None:
        raise RuntimeError("Cannot determine CPU count")
    available_cpus = max(cpu_count, 1)
    num_cpus_per_actor = max(1, math.ceil(available_cpus / max_concurrent))

    client_resources = {"num_cpus": float(num_cpus_per_actor), "num_gpus": 0.0}

    logger.info(
        "starting FedProx training",
        mu=mu,
        seed=seed,
        n_clients=num_clients,
    )

    client_fn = _make_client_fn(
        client_data,
        client_ids,
        cfg,
        device,
        mu,
        prepared_dir=prepared_dir,
    )

    _object_store_bytes = cfg.machine.ray_object_store_mb * 1024 * 1024
    try:
        start_simulation(
            client_fn=client_fn,
            num_clients=num_clients,
            config=ServerConfig(num_rounds=rounds_max),
            strategy=strategy,
            client_resources=client_resources,
            ray_init_args={"object_store_memory": _object_store_bytes},
        )
    finally:
        ray.shutdown()

    converged_round = monitor.converged_round
    total_rounds = monitor.num_recorded

    final_params = strategy.latest_parameters
    if final_params is not None:
        set_parameters(model, final_params)

    import torch as _torch

    ckpt_file = ckpt_dir / MODEL_CHECKPOINT
    tmp_file = ckpt_file.with_suffix(".pt.tmp")
    _torch.save(model.state_dict(), tmp_file)
    tmp_file.rename(ckpt_file)

    # Score stage: reload full splits from disk.
    if prepared_dir is not None:
        scoring_data = load_client_data(
            prepared_dir, device=torch.device("cpu"), splits=ALL_SPLITS
        )
    else:
        scoring_data = client_data

    score_base = ckpt_dir / "scores"
    score_clients(
        model=model,
        client_data=scoring_data,
        score_base=score_base,
        regime=regime,
        seed=seed,
        alpha=None,
        dataset=dataset_for_regime(regime).value,
        checkpoint_path=ckpt_file,
    )

    logger.info(
        "FedProx training complete",
        mu=mu,
        seed=seed,
        total_rounds=total_rounds,
        converged_round=converged_round,
    )

    return FedProxResult(
        mu=mu,
        seed=seed,
        converged_round=converged_round,
        total_rounds=total_rounds,
        checkpoint_dir=ckpt_dir,
        score_dir=score_base,
        loss_history=monitor.loss_history,
    )
