# SPDX-License-Identifier: Proprietary
"""Tests for FedRep-AE client and absorption ratio classification."""

from __future__ import annotations

import copy

import pytest
import torch

from datp.core.enums import (
    ABSORPTION_PARTIAL_THRESHOLD,
    ABSORPTION_STRONG_RETENTION_THRESHOLD,
    AbsorptionClass,
    classify_absorption,
)
from datp.models.autoencoder import Autoencoder
from datp.training.fl.fedrep import DatpFedRepClient


class TestFedRepClient:
    """Tests for the FedRep-AE client's encoder/decoder separation."""

    @staticmethod
    def _make_model() -> Autoencoder:
        return Autoencoder(
            input_dim=4, hidden_dims=[3, 2], activation="relu", use_bn=False
        )

    def test_get_parameters_returns_only_encoder(self) -> None:
        """get_parameters() returns encoder params, not decoder params."""
        model = self._make_model()
        train_data = torch.randn(16, 4)
        val_data = torch.randn(8, 4)

        class _MockCfg:
            federation = type("F", (), {"local_epochs": 1})()
            machine = type("M", (), {"batch_size_train": 8})()
            model = type("M", (), {"lr": 0.01})()

        client = DatpFedRepClient(
            cid="test",
            model=model,
            train_data=train_data,
            val_data=val_data,
            cfg=_MockCfg(),
        )

        params = client.get_parameters({})
        encoder_param_count = sum(p.numel() for p in model.encoder.parameters())
        total_param_count = sum(p.numel() for p in model.parameters())

        # Encoder only — fewer params than full model.
        returned_count = sum(int(p.size) for p in params)
        assert returned_count == encoder_param_count
        assert returned_count < total_param_count

    def test_fit_trains_and_returns_encoder_only(self) -> None:
        """fit() returns only encoder params after local training."""
        model = self._make_model()
        train_data = torch.randn(16, 4)
        val_data = torch.randn(8, 4)

        class _MockCfg:
            federation = type("F", (), {"local_epochs": 1})()
            machine = type("M", (), {"batch_size_train": 8})()
            model = type("M", (), {"lr": 0.01})()

        from datp.training.fl.client import get_parameters

        client = DatpFedRepClient(
            cid="test",
            model=model,
            train_data=train_data,
            val_data=val_data,
            cfg=_MockCfg(),
        )

        encoder_params = get_parameters(model.encoder)
        result_params, n_train, metrics = client.fit(encoder_params, {})

        assert n_train == 16
        assert "train_loss" in metrics
        assert isinstance(metrics["train_loss"], float)
        # Returned params count should match encoder param count.
        encoder_param_count = sum(p.numel() for p in model.encoder.parameters())
        returned_count = sum(int(p.size) for p in result_params)
        assert returned_count == encoder_param_count

    def test_encoder_decoder_independent(self) -> None:
        """After fit(), encoder changed but decoder still works."""
        model = self._make_model()
        train_data = torch.randn(32, 4)
        val_data = torch.randn(8, 4)

        class _MockCfg:
            federation = type("F", (), {"local_epochs": 1})()
            machine = type("M", (), {"batch_size_train": 8})()
            model = type("M", (), {"lr": 0.01})()

        from datp.training.fl.client import get_parameters

        # Snapshot decoder weights before training.
        decoder_before = [p.detach().clone() for p in model.decoder.parameters()]

        client = DatpFedRepClient(
            cid="test",
            model=model,
            train_data=train_data,
            val_data=val_data,
            cfg=_MockCfg(),
        )

        encoder_params = get_parameters(model.encoder)
        client.fit(encoder_params, {})

        # Decoder should have changed (personalized) during local training.
        decoder_after = [p.detach().clone() for p in model.decoder.parameters()]
        any_changed = any(
            not torch.equal(b, a)
            for b, a in zip(decoder_before, decoder_after, strict=True)
        )
        assert any_changed, "Decoder should be personalized during local training"

    def test_deterministic_same_seed(self) -> None:
        """Same seed → identical training output."""
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

        client_a = DatpFedRepClient(
            cid="test",
            model=model_a,
            train_data=train_data,
            val_data=val_data,
            cfg=_MockCfg(),
        )
        client_b = DatpFedRepClient(
            cid="test",
            model=model_b,
            train_data=train_data,
            val_data=val_data,
            cfg=_MockCfg(),
        )

        encoder_params = get_parameters(model.encoder)

        torch.manual_seed(42)
        _, _, m_a = client_a.fit(encoder_params, {})
        torch.manual_seed(42)
        _, _, m_b = client_b.fit(encoder_params, {})

        assert m_a["train_loss"] == pytest.approx(m_b["train_loss"], abs=1e-6)

    def test_not_labeled_ditto(self) -> None:
        """FedRep-AE is never labeled Ditto."""
        assert DatpFedRepClient.__doc__ is not None
        assert "Ditto" not in DatpFedRepClient.__doc__
        assert "ditto" not in DatpFedRepClient.__name__.lower()
        import datp.training.fl.fedrep as fedrep_module

        assert fedrep_module.__doc__ is not None
        assert "NOT Ditto" in fedrep_module.__doc__


class TestAbsorptionClassification:
    """Absorption ratio classification per PRE_CODING_PLAN §6.4."""

    def test_strong_retention_above_threshold(self) -> None:
        assert (
            classify_absorption(ABSORPTION_STRONG_RETENTION_THRESHOLD)
            == AbsorptionClass.STRONG_RETENTION
        )
        assert classify_absorption(0.9) == AbsorptionClass.STRONG_RETENTION

    def test_partial_between_thresholds(self) -> None:
        assert classify_absorption(0.5) == AbsorptionClass.PARTIAL
        assert classify_absorption(0.25) == AbsorptionClass.PARTIAL

    def test_near_full_below_partial_threshold(self) -> None:
        assert classify_absorption(0.24) == AbsorptionClass.NEAR_FULL
        assert classify_absorption(0.0) == AbsorptionClass.NEAR_FULL
        assert classify_absorption(-0.1) == AbsorptionClass.NEAR_FULL

    def test_thresholds_are_ordered(self) -> None:
        assert ABSORPTION_STRONG_RETENTION_THRESHOLD > ABSORPTION_PARTIAL_THRESHOLD

    def test_all_classes_reachable(self) -> None:
        classes = {
            classify_absorption(1.0),
            classify_absorption(0.5),
            classify_absorption(0.0),
        }
        assert len(classes) == 3

    def test_absorption_ratio_formula_identity(self) -> None:
        """Absorption ratio = Δ_personalized / Δ_FedAvg.

        Δ = CV(FPR)[B1] − CV(FPR)[B2] for each model variant.
        """
        # Example values: FedAvg Δ=0.8, Personalized Δ=0.4 → ratio=0.5
        delta_fedavg = 0.8
        delta_personalized = 0.4
        ratio = delta_personalized / delta_fedavg
        assert classify_absorption(ratio) == AbsorptionClass.PARTIAL
