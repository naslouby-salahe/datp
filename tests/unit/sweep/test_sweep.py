from __future__ import annotations

from pathlib import Path

from datp.core.enums import Baseline, Regime
from datp.core.identity import RunIdentity
from datp.sweep.run_sweep import SweepResult, build_experiment_matrix, run_sweep
from datp.sweep.validator import validate_sweep
from tests.fixtures.payloads import valid_metrics_json


class TestBuildExperimentMatrix:
    def test_total_count(self):
        cells = build_experiment_matrix()
        assert len(cells) == 135

    def test_regime_a_count(self):
        cells = build_experiment_matrix()
        regime_a = [c for c in cells if c.regime == "a"]
        assert len(regime_a) == 25

    def test_regime_b_count(self):
        cells = build_experiment_matrix()
        regime_b = [c for c in cells if c.regime == "b"]
        assert len(regime_b) == 20

    def test_regime_c_count(self):
        cells = build_experiment_matrix()
        regime_c = [c for c in cells if c.regime == "c"]
        assert len(regime_c) == 90

    def test_b3_only_regime_a(self):
        cells = build_experiment_matrix()
        b3_cells = [c for c in cells if c.baseline == "b3"]
        assert all(c.regime == "a" for c in b3_cells)
        assert len(b3_cells) > 0

    def test_b0_in_regime_a_and_b_only(self):
        cells = build_experiment_matrix()
        b0_cells = [c for c in cells if c.baseline == "b0"]
        assert all(c.regime in ("a", "b") for c in b0_cells)
        assert len(b0_cells) > 0

    def test_b0_not_in_regime_c(self):
        cells = build_experiment_matrix()
        regime_c = [c for c in cells if c.regime == "c"]
        assert all(c.baseline != "b0" for c in regime_c)

    def test_cells_are_experiment_cell_instances(self):
        cells = build_experiment_matrix()
        assert all(isinstance(c, RunIdentity) for c in cells)


class TestValidateSweep:
    def test_all_valid(self):
        cells = build_experiment_matrix()
        errors, configs = validate_sweep(cells)
        assert errors == []
        assert len(configs) == len(cells)


class TestRunSweep:
    def test_dry_run_exits_cleanly(self, tmp_path: Path):
        result = run_sweep(dry_run=True, base_dir=tmp_path, regime=None)
        assert isinstance(result, SweepResult)
        assert result.total == 135
        assert result.completed == 0
        assert result.failed == 0

    def test_skips_completed_runs(self, tmp_path: Path):
        from unittest.mock import patch

        baseline, regime, seed = Baseline.B1, Regime.A, 0

        from datp.artifacts.paths import ExperimentLocator

        rp = ExperimentLocator.for_main(tmp_path, regime).result(baseline, seed)
        rp.mkdir(parents=True, exist_ok=True)
        (rp / "metrics.json").write_text(valid_metrics_json("b1", "a", 0))

        _fail = RuntimeError("no data — mocked for unit test")
        # Patch the executor methods used by run_sweep's new architecture.
        with (
            patch(
                "datp.pipeline.executor.SharedTrainingExecutor.build_context",
                side_effect=_fail,
            ),
            patch(
                "datp.pipeline.executor.IsolatedBaselineExecutor.run",
                side_effect=_fail,
            ),
        ):
            result = run_sweep(dry_run=False, base_dir=tmp_path, regime="a")

        assert result.skipped >= 1
        assert result.failed == result.total - result.skipped
