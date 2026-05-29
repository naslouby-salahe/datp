# SPDX-License-Identifier: Proprietary
"""Tests for stress-test absorption analysis (T19)."""

from __future__ import annotations

import math
import tempfile
from pathlib import Path

import numpy as np
import pytest

from datp.analyses.robustness.stress_test_absorption import (
    AbsorptionRow,
    AbsorptionTable,
    StressTestKind,
    _compute_cv_fpr,
    compute_absorption_ratio,
    write_absorption_table,
)
from datp.core.enums import (
    AbsorptionClass,
    Baseline,
    Regime,
    classify_absorption,
)
from datp.evaluation.metrics import ClientMetrics


def _cm(
    client_id: str,
    fpr: float,
    tpr: float,
    balanced_accuracy: float,
    macro_f1: float,
    confusion_matrix: dict[str, int],
    n_benign: int,
    n_attack: int,
) -> ClientMetrics:
    """Helper that fills tnr/fnr/precision/recall from confusion matrix."""
    tp = confusion_matrix.get("tp", 0)
    fp = confusion_matrix.get("fp", 0)
    fn = confusion_matrix.get("fn", 0)
    return ClientMetrics(
        client_id=client_id,
        fpr=fpr,
        tpr=tpr,
        tnr=1.0 - fpr,
        fnr=1.0 - tpr,
        precision=tp / (tp + fp) if (tp + fp) > 0 else math.nan,
        recall=tp / (tp + fn) if (tp + fn) > 0 else math.nan,
        balanced_accuracy=balanced_accuracy,
        macro_f1=macro_f1,
        confusion_matrix=confusion_matrix,
        n_benign=n_benign,
        n_attack=n_attack,
    )


class TestAbsorptionRatio:
    """Absorption ratio = Δ_stress / Δ_FedAvg, classified per locked thresholds."""

    def test_ratio_strong_retention(self) -> None:
        ratio, cls = compute_absorption_ratio(delta_stress=0.8, delta_fedavg=0.8)
        assert ratio == pytest.approx(1.0)
        assert cls == AbsorptionClass.STRONG_RETENTION

    def test_ratio_partial(self) -> None:
        ratio, cls = compute_absorption_ratio(delta_stress=0.4, delta_fedavg=0.8)
        assert ratio == pytest.approx(0.5)
        assert cls == AbsorptionClass.PARTIAL

    def test_ratio_near_full(self) -> None:
        ratio, cls = compute_absorption_ratio(delta_stress=0.1, delta_fedavg=0.8)
        assert ratio == pytest.approx(0.125)
        assert cls == AbsorptionClass.NEAR_FULL

    def test_ratio_negative_b1_b2_reversal(self) -> None:
        """When B2 better than B1 (CV(FPR)[B1] < CV(FPR)[B2]), Δ negative."""
        ratio, cls = compute_absorption_ratio(delta_stress=0.1, delta_fedavg=0.8)
        assert ratio is not None
        assert cls is not None

        # But when Δ_FedAvg ≤ 0, absorption is undefined.
        ratio, cls = compute_absorption_ratio(delta_stress=0.1, delta_fedavg=-0.2)
        assert ratio is None
        assert cls is None

    def test_zero_delta_fedavg_undefined(self) -> None:
        ratio, cls = compute_absorption_ratio(delta_stress=0.1, delta_fedavg=0.0)
        assert ratio is None
        assert cls is None

    def test_classification_at_boundaries(self) -> None:
        """Boundary values per PRE_CODING_PLAN §6.4."""
        assert classify_absorption(0.75) == AbsorptionClass.STRONG_RETENTION
        assert classify_absorption(0.7499) == AbsorptionClass.PARTIAL
        assert classify_absorption(0.25) == AbsorptionClass.PARTIAL
        assert classify_absorption(0.2499) == AbsorptionClass.NEAR_FULL
        assert classify_absorption(0.0) == AbsorptionClass.NEAR_FULL
        assert classify_absorption(-0.1) == AbsorptionClass.NEAR_FULL


class TestCvFprComputation:
    """CV(FPR) computed from eligible-client metrics only."""

    def test_all_eligible(self) -> None:
        metrics = [
            _cm(
                client_id="c1",
                fpr=0.1,
                tpr=0.9,
                balanced_accuracy=0.9,
                macro_f1=0.9,
                confusion_matrix={"tp": 9, "fp": 1, "tn": 9, "fn": 1},
                n_benign=10,
                n_attack=10,
            ),
            _cm(
                client_id="c2",
                fpr=0.3,
                tpr=0.8,
                balanced_accuracy=0.75,
                macro_f1=0.75,
                confusion_matrix={"tp": 8, "fp": 3, "tn": 7, "fn": 2},
                n_benign=10,
                n_attack=10,
            ),
        ]
        r = _compute_cv_fpr(metrics, ["c1", "c2"])
        assert r.eligible_count == 2
        assert r.client_count == 2
        assert r.coverage == pytest.approx(1.0)
        # CV = std / mean = 0.1414 / 0.2 ≈ 0.707
        assert r.cv_fpr > 0
        assert r.mean_fpr == pytest.approx(0.2)

    def test_partial_eligibility(self) -> None:
        metrics = [
            _cm(
                client_id="c1",
                fpr=0.1,
                tpr=0.9,
                balanced_accuracy=0.9,
                macro_f1=0.9,
                confusion_matrix={"tp": 9, "fp": 1, "tn": 9, "fn": 1},
                n_benign=10,
                n_attack=10,
            ),
            _cm(
                client_id="c2",
                fpr=0.5,
                tpr=0.7,
                balanced_accuracy=0.6,
                macro_f1=0.6,
                confusion_matrix={"tp": 7, "fp": 5, "tn": 5, "fn": 3},
                n_benign=10,
                n_attack=10,
            ),
        ]
        r = _compute_cv_fpr(metrics, ["c1"])
        assert r.eligible_count == 1
        assert r.client_count == 2
        assert r.coverage == pytest.approx(0.5)
        assert r.mean_fpr == pytest.approx(0.1)

    def test_no_eligible(self) -> None:
        metrics = [
            _cm(
                client_id="c1",
                fpr=0.1,
                tpr=0.9,
                balanced_accuracy=0.9,
                macro_f1=0.9,
                confusion_matrix={"tp": 9, "fp": 1, "tn": 9, "fn": 1},
                n_benign=10,
                n_attack=10,
            ),
        ]
        r = _compute_cv_fpr(metrics, [])
        assert r.cv_fpr == pytest.approx(0.0)
        assert np.isnan(r.mean_fpr)
        assert r.eligible_count == 0
        assert r.client_count == 1
        assert r.coverage == pytest.approx(0.0)

    def test_single_eligible_cv_zero(self) -> None:
        """Single value → CV is nan (ddof=1 with n=1 → std=nan)."""
        metrics = [
            _cm(
                client_id="c1",
                fpr=0.1,
                tpr=0.9,
                balanced_accuracy=0.9,
                macro_f1=0.9,
                confusion_matrix={"tp": 9, "fp": 1, "tn": 9, "fn": 1},
                n_benign=10,
                n_attack=10,
            ),
        ]
        r = _compute_cv_fpr(metrics, ["c1"])
        assert r.eligible_count == 1
        # Single value → CV is nan, our wrapper returns 0.0.
        assert r.cv_fpr == pytest.approx(0.0)


class TestAbsorptionRowModel:
    """AbsorptionRow model validation."""

    def test_row_construction(self) -> None:
        row = AbsorptionRow(
            stress_test="fedprox",
            mu=0.01,
            seed=0,
            regime=Regime.A,
            threshold_baseline=Baseline.B1,
            cv_fpr=0.5,
            mean_fpr=0.1,
            eligible_count=8,
            client_count=9,
            coverage_ratio=0.889,
            absorption_ratio=0.625,
            absorption_class=AbsorptionClass.PARTIAL,
            cv_fpr_fedavg_b1=0.8,
            cv_fpr_fedavg_b2=0.0,
            delta_stress=0.5,
            delta_fedavg=0.8,
        )
        assert row.stress_test == "fedprox"
        assert row.absorption_class == AbsorptionClass.PARTIAL

    def test_row_no_absorption(self) -> None:
        """B4 row has no absorption fields."""
        row = AbsorptionRow(
            stress_test="fedrep",
            mu=None,
            seed=0,
            regime=Regime.A,
            threshold_baseline=Baseline.B4,
            cv_fpr=0.3,
            mean_fpr=0.05,
            eligible_count=9,
            client_count=9,
            coverage_ratio=1.0,
            absorption_ratio=None,
            absorption_class=None,
            cv_fpr_fedavg_b1=None,
            cv_fpr_fedavg_b2=None,
            delta_stress=None,
            delta_fedavg=None,
        )
        assert row.absorption_ratio is None
        assert row.threshold_baseline == Baseline.B4


class TestAbsorptionTableModel:
    """AbsorptionTable model validation."""

    def test_table_construction(self) -> None:
        rows = [
            AbsorptionRow(
                stress_test="fedprox",
                mu=0.0,
                seed=0,
                regime=Regime.A,
                threshold_baseline=Baseline.B1,
                cv_fpr=0.5,
                mean_fpr=0.1,
                eligible_count=8,
                client_count=9,
                coverage_ratio=0.889,
                absorption_ratio=0.75,
                absorption_class=AbsorptionClass.STRONG_RETENTION,
                cv_fpr_fedavg_b1=0.8,
                cv_fpr_fedavg_b2=0.0,
                delta_stress=0.6,
                delta_fedavg=0.8,
            ),
        ]
        table = AbsorptionTable(rows=rows, n_stress_tests=1, n_seeds=1, n_thresholds=3)
        assert table.n_stress_tests == 1
        assert len(table.rows) == 1

    def test_table_csv_json_export(self) -> None:
        rows = [
            AbsorptionRow(
                stress_test="fedprox",
                mu=0.0,
                seed=0,
                regime=Regime.A,
                threshold_baseline=Baseline.B1,
                cv_fpr=0.5,
                mean_fpr=0.1,
                eligible_count=8,
                client_count=9,
                coverage_ratio=0.889,
                absorption_ratio=0.625,
                absorption_class=AbsorptionClass.PARTIAL,
                cv_fpr_fedavg_b1=0.8,
                cv_fpr_fedavg_b2=0.0,
                delta_stress=0.5,
                delta_fedavg=0.8,
            ),
        ]
        table = AbsorptionTable(rows=rows, n_stress_tests=1, n_seeds=1, n_thresholds=3)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            write_absorption_table(table, out)
            assert (out / "stress_test_absorption.csv").is_file()
            assert (out / "stress_test_absorption.json").is_file()

            csv_content = (out / "stress_test_absorption.csv").read_text()
            assert "fedprox" in csv_content
            assert "partial" in csv_content

            json_content = (out / "stress_test_absorption.json").read_text()
            assert "fedprox" in json_content


class TestStressTestKind:
    """Stress-test kind labels are never Baseline enum members."""

    def test_fedprox_not_in_baseline(self) -> None:
        assert StressTestKind.FEDPROX not in {b.value for b in Baseline}

    def test_fedrep_not_in_baseline(self) -> None:
        assert StressTestKind.FEDREP not in {b.value for b in Baseline}

    def test_fedprox_not_labeled_ditto(self) -> None:
        assert "ditto" not in StressTestKind.FEDPROX.lower()
        assert "ditto" not in StressTestKind.FEDREP.lower()
