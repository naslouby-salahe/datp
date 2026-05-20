from __future__ import annotations

import typing


def test_baseline_types_importable():
    from datp.baselines.common.types import (
        B0Result,
        BaselineResult,
        ClientEvalResult,
        ClientEvalResultWithAuroc,
    )

    import typing

    for cls in (B0Result, BaselineResult, ClientEvalResult, ClientEvalResultWithAuroc):
        assert len(typing.get_type_hints(cls)) > 0, f"{cls.__name__} has no type hints"


def test_client_metrics_is_pydantic_model():
    from pydantic import BaseModel

    from datp.evaluation.metrics import ClientMetrics

    assert issubclass(ClientMetrics, BaseModel)


def test_evaluation_result_is_pydantic_model():
    from pydantic import BaseModel

    from datp.evaluation.metrics import EvaluationResult

    assert issubclass(EvaluationResult, BaseModel)


def test_baseline_result_required_keys():
    from datp.baselines.common.types import BaselineResult

    hints = typing.get_type_hints(BaselineResult)
    expected = {
        "baseline",
        "regime",
        "seed",
        "per_client",
        "n_clients",
        "calibration_pending_clients",
    }
    assert expected.issubset(hints.keys()), f"Missing keys: {expected - hints.keys()}"


def test_b0_result_keys():
    from datp.baselines.common.types import B0Result

    hints = typing.get_type_hints(B0Result)
    b0_specific = {"tau_b0", "q", "n_min", "auroc"}
    base_keys = {
        "baseline",
        "regime",
        "seed",
        "per_client",
        "n_clients",
        "calibration_pending_clients",
    }
    assert b0_specific.issubset(hints.keys()), (
        f"Missing B0 keys: {b0_specific - hints.keys()}"
    )
    assert base_keys.issubset(hints.keys()), (
        f"Missing base keys: {base_keys - hints.keys()}"
    )


def test_client_eval_result_with_auroc_keys():
    from datp.baselines.common.types import ClientEvalResultWithAuroc

    hints = typing.get_type_hints(ClientEvalResultWithAuroc)
    expected = {
        "fpr",
        "tpr",
        "balanced_accuracy",
        "macro_f1",
        "n_benign",
        "n_attack",
        "auroc",
    }
    assert expected.issubset(hints.keys()), f"Missing keys: {expected - hints.keys()}"


def test_client_metrics_dict_keys():
    from datp.evaluation.metrics import ClientMetrics

    field_names = set(ClientMetrics.model_fields.keys())
    expected = {
        "client_id",
        "fpr",
        "tpr",
        "balanced_accuracy",
        "macro_f1",
        "confusion_matrix",
        "n_benign",
        "n_attack",
    }
    assert expected.issubset(field_names), f"Missing keys: {expected - field_names}"
