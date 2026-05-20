from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from datp.cli import main
from datp.cli.config import preview_config
from datp.config.compose import ComposeError, compose_config


class TestComposeConfig:
    def test_basic_composition(self) -> None:
        cfg = compose_config(regime="a", baseline="b1", seed=0)
        assert cfg.regime == "a"
        assert cfg.baseline == "b1"
        assert cfg.seed == 0
        assert cfg.model.input_dim == 115
        assert cfg.federation.convergence.rounds_initial == 40
        assert cfg.threshold.q == 0.95

    def test_regime_c_requires_alpha(self) -> None:
        with pytest.raises(ComposeError, match="alpha is required for regime c"):
            compose_config(regime="c", baseline="b1", seed=0)

    def test_regime_c_with_alpha(self) -> None:
        cfg = compose_config(regime="c", baseline="b1", seed=0, alpha=0.5)
        assert cfg.alpha == 0.5

    def test_b3_only_regime_a(self) -> None:
        with pytest.raises(ComposeError, match="B3 is only valid for regime a"):
            compose_config(regime="b", baseline="b3", seed=0)

    def test_b0_regime_c_fails(self) -> None:
        with pytest.raises(ComposeError, match="B0 is not valid for regime c"):
            compose_config(regime="c", baseline="b0", seed=0, alpha=0.1)

    def test_invalid_regime(self) -> None:
        with pytest.raises(ComposeError, match="Invalid regime"):
            compose_config(regime="z", baseline="b1", seed=0)

    def test_invalid_baseline(self) -> None:
        with pytest.raises(ComposeError, match="Invalid baseline"):
            compose_config(regime="a", baseline="b9", seed=0)

    def test_case_insensitive(self) -> None:
        cfg = compose_config(regime="A", baseline="B1", seed=0)
        assert cfg.regime == "a"
        assert cfg.baseline == "b1"

    def test_alpha_absent_when_not_regime_c(self) -> None:
        cfg = compose_config(regime="a", baseline="b1", seed=0)
        assert cfg.alpha is None

    def test_deep_copy_isolation(self) -> None:
        cfg1 = compose_config(regime="a", baseline="b1", seed=0)
        cfg2 = compose_config(regime="a", baseline="b1", seed=1)
        # Frozen model — assignment should raise
        with pytest.raises(Exception):
            cfg1.model.input_dim = 999
        assert cfg2.model.input_dim == 115


class TestPreviewConfig:
    def test_writes_resolved_config(self, tmp_path: Path) -> None:
        dest = preview_config(
            regime="a",
            baseline="b1",
            seed=0,
            output_dir=tmp_path,
        )
        assert dest.exists()
        assert dest.name == "resolved_config.yaml"
        content = yaml.safe_load(dest.read_text())
        assert content["regime"] == "a"
        assert content["baseline"] == "b1"
        assert content["seed"] == 0

    def test_default_output_path(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        dest = preview_config(regime="b", baseline="b2", seed=42)
        assert dest.parent == Path("outputs/results/b/b2/seed_42")
        assert dest.name == "resolved_config.yaml"

    def test_regime_c_output_path_includes_alpha(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        dest = preview_config(regime="c", baseline="b1", seed=0, alpha=0.5)
        assert str(dest).endswith("seed_0/alpha_0.5/resolved_config.yaml")

    def test_validation_failure_propagates(self, tmp_path: Path) -> None:
        with pytest.raises(ComposeError, match="Invalid regime"):
            preview_config(regime="z", baseline="b1", seed=0, output_dir=tmp_path)

    def test_yaml_is_valid(self, tmp_path: Path) -> None:
        dest = preview_config(regime="a", baseline="b4", seed=7, output_dir=tmp_path)
        content = yaml.safe_load(dest.read_text())
        assert isinstance(content, dict)
        assert content["federation"]["convergence"]["rounds_max"] == 150


class TestCLI:
    def test_preview_exits_zero(self, tmp_path: Path) -> None:
        rc = main(
            [
                "config",
                "preview",
                "--regime=a",
                "--baseline=b1",
                "--seed=0",
                f"--output-dir={tmp_path}",
            ]
        )
        assert rc == 0
        assert (tmp_path / "resolved_config.yaml").exists()

    def test_preview_invalid_regime_exits_one(self, tmp_path: Path) -> None:
        rc = main(
            [
                "config",
                "preview",
                "--regime=z",
                "--baseline=b1",
                "--seed=0",
                f"--output-dir={tmp_path}",
            ]
        )
        assert rc != 0

    def test_no_command_exits_one(self) -> None:
        rc = main([])
        assert rc == 1

    def test_training_not_invoked(self, tmp_path: Path) -> None:
        rc = main(
            [
                "config",
                "preview",
                "--regime=a",
                "--baseline=b1",
                "--seed=0",
                f"--output-dir={tmp_path}",
            ]
        )
        assert rc == 0
        content = yaml.safe_load((tmp_path / "resolved_config.yaml").read_text())
        assert "regime" in content
        assert not (tmp_path / "metrics.json").exists()
