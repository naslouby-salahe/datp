# SPDX-License-Identifier: Proprietary
"""Shared local training mechanics: batch iteration, loss, optimizers.

Every Flower client delegates to these helpers. No client reimplements the training loop.
"""

from __future__ import annotations

import math
from collections.abc import Iterator

import torch
import torch.nn as nn

from datp.core.errors import fmt
from datp.models.autoencoder import Autoencoder

_MODULE = "training.local"


def _iter_shuffled_batches(data: torch.Tensor, batch_size: int) -> Iterator[torch.Tensor]:
    n = len(data)
    indices = torch.randperm(n, device=data.device)
    for start in range(0, n, batch_size):
        yield data[indices[start : start + batch_size]]


def train_local(
    model: Autoencoder,
    data: torch.Tensor,
    *,
    epochs: int,
    batch_size: int,
    lr: float,
    mu: float = 0.0,
    global_params: list[torch.Tensor] | None = None,
) -> float:
    """Standard AE local training loop with optional FedProx proximal term.

    Returns the average reconstruction loss of the final epoch.
    When mu > 0, the proximal term (mu/2)||w - w_global||² is added to the loss.
    """
    if epochs < 1:
        raise ValueError(fmt(_MODULE, "epochs must be >= 1", ">= 1", str(epochs)))
    if batch_size < 1:
        raise ValueError(fmt(_MODULE, "batch_size must be >= 1", ">= 1", str(batch_size)))
    if data.numel() == 0:
        raise ValueError(fmt(_MODULE, "training data must be non-empty", "> 0 samples", "0"))

    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=0.0)
    last_loss = float("nan")

    for _epoch in range(epochs):
        epoch_loss = 0.0
        n_batches = 0
        for batch in _iter_shuffled_batches(data, batch_size):
            optimizer.zero_grad()
            x_hat = model(batch)
            recon_loss = nn.functional.mse_loss(x_hat, batch)

            if mu > 0 and global_params is not None:
                prox_term = sum(
                    ((p - gp) ** 2).sum()
                    for p, gp in zip(model.parameters(), global_params, strict=True)
                )
                loss = recon_loss + 0.5 * mu * prox_term
            else:
                loss = recon_loss

            loss.backward()
            optimizer.step()

            epoch_loss += recon_loss.item()
            n_batches += 1

        last_loss = epoch_loss / max(n_batches, 1)

    if not math.isfinite(last_loss):
        raise RuntimeError(
            fmt(_MODULE, "Training produced non-finite loss", "finite loss", repr(last_loss))
        )

    return last_loss


def train_decoder_only(
    model: Autoencoder,
    data: torch.Tensor,
    *,
    epochs: int,
    batch_size: int,
    lr: float,
) -> None:
    """FedRep Phase 1: train decoder with encoder frozen."""
    if epochs < 1:
        raise ValueError(fmt(_MODULE, "epochs must be >= 1", ">= 1", str(epochs)))
    if batch_size < 1:
        raise ValueError(fmt(_MODULE, "batch_size must be >= 1", ">= 1", str(batch_size)))
    if data.numel() == 0:
        raise ValueError(fmt(_MODULE, "training data must be non-empty", "> 0 samples", "0"))

    decoder_optimizer = torch.optim.Adam(
        model.decoder.parameters(), lr=lr, weight_decay=0.0
    )

    for _epoch in range(epochs):
        for batch in _iter_shuffled_batches(data, batch_size):
            decoder_optimizer.zero_grad()
            with torch.no_grad():
                z = model.encoder(batch)
            x_hat = model.decoder(z)
            loss = nn.functional.mse_loss(x_hat, batch)
            loss.backward()
            decoder_optimizer.step()


def evaluate_benign(model: Autoencoder, val_data: torch.Tensor) -> float:
    """Benign-only validation loss — never evaluated on attack data."""
    model.eval()
    with torch.inference_mode():
        x_hat = model(val_data)
        return nn.functional.mse_loss(x_hat, val_data).item()
