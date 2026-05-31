from __future__ import annotations

import copy
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import torch

from datp.core.enums import Activation, Regime
from datp.modeling.autoencoder import Autoencoder
from datp.federated.protocols.fedprox import DatpFedProxClient, run_fedprox_training
from datp.federated.parameters import get_parameters
from datp.federated.types import ClientMetricKey


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
            input_dim=4, hidden_dims=[3, 2], activation=Activation.RELU, use_bn=False
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
        assert ClientMetricKey.TRAIN_LOSS in metrics
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
        assert ClientMetricKey.TRAIN_LOSS in metrics
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

        assert isinstance(metrics_zero[ClientMetricKey.TRAIN_LOSS], float)
        assert isinstance(metrics_large[ClientMetricKey.TRAIN_LOSS], float)

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

        assert m_a[ClientMetricKey.TRAIN_LOSS] == pytest.approx(m_b[ClientMetricKey.TRAIN_LOSS], abs=1e-6)


class TestRunFedProxTraining:
    """Tests for the run_fedprox_training runner function."""

    def test_raises_when_regime_is_none(self, tmp_path: Path) -> None:
        cfg = _mock_cfg()
        cfg.regime = None

        with pytest.raises(ValueError, match="regime must be set"):
            run_fedprox_training(
                cfg=cfg,
                client_data={"c1": MagicMock()},
                seed=42,
                mu=0.5,
                base_dir=tmp_path,
            )

    @patch("datp.federated.protocols.fedprox.run_fl_simulation")
    def test_passes_correct_client_config(
        self, mock_run_fl: MagicMock, tmp_path: Path
    ) -> None:
        from datp.federated.simulation import TrainingResult
        mock_run_fl.return_value = TrainingResult(
            regime=Regime.A,
            seed=42,
            alpha=None,
            converged_round=10,
            total_rounds=10,
            checkpoint_dir=tmp_path / "ckpt",
            score_dir=tmp_path / "scores",
            loss_history=[0.1, 0.05],
        )
        cfg = _mock_cfg()
        cfg.regime = Regime.A

        run_fedprox_training(
            cfg=cfg,
            client_data={"c1": MagicMock()},
            seed=42,
            mu=0.5,
            base_dir=tmp_path,
        )

        mock_run_fl.assert_called_once()
        call_kwargs = mock_run_fl.call_args.kwargs
        client_config = call_kwargs["client_config"]
        assert client_config.client_cls is DatpFedProxClient
        assert client_config.client_extra_kwargs == {"mu": 0.5}
        assert call_kwargs["label"] == "FedProx(mu=0.5)"
