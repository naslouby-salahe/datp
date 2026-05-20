from __future__ import annotations

import pytest

from datp.evaluation.artifact_validation import validate_metrics_payload


def _base_provenance(**overrides: str) -> dict:
    base = {
        "config_identity": "abc123",
        "split_manifest_identity": "def456",
        "model_checkpoint_identity": "ghi789",
        "score_artifact_identity": "jkl012",
        "metric_code_version": "v1",
        "threshold_code_version": "v1",
        "package_version": "v1",
        "generated_at_utc": "2026-01-01T00:00:00+00:00",
    }
    base.update(overrides)
    return base


def _base_client(client_id: str = "c1", calibration_pending: bool = False) -> dict:
    return {
        "client_id": client_id,
        "fpr": 0.0,
        "tpr": 1.0,
        "tnr": 1.0,
        "fnr": 0.0,
        "precision": 1.0,
        "recall": 1.0,
        "balanced_accuracy": 1.0,
        "macro_f1": 1.0,
        "confusion_matrix": {"tp": 10, "fp": 0, "tn": 10, "fn": 0},
        "n_benign": 10,
        "n_attack": 10,
        "benign_count": 10,
        "attack_count": 10,
        "calibration_pending": calibration_pending,
        "evaluation_incomplete": False,
        "threshold_value": 0.5,
        "threshold_source": "b1",
    }


def _valid_payload(**overrides) -> dict:
    payload = {
        "schema_version": "2",
        "metric_schema_version": "2",
        "threshold_schema_version": "1",
        "run_id": "a_b1_seed0",
        "dataset": "nbaiot",
        "baseline": "b1",
        "regime": "a",
        "seed": 0,
        "alpha": None,
        "threshold_scope": "eligible_client_arithmetic_mean",
        "threshold_strategy_name": "b1",
        "tau_global": 0.5,
        "per_client": [_base_client()],
        "eligible_ids": ["c1"],
        "pending_ids": [],
        "eval_incomplete_ids": [],
        "eligible_count": 1,
        "pending_count": 0,
        "eval_incomplete_count": 0,
        "client_count": 1,
        "coverage_ratio": 1.0,
        "cv_fpr": 0.0,
        "mean_fpr": 0.0,
        "std_fpr": 0.0,
        "cv_tpr": 0.0,
        "iqr_fpr": 0.0,
        "iqr_tpr": 0.0,
        "worst_client_fpr": 0.0,
        "worst_client_id": "c1",
        "worst_ba": 1.0,
        "p10_macro_f1": 1.0,
        "aggregate_metrics": {},
        "provenance": _base_provenance(),
    }
    payload.update(overrides)
    return payload


class TestProvenanceValidation:
    def test_valid_payload_passes(self) -> None:
        assert validate_metrics_payload(_valid_payload(), module="test") == []

    @pytest.mark.parametrize("field", [
        "config_identity",
        "split_manifest_identity",
        "model_checkpoint_identity",
        "score_artifact_identity",
    ])
    def test_unknown_identity_fails(self, field: str) -> None:
        payload = _valid_payload(provenance=_base_provenance(**{field: "UNKNOWN"}))
        errors = validate_metrics_payload(payload, module="test")
        assert any("UNKNOWN" in e or "vague" in e for e in errors)

    @pytest.mark.parametrize("field,value", [
        ("config_identity", "MISSING_CONFIG_HASH"),
        ("split_manifest_identity", "MISSING_MANIFEST_HASH"),
        ("model_checkpoint_identity", "MISSING_CHECKPOINT_HASH"),
        ("score_artifact_identity", "MISSING_SCORE_HASH"),
    ])
    def test_missing_hash_fails(self, field: str, value: str) -> None:
        payload = _valid_payload(provenance=_base_provenance(**{field: value}))
        errors = validate_metrics_payload(payload, module="test")
        assert any("MISSING_" in e or "unresolved" in e for e in errors)

    def test_not_applicable_passes(self) -> None:
        payload = _valid_payload(
            provenance=_base_provenance(
                model_checkpoint_identity="NOT_APPLICABLE_B0_OWN_MODEL",
                score_artifact_identity="NOT_APPLICABLE_B0_DIRECT_EVAL",
            )
        )
        errors = validate_metrics_payload(payload, module="test")
        assert errors == []


class TestEligibilityValidation:
    @pytest.mark.parametrize("missing_key", [
        "eligible_ids",
        "pending_ids",
        "eval_incomplete_ids",
    ])
    def test_missing_id_list_fails(self, missing_key: str) -> None:
        payload = _valid_payload()
        del payload[missing_key]
        errors = validate_metrics_payload(payload, module="test")
        assert any(missing_key in e for e in errors)

    def test_eligible_pending_overlap_fails(self) -> None:
        payload = _valid_payload(
            per_client=[_base_client("c1", calibration_pending=True)],
            eligible_ids=["c1"],
            pending_ids=["c1"],
        )
        errors = validate_metrics_payload(payload, module="test")
        assert any("overlap" in e for e in errors)

    def test_calibration_pending_excluded_from_eligible(self) -> None:
        payload = _valid_payload(
            per_client=[
                _base_client("c1"),
                _base_client("c2", calibration_pending=True),
            ],
            eligible_ids=["c1"],
            pending_ids=["c2"],
            eligible_count=1,
            pending_count=1,
            client_count=2,
            coverage_ratio=0.5,
        )
        errors = validate_metrics_payload(payload, module="test")
        assert errors == []

    def test_pending_client_without_flag_fails(self) -> None:
        payload = _valid_payload(
            per_client=[
                _base_client("c1"),
                _base_client("c2", calibration_pending=False),  # flag missing
            ],
            eligible_ids=["c1"],
            pending_ids=["c2"],
            eligible_count=1,
            pending_count=1,
            client_count=2,
            coverage_ratio=0.5,
        )
        errors = validate_metrics_payload(payload, module="test")
        assert any("calibration_pending" in e for e in errors)
