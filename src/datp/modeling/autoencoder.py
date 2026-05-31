# SPDX-License-Identifier: Proprietary
from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F

from datp.core.enums import Activation

_ACTIVATION_CLASSES: dict[Activation, type[nn.Module]] = {
    Activation.RELU: nn.ReLU,
    Activation.LEAKY_RELU: nn.LeakyReLU,
    Activation.ELU: nn.ELU,
    Activation.TANH: nn.Tanh,
    Activation.SIGMOID: nn.Sigmoid,
}


class Autoencoder(nn.Module):
    def __init__(
        self,
        input_dim: int,
        hidden_dims: list[int],
        activation: Activation,
        use_bn: bool,
    ) -> None:
        super().__init__()
        if not hidden_dims:
            raise ValueError("hidden_dims must be non-empty")
        act_cls = _ACTIVATION_CLASSES[activation]

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


def validate_model_on_cuda(model: nn.Module) -> None:
    for name, param in model.named_parameters():
        if not param.is_cuda:
            raise RuntimeError(
                f"[modeling.autoencoder] Parameter '{name}' is on "
                f"{param.device}, not CUDA. "
                f"Expected: CUDA device. Got: {param.device}."
            )
