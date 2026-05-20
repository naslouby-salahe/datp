from __future__ import annotations

from pathlib import Path

from datp.config.compose import BASE_CONFIG
from datp.evaluation.metrics import EvaluationResult
from datp.pipeline.diagnostic import _make_contingency_decision


def _eval(cv_fpr: float, *, seed: int = 1) -> EvaluationResult:
    return EvaluationResult(
        baseline="b1",
        regime="a",
        seed=seed,
        alpha=None,
        per_client=[],
        eligible_ids=[],
        pending_ids=[],
        eval_incomplete_ids=[],
        coverage_ratio=0.0,
        cv_fpr=cv_fpr,
        mean_fpr=0.0,
        std_fpr=0.0,
        cv_tpr=0.0,
        iqr_fpr=0.0,
        iqr_tpr=0.0,
        worst_client_fpr=0.0,
        worst_client_id=None,
        eligible_count=0,
        client_count=0,
        worst_ba=0.0,
        p10_macro_f1=0.0,
    )


def test_contingency_decision_uses_passed_dispersion_threshold() -> None:
    threshold = BASE_CONFIG.statistics.dispersion_threshold + 0.25

    decision = _make_contingency_decision(
        _eval(threshold - 0.01),
        _eval(0.0),
        dispersion_threshold=threshold,
    )

    assert decision.dispersion_threshold == threshold
    assert decision.decision == "contingency"


def test_contingency_decision_goes_when_b1_exceeds_threshold() -> None:
    decision = _make_contingency_decision(
        _eval(0.4),
        _eval(0.1),
        dispersion_threshold=0.2,
    )

    assert decision.decision == "go"


def test_filelock_dependency_declared_in_pyproject() -> None:
    pyproject = Path(__file__).resolve().parents[3] / "pyproject.toml"
    assert '"filelock"' in pyproject.read_text(encoding="utf-8")
