# SPDX-License-Identifier: Proprietary
"""Canonical owner of FL parameter conversion between PyTorch and NumPy."""

from __future__ import annotations

import numpy as np
import torch
import torch.nn as nn

from datp.core.errors import fmt

_MODULE = "training.parameters"


def get_parameters(model: nn.Module) -> list[np.ndarray]:
    return [p.detach().cpu().numpy().copy() for p in model.parameters()]


def set_parameters(model: nn.Module, parameters: list[np.ndarray]) -> None:
    params_list = list(model.parameters())
    if len(params_list) != len(parameters):
        raise ValueError(
            fmt(
                _MODULE,
                "Parameter count mismatch",
                f"{len(params_list)} parameter tensors",
                f"{len(parameters)} arrays provided",
            )
        )
    with torch.no_grad():
        for i, (param, arr) in enumerate(zip(params_list, parameters, strict=True)):
            expected_shape = tuple(param.shape)
            actual_shape = tuple(arr.shape)
            if expected_shape != actual_shape:
                raise ValueError(
                    fmt(
                        _MODULE,
                        f"Shape mismatch at parameter index {i}",
                        f"shape={expected_shape}",
                        f"shape={actual_shape}",
                    )
                )
            tensor = torch.from_numpy(arr).to(dtype=param.dtype, device=param.device, non_blocking=True)
            param.copy_(tensor)
