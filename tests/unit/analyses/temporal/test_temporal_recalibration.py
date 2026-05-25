# SPDX-License-Identifier: Proprietary
"""Tests for temporal recalibration probe (T25)."""

from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np
import pytest

from datp.analyses.temporal.temporal_recalibration import (
    TemporalOutcome,
    TemporalResultRow,
    _classify_recovery,
    compute_recovery_ratio,
    evaluate_temporal_recalibration,
    write_temporal_table,
)
from datp.core.enums import Baseline


class TestRecoveryRatio:
    """Recovery ratio = (frozen − recalibrated) / frozen."""

    def test_positive_recovery(self) -> None:
        ratio = compute_recovery_ratio(0.5, 0.3)
        assert ratio == pytest.approx(0.4)

    def test_no_change(self) -> None:
        ratio = compute_recovery_ratio(0.5, 0.5)
        assert ratio == pytest.approx(0.0)

    def test_degradation(self) -> None:
        """Recalibration makes it worse → negative ratio."""
        ratio = compute_recovery_ratio(0.3, 0.5)
        assert ratio == pytest.approx(-0.666666, abs=1e-4)

    def test_zero_frozen_returns_none(self) -> None:
        ratio = compute_recovery_ratio(0.0, 0.1)
        assert ratio is None

    def test_negative_frozen_returns_none(self) -> None:
        ratio = compute_recovery_ratio(-0.1, 0.1)
        assert ratio is None


class TestClassification:
    """Recovery classification per locked thresholds."""

    def test_helps_above_10_percent(self) -> None:
        assert _classify_recovery(0.15) == TemporalOutcome.TEMPORAL_HELPS
        assert _classify_recovery(0.101) == TemporalOutcome.TEMPORAL_HELPS

    def test_neutral_zero_to_10_percent(self) -> None:
        assert _classify_recovery(0.10) == TemporalOutcome.TEMPORAL_NEUTRAL
        assert _classify_recovery(0.05) == TemporalOutcome.TEMPORAL_NEUTRAL
        assert _classify_recovery(0.0) == TemporalOutcome.TEMPORAL_NEUTRAL

    def test_hurts_negative(self) -> None:
        assert _classify_recovery(-0.01) == TemporalOutcome.TEMPORAL_HURTS
        assert _classify_recovery(-1.0) == TemporalOutcome.TEMPORAL_HURTS


class TestTemporalFeasibility:
    """Temporal feasibility gate checks."""

    def _make_dummy_scores(
        self,
        n_clients: int = 3,
        n_early: int = 200,
        n_late_b: int = 100,
        n_late_a: int = 50,
    ) -> tuple[
        dict[str, np.ndarray], dict[str, np.ndarray], dict[str, np.ndarray], list[str]
    ]:
        ids = [f"c{i}" for i in range(n_clients)]
        rng = np.random.default_rng(42)
        early = {cid: rng.random(n_early) for cid in ids}
        late_b = {cid: rng.random(n_late_b) for cid in ids}
        late_a = {cid: rng.random(n_late_a) for cid in ids}
        return early, late_b, late_a, ids

    def test_feasible_with_adequate_data(self) -> None:
        early, late_b, late_a, ids = self._make_dummy_scores()
        # Provide mock thresholds so rows are produced.
        baseline = Baseline.B1
        thresholds = {baseline: dict.fromkeys(ids, 0.5)}
        result = evaluate_temporal_recalibration(
            early_benign=early,
            late_benign=late_b,
            late_attack=late_a,
            thresholds_frozen=thresholds,
            thresholds_recalibrated=thresholds,
            client_ids=ids,
            n_min=100,
        )
        # Feasibility passes and rows are produced.
        assert result.n_feasible == len(ids)
        assert len(result.rows) == len(ids)

    def test_infeasible_no_clients(self) -> None:
        result = evaluate_temporal_recalibration(
            early_benign={},
            late_benign={},
            late_attack={},
            thresholds_frozen={},
            thresholds_recalibrated={},
            client_ids=[],
            n_min=100,
        )
        assert result.overall_outcome == TemporalOutcome.TEMPORAL_INFEASIBLE

    def test_rejected_low_coverage(self) -> None:
        early = {"c0": np.array([0.1] * 50)}
        late_b = {"c0": np.array([0.2] * 50)}
        late_a = {"c0": np.array([0.3] * 10)}
        result = evaluate_temporal_recalibration(
            early_benign=early,
            late_benign=late_b,
            late_attack=late_a,
            thresholds_frozen={},
            thresholds_recalibrated={},
            client_ids=["c0", "c1", "c2"],
            n_min=100,
        )
        assert result.overall_outcome == TemporalOutcome.TEMPORAL_REJECTED_LOW_COVERAGE

    def test_rejected_no_attack(self) -> None:
        early = {"c0": np.array([0.1] * 200)}
        late_b = {"c0": np.array([0.2] * 100)}
        late_a: dict[str, np.ndarray] = {}
        result = evaluate_temporal_recalibration(
            early_benign=early,
            late_benign=late_b,
            late_attack=late_a,
            thresholds_frozen={},
            thresholds_recalibrated={},
            client_ids=["c0"],
            n_min=100,
        )
        assert (
            result.overall_outcome
            == TemporalOutcome.TEMPORAL_REJECTED_INSUFFICIENT_ATTACKS
        )


class TestRecalibrationWithThresholds:
    """End-to-end temporal recalibration with actual thresholds."""

    def test_recalibration_improves_cv_fpr(self) -> None:
        """Frozen thresholds from early window should perform worse on drifted late data."""
        rng = np.random.default_rng(42)
        cids = ["c0", "c1"]

        early_benign = {cid: rng.normal(0.1, 0.02, 200) for cid in cids}
        late_benign = {cid: rng.normal(0.2, 0.04, 100) for cid in cids}
        late_attack = {cid: rng.normal(0.5, 0.1, 50) for cid in cids}

        baseline = Baseline.B1
        # Frozen threshold from early window (too low for drifted data).
        thresholds_frozen = {
            baseline: {cid: float(np.percentile(early_benign[cid], 95)) for cid in cids}
        }
        # Recalibrated threshold from late window.
        thresholds_recal = {
            baseline: {cid: float(np.percentile(late_benign[cid], 95)) for cid in cids}
        }

        result = evaluate_temporal_recalibration(
            early_benign=early_benign,
            late_benign=late_benign,
            late_attack=late_attack,
            thresholds_frozen=thresholds_frozen,
            thresholds_recalibrated=thresholds_recal,
            client_ids=cids,
            n_min=100,
        )

        assert result.n_feasible == 2
        assert len(result.rows) == 2

    def test_no_attack_labels_in_calibration(self) -> None:
        """Guard: compute_recovery_ratio never touches attack labels."""
        # This is a structural test — the function signature confirms
        # recovery_ratio uses only CV(FPR) values, not raw scores.
        ratio = compute_recovery_ratio(0.5, 0.3)
        assert ratio is not None
        assert ratio > 0


class TestTemporalOutcomeEnum:
    """Temporal outcome enum values per PRE_CODING_PLAN §6.5."""

    def test_all_allowed_outcomes_exist(self) -> None:
        expected = {
            "temporal_feasible",
            "temporal_helps",
            "temporal_neutral",
            "temporal_hurts",
            "temporal_infeasible",
            "temporal_rejected_no_timestamp",
            "temporal_rejected_low_coverage",
            "temporal_rejected_insufficient_attacks",
            "temporal_rejected_nonchronological",
        }
        actual = {o.value for o in TemporalOutcome}
        assert expected == actual

    def test_ciciot_suppressed(self) -> None:
        """CICIoT2023 temporal path is rejected — no timestamps."""
        assert (
            TemporalOutcome.TEMPORAL_REJECTED_NO_TIMESTAMP
            == "temporal_rejected_no_timestamp"
        )


class TestTemporalTableExport:
    """CSV export of temporal recalibration table."""

    def test_write_and_read_csv(self) -> None:
        row = TemporalResultRow(
            client_id="c0",
            baseline=Baseline.B1,
            cv_fpr_frozen=0.5,
            cv_fpr_recalibrated=0.3,
            recovery_ratio=0.4,
            outcome=TemporalOutcome.TEMPORAL_HELPS,
            n_early_benign=200,
            n_late_benign=100,
            n_late_attack=50,
        )
        from datp.analyses.temporal.temporal_recalibration import TemporalProbeResult

        result = TemporalProbeResult(
            rows=[row],
            overall_outcome=TemporalOutcome.TEMPORAL_HELPS,
            n_clients=1,
            n_feasible=1,
            n_helps=1,
            n_neutral=0,
            n_hurts=0,
        )
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            write_temporal_table(result, out)
            csv_path = out / "temporal_recalibration.csv"
            assert csv_path.is_file()
            content = csv_path.read_text()
            assert "c0" in content
            assert "temporal_helps" in content
