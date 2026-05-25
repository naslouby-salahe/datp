"""Reusable execution wrappers for analysis entry points."""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from pathlib import Path
from typing import Any, TypeVar, cast

from datp.config.compose import compose_analysis_config
from datp.config.models import DatpConfig

_R = TypeVar("_R")


def analysis_runner(
    writer_func: Callable[[Any, Path], object] | None = None,
) -> Callable[[Callable[..., _R]], Callable[..., _R]]:
    """Resolve config/base_dir and optionally call ``writer_func``."""

    def decorator(func: Callable[..., _R]) -> Callable[..., _R]:
        @wraps(func)
        def wrapper(
            base_dir: Path,
            *,
            config: DatpConfig | None = None,
            write_outputs: bool = False,
            **kwargs: Any,
        ) -> _R:
            cfg = config if config is not None else compose_analysis_config()
            resolved_dir = base_dir.resolve()
            result = func(resolved_dir, config=cfg, **kwargs)
            if write_outputs and writer_func is not None:
                writer_func(result, resolved_dir)
            return result

        return cast(Callable[..., _R], wrapper)

    return decorator
