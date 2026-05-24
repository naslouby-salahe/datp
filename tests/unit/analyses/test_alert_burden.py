"""Unit tests for Alert-Burden Table analysis (T13)."""

from __future__ import annotations

from pathlib import Path

import pytest

from datp.analyses.alert_burden import AlertBurdenSuppression, run_alert_burden


class TestAlertBurden:
    def test_always_suppressed(self):
        result = run_alert_burden(Path("."))
        assert result.suppressed
        assert "no timestamps" in result.reason.lower() or "no" in result.reason.lower()

    def test_suppression_note_contains_no_rate_claim(self):
        result = run_alert_burden(Path("."))
        assert "never invent" in result.reason.lower()

    def test_write_outputs_creates_suppression_file(self, tmp_path: Path):
        run_alert_burden(tmp_path, write_outputs=True)
        suppression = tmp_path / "analysis" / "alert_burden_suppression.json"
        assert suppression.is_file()
        import json

        data = json.loads(suppression.read_text())
        assert data["suppressed"] is True

    def test_schema_frozen(self):
        result = AlertBurdenSuppression()
        with pytest.raises(Exception):
            result.suppressed = False  # type: ignore[misc]
