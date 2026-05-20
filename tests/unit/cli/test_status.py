from __future__ import annotations

import re

from datp.artifacts.paths import ExperimentLocator
from datp.cli.status import get_status
from datp.core.enums import (
    Baseline,
    Regime,
)
from datp.core.identity import RunIdentity
from tests.fixtures.payloads import valid_metrics_json


class TestAllMissingFreshDir:
    def test_all_missing_fresh_dir(self, tmp_path):
        report = get_status(regime=None, base_dir=tmp_path)
        total_missing = sum(rr.missing_count for rr in report.regime_reports.values())
        total_complete = sum(rr.complete_count for rr in report.regime_reports.values())
        total_aborted = sum(rr.aborted_count for rr in report.regime_reports.values())

        assert total_missing == 135  # 25 + 20 + 90 (B0-B4 main baselines)
        assert total_complete == 0
        assert total_aborted == 0


class TestCompleteDetected:
    def test_complete_detected(self, tmp_path):
        rp = ExperimentLocator.for_main(tmp_path, Regime.A).result(Baseline.B1, seed=0)
        rp.mkdir(parents=True, exist_ok=True)
        (rp / "metrics.json").write_text(valid_metrics_json("b1", "a", 0))

        report = get_status(regime="a", base_dir=tmp_path)
        rr = report.regime_reports["a"]

        assert rr.complete_count == 1
        assert rr.complete[0] == RunIdentity(
            regime=Regime.A, baseline=Baseline.B1, seed=0, alpha=None
        )
        assert rr.missing_count == 24
        assert rr.aborted_count == 0


class TestAbortedDetected:
    def test_aborted_detected(self, tmp_path):
        rp = ExperimentLocator.for_main(tmp_path, Regime.B).result(Baseline.B2, seed=1)
        rp.mkdir(parents=True, exist_ok=True)
        (rp / "ABORTED.txt").write_text("round=5; OOM error")

        report = get_status(regime="b", base_dir=tmp_path)
        rr = report.regime_reports["b"]

        assert rr.aborted_count == 1
        assert rr.aborted[0] == RunIdentity(
            regime=Regime.B, baseline=Baseline.B2, seed=1, alpha=None
        )
        assert rr.missing_count == 19
        assert rr.complete_count == 0


class TestRegimeFilter:
    def test_regime_filter(self, tmp_path):
        report = get_status(regime="a", base_dir=tmp_path)

        assert list(report.regime_reports.keys()) == ["a"]
        rr = report.regime_reports["a"]
        assert rr.total == 25
        assert all(c.regime == "a" for c in rr.missing)


class TestSummaryLinesFormat:
    def test_summary_lines_format(self, tmp_path):
        report = get_status(regime=None, base_dir=tmp_path)
        lines = report.summary_lines()

        # 3 regime lines + 1 overall line
        assert len(lines) == 4

        pattern = re.compile(
            r"^(Regime [ABC]|Overall):?\s+"
            r"complete=\d+\s+"
            r"missing=\d+\s+"
            r"aborted=\d+\s+"
            r"\(total=\d+\)$"
        )
        for line in lines:
            assert pattern.match(line), f"Line did not match expected format: {line!r}"

        assert "total=25" in lines[0]
        assert "total=20" in lines[1]
        assert "total=90" in lines[2]
        assert "total=135" in lines[3]
