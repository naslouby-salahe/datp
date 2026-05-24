from __future__ import annotations

import json
from pathlib import Path

import pytest

from datp.artifacts.results import results_exist
from datp.core.enums import (
    Baseline,
    Regime,
)
from tests.fixtures.payloads import valid_metrics_dict


class TestResultsExist:
    def test_completed_run(self, tmp_path: Path) -> None:
        rdir = tmp_path / "results" / "a" / "b1" / "seed_42"
        rdir.mkdir(parents=True)
        (rdir / "metrics.json").write_text(json.dumps(valid_metrics_dict()))

        assert results_exist(Baseline.B1, Regime.A, 42, None, base_dir=tmp_path) is True

    def test_stale_pre_schema_payload_returns_false(self, tmp_path: Path) -> None:
        rdir = tmp_path / "results" / "a" / "b1" / "seed_42"
        rdir.mkdir(parents=True)
        (rdir / "metrics.json").write_text(json.dumps({"auroc": 0.99}))

        assert (
            results_exist(Baseline.B1, Regime.A, 42, None, base_dir=tmp_path) is False
        )

    def test_unknown_provenance_returns_false(self, tmp_path: Path) -> None:
        rdir = tmp_path / "results" / "a" / "b1" / "seed_42"
        rdir.mkdir(parents=True)
        payload = valid_metrics_dict()
        payload["provenance"]["config_identity"] = "UNKNOWN"
        (rdir / "metrics.json").write_text(json.dumps(payload))

        assert (
            results_exist(Baseline.B1, Regime.A, 42, None, base_dir=tmp_path) is False
        )

    def test_missing_hash_provenance_returns_false(self, tmp_path: Path) -> None:
        rdir = tmp_path / "results" / "a" / "b1" / "seed_42"
        rdir.mkdir(parents=True)
        payload = valid_metrics_dict()
        payload["provenance"]["score_artifact_identity"] = "MISSING_SCORE_HASH"
        (rdir / "metrics.json").write_text(json.dumps(payload))

        assert (
            results_exist(Baseline.B1, Regime.A, 42, None, base_dir=tmp_path) is False
        )

    @pytest.mark.parametrize(
        "missing_key",
        [
            "eligible_ids",
            "pending_ids",
            "eval_incomplete_ids",
        ],
    )
    def test_missing_required_id_list_returns_false(
        self, tmp_path: Path, missing_key: str
    ) -> None:
        rdir = tmp_path / "results" / "a" / "b1" / "seed_42"
        rdir.mkdir(parents=True)
        payload = valid_metrics_dict()
        del payload[missing_key]
        (rdir / "metrics.json").write_text(json.dumps(payload))

        assert (
            results_exist(Baseline.B1, Regime.A, 42, None, base_dir=tmp_path) is False
        )

    def test_missing_metrics(self, tmp_path: Path) -> None:
        assert (
            results_exist(Baseline.B1, Regime.A, 42, None, base_dir=tmp_path) is False
        )

    def test_empty_metrics(self, tmp_path: Path) -> None:
        rdir = tmp_path / "results" / "a" / "b1" / "seed_42"
        rdir.mkdir(parents=True)
        (rdir / "metrics.json").touch()

        assert (
            results_exist(Baseline.B1, Regime.A, 42, None, base_dir=tmp_path) is False
        )

    def test_tmp_placeholder_not_counted(self, tmp_path: Path) -> None:
        rdir = tmp_path / "results" / "a" / "b1" / "seed_42"
        rdir.mkdir(parents=True)
        (rdir / "metrics.json.tmp").write_text('{"partial": true}')

        assert (
            results_exist(Baseline.B1, Regime.A, 42, None, base_dir=tmp_path) is False
        )

    def test_regime_c_with_alpha(self, tmp_path: Path) -> None:
        rdir = tmp_path / "results" / "c" / "b4" / "seed_7" / "alpha_0.5"
        rdir.mkdir(parents=True)
        (rdir / "metrics.json").write_text(
            json.dumps(valid_metrics_dict(baseline="b4", regime="c", seed=7))
        )

        assert (
            results_exist(Baseline.B4, Regime.C, 7, alpha=0.5, base_dir=tmp_path)
            is True
        )
        assert (
            results_exist(Baseline.B4, Regime.C, 7, alpha=1.0, base_dir=tmp_path)
            is False
        )

    def test_different_baseline_not_found(self, tmp_path: Path) -> None:
        rdir = tmp_path / "results" / "a" / "b1" / "seed_42"
        rdir.mkdir(parents=True)
        (rdir / "metrics.json").write_text(json.dumps(valid_metrics_dict()))

        assert results_exist(Baseline.B1, Regime.A, 42, None, base_dir=tmp_path) is True
        assert (
            results_exist(Baseline.B2, Regime.A, 42, None, base_dir=tmp_path) is False
        )
