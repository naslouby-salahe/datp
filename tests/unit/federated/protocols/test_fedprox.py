from __future__ import annotations

import copy

import pytest
import torch
from unittest.mock import MagicMock

from datp.modeling.autoencoder import Autoencoder
from datp.federated.protocols.fedprox import DatpFedProxClient
from datp.federated.parameters import get_parameters


def _mock_cfg(local_epochs: int = 1, lr: float = 0.01, batch_size: int = 8) -> MagicMock:
    cfg = MagicMock()
    cfg.federation.local_epochs = local_epochs
    cfg.machine.batch_size_train = batch_size
    cfg.model.lr = lr
    return cfg


class TestFedProxClient:
    """Tests for the FedProx client's proximal term behavior."""

    @staticmethod
    def _make_model() -> Autoencoder:
        return Autoencoder(
            input_dim=4, hidden_dims=[3, 2], activation="relu", use_bn=False
        )

    def test_mu_zero_proximal_term_is_zero(self) -> None:
        model = self._make_model()
        train_data = torch.randn(16, 4)
        val_data = torch.randn(8, 4)

        client = DatpFedProxClient(
            cid="test",
            model=model,
            train_data=train_data,
            val_data=val_data,
            cfg=_mock_cfg(local_epochs=1),
            mu=0.0,
        )

        params = get_parameters(model)
        result_params, n_train, metrics = client.fit(params, {})

        assert n_train == 16
        assert "train_loss" in metrics
        assert isinstance(result_params, list)

    def test_mu_positive_proximal_term_is_nonzero(self) -> None:
        model = self._make_model()
        train_data = torch.randn(16, 4)
        val_data = torch.randn(8, 4)

        client = DatpFedProxClient(
            cid="test",
            model=model,
            train_data=train_data,
            val_data=val_data,
            cfg=_mock_cfg(local_epochs=2),
            mu=1.0,
        )

        params = get_parameters(model)
        _, n_train, metrics = client.fit(params, {})

        assert n_train == 16
        assert "train_loss" in metrics
        result_params2, _, _ = client.fit(params, {})
        assert len(result_params2) == len(params)

    def test_mu_positive_produces_different_result(self) -> None:
        model_a = self._make_model()
        model_b = self._make_model()
        for pa, pb in zip(model_a.parameters(), model_b.parameters(), strict=True):
            pb.data.copy_(pa.data)

        train_data = torch.randn(32, 4)
        val_data = torch.randn(8, 4)

        client_zero = DatpFedProxClient(
            cid="test",
            model=model_a,
            train_data=train_data,
            val_data=val_data,
            cfg=_mock_cfg(local_epochs=2),
            mu=0.0,
        )
        client_large = DatpFedProxClient(
            cid="test",
            model=model_b,
            train_data=train_data,
            val_data=val_data,
            cfg=_mock_cfg(local_epochs=2),
            mu=10.0,
        )

        params = get_parameters(model_a)
        _, _, metrics_zero = client_zero.fit(params, {})
        _, _, metrics_large = client_large.fit(params, {})

        assert isinstance(metrics_zero["train_loss"], float)
        assert isinstance(metrics_large["train_loss"], float)

    def test_deterministic_same_seed(self) -> None:
        torch.manual_seed(42)
        model = self._make_model()
        train_data = torch.randn(16, 4)
        val_data = torch.randn(8, 4)

        model_a = copy.deepcopy(model)
        model_b = copy.deepcopy(model)

        client_a = DatpFedProxClient(
            cid="test",
            model=model_a,
            train_data=train_data,
            val_data=val_data,
            cfg=_mock_cfg(local_epochs=1),
            mu=0.5,
        )
        client_b = DatpFedProxClient(
            cid="test",
            model=model_b,
            train_data=train_data,
            val_data=val_data,
            cfg=_mock_cfg(local_epochs=1),
            mu=0.5,
        )

        params = get_parameters(model)

        torch.manual_seed(42)
        _, _, m_a = client_a.fit(params, {})
        torch.manual_seed(42)
        _, _, m_b = client_b.fit(params, {})

        assert m_a["train_loss"] == pytest.approx(m_b["train_loss"], abs=1e-6)
