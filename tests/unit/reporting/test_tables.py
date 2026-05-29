from __future__ import annotations

from pathlib import Path

import numpy as np

from datp.config.compose import BASE_CONFIG
from datp.core.enums import Baseline
from datp.evaluation.metrics import ClientMetrics, EvaluationResult
from datp.reporting.engine import format_mean_std as _format_mean_std
from datp.reporting.tables import (
    MANDATORY_FOOTNOTE,
    generate_table3,
)

RNG = np.random.RandomState(99)

_DEVICE_IDS = [f"dev_{i}" for i in range(6)]
_ELIGIBLE_IDS = _DEVICE_IDS[:5]
_PENDING_IDS = _DEVICE_IDS[5:]


def _make_client_metrics(client_id: str) -> ClientMetrics:
    fpr = float(RNG.uniform(0.01, 0.15))
    tpr = float(RNG.uniform(0.85, 0.99))
    tnr = 1.0 - fpr
    fnr = 1.0 - tpr
    return ClientMetrics(
        client_id=client_id,
        fpr=fpr,
        tpr=tpr,
        tnr=tnr,
        fnr=fnr,
        precision=90 / (90 + 5),
        recall=90 / (90 + 10),
        balanced_accuracy=float(RNG.uniform(0.80, 0.98)),
        macro_f1=float(RNG.uniform(0.75, 0.95)),
        confusion_matrix={"tp": 90, "fp": 5, "tn": 95, "fn": 10},
        n_benign=100,
        n_attack=100,
    )


def _make_eval_result(baseline: Baseline, seed: int) -> EvaluationResult:
    per_client = [_make_client_metrics(d) for d in _DEVICE_IDS]
    eligible_fprs = [c.fpr for c in per_client if c.client_id in _ELIGIBLE_IDS]
    eligible_tprs = [c.tpr for c in per_client if c.client_id in _ELIGIBLE_IDS]
    cv_fpr = (
        float(np.std(eligible_fprs, ddof=1) / np.mean(eligible_fprs))
        if np.mean(eligible_fprs) != 0
        else 0.0
    )
    cv_tpr = (
        float(np.std(eligible_tprs, ddof=1) / np.mean(eligible_tprs))
        if np.mean(eligible_tprs) != 0
        else 0.0
    )
    mean_fpr = float(np.mean(eligible_fprs))
    std_fpr = float(np.std(eligible_fprs, ddof=1))
    fpr_arr = np.array(eligible_fprs)
    tpr_arr = np.array(eligible_tprs)
    iqr_fpr = (
        float(np.percentile(fpr_arr, 75) - np.percentile(fpr_arr, 25))
        if len(fpr_arr) >= 2
        else float("nan")
    )
    iqr_tpr = (
        float(np.percentile(tpr_arr, 75) - np.percentile(tpr_arr, 25))
        if len(tpr_arr) >= 2
        else float("nan")
    )
    ba_list = [c.balanced_accuracy for c in per_client if c.client_id in _ELIGIBLE_IDS]
    f1_list = [c.macro_f1 for c in per_client if c.client_id in _ELIGIBLE_IDS]
    worst_fpr = float(max(eligible_fprs)) if eligible_fprs else float("nan")
    worst_id: str | None = next(
        (
            c.client_id
            for c in per_client
            if c.client_id in _ELIGIBLE_IDS and c.fpr == worst_fpr
        ),
        None,
    )
    return EvaluationResult(
        baseline=baseline,
        regime="a",
        seed=seed,
        alpha=None,
        dataset="nbaiot",
        per_client=per_client,
        eligible_ids=list(_ELIGIBLE_IDS),
        pending_ids=list(_PENDING_IDS),
        eval_incomplete_ids=[],
        coverage_ratio=len(_ELIGIBLE_IDS) / len(_DEVICE_IDS),
        cv_fpr=cv_fpr,
        mean_fpr=mean_fpr,
        std_fpr=std_fpr,
        cv_tpr=cv_tpr,
        iqr_fpr=iqr_fpr,
        iqr_tpr=iqr_tpr,
        max_min_fpr_gap=worst_fpr - float(min(eligible_fprs)) if len(eligible_fprs) >= 2 else 0.0,
        worst_client_fpr=worst_fpr,
        worst_client_id=worst_id,
        eligible_count=len(eligible_fprs),
        client_count=len(per_client),
        worst_ba=float(min(ba_list)) if ba_list else float("nan"),
        p10_macro_f1=float(np.percentile(f1_list, 10)) if f1_list else float("nan"),
    )


def _synthetic_results() -> dict[str, list[EvaluationResult]]:
    data: dict[str, list[EvaluationResult]] = {}
    for bl in ("b1", "b2", "b4"):
        data[bl] = [_make_eval_result(bl, seed) for seed in range(2)]
    return data


def test_generate_table3_creates_files(tmp_path: Path) -> None:
    tex_path = generate_table3(
        _synthetic_results(),
        tmp_path,
        baseline_labels=BASE_CONFIG.reporting.style.baseline_labels,
    )
    assert tex_path.exists()
    assert tex_path.suffix == ".tex"
    csv_path = tmp_path / "table3_nbaiot.csv"
    assert csv_path.exists()


def test_table3_contains_footnote(tmp_path: Path) -> None:
    tex_path = generate_table3(
        _synthetic_results(),
        tmp_path,
        baseline_labels=BASE_CONFIG.reporting.style.baseline_labels,
    )
    content = tex_path.read_text(encoding="utf-8")
    assert MANDATORY_FOOTNOTE in content


def test_table3_contains_coverage_ratio(tmp_path: Path) -> None:
    tex_path = generate_table3(
        _synthetic_results(),
        tmp_path,
        baseline_labels=BASE_CONFIG.reporting.style.baseline_labels,
    )
    content = tex_path.read_text(encoding="utf-8")
    # Coverage ratio for 5/6 eligible ≈ 0.83
    assert "0.83" in content


def test_table_labels_p10_macro_f1_precisely(tmp_path: Path) -> None:
    tex_path = generate_table3(
        _synthetic_results(),
        tmp_path,
        baseline_labels=BASE_CONFIG.reporting.style.baseline_labels,
    )
    content = tex_path.read_text(encoding="utf-8")
    assert "P10 client Macro-F1" in content
    assert "& Worst BA & Macro-F1 &" not in content


def test_format_mean_std_bold() -> None:
    result = _format_mean_std(0.123, 0.045, bold=True)
    assert "\\textbf" in result
    assert "0.123" in result
    assert "0.045" in result


def test_format_mean_std_normal() -> None:
    result = _format_mean_std(0.123, 0.045, bold=False)
    assert "\\textbf" not in result
    assert "0.123" in result
    assert "±" in result
