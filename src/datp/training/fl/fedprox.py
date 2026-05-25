# SPDX-License-Identifier: Proprietary
"""FedProx client: adds proximal term (µ/2)||w - w_global||² to local loss.

FedProx is a locked aggregation-side stress test, not a core baseline.
It is never added to the Baseline enum.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import torch
import torch.nn as nn

from datp.models.autoencoder import Autoencoder
from datp.training.fl.client import DatpClient, get_parameters, set_parameters


class DatpFedProxClient(DatpClient):
    def __init__(
        self,
        cid: str,
        model: Autoencoder,
        train_data: torch.Tensor,
        val_data: torch.Tensor,
        cfg,
        mu: float,
    ) -> None:
        super().__init__(cid, model, train_data, val_data, cfg)
        self._mu = mu

    def fit(
        self,
        parameters: list[np.ndarray],
        config: dict[str, Any],  # noqa: ARG002
    ) -> tuple[list[np.ndarray], int, dict[str, Any]]:
        set_parameters(self.model, parameters)
        self.model.train()

        # Save global parameters for proximal term computation.
        global_params = [p.detach().clone() for p in self.model.parameters()]

        mu = self._mu
        optimizer = torch.optim.Adam(
            self.model.parameters(), lr=self._lr, weight_decay=0.0
        )
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
                recon_loss = nn.functional.mse_loss(x_hat, batch)

                if mu > 0:
                    prox_term = 0.0
                    for param, global_param in zip(
                        self.model.parameters(), global_params, strict=True
                    ):
                        prox_term += ((param - global_param) ** 2).sum()
                    loss = recon_loss + 0.5 * mu * prox_term
                else:
                    loss = recon_loss

                loss.backward()
                optimizer.step()

                epoch_loss += recon_loss.item()
                n_batches += 1

            last_loss = epoch_loss / max(n_batches, 1)

        return get_parameters(self.model), n_train, {"train_loss": last_loss}
