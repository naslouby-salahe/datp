from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import torch
from filelock import FileLock, Timeout

from datp.artifacts.constants import MODEL_CHECKPOINT
from datp.artifacts.paths import ExperimentLocator
from datp.core.errors import fmt
from datp.core.logging import get_logger
from datp.pipeline.enums import SweepStep
from datp.pipeline.models import PipelineRequest

logger = get_logger(__name__)
_MODULE = "pipeline.training"


def train_once_guard(
    checkpoint_file: Path,
    event: str,
    train_fn: Callable[[], None],
    *,
    lock_timeout: float,
    **log_fields: Any,
) -> None:
    checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
    lock_path = checkpoint_file.parent / ".train.lock"

    try:
        lock = FileLock(str(lock_path), timeout=lock_timeout)
    except OSError as exc:  # pragma: no cover
        raise RuntimeError(
            fmt(_MODULE, "Cannot create file lock", str(lock_path), str(exc))
        ) from exc

    try:
        with lock:
            if checkpoint_file.exists():
                logger.info(
                    "train_skip",
                    experiment=event,
                    checkpoint=str(checkpoint_file),
                    **log_fields,
                )
                return

            logger.info(
                "train_start",
                experiment=event,
                checkpoint=str(checkpoint_file),
                **log_fields,
            )
            train_fn()
    except Timeout as exc:  # pragma: no cover
        raise RuntimeError(
            fmt(
                _MODULE,
                f"Timed out waiting for checkpoint lock after {lock_timeout:.0f}s",
                "lock acquired",
                str(lock_path),
            )
        ) from exc


def ensure_fl_checkpoint(
    request: PipelineRequest,
    *,
    step_fn: Callable[[SweepStep, str], None] | None,
    checkpoint_status_fn: Callable[[bool, Path], None] | None,
    lock_timeout: float,
) -> None:
    """Run FL training iff the shared checkpoint is missing; holds a per-checkpoint-directory file lock to prevent duplicate training across parallel sweep processes."""
    key = request.key
    ckpt_dir = ExperimentLocator.for_main(request.base_dir, key.regime).checkpoint(
        key.seed, key.alpha
    )
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    ckpt_file = ckpt_dir / MODEL_CHECKPOINT

    alpha_label = f" alpha={key.alpha:g}" if key.alpha is not None else ""
    label = f"regime={key.regime} seed={key.seed}{alpha_label}"

    if step_fn is not None:
        step_fn(SweepStep.CHECK_CHECKPOINT, label)

    lock_path = ckpt_dir / ".train.lock"
    try:
        lock = FileLock(str(lock_path), timeout=lock_timeout)
    except OSError as exc:  # pragma: no cover
        raise RuntimeError(
            fmt(_MODULE, "Cannot create file lock", str(lock_path), str(exc))
        ) from exc

    try:
        with lock:
            _ensure_fl_checkpoint_locked(
                request=request,
                ckpt_dir=ckpt_dir,
                ckpt_file=ckpt_file,
                label=label,
                step_fn=step_fn,
                checkpoint_status_fn=checkpoint_status_fn,
            )
    except Timeout:  # pragma: no cover
        raise RuntimeError(
            fmt(
                _MODULE,
                f"Timed out waiting for checkpoint lock after {lock_timeout:.0f}s",
                "lock acquired",
                str(lock_path),
            )
        )


def _ensure_fl_checkpoint_locked(
    *,
    request: PipelineRequest,
    ckpt_dir: Path,
    ckpt_file: Path,
    label: str,
    step_fn: Callable[[SweepStep, str], None] | None,
    checkpoint_status_fn: Callable[[bool, Path], None] | None,
) -> None:
    from datp.baselines.common.data_loading import (
        ALL_SPLITS,
        TRAINING_SPLITS,
        load_client_data,
    )
    from datp.training.protocols.fedavg import run_fl_training

    key = request.key

    if checkpoint_status_fn is not None:
        checkpoint_status_fn(ckpt_file.exists(), ckpt_file)

    if ckpt_file.exists():
        from datp.training.scoring import (
            load_model_from_checkpoint,
            score_clients,
            validate_scoring_manifest,
        )

        loc = ExperimentLocator.for_main(request.base_dir, key.regime)
        score_base = loc.score(key.seed, key.alpha)
        try:
            validate_scoring_manifest(score_base)
            logger.info(
                "checkpoint exists, skipping training",
                regime=key.regime,
                seed=key.seed,
                alpha=key.alpha,
            )
            return
        except (FileNotFoundError, ValueError):
            pass
        # Checkpoint exists but scoring was interrupted — run scoring only.
        logger.info(
            "checkpoint exists but scoring incomplete; running score-only recovery",
            regime=key.regime,
            seed=key.seed,
            alpha=key.alpha,
        )
        scoring_data = load_client_data(
            request.prepared_dir, device=torch.device("cpu"), splits=ALL_SPLITS
        )
        model = load_model_from_checkpoint(request.cfg, ckpt_dir=ckpt_dir, require_cuda=request.cfg.machine.require_cuda)
        from datp.data.regimes.catalog import dataset_for_regime

        score_clients(
            model=model,
            client_data=scoring_data,
            score_base=score_base,
            regime=key.regime,
            seed=key.seed,
            alpha=key.alpha,
            dataset=dataset_for_regime(key.regime).value,
            checkpoint_path=ckpt_file,
        )
        return

    if step_fn is not None:
        step_fn(SweepStep.TRAIN_FL, label)

    client_data = load_client_data(
        request.prepared_dir, device=torch.device("cpu"), splits=TRAINING_SPLITS
    )
    run_fl_training(
        request.cfg,
        client_data,
        key.seed,
        key.alpha,
        base_dir=request.base_dir,
        prepared_dir=request.prepared_dir,
        output_locator=None,
    )
