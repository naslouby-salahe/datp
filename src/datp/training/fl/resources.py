# SPDX-License-Identifier: Proprietary
from __future__ import annotations

import math
import os
from pathlib import Path

from datp.core.errors import fmt

_MODULE = "training.fl.resources"
_BYTES_PER_GIB = 1024 ** 3
_KIB_PER_GIB = 1024 ** 2
_MEMINFO_PATH = Path("/proc/meminfo")
_RAY_MEMORY_ENV_KEY = "RAY_memory_usage_threshold"


def get_ray_memory_threshold(threshold: float) -> float:
    return threshold


def ensure_ray_memory_threshold(threshold: float) -> None:
    """Sets RAY_memory_usage_threshold env var if unset; raises if already set above threshold."""
    current = os.environ.get(_RAY_MEMORY_ENV_KEY)
    if current is None:
        os.environ[_RAY_MEMORY_ENV_KEY] = str(threshold)
        return
    try:
        val = float(current)
    except ValueError as exc:
        raise RuntimeError(
            fmt(_MODULE, f"{_RAY_MEMORY_ENV_KEY} is not a valid float",
                f"<= {threshold}", repr(current))
        ) from exc
    if val > threshold:
        raise RuntimeError(
            fmt(_MODULE, f"{_RAY_MEMORY_ENV_KEY} too high",
                f"<= {threshold}", str(val))
        )


def derive_max_concurrent(
    available_ram_gb: float,
    per_client_ram_gb: float,
    reserve_gb: float,
) -> int:
    """Derive ``max_concurrent`` from available RAM: ``max(1, floor((available_ram_gb - reserve_gb) / per_client_ram_gb))``."""
    if per_client_ram_gb <= 0:
        raise ValueError(
            fmt(_MODULE, "per_client_ram_gb must be > 0", "> 0", str(per_client_ram_gb))
        )
    usable = available_ram_gb - reserve_gb
    return max(1, math.floor(usable / per_client_ram_gb))


def _read_meminfo_gib() -> float | None:
    try:
        with _MEMINFO_PATH.open() as f:
            for line in f:
                if line.startswith("MemAvailable:"):
                    kb = int(line.split()[1])
                    return kb / _KIB_PER_GIB
    except (OSError, ValueError, IndexError):
        return None
    return None


def get_available_ram_gb() -> float:
    try:
        import psutil  # type: ignore[import-untyped]
    except ImportError:
        psutil = None
    if psutil is not None:
        return psutil.virtual_memory().available / _BYTES_PER_GIB
    from_proc = _read_meminfo_gib()
    if from_proc is not None:
        return from_proc
    raise RuntimeError(
        fmt(_MODULE, "Cannot determine available RAM",
            "psutil installed or Linux /proc/meminfo readable", "neither available")
    )
