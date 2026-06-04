# SPDX-License-Identifier: Proprietary
"""Shared FL simulation orchestration — train once per (regime, seed, α); score artifacts produced afterward."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import torch
import torch.nn as nn
from typing import cast

from flwr.client import Client, ClientApp
from flwr.common import Context, Parameters, ndarrays_to_parameters
from flwr.common.telemetry import EventType
from flwr.server import ServerApp, ServerConfig
from flwr.server.serverapp_components import ServerAppComponents
from flwr.simulation.run_simulation import BackendConfig, _run_simulation

from datp import configure_runtime_env
from datp.artifacts.lifecycle import RunLifecycle
from datp.artifacts.names import ArtifactFile
from datp.federated.data_loading import (
    ALL_SPLITS,
    load_client_data,
)
from datp.config.models import DatpConfig
from datp.core.enums import DeviceType, Regime
from datp.core.errors import fmt
from datp.core.logging import get_logger
from datp.core.seeds import set_seeds
from datp.core.tracking import log_artifact, log_metrics, log_params
from datp.data.regimes.catalog import dataset_for_regime
from datp.modeling.autoencoder import Autoencoder
from datp.federated.catalog import TrainingClientCatalog
from datp.federated.checkpoints import (
    ConvergenceSnapshot,
    save_checkpoint,
    save_convergence_artifacts,
)
from datp.federated.clients import DatpClient
from datp.federated.convergence import ConvergenceMonitor
from datp.federated.factories import build_model, make_client_fn
from datp.federated.parameters import get_parameters, set_parameters
from datp.core.device import resolve_device
from datp.federated.runtime import (
    derive_client_resources,
    ensure_ray_memory_threshold,
)
from datp.scoring.generation import score_clients
from datp.federated.strategies import DatpFedAvg
from datp.federated.types import ClientData

logger = get_logger(__name__)

_MODULE = "training.simulation"


@dataclass(frozen=True, slots=True)
class SimClientConfig:
    """Per-simulation client and scoring options.

    Groups the four optional client-override parameters so run_fl_simulation
    stays within the 13-argument quality limit.
    """

    client_cls: type[DatpClient] = DatpClient
    client_extra_kwargs: dict[str, object] | None = None
    encoder_only: bool = False
    score_after: bool = True


@dataclass(frozen=True, slots=True)
class TrainingResult:
    regime: Regime
    seed: int
    alpha: float | None
    converged_round: int | None
    total_rounds: int
    checkpoint_dir: Path
    score_dir: Path
    loss_history: list[float]


def validate_regime(cfg: DatpConfig) -> Regime:
    regime = cfg.regime
    if regime is None:
        raise ValueError(
            fmt(
                _MODULE, "regime must be set in config", "non-null regime", repr(regime)
            )
        )
    return regime


def _init_model_and_params(
    cfg: DatpConfig,
    model_cls: type[Autoencoder],
    device: torch.device,
    encoder_only: bool,
) -> tuple[Autoencoder, nn.Module, Parameters]:
    """Build model on device; return (model, param_module, initial_parameters).

    param_module is model.encoder when encoder_only=True (FedRep), else the full model.
    """
    model = build_model(cfg, model_cls)
    model.to(device)
    param_module: nn.Module = model.encoder if encoder_only else model
    return model, param_module, ndarrays_to_parameters(get_parameters(param_module))


def _execute_flower_simulation(
    cfg: DatpConfig,
    client_fn: Callable[[Context], Client],
    num_clients: int,
    strategy: DatpFedAvg | None,
    label: str,
) -> None:
    """Configure Ray, run Flower simulation; Ray lifecycle managed by the backend."""
    configure_runtime_env()
    ensure_ray_memory_threshold(cfg.runtime.ray_memory_threshold)
    client_resources = derive_client_resources(
        per_client_ram_gb=cfg.machine.per_client_ram_gb,
        reserve_ram_gb=cfg.machine.reserve_ram_gb,
        max_concurrent_override=cfg.machine.max_concurrent_override,
        require_cuda=cfg.machine.require_cuda,
        ray_num_gpus_per_client=cfg.machine.ray_num_gpus_per_client,
    )
    object_store_bytes = cfg.machine.ray_object_store_mb * 1024 * 1024
    num_rounds = cfg.federation.convergence.rounds_max
    round_timeout = cfg.federation.convergence.round_timeout_s

    def server_fn(_: Context) -> ServerAppComponents:
        return ServerAppComponents(
            strategy=strategy,
            config=ServerConfig(num_rounds=num_rounds, round_timeout=round_timeout),
        )

    _run_simulation(
        num_supernodes=num_clients,
        client_app=ClientApp(client_fn=client_fn),
        server_app=ServerApp(server_fn=server_fn),
        backend_config=cast(BackendConfig, {
            "init_args": {"object_store_memory": object_store_bytes},
            "client_resources": client_resources,
        }),
        exit_event=EventType.PYTHON_API_RUN_SIMULATION_LEAVE,
    )
    logger.info("ray shutdown after FL simulation", label=label)


def _save_training_artifacts(
    model: nn.Module,
    param_module: nn.Module,
    strategy: DatpFedAvg,
    ckpt_dir: Path,
    monitor: ConvergenceMonitor,
    cfg: DatpConfig,
    lifecycle: RunLifecycle,
    total_rounds: int,
) -> None:
    """Restore aggregated parameters, save checkpoint and convergence artifacts."""
    final_params = strategy.latest_parameters
    if final_params is None:
        raise RuntimeError(
            fmt(
                _MODULE,
                "Final aggregated parameters unavailable after FL simulation — "
                "cannot save checkpoint from untrained/initial model",
                "non-null strategy.latest_parameters",
                "None",
            )
        )
    set_parameters(param_module, final_params)

    save_checkpoint(model, ckpt_dir)
    save_convergence_artifacts(
        ckpt_dir,
        ConvergenceSnapshot(
            loss_history=monitor.loss_history,
            converged_round=monitor.converged_round,
            criterion_value=monitor.latest_relative_change,
        ),
        cfg.federation.convergence,
    )
    lifecycle.last_completed_round = total_rounds


def load_scoring_data(
    client_data: dict[str, ClientData] | None,
    prepared_dir: Path | None,
) -> dict[str, ClientData]:
    """Resolve scoring data: reload from disk when prepared_dir was used; otherwise return existing."""
    if prepared_dir is not None:
        return load_client_data(
            prepared_dir, device=torch.device(DeviceType.CPU), splits=ALL_SPLITS
        )
    if client_data:
        return client_data
    raise ValueError(
        fmt(_MODULE, "No scoring data source", "client_data or prepared_dir", "neither")
    )


def run_fl_simulation(
    cfg: DatpConfig,
    client_data: dict[str, ClientData] | None,
    seed: int,
    alpha: float | None,
    *,
    model_cls: type[Autoencoder],
    ckpt_dir: Path,
    score_base: Path,
    label: str,
    prepared_dir: Path | None = None,
    client_config: SimClientConfig = SimClientConfig(),
) -> TrainingResult:
    regime = validate_regime(cfg)

    catalog = TrainingClientCatalog(
        client_data=client_data,
        prepared_dir=prepared_dir,
    )

    if prepared_dir is not None:
        catalog.validate_prepared_splits()

    device = resolve_device(cfg.machine.require_cuda)
    set_seeds(seed)

    model, param_module, initial_parameters = _init_model_and_params(
        cfg, model_cls, device, client_config.encoder_only
    )

    client_ids = catalog.client_ids
    num_clients = catalog.num_clients
    logger.info(
        "starting FL training",
        label=label,
        regime=regime,
        seed=seed,
        alpha=alpha,
        n_clients=num_clients,
    )

    strategy = DatpFedAvg.from_config(
        cfg, initial_parameters=initial_parameters, num_clients=num_clients
    )
    monitor = strategy.convergence_monitor
    converged_round: int | None = None
    total_rounds = 0

    with RunLifecycle(ckpt_dir, seed=seed) as lifecycle:
        client_fn = make_client_fn(
            (client_data or {}) if prepared_dir is None else {},
            client_ids,
            cfg,
            device,
            prepared_dir=prepared_dir,
            model_cls=model_cls,
            client_cls=client_config.client_cls,
            extra_kwargs=client_config.client_extra_kwargs,
            seed=seed,
        )

        _execute_flower_simulation(cfg, client_fn, num_clients, strategy, label)

        total_rounds = monitor.num_recorded
        converged_round = monitor.converged_round
        logger.info(
            "FL training complete",
            label=label,
            total_rounds=total_rounds,
            converged_round=converged_round,
        )

        _save_training_artifacts(
            model,
            param_module,
            strategy,
            ckpt_dir,
            monitor,
            cfg,
            lifecycle,
            total_rounds,
        )

    if client_config.score_after:
        scoring_data = load_scoring_data(client_data, prepared_dir)
        score_clients(
            model=model,
            client_data=scoring_data,
            score_base=score_base,
            regime=regime,
            seed=seed,
            alpha=alpha,
            dataset=dataset_for_regime(regime),
            checkpoint_path=ckpt_dir / ArtifactFile.MODEL_CHECKPOINT,
            scoring_batch_size=cfg.machine.scoring_batch_size,
        )

    log_params({
        "regime": str(regime),
        "seed": str(seed),
        "rounds_max": str(cfg.federation.convergence.rounds_max),
        "label": label,
    })
    log_metrics(
        {
            "converged_round": float(converged_round)
            if converged_round is not None
            else float(total_rounds),
            "total_rounds": float(total_rounds),
        },
        step=None,
        prefix=None,
    )
    ckpt_file = ckpt_dir / ArtifactFile.MODEL_CHECKPOINT
    if ckpt_file.exists():
        log_artifact(ckpt_file, artifact_path=None)

    return TrainingResult(
        regime=regime,
        seed=seed,
        alpha=alpha,
        converged_round=converged_round,
        total_rounds=total_rounds,
        checkpoint_dir=ckpt_dir,
        score_dir=score_base,
        loss_history=monitor.loss_history,
    )
