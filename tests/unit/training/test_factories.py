# SPDX-License-Identifier: Proprietary
"""Tests for datp.training.factories — unified Flower client factory."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import torch
from flwr.common import Context
from flwr.common.record import RecordDict

from datp.training.factories import make_client_fn
from datp.training.protocols.fedprox import DatpFedProxClient
from datp.training.protocols.fedrep import DatpFedRepClient
from datp.training.scoring import ClientData


def _make_cfg() -> MagicMock:
    cfg = MagicMock()
    cfg.model.input_dim = 4
    cfg.model.hidden_dims = [3, 2]
    cfg.model.activation = "relu"
    cfg.model.use_bn = False
    cfg.model.lr = 0.01
    cfg.federation.local_epochs = 1
    cfg.machine.batch_size_train = 8
    return cfg


def _make_client_data() -> dict[str, ClientData]:
    return {
        "client_a": ClientData(
            train=torch.randn(16, 4),
            val=torch.randn(8, 4),
            test_benign=torch.randn(8, 4),
            test_attack=torch.randn(8, 4),
        ),
        "client_b": ClientData(
            train=torch.randn(16, 4),
            val=torch.randn(8, 4),
            test_benign=torch.randn(8, 4),
            test_attack=torch.randn(8, 4),
        ),
    }


def _make_context(partition_id: int) -> Context:
    return Context(
        run_id=0,
        node_id=0,
        node_config={"partition-id": str(partition_id)},
        state=RecordDict(),
        run_config={},
    )


class TestMakeClientFn:
    """Factory returns correct client types from in-memory data."""

    def test_returns_callable(self) -> None:
        cfg = _make_cfg()
        client_data = _make_client_data()
        client_ids = sorted(client_data.keys())
        fn = make_client_fn(client_data, client_ids, cfg, torch.device("cpu"))
        assert callable(fn)

    def test_default_client_cls(self) -> None:
        cfg = _make_cfg()
        client_data = _make_client_data()
        client_ids = sorted(client_data.keys())
        fn = make_client_fn(client_data, client_ids, cfg, torch.device("cpu"))
        client = fn(_make_context(0))
        assert client is not None

    def test_custom_client_cls_fedprox(self) -> None:
        cfg = _make_cfg()
        client_data = _make_client_data()
        client_ids = sorted(client_data.keys())
        fn = make_client_fn(
            client_data,
            client_ids,
            cfg,
            torch.device("cpu"),
            client_cls=DatpFedProxClient,
            extra_kwargs={"mu": 0.5},
        )
        client = fn(_make_context(0))
        assert client is not None

    def test_custom_client_cls_fedrep(self, tmp_path: Path) -> None:
        cfg = _make_cfg()
        client_data = _make_client_data()
        client_ids = sorted(client_data.keys())
        fn = make_client_fn(
            client_data,
            client_ids,
            cfg,
            torch.device("cpu"),
            client_cls=DatpFedRepClient,
            extra_kwargs={"decoder_ckpt_dir": tmp_path},
        )
        client = fn(_make_context(1))
        assert client is not None

    def test_partition_id_maps_to_correct_client(self) -> None:
        cfg = _make_cfg()
        client_data = _make_client_data()
        client_ids = sorted(client_data.keys())
        # Partition 0 -> first client, partition 1 -> second client.
        fn = make_client_fn(client_data, client_ids, cfg, torch.device("cpu"))
        # Both should produce valid clients without error.
        fn(_make_context(0))
        fn(_make_context(1))


class TestMakeClientFnPreparedDir:
    """Factory path using prepared_dir (lazy disk loading)."""

    def test_uses_discover_and_load(self, tmp_path: Path) -> None:
        cfg = _make_cfg()
        client_ids = ["client_a", "client_b"]
        client_data: dict[str, ClientData] = {}

        # Create directory structure.
        for cid in client_ids:
            d = tmp_path / cid
            d.mkdir()
            # Create dummy parquet files that load_single_client_training_data expects.
            # We mock the loading function instead.

        train_t = torch.randn(8, 4)
        cal_t = torch.randn(4, 4)

        with patch(
            "datp.training.factories.load_single_client_training_data",
            return_value=(train_t, cal_t),
        ), patch(
            "datp.training.factories.discover_client_dirs",
            return_value=[tmp_path / cid for cid in client_ids],
        ):
            fn = make_client_fn(
                client_data,
                client_ids,
                cfg,
                torch.device("cpu"),
                prepared_dir=tmp_path,
            )
            client = fn(_make_context(0))
            assert client is not None


class TestPreparedDirUpfrontValidation:
    """make_client_fn must fail upfront with a clear error when prepared_dir
    is missing a directory for one of the declared client_ids."""

    def test_missing_client_dir_raises_upfront(self, tmp_path: Path) -> None:
        cfg = _make_cfg()
        client_ids = ["client_a", "client_b", "client_missing"]
        client_data: dict[str, ClientData] = {}

        import pytest

        with patch(
            "datp.training.factories.discover_client_dirs",
            return_value=[tmp_path / "client_a", tmp_path / "client_b"],
        ):
            with pytest.raises(
                FileNotFoundError, match="Prepared client directories missing"
            ) as exc_info:
                make_client_fn(
                    client_data,
                    client_ids,
                    cfg,
                    torch.device("cpu"),
                    prepared_dir=tmp_path,
                )
            assert "client_missing" in str(exc_info.value)

    def test_all_client_dirs_present_returns_callable(self, tmp_path: Path) -> None:
        cfg = _make_cfg()
        client_ids = ["client_a", "client_b"]
        client_data: dict[str, ClientData] = {}

        with patch(
            "datp.training.factories.discover_client_dirs",
            return_value=[tmp_path / cid for cid in client_ids],
        ):
            fn = make_client_fn(
                client_data,
                client_ids,
                cfg,
                torch.device("cpu"),
                prepared_dir=tmp_path,
            )
            assert callable(fn)


class TestWorkerSideSeeding:
    """make_client_fn(seed=...) must seed the worker process at client_fn entry."""

    def test_seed_param_calls_set_seeds(self) -> None:
        cfg = _make_cfg()
        client_data = _make_client_data()
        client_ids = sorted(client_data.keys())

        with patch("datp.training.factories.set_seeds") as mock_seeds:
            fn = make_client_fn(
                client_data, client_ids, cfg, torch.device("cpu"), seed=42
            )
            fn(_make_context(0))
            fn(_make_context(1))

        assert mock_seeds.call_count == 2
        # partition 0 → seed^0 == 42, partition 1 → seed^1 == 43
        assert mock_seeds.call_args_list[0].args == (42,)
        assert mock_seeds.call_args_list[1].args == (43,)

    def test_no_seed_skips_set_seeds(self) -> None:
        cfg = _make_cfg()
        client_data = _make_client_data()
        client_ids = sorted(client_data.keys())

        with patch("datp.training.factories.set_seeds") as mock_seeds:
            fn = make_client_fn(client_data, client_ids, cfg, torch.device("cpu"))
            fn(_make_context(0))

        mock_seeds.assert_not_called()

    def test_seed_param_in_prepared_dir_path(self, tmp_path: Path) -> None:
        cfg = _make_cfg()
        client_ids = ["client_a", "client_b"]
        client_data: dict[str, ClientData] = {}
        train_t = torch.randn(8, 4)
        cal_t = torch.randn(4, 4)

        with patch(
            "datp.training.factories.discover_client_dirs",
            return_value=[tmp_path / cid for cid in client_ids],
        ), patch(
            "datp.training.factories.load_single_client_training_data",
            return_value=(train_t, cal_t),
        ), patch("datp.training.factories.set_seeds") as mock_seeds:
            fn = make_client_fn(
                client_data,
                client_ids,
                cfg,
                torch.device("cpu"),
                prepared_dir=tmp_path,
                seed=7,
            )
            fn(_make_context(1))

        mock_seeds.assert_called_once_with(7 ^ 1)
