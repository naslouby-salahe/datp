from __future__ import annotations

import json
from pathlib import Path

import pytest

from datp.data.contracts import RegimeCClientSummary, RegimeCManifestMetadata
from datp.validation.datasets import build_regime_c_alpha_audit, compute_regime_c_severity_trend
from datp.validation.enums import SeverityTrendStatus, SeverityVariable
from datp.validation.schemas import RegimeCAlphaAuditRecord


def _write_regime_c_manifest(
    prepared_dir: Path,
    *,
    n_clients: int = 5,
    js_divergence: float | None = 0.12,
    pending_ids: list[str] | None = None,
    device_mixtures: dict[str, dict[str, float]] | None = None,
) -> Path:
    pending_ids = pending_ids or []
    device_mixtures = device_mixtures or {}

    client_summaries: list[RegimeCClientSummary] = []
    for i in range(n_clients):
        cid = f"client_{i}"
        is_pending = cid in pending_ids
        mix = device_mixtures.get(
            cid, {"Danmini_Doorbell": 0.5, "Ecobee_Thermostat": 0.5}
        )
        client_summaries.append(
            RegimeCClientSummary(
                client_id=cid,
                train_count=100,
                cal_count=50 if is_pending else 200,
                test_benign_count=300,
                test_attack_count=150,
                calibration_pending=is_pending,
                device_mixture_proportions=mix,
            )
        )

    metadata_model = RegimeCManifestMetadata(
        n_clients=n_clients,
        js_divergence=js_divergence,
        client_summaries=client_summaries,
    )

    manifest = {
        "dataset": "nbaiot",
        "file_hashes": {"fixture": "abc"},
        "metadata": metadata_model.model_dump(),
        "created": "2026-04-26T00:00:00+00:00",
    }
    prepared_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = prepared_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return manifest_path


class TestBuildRegimeCAlphaAudit:
    def test_returns_none_when_no_manifest(self, tmp_path: Path) -> None:
        record = build_regime_c_alpha_audit(tmp_path / "nonexistent", alpha=0.3, seed=0)
        assert record is None

    def test_returns_record_with_basic_fields(self, tmp_path: Path) -> None:
        prepared = tmp_path / "regime_c" / "alpha_0.3" / "seed_0"
        _write_regime_c_manifest(prepared, n_clients=5)
        record = build_regime_c_alpha_audit(prepared, alpha=0.3, seed=0)
        assert record is not None
        assert isinstance(record, RegimeCAlphaAuditRecord)
        assert record.alpha == "0.3"
        assert record.seed == 0
        assert record.n_clients == 5

    def test_js_divergence_surfaced(self, tmp_path: Path) -> None:
        prepared = tmp_path / "alpha"
        _write_regime_c_manifest(prepared, js_divergence=0.25)
        record = build_regime_c_alpha_audit(prepared, alpha=0.3, seed=1)
        assert record is not None
        assert record.js_divergence_mean == pytest.approx(0.25)

    def test_js_divergence_none_when_not_in_manifest(self, tmp_path: Path) -> None:
        prepared = tmp_path / "alpha"
        _write_regime_c_manifest(prepared, js_divergence=None)
        record = build_regime_c_alpha_audit(prepared, alpha=0.3, seed=1)
        assert record is not None
        assert record.js_divergence_mean is None

    def test_calibration_pending_count_correct(self, tmp_path: Path) -> None:
        prepared = tmp_path / "alpha"
        _write_regime_c_manifest(
            prepared, n_clients=5, pending_ids=["client_0", "client_2"]
        )
        record = build_regime_c_alpha_audit(prepared, alpha=0.1, seed=0)
        assert record is not None
        assert record.n_calibration_pending == 2
        assert record.n_eligible == 3

    def test_pending_client_ids_populated(self, tmp_path: Path) -> None:
        prepared = tmp_path / "alpha"
        _write_regime_c_manifest(
            prepared, n_clients=5, pending_ids=["client_0", "client_2"]
        )
        record = build_regime_c_alpha_audit(prepared, alpha=0.1, seed=0)
        assert record is not None
        assert set(record.pending_client_ids) == {"client_0", "client_2"}

    def test_device_mixture_proportions_present(self, tmp_path: Path) -> None:
        prepared = tmp_path / "alpha"
        mixtures = {
            "client_0": {"Danmini_Doorbell": 0.7, "Ecobee_Thermostat": 0.3},
            "client_1": {"Danmini_Doorbell": 0.4, "Ecobee_Thermostat": 0.6},
        }
        _write_regime_c_manifest(prepared, n_clients=2, device_mixtures=mixtures)
        record = build_regime_c_alpha_audit(prepared, alpha=0.3, seed=0)
        assert record is not None
        assert "client_0" in record.device_mixture_proportions
        assert record.device_mixture_proportions["client_0"][
            "Danmini_Doorbell"
        ] == pytest.approx(0.7)

    def test_device_mixture_js_computed(self, tmp_path: Path) -> None:
        prepared = tmp_path / "alpha"
        mixtures = {
            "client_0": {"dev_a": 1.0, "dev_b": 0.0},
            "client_1": {"dev_a": 0.0, "dev_b": 1.0},
        }
        _write_regime_c_manifest(prepared, n_clients=2, device_mixtures=mixtures)
        record = build_regime_c_alpha_audit(prepared, alpha=0.3, seed=0)
        assert record is not None
        assert record.device_mixture_js_mean is not None
        assert record.device_mixture_js_mean > 0.0

    def test_device_mixture_js_zero_for_identical(self, tmp_path: Path) -> None:
        prepared = tmp_path / "alpha"
        same_mix = {"dev_a": 0.5, "dev_b": 0.5}
        mixtures = {f"client_{i}": same_mix for i in range(3)}
        _write_regime_c_manifest(prepared, n_clients=3, device_mixtures=mixtures)
        record = build_regime_c_alpha_audit(prepared, alpha=0.3, seed=0)
        assert record is not None
        assert record.device_mixture_js_mean == pytest.approx(0.0, abs=1e-9)

    def test_coverage_ratio_format(self, tmp_path: Path) -> None:
        prepared = tmp_path / "alpha"
        _write_regime_c_manifest(prepared, n_clients=5, pending_ids=["client_4"])
        record = build_regime_c_alpha_audit(prepared, alpha=0.5, seed=0)
        assert record is not None
        # 4 eligible out of 5
        assert record.coverage_ratio == "4/5"

    def test_scope_note_present_and_correct(self, tmp_path: Path) -> None:
        prepared = tmp_path / "alpha"
        _write_regime_c_manifest(prepared, n_clients=3)
        record = build_regime_c_alpha_audit(prepared, alpha=0.3, seed=0)
        assert record is not None
        assert "severity/context" in record.scope_note.lower()
        assert "confirmatory" in record.scope_note.lower()

    def test_iid_alpha_label(self, tmp_path: Path) -> None:
        prepared = tmp_path / "alpha_iid"
        _write_regime_c_manifest(prepared, n_clients=3)
        record = build_regime_c_alpha_audit(prepared, alpha=float("inf"), seed=0)
        assert record is not None
        assert record.alpha == "iid"


class TestRegimeCSeverityTrend:
    def _make_record(
        self,
        alpha: str,
        seed: int,
        dmjs: float | None = None,
        delta: float | None = None,
    ) -> "RegimeCAlphaAuditRecord":
        from datp.validation.schemas import RegimeCAlphaAuditRecord

        return RegimeCAlphaAuditRecord(
            alpha=alpha,
            seed=seed,
            n_clients=20,
            n_eligible=18,
            n_calibration_pending=2,
            coverage_ratio="18/20",
            js_divergence_mean=0.1,
            device_mixture_js_mean=dmjs,
            delta_b1_b2=delta,
        )

    def test_insufficient_data_when_fewer_than_3_pairs(self) -> None:
        records = [self._make_record("0.1", 0, dmjs=0.4, delta=0.5)]
        results = compute_regime_c_severity_trend(records, significance_alpha=0.05)
        assert len(results) == 3
        for r in results:
            assert r.status == SeverityTrendStatus.INSUFFICIENT_DATA
            assert r.spearman_rho is None

    def test_handles_none_cells_gracefully(self) -> None:
        records = [
            self._make_record("0.1", 0, dmjs=None, delta=0.5),
            self._make_record("0.3", 0, dmjs=None, delta=0.4),
            self._make_record("1.0", 0, dmjs=None, delta=0.2),
        ]
        results = compute_regime_c_severity_trend(records, significance_alpha=0.05)
        dmjs_result = next(
            r for r in results if r.severity_variable == SeverityVariable.DEVICE_MIXTURE_JS_MEAN
        )
        assert dmjs_result.status == SeverityTrendStatus.INSUFFICIENT_DATA
        assert dmjs_result.n_cells == 0

    def test_returns_three_trend_records(self) -> None:
        records = [
            self._make_record(str(a), 0, dmjs=float(i) * 0.1, delta=float(i) * 0.05)
            for i, a in enumerate([0.1, 0.3, 0.5, 1.0])
        ]
        results = compute_regime_c_severity_trend(records, significance_alpha=0.05)
        assert len(results) == 3
        vars_ = {r.severity_variable for r in results}
        assert vars_ == {
            SeverityVariable.DEVICE_MIXTURE_JS_MEAN,
            SeverityVariable.RECON_ERROR_JS_MEAN,
            SeverityVariable.ALPHA_NUMERIC,
        }

    def test_iid_excluded_from_alpha_numeric_test(self) -> None:
        records = [
            self._make_record("0.1", 0, dmjs=0.4, delta=0.5),
            self._make_record("0.5", 0, dmjs=0.2, delta=0.3),
            self._make_record("1.0", 0, dmjs=0.1, delta=0.1),
            self._make_record("iid", 0, dmjs=0.0, delta=0.0),
        ]
        results = compute_regime_c_severity_trend(records, significance_alpha=0.05)
        alpha_result = next(
            r for r in results if r.severity_variable == SeverityVariable.ALPHA_NUMERIC
        )
        assert alpha_result.n_cells == 3


class TestEnrichRegimeCRecordsWithCv:
    def _make_record(self, alpha: str, seed: int) -> "RegimeCAlphaAuditRecord":
        return RegimeCAlphaAuditRecord(
            alpha=alpha,
            seed=seed,
            n_clients=20,
            n_eligible=18,
            n_calibration_pending=2,
            coverage_ratio="18/20",
            js_divergence_mean=0.1,
        )

    def test_populates_cv_fpr_from_cell_panel(self) -> None:
        from datp.validation.results import _CellPanel, _enrich_regime_c_records_with_cv
        from datp.core.enums import Baseline, Regime

        records = [self._make_record("0.3", 1)]
        panel: dict[tuple[Regime, int, str | None, Baseline], _CellPanel] = {
            (Regime.C, 1, "0.3", Baseline.B1): _CellPanel(cv_fpr=0.4),
            (Regime.C, 1, "0.3", Baseline.B2): _CellPanel(cv_fpr=0.2),
            (Regime.C, 1, "0.3", Baseline.B4): _CellPanel(cv_fpr=0.3),
        }
        enriched = _enrich_regime_c_records_with_cv(records, panel)
        assert len(enriched) == 1
        r = enriched[0]
        import pytest

        assert r.b1_cv_fpr == pytest.approx(0.4)
        assert r.b2_cv_fpr == pytest.approx(0.2)
        assert r.b4_cv_fpr == pytest.approx(0.3)
        assert r.delta_b1_b2 == pytest.approx(0.2)
        assert r.delta_b1_b4 == pytest.approx(0.1)
        assert r.eligible_only_cv_fpr == pytest.approx(0.4)

    def test_missing_panel_entries_leave_fields_none(self) -> None:
        from datp.validation.results import _enrich_regime_c_records_with_cv

        records = [self._make_record("0.5", 0)]
        enriched = _enrich_regime_c_records_with_cv(records, {})
        assert enriched[0].b1_cv_fpr is None
        assert enriched[0].delta_b1_b2 is None

    def test_iid_alpha_lookup(self) -> None:
        from datp.validation.results import _CellPanel, _enrich_regime_c_records_with_cv
        from datp.core.enums import Baseline, Regime

        records = [self._make_record("iid", 2)]
        panel: dict[tuple[Regime, int, str | None, Baseline], _CellPanel] = {
            (Regime.C, 2, "iid", Baseline.B1): _CellPanel(cv_fpr=0.1),
            (Regime.C, 2, "iid", Baseline.B2): _CellPanel(cv_fpr=0.08),
        }
        enriched = _enrich_regime_c_records_with_cv(records, panel)
        import pytest

        assert enriched[0].b1_cv_fpr == pytest.approx(0.1)
        assert enriched[0].b2_cv_fpr == pytest.approx(0.08)


class TestB4StabilityFromClusterRecords:
    def test_empty_returns_empty(self) -> None:
        from datp.validation.results import _b4_stability_from_cluster_records

        assert _b4_stability_from_cluster_records([]) == []

    def test_single_seed_returns_empty(self) -> None:
        from datp.validation.results import _b4_stability_from_cluster_records
        from datp.validation.schemas import ClusterAssignmentRecord
        from datp.core.enums import Regime

        records = [
            ClusterAssignmentRecord(
                run_id="r1",
                seed=0,
                regime=Regime.A,
                alpha=None,
                client_id=f"c{i}",
                cluster_id="cluster_0",
                threshold_value=0.5,
            )
            for i in range(3)
        ]
        result = _b4_stability_from_cluster_records(records)
        assert result == []

    def test_two_seeds_produces_one_ari_record(self) -> None:
        from datp.validation.results import _b4_stability_from_cluster_records
        from datp.validation.schemas import ClusterAssignmentRecord
        from datp.core.enums import Regime

        records = []
        for seed in (0, 1):
            for i in range(3):
                records.append(
                    ClusterAssignmentRecord(
                        run_id=f"r{seed}",
                        seed=seed,
                        regime=Regime.A,
                        alpha=None,
                        client_id=f"c{i}",
                        cluster_id=f"cluster_{i % 2}",
                        threshold_value=0.5,
                    )
                )
        result = _b4_stability_from_cluster_records(records)
        assert len(result) == 1
        assert -1.0 <= result[0].adjusted_rand_index <= 1.0
