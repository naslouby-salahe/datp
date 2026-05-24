# SPDX-License-Identifier: Proprietary
"""Train-once: encoder trains once per (regime, seed, α); score artifacts produced in a separate downstream stage."""

from __future__ import annotations

import json
import math
import os
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
import ray
import torch
import torch.nn as nn
from flwr.client import Client
from flwr.common import Context, ndarrays_to_parameters
from flwr.server import ServerConfig
from flwr.simulation import start_simulation

from datp import configure_runtime_env
from datp.artifacts.constants import (
    MODEL_CHECKPOINT,
    SCALER_FILE,
)
from datp.artifacts.markers import RunLifecycle
from datp.artifacts.paths import ExperimentLocator
from datp.baselines.common.data_loading import (
    ALL_SPLITS,
    discover_client_dirs,
    load_client_data,
    load_single_client_training_data,
)
from datp.config.models import DatpConfig
from datp.core.device import get_device
from datp.audit.enums import ConvergenceStatus
from datp.core.enums import (
    Regime,
)
from datp.core.errors import fmt
from datp.core.logging import get_logger
from datp.core.seeds import set_seeds
from datp.core.tracking import log_artifact, log_metrics, log_param
from datp.data.splits import Split, filename_for_split
from datp.data.regimes.catalog import dataset_for_regime
from datp.models.autoencoder import Autoencoder
from datp.training.fl.client import DatpClient, get_parameters, set_parameters
from datp.training.fl.resources import (
    derive_max_concurrent,
    ensure_ray_memory_threshold,
    get_available_ram_gb,
)
from datp.training.fl.scoring import ClientData, score_clients
from datp.training.fl.strategy import DatpFedAvg

logger = get_logger(__name__)

_MODULE = "fl.runner"
_NO_RAY_GPU = 0.0


@dataclass(slots=True)
class TrainingResult:
    regime: Regime
    seed: int
    alpha: float | None
    converged_round: int | None
    total_rounds: int
    checkpoint_dir: Path
    score_dir: Path
    loss_history: list[float] = field(default_factory=list)


def _build_model(cfg: DatpConfig, model_cls: type[Autoencoder]) -> Autoencoder:
    return model_cls(
        input_dim=cfg.model.input_dim,
        hidden_dims=cfg.model.encoder_dims,
        activation=cfg.model.activation,
        use_bn=cfg.model.use_bn,
    )


def _save_checkpoint(model: nn.Module, ckpt_dir: Path) -> Path:
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    ckpt_file = ckpt_dir / MODEL_CHECKPOINT

    tmp_file = ckpt_file.with_suffix(".pt.tmp")
    torch.save(model.state_dict(), tmp_file)
    tmp_file.rename(ckpt_file)

    logger.info("checkpoint saved", path=str(ckpt_file))
    return ckpt_file


def _save_convergence_artifacts(
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
    curve_path = ckpt_dir / "convergence_curve.csv"
    summary_path = ckpt_dir / "convergence_summary.json"
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
                "actual_rounds_run": len(loss_history),  # loss-recorded training rounds only; excludes empty Flower rounds after early stopping
                "convergence_round": converged_round,
                "convergence_criterion_value": criterion_value,
                "convergence_status": ConvergenceStatus.CONVERGED if converged_round is not None else ConvergenceStatus.NOT_CONVERGED,
                "weighted_validation_loss_per_round": loss_history,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def _validate_paths(prepared_dir: Path) -> None:
    required = tuple(filename_for_split(s) for s in Split) + (SCALER_FILE,)
    for client_dir in discover_client_dirs(prepared_dir):
        missing = [name for name in required if not (client_dir / name).exists()]
        if missing:
            raise FileNotFoundError(
                fmt(
                    _MODULE,
                    f"Missing prepared artifacts for {client_dir.name}",
                    ", ".join(required),
                    ", ".join(missing),
                )
            )
    logger.info("prepared artifact preflight passed", prepared_dir=str(prepared_dir))


def _make_client_fn(
    client_data: dict[str, ClientData],
    client_ids: list[str],
    cfg: DatpConfig,
    model_cls: type[Autoencoder],
    device: torch.device,
    prepared_dir: Path | None,
) -> Callable[[Context], Client]:
    """When prepared_dir is set, each Ray actor loads only its own client data from disk (reduces per-actor RAM)."""
    if prepared_dir is not None:
        client_dir_map: dict[str, Path] = {
            d.name: d for d in discover_client_dirs(prepared_dir)
        }

        def client_fn(context: Context) -> Client:
            idx = int(context.node_config["partition-id"])
            client_id = client_ids[idx]
            train_t, cal_t = load_single_client_training_data(
                client_dir_map[client_id], device,
            )
            model = _build_model(cfg, model_cls)
            model.to(device)
            return DatpClient(
                cid=client_id,
                model=model,
                train_data=train_t,
                val_data=cal_t,
                cfg=cfg,
            ).to_client()

        return client_fn

    def client_fn(context: Context) -> Client:
        idx = int(context.node_config["partition-id"])
        client_id = client_ids[idx]
        splits = client_data[client_id]
        model = _build_model(cfg, model_cls)
        model.to(device)
        return DatpClient(
            cid=client_id,
            model=model,
            train_data=splits.train.to(device, non_blocking=True),
            val_data=splits.val.to(device, non_blocking=True),
            cfg=cfg,
        ).to_client()

    return client_fn


def _run_fl_simulation(
    cfg: DatpConfig,
    client_data: dict[str, ClientData],
    seed: int,
    alpha: float | None,
    *,
    model_cls: type[Autoencoder],
    build_strategy: Callable[..., DatpFedAvg],
    ckpt_dir: Path,
    score_base: Path,
    label: str,
    prepared_dir: Path | None,
) -> TrainingResult:
    """When prepared_dir is set, the score stage reloads full splits from disk; test_attack is not held in RAM during training."""
    regime = cfg.regime
    assert regime is not None, "regime must be set in config"
    rounds_max = cfg.federation.convergence.rounds_max

    if prepared_dir is not None:
        _validate_paths(prepared_dir)

    device = get_device()

    set_seeds(seed)

    model = _build_model(cfg, model_cls)
    model.to(device)
    initial_params = get_parameters(model)
    initial_parameters = ndarrays_to_parameters(initial_params)

    client_ids = sorted(client_data.keys())
    num_clients = len(client_ids)
    if num_clients == 0:
        raise ValueError(
            fmt(_MODULE, "No clients provided", ">= 1 client", "0")
        )
    logger.info(
        "starting FL training",
        label=label, regime=regime, seed=seed, alpha=alpha, n_clients=num_clients,
    )

    strategy = build_strategy(initial_parameters, num_clients)
    monitor = strategy.convergence_monitor
    converged_round: int | None = None
    total_rounds = 0

    with RunLifecycle(ckpt_dir, seed=seed) as lifecycle:
        client_fn = _make_client_fn(
            client_data, client_ids, cfg, model_cls, device,
            prepared_dir=prepared_dir,
        )

        # Free main-process tensors before spawning Ray actors.
        if prepared_dir is not None:
            client_data.clear()

        # Allow Ray workers to access CUDA even with num_gpus=0 (default).
        # Without this, Ray overrides CUDA_VISIBLE_DEVICES="" and hides the GPU.
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
            raise RuntimeError(fmt(_MODULE, "Cannot determine CPU count", "os.cpu_count() returns int", "None"))
        available_cpus = max(cpu_count, 1)
        num_cpus_per_actor = max(1, math.ceil(available_cpus / max_concurrent))

        _num_gpus = _NO_RAY_GPU  # GPU shared via CUDA context, not via Ray allocation
        client_resources = {
            "num_cpus": float(num_cpus_per_actor),
            "num_gpus": _num_gpus,
        }
        logger.info(
            "derived FL client resources",
            available_ram_gb=available_ram_gb,
            max_concurrent=max_concurrent,
            available_cpus=available_cpus,
            num_cpus_per_actor=num_cpus_per_actor,
            per_client_ram_gb=cfg.machine.per_client_ram_gb,
            reserve_ram_gb=cfg.machine.reserve_ram_gb,
            ray_object_store_mb=cfg.machine.ray_object_store_mb,
        )

        # Object store sized per config; default 30% of RAM is too large for small numpy payloads.
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
            logger.info("ray shutdown after FL simulation", label=label)

        converged_round = monitor.converged_round
        total_rounds = monitor.num_recorded

        logger.info(
            "FL training complete",
            label=label, total_rounds=total_rounds, converged_round=converged_round,
        )

        final_params = strategy.latest_parameters
        if final_params is not None:
            set_parameters(model, final_params)
        else:
            logger.warning(
                "strategy latest_parameters unavailable after simulation",
                label=label,
            )

        _save_checkpoint(model, ckpt_dir)
        _save_convergence_artifacts(
            ckpt_dir,
            monitor.loss_history,
            converged_round,
            monitor.latest_relative_change,
            rounds_initial=cfg.federation.convergence.rounds_initial,
            rounds_max=cfg.federation.convergence.rounds_max,
            relative_threshold=cfg.federation.convergence.relative_threshold,
            window=cfg.federation.convergence.window,
        )
        lifecycle.last_completed_round = total_rounds

    # Score stage: reload full splits from disk if prepared_dir was used (training loaded partial splits).
    if prepared_dir is not None:
        scoring_data = load_client_data(prepared_dir, device=torch.device("cpu"), splits=ALL_SPLITS)
    else:
        scoring_data = client_data

    score_clients(
        model=model,
        client_data=scoring_data,
        score_base=score_base,
        regime=regime,
        seed=seed,
        alpha=alpha,
        dataset=dataset_for_regime(regime).value,
        checkpoint_path=ckpt_dir / MODEL_CHECKPOINT,
    )

    log_param("regime", regime)
    log_param("seed", seed)
    log_param("rounds_max", rounds_max)
    log_param("label", label)
    log_metrics({
        "converged_round": float(converged_round) if converged_round is not None else float(total_rounds),
        "total_rounds": float(total_rounds),
    }, step=None, prefix=None)
    ckpt_file = ckpt_dir / MODEL_CHECKPOINT
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


def run_fl_training(
    cfg,  # DatpConfig
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
    assert regime is not None, "regime must be set in config"
    assert base_dir is not None or output_locator is not None, "base_dir or output_locator required"
    _base_dir: Path = base_dir if base_dir is not None else Path(".")

    def _build_strategy(initial_parameters, num_clients):
        return DatpFedAvg.from_config(
            cfg,
            initial_parameters=initial_parameters,
            num_clients=num_clients,
            bn_param_indices=None,
        )

    loc = output_locator if output_locator is not None else ExperimentLocator.for_main(_base_dir, regime)
    return _run_fl_simulation(
        cfg, client_data, seed, alpha,
        model_cls=Autoencoder,
        build_strategy=_build_strategy,
        ckpt_dir=loc.checkpoint(seed, alpha),
        score_base=loc.score(seed, alpha),
        label="FL",
        prepared_dir=prepared_dir,
    )
