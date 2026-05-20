from __future__ import annotations

import inspect
from pathlib import Path

import polars as pl
import pytest
import torch.nn as nn

from datp.artifacts.constants import (
    SCALER_FILE,
)
from datp.artifacts.paths import ExperimentLocator
from datp.core.enums import Regime
from datp.data.common.storage import write_artifact
from datp.data.splits import Split, filename_for_split
from datp.training.fl.runner import (
    _save_checkpoint,
    _validate_paths,
    run_fl_training,
)


def _write_client(prepared_dir: Path, *, omit: str | None = None) -> None:
    client_dir = prepared_dir / "client_0"
    client_dir.mkdir(parents=True)
    df = pl.DataFrame({"f0": [0.0], "f1": [1.0]})
    for split in Split:
        artifact = filename_for_split(split)
        if artifact != omit:
            write_artifact(df, client_dir / artifact)
    if omit != SCALER_FILE:
        (client_dir / SCALER_FILE).write_bytes(b"scaler")


def test_validate_paths_accepts_complete_client(tmp_path: Path) -> None:
    prepared_dir = tmp_path / "prepared"
    _write_client(prepared_dir)

    _validate_paths(prepared_dir)


def test_validate_paths_rejects_missing_test_attack(tmp_path: Path) -> None:
    prepared_dir = tmp_path / "prepared"
    _write_client(prepared_dir, omit=filename_for_split(Split.TEST_ATTACK))

    with pytest.raises(FileNotFoundError, match="test_attack.parquet"):
        _validate_paths(prepared_dir)


def test_save_checkpoint_writes_final_path_atomically(tmp_path: Path) -> None:
    model = nn.Linear(2, 1)

    ckpt_file = _save_checkpoint(model, tmp_path)

    assert ckpt_file.name == "model.pt"
    assert ckpt_file.exists()
    assert not (tmp_path / "model.pt.tmp").exists()


# output_locator signature tests


class TestOutputLocatorSignature:
    def test_run_fl_training_accepts_output_locator(self) -> None:
        sig = inspect.signature(run_fl_training)
        p = sig.parameters.get("output_locator")
        assert p is not None, "run_fl_training must have output_locator parameter"
        assert p.default is None


class TestOutputLocatorRouting:
    def _capture_sim_calls(self, monkeypatch: pytest.MonkeyPatch) -> list[dict]:
        captured: list[dict] = []
        import datp.training.fl.runner as runner_mod

        def fake_sim(*args, **kwargs) -> object:
            captured.append(kwargs)
            raise RuntimeError("stop-in-sim")

        monkeypatch.setattr(runner_mod, "_run_fl_simulation", fake_sim)
        return captured

    def test_run_fl_training_with_output_locator(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from datp.config.compose import BASE_CONFIG

        seed = 3
        cfg = BASE_CONFIG.model_copy(update={"regime": Regime.A})
        loc = ExperimentLocator.for_main(tmp_path, Regime.A)
        captured = self._capture_sim_calls(monkeypatch)

        with pytest.raises(RuntimeError, match="stop-in-sim"):
            run_fl_training(cfg, {}, seed, output_locator=loc)

        assert len(captured) == 1
        assert captured[0]["ckpt_dir"] == loc.checkpoint(seed)
        assert captured[0]["score_base"] == loc.score(seed)

    def test_run_fl_training_default_locator_uses_base_dir_regime(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from datp.config.compose import BASE_CONFIG

        seed = 2
        base_dir = tmp_path / "outputs"
        cfg = BASE_CONFIG.model_copy(update={"regime": Regime.A})
        captured = self._capture_sim_calls(monkeypatch)

        with pytest.raises(RuntimeError, match="stop-in-sim"):
            run_fl_training(cfg, {}, seed, base_dir=base_dir)

        expected_loc = ExperimentLocator.for_main(base_dir, cfg.regime)
        assert captured[0]["ckpt_dir"] == expected_loc.checkpoint(seed)
        assert captured[0]["score_base"] == expected_loc.score(seed)


class TestConvergenceSummaryStatus:
    def test_converged_status_uses_enum_value(self, tmp_path: Path) -> None:
        import json
        from datp.audit.enums import ConvergenceStatus
        from datp.training.fl.runner import _save_convergence_artifacts

        _save_convergence_artifacts(
            tmp_path,
            [0.5, 0.4, 0.3],
            converged_round=3,
            criterion_value=0.001,
            rounds_initial=40,
            rounds_max=150,
            relative_threshold=0.005,
            window=10,
        )
        summary = json.loads((tmp_path / "convergence_summary.json").read_text())
        assert summary["convergence_status"] == ConvergenceStatus.CONVERGED

    def test_not_converged_status_uses_enum_value(self, tmp_path: Path) -> None:
        import json
        from datp.audit.enums import ConvergenceStatus
        from datp.training.fl.runner import _save_convergence_artifacts

        _save_convergence_artifacts(
            tmp_path,
            [0.5, 0.4, 0.3],
            converged_round=None,
            criterion_value=None,
            rounds_initial=40,
            rounds_max=150,
            relative_threshold=0.005,
            window=10,
        )
        summary = json.loads((tmp_path / "convergence_summary.json").read_text())
        assert summary["convergence_status"] == ConvergenceStatus.NOT_CONVERGED

    def test_convergence_summary_includes_all_required_fields(
        self, tmp_path: Path
    ) -> None:
        import json
        from datp.training.fl.runner import _save_convergence_artifacts

        _save_convergence_artifacts(
            tmp_path,
            [0.5, 0.4],
            converged_round=2,
            criterion_value=0.002,
            rounds_initial=40,
            rounds_max=150,
            relative_threshold=0.005,
            window=10,
        )
        summary = json.loads((tmp_path / "convergence_summary.json").read_text())
        required = {
            "rounds_initial",
            "rounds_max",
            "relative_threshold",
            "window",
            "actual_rounds_run",
            "convergence_round",
            "convergence_status",
            "weighted_validation_loss_per_round",
        }
        assert required.issubset(summary.keys())
        assert summary["rounds_initial"] == 40
        assert summary["rounds_max"] == 150
        assert abs(summary["relative_threshold"] - 0.005) < 1e-9
        assert summary["window"] == 10
