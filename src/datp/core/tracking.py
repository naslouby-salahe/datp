from __future__ import annotations

import contextlib
import math
from pathlib import Path
from typing import Any, Generator

from datp.core.logging import get_logger

logger = get_logger(__name__)

_TRACKING_ENABLED = False
_MLFLOW: Any | None = None


def _import_mlflow() -> Any | None:
    global _MLFLOW  # noqa: PLW0603
    if _MLFLOW is not None:
        return _MLFLOW
    try:
        import mlflow
    except ImportError:
        return None
    _MLFLOW = mlflow
    return mlflow


def is_tracking_enabled() -> bool:
    return _TRACKING_ENABLED


def init_tracking(
    *,
    experiment_name: str,
    tracking_uri: str,
) -> None:
    global _TRACKING_ENABLED  # noqa: PLW0603

    mlflow = _import_mlflow()
    if mlflow is None:
        _TRACKING_ENABLED = False
        logger.debug("mlflow unavailable; tracking disabled")
        return

    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(experiment_name)
    _TRACKING_ENABLED = True
    logger.info(
        "tracking initialized",
        experiment_name=experiment_name,
        tracking_uri=tracking_uri,
    )


@contextlib.contextmanager
def tracking_run(
    *,
    run_name: str,
    params: dict[str, Any] | None,
    tags: dict[str, Any] | None,
    nested: bool | None,
) -> Generator[Any, None, None]:
    if not _TRACKING_ENABLED:
        yield None
        return

    mlflow = _import_mlflow()
    if mlflow is None:
        yield None
        return

    resolved_nested = mlflow.active_run() is not None if nested is None else nested
    with mlflow.start_run(run_name=run_name, nested=resolved_nested) as run:
        if tags:
            mlflow.set_tags({key: str(value) for key, value in tags.items()})
        if params:
            log_params(params)
        yield run


def log_metrics(
    metrics: dict[str, float | int],
    *,
    step: int | None,
    prefix: str | None,
) -> None:
    if not _TRACKING_ENABLED:
        return
    mlflow = _import_mlflow()
    if mlflow is None:
        return

    payload: dict[str, float] = {}
    for key, value in metrics.items():
        if not isinstance(value, (int, float)):
            continue
        numeric_value = float(value)
        if not math.isfinite(numeric_value):
            continue
        metric_key = f"{prefix}.{key}" if prefix else key
        payload[metric_key] = numeric_value

    if payload:
        mlflow.log_metrics(payload, step=step)


def log_param(key: str, value: Any) -> None:
    if not _TRACKING_ENABLED:
        return
    mlflow = _import_mlflow()
    if mlflow is None:
        return
    mlflow.log_param(key, str(value))


def log_params(params: dict[str, Any]) -> None:
    if not _TRACKING_ENABLED:
        return
    mlflow = _import_mlflow()
    if mlflow is None:
        return
    mlflow.log_params({key: str(value) for key, value in params.items()})


def set_tags(tags: dict[str, Any]) -> None:
    if not _TRACKING_ENABLED:
        return
    mlflow = _import_mlflow()
    if mlflow is None:
        return
    mlflow.set_tags({key: str(value) for key, value in tags.items()})


def log_artifact(
    path: str | Path,
    *,
    artifact_path: str | None,
) -> None:
    if not _TRACKING_ENABLED:
        return
    mlflow = _import_mlflow()
    if mlflow is None:
        return
    mlflow.log_artifact(str(path), artifact_path=artifact_path)


def log_dict(
    payload: dict[str, Any] | list[Any],
    artifact_file: str | Path,
) -> None:
    if not _TRACKING_ENABLED:
        return
    mlflow = _import_mlflow()
    if mlflow is None:
        return
    mlflow.log_dict(payload, str(artifact_file))
