# SPDX-License-Identifier: Proprietary
"""Ray runtime configuration: memory thresholds, resource derivation, RAM detection, device policy."""

from __future__ import annotations

import math
import os
from pathlib import Path

import torch

from datp.core.errors import fmt

_MODULE = "training.runtime"
_BYTES_PER_GIB = 1024**3
_KIB_PER_GIB = 1024**2
_MEMINFO_PATH = Path("/proc/meminfo")
_RAY_MEMORY_ENV_KEY = "RAY_memory_usage_threshold"


def ensure_ray_memory_threshold(threshold: float) -> None:
    current = os.environ.get(_RAY_MEMORY_ENV_KEY)
    if current is None:
        os.environ[_RAY_MEMORY_ENV_KEY] = str(threshold)
        return
    try:
        val = float(current)
    except ValueError as exc:
        raise RuntimeError(
            fmt(
                _MODULE,
                f"{_RAY_MEMORY_ENV_KEY} is not a valid float",
                f"<= {threshold}",
                repr(current),
            )
        ) from exc
    if val > threshold:
        raise RuntimeError(
            fmt(_MODULE, f"{_RAY_MEMORY_ENV_KEY} too high", f"<= {threshold}", str(val))
        )


def derive_max_concurrent(
    available_ram_gb: float,
    per_client_ram_gb: float,
    reserve_gb: float,
) -> int:
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
        fmt(
            _MODULE,
            "Cannot determine available RAM",
            "psutil installed or Linux /proc/meminfo readable",
            "neither available",
        )
    )


def resolve_device(require_cuda: bool) -> torch.device:
    """Resolve training device based on config policy.

    When require_cuda is True, checks CUDA availability and fails if missing.
    When require_cuda is False, returns CPU unconditionally.
    """
    if require_cuda:
        if not torch.cuda.is_available():
            raise RuntimeError(
                fmt(
                    _MODULE,
                    "CUDA required by config but not available",
                    "torch.cuda.is_available() == True",
                    "torch.cuda.is_available() == False",
                )
            )
        return torch.device("cuda")
    return torch.device("cpu")


def derive_client_resources(
    per_client_ram_gb: float,
    reserve_ram_gb: float,
    max_concurrent_override: int | None,
    ray_object_store_mb: int,
    require_cuda: bool,
    ray_num_gpus_per_client: float,
) -> dict[str, float]:
    """Derive Ray actor resource dict from machine config.

    GPU allocation:
      - When require_cuda is True: num_gpus = ray_num_gpus_per_client.
      - When require_cuda is False: num_gpus = 0.0 and actors use CPU only.
    """
    available_ram_gb = get_available_ram_gb()
    if max_concurrent_override is not None:
        max_concurrent = max_concurrent_override
    else:
        max_concurrent = derive_max_concurrent(
            available_ram_gb,
            per_client_ram_gb=per_client_ram_gb,
            reserve_gb=reserve_ram_gb,
        )
    cpu_count = os.cpu_count()
    if cpu_count is None:
        raise RuntimeError(
            fmt(
                _MODULE,
                "Cannot determine CPU count",
                "os.cpu_count() returns int",
                "None",
            )
        )
    available_cpus = max(cpu_count, 1)
    num_cpus_per_actor = max(1, math.ceil(available_cpus / max_concurrent))

    num_gpus = ray_num_gpus_per_client if require_cuda else 0.0
    return {
        "num_cpus": float(num_cpus_per_actor),
        "num_gpus": num_gpus,
    }
