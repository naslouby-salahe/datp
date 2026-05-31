from __future__ import annotations

import torch

from datp.core.errors import fmt

_MODULE = "core.device"


def resolve_device(require_cuda: bool) -> torch.device:
    """Resolve training device based on config policy.

    When *require_cuda* is ``True``, checks CUDA availability and fails if missing.
    When *require_cuda* is ``False``, returns CPU unconditionally.
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
