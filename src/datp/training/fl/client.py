# SPDX-License-Identifier: Proprietary
"""Shared FL client; no baseline-specific branching — B1/B2/B3/B4 all train the same encoder."""

from __future__ import annotations

from typing import Any

import numpy as np
import torch
import torch.nn as nn
from flwr.client import NumPyClient

from datp.core.logging import get_logger
from datp.models.autoencoder import Autoencoder

logger = get_logger(__name__)


def get_parameters(model: nn.Module) -> list[np.ndarray]:
    return [p.detach().cpu().numpy() for p in model.parameters()]


def set_parameters(model: nn.Module, parameters: list[np.ndarray]) -> None:
    with torch.no_grad():
        for param, arr in zip(model.parameters(), parameters, strict=True):
            param.copy_(torch.from_numpy(arr).to(param.device, non_blocking=True))


class DatpClient(NumPyClient):
    def __init__(
        self,
        cid: str,
        model: Autoencoder,
        train_data: torch.Tensor,
        val_data: torch.Tensor,
        cfg,  # DatpConfig
    ) -> None:
        self.cid = cid
        self.model = model
        self.train_data = train_data
        self.val_data = val_data

        self._local_epochs: int = cfg.federation.local_epochs
        self._batch_size: int = cfg.machine.batch_size_train
        self._lr: float = cfg.model.lr

    def get_parameters(self, config: dict[str, Any]) -> list[np.ndarray]:  # noqa: ARG002
        return get_parameters(self.model)

    def fit(
        self,
        parameters: list[np.ndarray],
        config: dict[str, Any],  # noqa: ARG002
    ) -> tuple[list[np.ndarray], int, dict[str, Any]]:
        set_parameters(self.model, parameters)
        self.model.train()

        optimizer = torch.optim.Adam(self.model.parameters(), lr=self._lr)
        n_train = len(self.train_data)

        last_loss = float("nan")
        for _epoch in range(self._local_epochs):
            indices = torch.randperm(n_train, device=self.train_data.device)
            epoch_loss = 0.0
            n_batches = 0
            for start in range(0, n_train, self._batch_size):
                batch_idx = indices[start : start + self._batch_size]
                batch = self.train_data[batch_idx]

                optimizer.zero_grad()
                x_hat = self.model(batch)
                loss = nn.functional.mse_loss(x_hat, batch)
                loss.backward()
                optimizer.step()

                epoch_loss += loss.item()
                n_batches += 1

            last_loss = epoch_loss / max(n_batches, 1)

        return get_parameters(self.model), n_train, {"train_loss": last_loss}

    def evaluate(
        self,
        parameters: list[np.ndarray],
        config: dict[str, Any],  # noqa: ARG002
    ) -> tuple[float, int, dict[str, Any]]:
        """Benign-only validation — never evaluated on attack data."""
        set_parameters(self.model, parameters)
        self.model.eval()

        with torch.inference_mode():
            x_hat = self.model(self.val_data)
            loss = nn.functional.mse_loss(x_hat, self.val_data).item()

        return loss, len(self.val_data), {"val_loss": loss}
