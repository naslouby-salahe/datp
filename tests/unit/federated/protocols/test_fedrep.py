# SPDX-License-Identifier: Proprietary
"""Tests for FedRep-AE client, decoder persistence, and per-client scoring."""

from __future__ import annotations

import copy
from pathlib import Path
from unittest.mock import patch

import pytest
import torch

from unittest.mock import MagicMock

from datp.artifacts.constants import DECODER_CHECKPOINT, MODEL_CHECKPOINT
from datp.core.enums import (
    ABSORPTION_PARTIAL_THRESHOLD,
    ABSORPTION_STRONG_RETENTION_THRESHOLD,
    AbsorptionClass,
    Regime,
    classify_absorption,
)
from datp.modeling.autoencoder import Autoencoder
from datp.federated.protocols.fedrep import DatpFedRepClient, run_fedrep_training
from datp.scoring.generation import ClientData, score_fedrep_clients


def _make_ae(input_dim: int = 4, hidden_dims: list[int] | None = None) -> Autoencoder:
    return Autoencoder(
        input_dim=input_dim,
        hidden_dims=hidden_dims or [3, 2],
        activation="relu",
        use_bn=False,
    )


def _mock_cfg() -> MagicMock:
    cfg = MagicMock()
    cfg.federation.local_epochs = 1
    cfg.machine.batch_size_train = 8
    cfg.model.lr = 0.01
    return cfg


class TestFedRepClient:
    """Tests for the FedRep-AE client's encoder/decoder separation."""

    def test_get_parameters_returns_only_encoder(self, tmp_path: Path) -> None:
        model = _make_ae()
        client = DatpFedRepClient(
            cid="test",
            model=model,
            train_data=torch.randn(16, 4),
            val_data=torch.randn(8, 4),
            cfg=_mock_cfg(),
            decoder_ckpt_dir=tmp_path,
        )

        params = client.get_parameters({})
        encoder_param_count = sum(p.numel() for p in model.encoder.parameters())
        total_param_count = sum(p.numel() for p in model.parameters())

        returned_count = sum(int(p.size) for p in params)
        assert returned_count == encoder_param_count
        assert returned_count < total_param_count

    def test_fit_trains_and_returns_encoder_only(self, tmp_path: Path) -> None:
        from datp.federated.parameters import get_parameters

        model = _make_ae()
        client = DatpFedRepClient(
            cid="test",
            model=model,
            train_data=torch.randn(16, 4),
            val_data=torch.randn(8, 4),
            cfg=_mock_cfg(),
            decoder_ckpt_dir=tmp_path,
        )

        result_params, n_train, metrics = client.fit(get_parameters(model.encoder), {})

        assert n_train == 16
        assert "train_loss" in metrics
        assert isinstance(metrics["train_loss"], float)
        encoder_param_count = sum(p.numel() for p in model.encoder.parameters())
        assert sum(int(p.size) for p in result_params) == encoder_param_count

    def test_encoder_decoder_independent(self, tmp_path: Path) -> None:
        from datp.federated.parameters import get_parameters

        model = _make_ae()
        decoder_before = [p.detach().clone() for p in model.decoder.parameters()]

        client = DatpFedRepClient(
            cid="test",
            model=model,
            train_data=torch.randn(32, 4),
            val_data=torch.randn(8, 4),
            cfg=_mock_cfg(),
            decoder_ckpt_dir=tmp_path,
        )
        client.fit(get_parameters(model.encoder), {})

        decoder_after = [p.detach().clone() for p in model.decoder.parameters()]
        assert any(
            not torch.equal(b, a)
            for b, a in zip(decoder_before, decoder_after, strict=True)
        ), "Decoder should be personalized during local training"

    def test_deterministic_same_seed(self, tmp_path: Path) -> None:
        from datp.federated.parameters import get_parameters

        torch.manual_seed(42)
        model = _make_ae()
        train_data = torch.randn(16, 4)
        val_data = torch.randn(8, 4)

        model_a = copy.deepcopy(model)
        model_b = copy.deepcopy(model)

        client_a = DatpFedRepClient(
            cid="test",
            model=model_a,
            train_data=train_data,
            val_data=val_data,
            cfg=_mock_cfg(),
            decoder_ckpt_dir=tmp_path / "a",
        )
        client_b = DatpFedRepClient(
            cid="test",
            model=model_b,
            train_data=train_data,
            val_data=val_data,
            cfg=_mock_cfg(),
            decoder_ckpt_dir=tmp_path / "b",
        )

        encoder_params = get_parameters(model.encoder)

        torch.manual_seed(42)
        _, _, m_a = client_a.fit(encoder_params, {})
        torch.manual_seed(42)
        _, _, m_b = client_b.fit(encoder_params, {})

        assert m_a["train_loss"] == pytest.approx(m_b["train_loss"], abs=1e-6)

    def test_not_labeled_ditto(self) -> None:
        assert DatpFedRepClient.__doc__ is not None
        assert "Ditto" not in DatpFedRepClient.__doc__
        assert "ditto" not in DatpFedRepClient.__name__.lower()
        import datp.federated.protocols.fedrep as fedrep_module

        assert fedrep_module.__doc__ is not None
        assert "NOT Ditto" in fedrep_module.__doc__


class TestDecoderPersistence:
    """DatpFedRepClient.fit() must save the per-client decoder checkpoint."""

    def test_decoder_file_created_after_fit(self, tmp_path: Path) -> None:
        from datp.federated.parameters import get_parameters

        model = _make_ae()
        client = DatpFedRepClient(
            cid="client_0",
            model=model,
            train_data=torch.randn(8, 4),
            val_data=torch.randn(4, 4),
            cfg=_mock_cfg(),
            decoder_ckpt_dir=tmp_path,
        )
        client.fit(get_parameters(model.encoder), {})

        expected = tmp_path / "client_0" / DECODER_CHECKPOINT
        assert expected.exists(), f"Decoder checkpoint not found: {expected}"

    def test_decoder_state_is_loadable_and_matches_model(self, tmp_path: Path) -> None:
        from datp.federated.parameters import get_parameters

        model = _make_ae()
        client = DatpFedRepClient(
            cid="c0",
            model=model,
            train_data=torch.randn(8, 4),
            val_data=torch.randn(4, 4),
            cfg=_mock_cfg(),
            decoder_ckpt_dir=tmp_path,
        )
        client.fit(get_parameters(model.encoder), {})

        saved_state = torch.load(
            tmp_path / "c0" / DECODER_CHECKPOINT, map_location="cpu", weights_only=True
        )
        current_state = {
            k: v.cpu() for k, v in model.decoder.state_dict().items()
        }
        for key in saved_state:
            assert torch.equal(saved_state[key], current_state[key]), (
                f"Decoder key {key!r} mismatch between saved checkpoint and current model"
            )

    def test_each_client_saves_to_its_own_dir(self, tmp_path: Path) -> None:
        from datp.federated.parameters import get_parameters

        model_a = _make_ae()
        model_b = _make_ae()

        for cid, model in [("alice", model_a), ("bob", model_b)]:
            client = DatpFedRepClient(
                cid=cid,
                model=model,
                train_data=torch.randn(8, 4),
                val_data=torch.randn(4, 4),
                cfg=_mock_cfg(),
                decoder_ckpt_dir=tmp_path,
            )
            client.fit(get_parameters(model.encoder), {})

        assert (tmp_path / "alice" / DECODER_CHECKPOINT).exists()
        assert (tmp_path / "bob" / DECODER_CHECKPOINT).exists()

    def test_decoder_persists_across_simulated_rounds(self, tmp_path: Path) -> None:
        """Prove that a second client construction loads the previously saved decoder."""
        from datp.federated.parameters import get_parameters

        torch.manual_seed(0)
        model = _make_ae()
        train_data = torch.randn(16, 4)
        val_data = torch.randn(8, 4)

        # Round 1: construct client, fit, decoder is trained and saved
        client_r1 = DatpFedRepClient(
            cid="c0",
            model=copy.deepcopy(model),
            train_data=train_data,
            val_data=val_data,
            cfg=_mock_cfg(),
            decoder_ckpt_dir=tmp_path,
        )
        torch.manual_seed(0)
        client_r1.fit(get_parameters(model.encoder), {})
        decoder_after_r1 = [p.detach().clone() for p in client_r1.model.decoder.parameters()]

        # Round 2: construct a NEW client (simulates Flower re-creating actors)
        fresh_model = copy.deepcopy(model)  # fresh random decoder

        client_r2 = DatpFedRepClient(
            cid="c0",
            model=fresh_model,
            train_data=train_data,
            val_data=val_data,
            cfg=_mock_cfg(),
            decoder_ckpt_dir=tmp_path,
        )

        # After construction, decoder should match round 1's saved state
        decoder_after_load = [p.detach().clone() for p in client_r2.model.decoder.parameters()]
        for r1_p, r2_p in zip(decoder_after_r1, decoder_after_load, strict=True):
            assert torch.equal(r1_p, r2_p), (
                "Client constructor must load previously saved decoder state"
            )


class TestScoreFedRepClients:
    """score_fedrep_clients() must use each client's own model."""

    @staticmethod
    def _make_client_data(n: int = 4, d: int = 4) -> ClientData:
        return ClientData(
            train=torch.randn(n, d),
            val=torch.randn(n, d),
            test_benign=torch.randn(n, d),
            test_attack=torch.randn(n, d),
        )

    def test_creates_parquets_for_all_clients_and_splits(
        self, tmp_path: Path
    ) -> None:
        from datp.artifacts.constants import PARQUET_SUFFIX

        client_data = {"c0": self._make_client_data(), "c1": self._make_client_data()}
        client_models = {cid: _make_ae() for cid in client_data}

        score_fedrep_clients(
            client_models=client_models,
            client_data=client_data,
            score_base=tmp_path,
            regime=Regime.A,
            seed=0,
            alpha=None,
            dataset="test_dataset",
            checkpoint_path=None,
            scoring_batch_size=4096,
        )

        for cid in client_data:
            for stage in ["cal", "test_benign", "test_attack"]:
                assert (tmp_path / stage / f"{cid}{PARQUET_SUFFIX}").exists()

    def test_manifest_is_complete(self, tmp_path: Path) -> None:
        from datp.scoring.generation import validate_scoring_manifest

        client_data = {"c0": self._make_client_data()}
        client_models = {"c0": _make_ae()}

        score_fedrep_clients(
            client_models=client_models,
            client_data=client_data,
            score_base=tmp_path,
            regime=Regime.A,
            seed=0,
            alpha=None,
            dataset="test_dataset",
            checkpoint_path=None,
            scoring_batch_size=4096,
        )

        manifest = validate_scoring_manifest(tmp_path)
        assert manifest["completion_status"] == "complete"

    def test_per_client_models_produce_different_scores(
        self, tmp_path: Path
    ) -> None:
        import polars as pl
        from datp.artifacts.constants import PARQUET_SUFFIX

        torch.manual_seed(0)
        model_c0 = _make_ae()
        torch.manual_seed(1)
        model_c1 = _make_ae()

        shared_data = torch.randn(8, 4)
        client_data = {
            "c0": ClientData(
                train=shared_data, val=shared_data,
                test_benign=shared_data, test_attack=shared_data,
            ),
            "c1": ClientData(
                train=shared_data, val=shared_data,
                test_benign=shared_data, test_attack=shared_data,
            ),
        }

        score_fedrep_clients(
            client_models={"c0": model_c0, "c1": model_c1},
            client_data=client_data,
            score_base=tmp_path,
            regime=Regime.A,
            seed=0,
            alpha=None,
            dataset="test_dataset",
            checkpoint_path=None,
            scoring_batch_size=4096,
        )

        from datp.artifacts.constants import SCORE_COLUMN

        scores_c0 = pl.read_parquet(tmp_path / "cal" / f"c0{PARQUET_SUFFIX}")[SCORE_COLUMN]
        scores_c1 = pl.read_parquet(tmp_path / "cal" / f"c1{PARQUET_SUFFIX}")[SCORE_COLUMN]
        assert not (scores_c0 == scores_c1).all(), (
            "Different models on same data should produce different scores"
        )


class TestRunFedRepTraining:
    """run_fedrep_training() must load per-client decoders and produce per-client scores."""

    def test_produces_per_client_score_files(self, tmp_path: Path) -> None:
        from datp.artifacts.constants import PARQUET_SUFFIX
        from datp.federated.simulation import TrainingResult
        import datp.federated.protocols.fedrep as fedrep_mod

        input_dim, hidden_dims = 4, [3, 2]
        client_data = {
            "c0": ClientData(
                train=torch.randn(8, input_dim), val=torch.randn(4, input_dim),
                test_benign=torch.randn(4, input_dim), test_attack=torch.randn(4, input_dim),
            ),
            "c1": ClientData(
                train=torch.randn(8, input_dim), val=torch.randn(4, input_dim),
                test_benign=torch.randn(4, input_dim), test_attack=torch.randn(4, input_dim),
            ),
        }

        # New path includes regime
        ckpt_dir = tmp_path / "fedrep" / "a" / "seed_0"
        ckpt_dir.mkdir(parents=True)

        # Simulate what run_fl_simulation (training) would produce.
        encoder_model = _make_ae(input_dim, hidden_dims)
        torch.save(encoder_model.state_dict(), ckpt_dir / MODEL_CHECKPOINT)
        for cid in client_data:
            decoder_dir = ckpt_dir / cid
            decoder_dir.mkdir()
            per_client = _make_ae(input_dim, hidden_dims)
            torch.save(per_client.decoder.state_dict(), decoder_dir / DECODER_CHECKPOINT)

        def _fake_run_fl_simulation(*args: object, **kwargs: object) -> TrainingResult:
            return TrainingResult(
                regime=Regime.A,
                seed=0,
                alpha=None,
                converged_round=1,
                total_rounds=1,
                checkpoint_dir=ckpt_dir,
                score_dir=ckpt_dir / "scores",
                loss_history=[],
            )

        cfg = MagicMock()
        cfg.model.input_dim = 4
        cfg.model.encoder_dims = [3, 2]
        cfg.model.activation = "relu"
        cfg.model.use_bn = False
        cfg.model.lr = 0.01
        cfg.federation.local_epochs = 1
        cfg.machine.batch_size_train = 8
        cfg.machine.scoring_batch_size = 4096
        cfg.regime = Regime.A

        cpu = torch.device("cpu")
        with (
            patch.object(fedrep_mod, "run_fl_simulation", _fake_run_fl_simulation),
            patch.object(fedrep_mod, "resolve_device", return_value=cpu),
        ):
            result = run_fedrep_training(
                cfg=cfg,
                client_data=client_data,
                seed=0,
                base_dir=tmp_path,
            )

        score_base = ckpt_dir / "scores"
        for cid in client_data:
            for stage in ["cal", "test_benign", "test_attack"]:
                assert (score_base / stage / f"{cid}{PARQUET_SUFFIX}").exists(), (
                    f"Missing score file: {cid}/{stage}"
                )

        assert result.checkpoint_dir == ckpt_dir


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
            classify_absorption(0.9),
            classify_absorption(0.5),
            classify_absorption(0.0),
        }
        assert len(classes) == 3
