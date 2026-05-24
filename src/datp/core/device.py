from __future__ import annotations

import torch

from datp.core.errors import fmt


def get_device() -> torch.device:
    """Single enforcement point for the CUDA requirement; raises if CUDA is unavailable."""
    if not torch.cuda.is_available():
        raise RuntimeError(
            fmt(
                "device",
                "CUDA is required but not available",
                "torch.cuda.is_available() == True",
                "torch.cuda.is_available() == False",
            )
        )
    return torch.device("cuda")
