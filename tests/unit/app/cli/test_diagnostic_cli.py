from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from datp.app.cli import app
from datp.core.enums import Regime
from datp.experiments.diagnostic import DiagnosticRequest


def _registered_commands() -> set[str]:
    return {cmd.name for cmd in app.registered_commands if cmd.name is not None}


class TestDiagnosticDRegistered:
    def test_diagnostic_d_command_registered(self) -> None:
        assert "diagnostic-d" in _registered_commands()

    def test_all_diagnostic_commands_registered(self) -> None:
        commands = _registered_commands()
        assert "diagnostic" in commands
        assert "diagnostic-b" in commands
        assert "diagnostic-c" in commands
        assert "diagnostic-d" in commands


class TestDiagnosticDRequest:
    def test_diagnostic_d_builds_regime_d_request(self, tmp_path: Path) -> None:
        from datp.app.cli.diagnostic import diagnostic_d

        captured: list[DiagnosticRequest] = []

        def fake_dispatch(request: DiagnosticRequest) -> None:
            captured.append(request)

        with patch("datp.app.cli.diagnostic._dispatch", side_effect=fake_dispatch):
            diagnostic_d(
                raw_dir=tmp_path / "raw",
                output_dir=tmp_path / "out",
                data_root=tmp_path,
                seed=3,
                skip_prepare=True,
            )

        assert len(captured) == 1
        req = captured[0]
        assert req.regime == Regime.D
        assert req.seed == 3
        assert req.alpha is None
        assert req.diagnostic_tag == "regime_d_b1_vs_b2"
        assert req.extras_fn is None

    def test_diagnostic_d_run_dir_uses_regime_d_label(self, tmp_path: Path) -> None:
        from datp.app.cli.diagnostic import diagnostic_d

        captured: list[DiagnosticRequest] = []

        with patch("datp.app.cli.diagnostic._dispatch", side_effect=lambda r: captured.append(r)):
            diagnostic_d(
                raw_dir=tmp_path / "raw",
                output_dir=tmp_path / "out",
                data_root=tmp_path,
                seed=0,
                skip_prepare=True,
            )

        assert "regime_d" in str(captured[0].run_dir)
        assert "seed0" in str(captured[0].run_dir)
