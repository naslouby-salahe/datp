# SPDX-License-Identifier: Proprietary
"""FedRep-AE client: shared encoder (FedAvg), localized decoder heads.

Choice documented per T18 / PRE_CODING_PLAN §6.4: FedRep-AE fallback.
This is NOT Ditto. It is a recognized shared-representation/local-head
personalization family (FedRep style, adapted to the DATP AE architecture).

The client is a stress test only — never added to the Baseline enum.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import torch
import torch.nn as nn

from datp.models.autoencoder import Autoencoder
from datp.training.fl.client import DatpClient, get_parameters, set_parameters


class DatpFedRepClient(DatpClient):
    """FedRep-AE: shared encoder aggregated via FedAvg, decoder personalized per-client.

    During local training:
      1. Encoder params are set from the global model.
      2. Phase 1 (decoder head): encoder frozen, decoder trained for local_epochs.
      3. Phase 2 (full model): both encoder + decoder trained for local_epochs.
      4. Only encoder params are returned to the server.

    The decoder never leaves the client — it is the personalization surface.
    """

    def __init__(
        self,
        cid: str,
        model: Autoencoder,
        train_data: torch.Tensor,
        val_data: torch.Tensor,
        cfg,
    ) -> None:
        super().__init__(cid, model, train_data, val_data, cfg)

    def get_parameters(self, config: dict[str, Any]) -> list[np.ndarray]:  # noqa: ARG002
        """Return only encoder parameters — decoder is local-only."""
        return [p.detach().cpu().numpy() for p in self.model.encoder.parameters()]

    def fit(
        self,
        parameters: list[np.ndarray],
        config: dict[str, Any],  # noqa: ARG002
    ) -> tuple[list[np.ndarray], int, dict[str, Any]]:
        # Set encoder params from global model.
        set_parameters(self.model.encoder, parameters)
        self.model.train()

        n_train = len(self.train_data)

        # ── Phase 1: train decoder only (encoder frozen) ──
        decoder_optimizer = torch.optim.Adam(
            self.model.decoder.parameters(), lr=self._lr, weight_decay=0.0
        )
        for _epoch in range(self._local_epochs):
            indices = torch.randperm(n_train, device=self.train_data.device)
            for start in range(0, n_train, self._batch_size):
                batch_idx = indices[start : start + self._batch_size]
                batch = self.train_data[batch_idx]

                decoder_optimizer.zero_grad()
                with torch.no_grad():
                    z = self.model.encoder(batch)
                x_hat = self.model.decoder(z)
                loss = nn.functional.mse_loss(x_hat, batch)
                loss.backward()
                decoder_optimizer.step()

        # ── Phase 2: train full model (encoder + decoder) ──
        full_optimizer = torch.optim.Adam(
            self.model.parameters(), lr=self._lr, weight_decay=0.0
        )
        last_loss = float("nan")
        for _epoch in range(self._local_epochs):
            indices = torch.randperm(n_train, device=self.train_data.device)
            epoch_loss = 0.0
            n_batches = 0
            for start in range(0, n_train, self._batch_size):
                batch_idx = indices[start : start + self._batch_size]
                batch = self.train_data[batch_idx]

                full_optimizer.zero_grad()
                x_hat = self.model(batch)
                loss = nn.functional.mse_loss(x_hat, batch)
                loss.backward()
                full_optimizer.step()

                epoch_loss += loss.item()
                n_batches += 1

            last_loss = epoch_loss / max(n_batches, 1)

        # Return only encoder parameters.
        return (
            get_parameters(self.model.encoder),
            n_train,
            {"train_loss": last_loss},
        )
