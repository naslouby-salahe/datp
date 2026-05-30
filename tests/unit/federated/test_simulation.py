from __future__ import annotations

import inspect
from pathlib import Path

import polars as pl
import pytest
import torch.nn as nn

from datp.artifacts.layout import ArtifactLayout
from datp.artifacts.names import ArtifactFile
from datp.core.enums import Regime
from datp.core.identity import TrainingCellId
from datp.data.common.storage import write_artifact
from datp.data.splits import Split, filename_for_split
from datp.federated.checkpoints import save_checkpoint
from datp.federated.protocols.fedavg import run_fl_training


from datp.federated.catalog import TrainingClientCatalog


def _write_client(prepared_dir: Path, *, omit: str | None = None) -> None:
    client_dir = prepared_dir / "client_0"
    client_dir.mkdir(parents=True)
    df = pl.DataFrame({"f0": [0.0], "f1": [1.0]})
    for split in Split:
        artifact = filename_for_split(split)
        if artifact != omit:
            write_artifact(df, client_dir / artifact)
    if omit != ArtifactFile.SCALER:
        (client_dir / ArtifactFile.SCALER).write_bytes(b"scaler")


def test_validate_paths_accepts_complete_client(tmp_path: Path) -> None:
    prepared_dir = tmp_path / "prepared"
    _write_client(prepared_dir)

    catalog = TrainingClientCatalog(prepared_dir=prepared_dir)
    catalog.validate_prepared_splits()


def test_validate_paths_rejects_missing_test_attack(tmp_path: Path) -> None:
    prepared_dir = tmp_path / "prepared"
    _write_client(prepared_dir, omit=filename_for_split(Split.TEST_ATTACK))

    catalog = TrainingClientCatalog(prepared_dir=prepared_dir)
    with pytest.raises(FileNotFoundError, match="test_attack.parquet"):
        catalog.validate_prepared_splits()


def test_save_checkpoint_writes_final_path_atomically(tmp_path: Path) -> None:
    model = nn.Linear(2, 1)

    ckpt_file = save_checkpoint(model, tmp_path)

    assert ckpt_file.name == "model.pt"
    assert ckpt_file.exists()
    assert not (tmp_path / "model.pt.tmp").exists()


class TestOutputLayoutSignature:
    def test_run_fl_training_accepts_output_layout(self) -> None:
        sig = inspect.signature(run_fl_training)
        p = sig.parameters.get("output_layout")
        assert p is not None, "run_fl_training must have output_layout parameter"
        assert p.default is None


class TestOutputLayoutRouting:
    def _capture_sim_calls(self, monkeypatch: pytest.MonkeyPatch) -> list[dict]:
        captured: list[dict] = []
        import datp.federated.protocols.fedavg as fedavg_mod
        import datp.federated.simulation as sim_mod

        def fake_sim(*args, **kwargs) -> object:
            captured.append(kwargs)
            raise RuntimeError("stop-in-sim")

        monkeypatch.setattr(sim_mod, "run_fl_simulation", fake_sim)
        monkeypatch.setattr(fedavg_mod, "run_fl_simulation", fake_sim)
        return captured

    def test_run_fl_training_with_output_layout(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from datp.config.compose import BASE_CONFIG

        seed = 3
        cfg = BASE_CONFIG.model_copy(update={"regime": Regime.A})
        layout = ArtifactLayout(base_dir=tmp_path, regime=Regime.A)
        cell = TrainingCellId(regime=Regime.A, seed=seed, alpha=None)
        captured = self._capture_sim_calls(monkeypatch)

        with pytest.raises(RuntimeError, match="stop-in-sim"):
            run_fl_training(cfg, {}, seed, output_layout=layout)

        assert len(captured) == 1
        assert captured[0]["ckpt_dir"] == layout.checkpoint_dir(cell)


class TestClientDataNotMutated:
    """run_fl_simulation must not clear the caller's client_data dict."""

    def test_client_data_keys_preserved_when_prepared_dir_set(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        import datp.federated.simulation as sim_mod

        sentinel: dict[str, object] = {"client_data_at_call": None}

        def fake_make_client_fn(
            client_data: dict,
            client_ids: list,
            cfg: object,
            device: object,
            **kwargs: object,
        ) -> object:
            sentinel["client_data_at_call"] = dict(client_data)
            raise RuntimeError("stop-early")

        from unittest.mock import MagicMock

        mock_strategy = MagicMock()

        class _FakeCatalog:
            def __init__(self, **_kw: object) -> None:
                pass

            client_ids = ["client_0"]
            num_clients = 1

            def validate_prepared_splits(self) -> None:
                pass

        monkeypatch.setattr(sim_mod, "TrainingClientCatalog", _FakeCatalog)
        monkeypatch.setattr(sim_mod, "make_client_fn", fake_make_client_fn)
        monkeypatch.setattr(
            sim_mod,
            "_validate_regime",
            lambda cfg: __import__("datp.core.enums", fromlist=["Regime"]).Regime.A,
        )
        monkeypatch.setattr(
            sim_mod, "resolve_device", lambda _: __import__("torch").device("cpu")
        )
        monkeypatch.setattr(sim_mod, "set_seeds", lambda _: None)
        monkeypatch.setattr(
            sim_mod, "_init_model_and_params", lambda *a, **k: (None, None, None)
        )

        from datp.scoring.generation import ClientData

        import torch

        original_data: dict[str, ClientData] = {
            "client_0": ClientData(
                train=torch.zeros(4, 2),
                val=torch.zeros(2, 2),
                test_benign=torch.zeros(2, 2),
                test_attack=torch.zeros(2, 2),
            )
        }
        prepared_dir = tmp_path / "prepared"

        mock_cfg = MagicMock()
        mock_cfg.machine.require_cuda = False

        with pytest.raises(RuntimeError, match="stop-early"):
            sim_mod.run_fl_simulation(
                cfg=mock_cfg,
                client_data=original_data,
                seed=0,
                alpha=None,
                model_cls=None,  # type: ignore[arg-type]
                build_strategy=lambda *a: mock_strategy,
                ckpt_dir=tmp_path,
                score_base=tmp_path,
                label="test",
                prepared_dir=prepared_dir,
            )

        assert set(original_data.keys()) == {"client_0"}, (
            "client_data must not be mutated by run_fl_simulation"
        )


class TestRayShutdownOwnership:
    """_execute_flower_simulation must not shut down Ray when it was initialized
    by an external caller — only the owner of init should call shutdown."""

    def _patch_common(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import datp.federated.simulation as sim_mod

        monkeypatch.setattr(sim_mod, "configure_runtime_env", lambda: None)
        monkeypatch.setattr(sim_mod, "ensure_ray_memory_threshold", lambda _: None)
        monkeypatch.setattr(
            sim_mod,
            "derive_client_resources",
            lambda **_kw: {"num_cpus": 1.0, "num_gpus": 0.0},
        )
        monkeypatch.setattr(sim_mod, "start_simulation", lambda **kwargs: None)

    def test_shutdown_called_when_ray_not_already_initialized(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import datp.federated.simulation as sim_mod
        from datp.config.compose import BASE_CONFIG

        self._patch_common(monkeypatch)
        monkeypatch.setattr(sim_mod.ray, "is_initialized", lambda: False)

        called: dict[str, int] = {"shutdown": 0}

        def fake_shutdown() -> None:
            called["shutdown"] += 1

        monkeypatch.setattr(sim_mod.ray, "shutdown", fake_shutdown)

        sim_mod._execute_flower_simulation(
            BASE_CONFIG,
            lambda _ctx: None,
            1,
            None,
            "test",  # type: ignore[arg-type]
        )

        assert called["shutdown"] == 1

    def test_shutdown_skipped_when_ray_externally_initialized(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import datp.federated.simulation as sim_mod
        from datp.config.compose import BASE_CONFIG

        self._patch_common(monkeypatch)
        monkeypatch.setattr(sim_mod.ray, "is_initialized", lambda: True)

        called: dict[str, int] = {"shutdown": 0}

        def fake_shutdown() -> None:
            called["shutdown"] += 1

        monkeypatch.setattr(sim_mod.ray, "shutdown", fake_shutdown)

        sim_mod._execute_flower_simulation(
            BASE_CONFIG,
            lambda _ctx: None,
            1,
            None,
            "test",  # type: ignore[arg-type]
        )

        assert called["shutdown"] == 0

    def test_shutdown_still_skipped_when_simulation_raises(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import datp.federated.simulation as sim_mod
        from datp.config.compose import BASE_CONFIG

        monkeypatch.setattr(sim_mod, "configure_runtime_env", lambda: None)
        monkeypatch.setattr(sim_mod, "ensure_ray_memory_threshold", lambda _: None)
        monkeypatch.setattr(
            sim_mod,
            "derive_client_resources",
            lambda **_kw: {"num_cpus": 1.0, "num_gpus": 0.0},
        )

        def boom(**_kwargs) -> None:
            raise RuntimeError("sim-boom")

        monkeypatch.setattr(sim_mod, "start_simulation", boom)
        monkeypatch.setattr(sim_mod.ray, "is_initialized", lambda: True)

        called: dict[str, int] = {"shutdown": 0}

        def fake_shutdown() -> None:
            called["shutdown"] += 1

        monkeypatch.setattr(sim_mod.ray, "shutdown", fake_shutdown)

        with pytest.raises(RuntimeError, match="sim-boom"):
            sim_mod._execute_flower_simulation(
                BASE_CONFIG,
                lambda _ctx: None,
                1,
                None,
                "test",  # type: ignore[arg-type]
            )

        assert called["shutdown"] == 0
