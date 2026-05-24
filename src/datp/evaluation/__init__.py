from __future__ import annotations

# Lazy attribute access breaks an import cycle: evaluation modules import
# from baselines and core, while downstream consumers (reporting, audit, CLI)
# import from evaluation.  Deferring actual imports to first attribute access
# prevents circular-import failures at module-load time.

__all__ = [
    "BinaryMetrics",
    "ClientMetrics",
    "EvaluationResult",
    "FilteredMetrics",
    "compute_client_metrics",
    "build_evaluation_result",
    "evaluate_baseline",
    "filter_eligible_metrics",
    "recompute_binary_metrics",
    "save_confusion_matrices",
]


def __getattr__(name: str) -> object:
    _from_metrics = {
        "BinaryMetrics",
        "ClientMetrics",
        "EvaluationResult",
        "build_evaluation_result",
        "compute_client_metrics",
        "evaluate_baseline",
        "recompute_binary_metrics",
    }
    _from_eligibility = {"FilteredMetrics", "filter_eligible_metrics"}
    _from_confusion = {"save_confusion_matrices"}

    if name in _from_metrics:
        from datp.evaluation import metrics as _m  # noqa: PLC0415

        return getattr(_m, name)
    if name in _from_eligibility:
        from datp.evaluation.eligibility import (  # noqa: PLC0415
            FilteredMetrics,
            filter_eligible_metrics,
        )

        if name == "FilteredMetrics":
            return FilteredMetrics
        return filter_eligible_metrics
    if name in _from_confusion:
        from datp.evaluation.confusion import save_confusion_matrices  # noqa: PLC0415

        return save_confusion_matrices
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
