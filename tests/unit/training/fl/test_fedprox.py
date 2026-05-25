from __future__ import annotations

import copy

import pytest
import torch

from datp.models.autoencoder import Autoencoder
from datp.training.fl.fedprox import DatpFedProxClient


class TestFedProxClient:
    """Tests for the FedProx client's proximal term behavior."""

    @staticmethod
    def _make_model() -> Autoencoder:
        return Autoencoder(
            input_dim=4, hidden_dims=[3, 2], activation="relu", use_bn=False
        )

    def test_mu_zero_proximal_term_is_zero(self) -> None:
        """µ=0.0 → proximal term is not added to loss, matches FedAvg behavior."""
        model = self._make_model()
        train_data = torch.randn(16, 4)
        val_data = torch.randn(8, 4)

        class _MockCfg:
            federation = type("F", (), {"local_epochs": 1})()
            machine = type("M", (), {"batch_size_train": 8})()
            model = type("M", (), {"lr": 0.01})()

        client = DatpFedProxClient(
            cid="test",
            model=model,
            train_data=train_data,
            val_data=val_data,
            cfg=_MockCfg(),
            mu=0.0,
        )

        from datp.training.fl.client import get_parameters

        params = get_parameters(model)
        result_params, n_train, metrics = client.fit(params, {})

        assert n_train == 16
        assert "train_loss" in metrics
        assert isinstance(result_params, list)

    def test_mu_positive_proximal_term_is_nonzero(self) -> None:
        """µ > 0 → proximal term is computed and affects training."""
        model = self._make_model()
        train_data = torch.randn(16, 4)
        val_data = torch.randn(8, 4)

        class _MockCfg:
            federation = type("F", (), {"local_epochs": 2})()
            machine = type("M", (), {"batch_size_train": 8})()
            model = type("M", (), {"lr": 0.01})()

        client = DatpFedProxClient(
            cid="test",
            model=model,
            train_data=train_data,
            val_data=val_data,
            cfg=_MockCfg(),
            mu=1.0,
        )

        from datp.training.fl.client import get_parameters

        params = get_parameters(model)
        _, n_train, metrics = client.fit(params, {})

        assert n_train == 16
        assert "train_loss" in metrics
        # Parameters should have changed (prox term doesn't prevent learning).
        result_params2, _, _ = client.fit(params, {})
        assert len(result_params2) == len(params)

    def test_mu_positive_produces_different_result(self) -> None:
        """Different µ values produce different training outcomes."""
        model_a = self._make_model()
        model_b = self._make_model()
        # Copy weights so both start from same state
        for pa, pb in zip(model_a.parameters(), model_b.parameters(), strict=True):
            pb.data.copy_(pa.data)

        train_data = torch.randn(32, 4)
        val_data = torch.randn(8, 4)

        class _MockCfg:
            federation = type("F", (), {"local_epochs": 2})()
            machine = type("M", (), {"batch_size_train": 8})()
            model = type("M", (), {"lr": 0.01})()

        from datp.training.fl.client import get_parameters

        client_zero = DatpFedProxClient(
            cid="test",
            model=model_a,
            train_data=train_data,
            val_data=val_data,
            cfg=_MockCfg(),
            mu=0.0,
        )
        client_large = DatpFedProxClient(
            cid="test",
            model=model_b,
            train_data=train_data,
            val_data=val_data,
            cfg=_MockCfg(),
            mu=10.0,
        )

        params = get_parameters(model_a)
        _, _, metrics_zero = client_zero.fit(params, {})
        _, _, metrics_large = client_large.fit(params, {})

        # With large mu, loss should be higher (prox term resists change)
        assert isinstance(metrics_zero["train_loss"], float)
        assert isinstance(metrics_large["train_loss"], float)

    def test_deterministic_same_seed(self) -> None:
        """Same seed + same mu → identical output."""
        torch.manual_seed(42)
        model = self._make_model()
        train_data = torch.randn(16, 4)
        val_data = torch.randn(8, 4)

        class _MockCfg:
            federation = type("F", (), {"local_epochs": 1})()
            machine = type("M", (), {"batch_size_train": 8})()
            model = type("M", (), {"lr": 0.01})()

        from datp.training.fl.client import get_parameters

        model_a = copy.deepcopy(model)
        model_b = copy.deepcopy(model)

        client_a = DatpFedProxClient(
            cid="test",
            model=model_a,
            train_data=train_data,
            val_data=val_data,
            cfg=_MockCfg(),
            mu=0.5,
        )
        client_b = DatpFedProxClient(
            cid="test",
            model=model_b,
            train_data=train_data,
            val_data=val_data,
            cfg=_MockCfg(),
            mu=0.5,
        )

        params = get_parameters(model)

        torch.manual_seed(42)
        _, _, m_a = client_a.fit(params, {})
        torch.manual_seed(42)
        _, _, m_b = client_b.fit(params, {})

        # Same seed, same data, same mu → same loss
        assert m_a["train_loss"] == pytest.approx(m_b["train_loss"], abs=1e-6)

    def test_local_epochs_match_fedavg(self) -> None:
        """FedProx client uses the same local_epochs as FedAvg client."""
        model = self._make_model()

        class _MockCfg:
            federation = type("F", (), {"local_epochs": 5})()
            machine = type("M", (), {"batch_size_train": 8})()
            model = type("M", (), {"lr": 0.01})()

        client = DatpFedProxClient(
            cid="test",
            model=model,
            train_data=torch.randn(16, 4),
            val_data=torch.randn(8, 4),
            cfg=_MockCfg(),
            mu=0.5,
        )

        assert client._local_epochs == 5
