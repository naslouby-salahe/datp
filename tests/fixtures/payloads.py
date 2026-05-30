from __future__ import annotations

import json


def valid_metrics_dict(baseline: str = "b1", regime: str = "a", seed: int = 0) -> dict:
    client = {
        "client_id": "c1",
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
        "calibration_pending": False,
        "evaluation_incomplete": False,
        "threshold_value": 0.5,
        "threshold_source": baseline,
    }
    return {
        "schema_version": "2",
        "metric_schema_version": "2",
        "threshold_schema_version": "1",
        "run_id": f"{regime}_{baseline}_seed{seed}",
        "run_kind": "main",
        "dataset": "nbaiot",
        "baseline": baseline,
        "regime": regime,
        "seed": seed,
        "alpha": None,
        "threshold_scope": "eligible_client_arithmetic_mean",
        "threshold_strategy_name": baseline,
        "tau_global": 0.5,
        "per_client": {client["client_id"]: client},
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
        "aggregate_metrics": {"cv_fpr": 0.0, "p10_client_macro_f1": 1.0},
        "provenance": {
            "config_identity": "abc123",
            "split_manifest_identity": "def456",
            "model_checkpoint_identity": "ghi789",
            "score_artifact_identity": "jkl012",
            "metric_code_version": "v1",
            "threshold_code_version": "v1",
            "package_version": "v1",
            "generated_at_utc": "2026-01-01T00:00:00+00:00",
        },
    }


def valid_metrics_json(baseline: str = "b1", regime: str = "a", seed: int = 0) -> str:
    return json.dumps(valid_metrics_dict(baseline, regime, seed))
