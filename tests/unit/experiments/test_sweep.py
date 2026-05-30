from __future__ import annotations

from pathlib import Path

from datp.core.enums import Baseline, Regime
from datp.core.identity import BaselineRunId
from datp.experiments.sweep import SweepResult, build_experiment_matrix, run_sweep
from datp.experiments.validator import validate_sweep
from tests.fixtures.payloads import valid_metrics_json

_TOTAL_CELLS = 310
_REGIME_A_CELLS = 50
_REGIME_B_CELLS = 40
_REGIME_C_CELLS = 180
_REGIME_D_CELLS = 40


class TestBuildExperimentMatrix:
    def test_total_count(self):
        cells = build_experiment_matrix()
        assert len(cells) == _TOTAL_CELLS

    def test_regime_a_count(self):
        cells = build_experiment_matrix()
        regime_a = [c for c in cells if c.regime == Regime.A]
        assert len(regime_a) == _REGIME_A_CELLS

    def test_regime_b_count(self):
        cells = build_experiment_matrix()
        regime_b = [c for c in cells if c.regime == Regime.B]
        assert len(regime_b) == _REGIME_B_CELLS

    def test_regime_c_count(self):
        cells = build_experiment_matrix()
        regime_c = [c for c in cells if c.regime == Regime.C]
        assert len(regime_c) == _REGIME_C_CELLS

    def test_regime_d_count(self):
        cells = build_experiment_matrix()
        regime_d = [c for c in cells if c.regime == Regime.D]
        assert len(regime_d) == _REGIME_D_CELLS

    def test_b3_only_regime_a(self):
        cells = build_experiment_matrix()
        b3_cells = [c for c in cells if c.baseline == Baseline.B3]
        assert all(c.regime == Regime.A for c in b3_cells)
        assert len(b3_cells) > 0

    def test_b0_in_non_dirichlet_regimes_only(self):
        cells = build_experiment_matrix()
        b0_cells = [c for c in cells if c.baseline == Baseline.B0]
        assert all(c.regime in (Regime.A, Regime.B, Regime.D) for c in b0_cells)
        assert len(b0_cells) > 0

    def test_b0_not_in_regime_c(self):
        cells = build_experiment_matrix()
        regime_c = [c for c in cells if c.regime == Regime.C]
        assert all(c.baseline != Baseline.B0 for c in regime_c)

    def test_cells_are_experiment_cell_instances(self):
        cells = build_experiment_matrix()
        assert all(isinstance(c, BaselineRunId) for c in cells)


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
        assert result.total == _TOTAL_CELLS
        assert result.completed == 0
        assert result.failed == 0

    def test_skips_completed_runs(self, tmp_path: Path):
        from unittest.mock import patch

        baseline, regime, seed = Baseline.B1, Regime.A, 0

        from datp.artifacts.layout import ArtifactLayout
        from datp.core.identity import TrainingCellId

        run = BaselineRunId(
            cell=TrainingCellId(regime=regime, seed=seed, alpha=None),
            baseline=baseline,
        )
        rp = ArtifactLayout(base_dir=tmp_path, regime=regime).baseline_run(run).result_dir
        rp.mkdir(parents=True, exist_ok=True)
        (rp / "metrics.json").write_text(valid_metrics_json("b1", "a", 0))

        _fail = RuntimeError("no data — mocked for unit test")
        # Patch the executor methods used by run_sweep's new architecture.
        with (
            patch(
                "datp.experiments.executor.SharedTrainingExecutor.build_context",
                side_effect=_fail,
            ),
            patch(
                "datp.experiments.executor.IsolatedBaselineExecutor.run",
                side_effect=_fail,
            ),
        ):
            result = run_sweep(dry_run=False, base_dir=tmp_path, regime=Regime.A)

        assert result.skipped >= 1
        assert result.failed == result.total - result.skipped
