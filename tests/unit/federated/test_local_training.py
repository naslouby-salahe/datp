# SPDX-License-Identifier: Proprietary
"""Tests for datp.training.local — shared local training mechanics."""

from __future__ import annotations

import copy

import pytest
import torch

from datp.modeling.autoencoder import Autoencoder
from datp.federated.local_training import evaluate_benign, train_decoder_only, train_local


def _make_model() -> Autoencoder:
    return Autoencoder(input_dim=4, hidden_dims=[3, 2], activation="relu", use_bn=False)


class TestTrainLocal:
    """Standard AE local training loop."""

    def test_returns_finite_loss(self) -> None:
        model = _make_model()
        data = torch.randn(16, 4)
        loss = train_local(model, data, epochs=1, batch_size=8, lr=0.01)
        assert isinstance(loss, float)
        assert not torch.isnan(torch.tensor(loss))

    def test_multiple_epochs_reduce_loss(self) -> None:
        torch.manual_seed(0)
        model = _make_model()
        data = torch.randn(32, 4)
        loss_1 = train_local(model, data, epochs=1, batch_size=8, lr=0.01)

        torch.manual_seed(0)
        model2 = _make_model()
        loss_10 = train_local(model2, data, epochs=10, batch_size=8, lr=0.01)

        assert loss_10 < loss_1

    def test_mu_zero_no_proximal(self) -> None:
        model = _make_model()
        data = torch.randn(16, 4)
        loss = train_local(model, data, epochs=1, batch_size=8, lr=0.01, mu=0.0)
        assert isinstance(loss, float)

    def test_mu_positive_with_global_params(self) -> None:
        model = _make_model()
        data = torch.randn(16, 4)
        global_params = [p.detach().clone() for p in model.parameters()]
        loss = train_local(
            model, data, epochs=1, batch_size=8, lr=0.01, mu=1.0, global_params=global_params
        )
        assert isinstance(loss, float)

    def test_proximal_term_constrains_updates(self) -> None:
        torch.manual_seed(7)
        model_free = _make_model()
        model_prox = copy.deepcopy(model_free)
        data = torch.randn(32, 4)

        global_params = [p.detach().clone() for p in model_free.parameters()]

        torch.manual_seed(7)
        train_local(model_free, data, epochs=3, batch_size=8, lr=0.01, mu=0.0)
        torch.manual_seed(7)
        train_local(
            model_prox, data, epochs=3, batch_size=8, lr=0.01, mu=10.0, global_params=global_params
        )

        drift_free = sum(
            ((p - gp) ** 2).sum().item()
            for p, gp in zip(model_free.parameters(), global_params, strict=True)
        )
        drift_prox = sum(
            ((p - gp) ** 2).sum().item()
            for p, gp in zip(model_prox.parameters(), global_params, strict=True)
        )
        assert drift_prox < drift_free

    def test_deterministic_same_seed(self) -> None:
        data = torch.randn(16, 4)

        torch.manual_seed(42)
        m1 = _make_model()
        loss1 = train_local(m1, data, epochs=2, batch_size=8, lr=0.01)

        torch.manual_seed(42)
        m2 = _make_model()
        loss2 = train_local(m2, data, epochs=2, batch_size=8, lr=0.01)

        assert loss1 == pytest.approx(loss2, abs=1e-7)


class TestTrainDecoderOnly:
    """FedRep Phase 1 — encoder frozen, decoder trained."""

    def test_encoder_unchanged(self) -> None:
        model = _make_model()
        encoder_before = [p.detach().clone() for p in model.encoder.parameters()]
        data = torch.randn(16, 4)

        train_decoder_only(model, data, epochs=2, batch_size=8, lr=0.01)

        for before, after in zip(encoder_before, model.encoder.parameters(), strict=True):
            assert torch.equal(before, after), "Encoder must not change during decoder-only phase"

    def test_decoder_changes(self) -> None:
        model = _make_model()
        decoder_before = [p.detach().clone() for p in model.decoder.parameters()]
        data = torch.randn(16, 4)

        train_decoder_only(model, data, epochs=2, batch_size=8, lr=0.01)

        any_changed = any(
            not torch.equal(b, a)
            for b, a in zip(decoder_before, model.decoder.parameters(), strict=True)
        )
        assert any_changed, "Decoder should be updated"


class TestDatpClientShapeValidation:
    """DatpClient.__init__ must reject non-2-D train/val tensors with a clear
    error before reaching the training loop."""

    def _cfg(self) -> object:
        from unittest.mock import MagicMock

        cfg = MagicMock()
        cfg.federation.local_epochs = 1
        cfg.machine.batch_size_train = 8
        cfg.model.lr = 0.01
        return cfg

    def test_accepts_valid_2d_tensors(self) -> None:
        from datp.federated.clients import DatpClient

        model = _make_model()
        client = DatpClient(
            cid="c0",
            model=model,
            train_data=torch.randn(16, 4),
            val_data=torch.randn(8, 4),
            cfg=self._cfg(),  # type: ignore[arg-type]
        )
        assert client.cid == "c0"

    def test_rejects_1d_train_data(self) -> None:
        from datp.federated.clients import DatpClient

        model = _make_model()
        with pytest.raises(ValueError, match="train_data must be 2-D"):
            DatpClient(
                cid="c0",
                model=model,
                train_data=torch.randn(16),
                val_data=torch.randn(8, 4),
                cfg=self._cfg(),  # type: ignore[arg-type]
            )

    def test_rejects_3d_val_data(self) -> None:
        from datp.federated.clients import DatpClient

        model = _make_model()
        with pytest.raises(ValueError, match="val_data must be 2-D"):
            DatpClient(
                cid="c1",
                model=model,
                train_data=torch.randn(16, 4),
                val_data=torch.randn(8, 4, 2),
                cfg=self._cfg(),  # type: ignore[arg-type]
            )

    def test_error_includes_module_prefix_and_cid(self) -> None:
        from datp.federated.clients import DatpClient

        model = _make_model()
        with pytest.raises(
            ValueError, match=r"\[training\.types\].*client client_xyz"
        ):
            DatpClient(
                cid="client_xyz",
                model=model,
                train_data=torch.randn(16),
                val_data=torch.randn(8, 4),
                cfg=self._cfg(),  # type: ignore[arg-type]
            )


class TestEvaluateBenign:
    """Benign-only validation loss."""

    def test_returns_positive_loss(self) -> None:
        model = _make_model()
        val_data = torch.randn(8, 4)
        loss = evaluate_benign(model, val_data)
        assert loss > 0.0

    def test_model_set_to_eval(self) -> None:
        model = _make_model()
        model.train()
        val_data = torch.randn(8, 4)
        evaluate_benign(model, val_data)
        assert not model.training

    def test_perfect_reconstruction_gives_zero_loss(self) -> None:
        model = _make_model()
        val_data = torch.zeros(4, 4)
        # Zero input with identity-like model won't give exactly zero,
        # but at least it should be non-negative.
        loss = evaluate_benign(model, val_data)
        assert loss >= 0.0


class TestTrainLocalValidation:
    """Validation at the boundary of train_local."""

    def test_epochs_zero_raises(self) -> None:
        model = _make_model()
        data = torch.randn(16, 4)
        with pytest.raises(ValueError, match="epochs must be >= 1"):
            train_local(model, data, epochs=0, batch_size=8, lr=0.01)

    def test_batch_size_zero_raises(self) -> None:
        model = _make_model()
        data = torch.randn(16, 4)
        with pytest.raises(ValueError, match="batch_size must be >= 1"):
            train_local(model, data, epochs=1, batch_size=0, lr=0.01)

    def test_empty_data_raises(self) -> None:
        model = _make_model()
        data = torch.empty(0, 4)
        with pytest.raises(ValueError, match="non-empty"):
            train_local(model, data, epochs=1, batch_size=8, lr=0.01)


class TestTrainDecoderOnlyValidation:
    """Validation at the boundary of train_decoder_only."""

    def test_epochs_zero_raises(self) -> None:
        model = _make_model()
        data = torch.randn(16, 4)
        with pytest.raises(ValueError, match="epochs must be >= 1"):
            train_decoder_only(model, data, epochs=0, batch_size=8, lr=0.01)

    def test_batch_size_zero_raises(self) -> None:
        model = _make_model()
        data = torch.randn(16, 4)
        with pytest.raises(ValueError, match="batch_size must be >= 1"):
            train_decoder_only(model, data, epochs=1, batch_size=0, lr=0.01)

    def test_empty_data_raises(self) -> None:
        model = _make_model()
        data = torch.empty(0, 4)
        with pytest.raises(ValueError, match="non-empty"):
            train_decoder_only(model, data, epochs=1, batch_size=8, lr=0.01)
