# SPDX-License-Identifier: Proprietary
from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F

from datp.modeling.activations import ACTIVATIONS


class Autoencoder(nn.Module):
    def __init__(
        self,
        input_dim: int,
        hidden_dims: list[int],
        activation: str,
        use_bn: bool,
    ) -> None:
        super().__init__()
        if not hidden_dims:
            raise ValueError("hidden_dims must be non-empty")
        act_key = activation.lower()
        if act_key not in ACTIVATIONS:
            raise ValueError(
                f"Unknown activation '{activation}'. Supported: {sorted(ACTIVATIONS)}"
            )
        act_cls = ACTIVATIONS[act_key]

        encoder_layers: list[nn.Module] = []
        dims = [input_dim, *hidden_dims]
        for i in range(len(dims) - 1):
            encoder_layers.append(nn.Linear(dims[i], dims[i + 1]))
            if use_bn:
                encoder_layers.append(nn.BatchNorm1d(dims[i + 1]))
            encoder_layers.append(act_cls())
        self.encoder = nn.Sequential(*encoder_layers)

        decoder_dims = list(reversed(dims))
        decoder_layers: list[nn.Module] = []
        for i in range(len(decoder_dims) - 1):
            decoder_layers.append(nn.Linear(decoder_dims[i], decoder_dims[i + 1]))
            if i < len(decoder_dims) - 2:
                if use_bn:
                    decoder_layers.append(nn.BatchNorm1d(decoder_dims[i + 1]))
                decoder_layers.append(act_cls())
            # No activation on the final layer — reconstruction error uses raw output.
        self.decoder = nn.Sequential(*decoder_layers)

        self._bottleneck_dim = hidden_dims[-1]

    @property
    def bottleneck_dim(self) -> int:
        return self._bottleneck_dim

    def encode(self, x: torch.Tensor) -> torch.Tensor:
        return self.encoder(x)

    def decode(self, z: torch.Tensor) -> torch.Tensor:
        return self.decoder(z)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.decode(self.encode(x))

    def reconstruction_error(self, x: torch.Tensor) -> torch.Tensor:
        """Per-sample MSE between input and reconstruction.

        Returns a 1-D tensor of shape ``(batch_size,)``.
        """
        x_hat = self.forward(x)
        return ((x - x_hat) ** 2).mean(dim=1)

    def reconstruction_loss(self, x: torch.Tensor) -> torch.Tensor:
        return F.mse_loss(self.forward(x), x)

    def bn_parameter_indices(self) -> set[int]:
        bn_names: set[str] = set()
        for name, module in self.named_modules():
            if isinstance(module, nn.BatchNorm1d):
                bn_names.add(name)

        indices: set[int] = set()
        for idx, (name, _param) in enumerate(self.named_parameters()):
            parts = name.rsplit(".", 1)
            module_path = parts[0] if len(parts) > 1 else ""
            if module_path in bn_names:
                indices.add(idx)
        return indices


def validate_model_on_cuda(model: nn.Module) -> None:
    for name, param in model.named_parameters():
        if not param.is_cuda:
            raise RuntimeError(
                f"[models.autoencoder] Parameter '{name}' is on "
                f"{param.device}, not CUDA. "
                f"Expected: CUDA device. Got: {param.device}."
            )
