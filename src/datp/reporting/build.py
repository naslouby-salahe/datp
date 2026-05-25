from __future__ import annotations

import csv
import json
import math
import shutil
from pathlib import Path
from typing import Any

import attrs
import numpy as np

from datp.artifacts.constants import (
    METRICS_FILE,
    MODEL_CHECKPOINT,
    REPORTING_AUDIT_FILE,
    SCORING_MANIFEST_FILE,
)
from datp.artifacts.markers import write_json_atomic
from datp.artifacts.paths import ExperimentLocator
from datp.config.models import DatpConfig
from datp.core.enums import (
    ISOLATED_BASELINES,
    REGIME_BASELINES,
    Baseline,
    Regime,
    ScoringStage,
)
from datp.core.identity import alpha_label
from datp.data.common.storage import read_artifact
from datp.evaluation.metric_keys import (
    CONFUSION_FN,
    CONFUSION_FP,
    CONFUSION_MATRIX_KEY,
    CONFUSION_TN,
    CONFUSION_TP,
    COVERAGE_RATIO_KEY,
    MetricName,
)
from datp.evaluation.artifact_validation import client_rows, validate_metrics_payload
from datp.evaluation.metrics import ClientMetrics, EvaluationResult
from datp.evaluation.metrics import build_evaluation_result, recompute_binary_metrics
from datp.reporting.figures import (
    generate_figure1,
    generate_figure2,
    generate_figure3,
    generate_figure4,
)
from datp.reporting.tables import generate_table3, generate_table4
from datp.statistics.bootstrap import bootstrap_ci
from datp.statistics.effect_size import cliffs_delta
from datp.statistics.wilcoxon import bonferroni_correct, wilcoxon_test

_REGIME_A_BASELINES = tuple(b.value for b in sorted(REGIME_BASELINES[Regime.A]))
_REGIME_B_BASELINES = tuple(b.value for b in sorted(REGIME_BASELINES[Regime.B]))
_REGIME_C_BASELINES = tuple(b.value for b in sorted(REGIME_BASELINES[Regime.C]))
_STATS_BASELINES_A = tuple(
    b.value
    for b in sorted(REGIME_BASELINES[Regime.A] - ISOLATED_BASELINES - {Baseline.B3})
)
_STATS_BASELINES_B = tuple(
    b.value for b in sorted(REGIME_BASELINES[Regime.B] - ISOLATED_BASELINES)
)
_REPORTING_SOURCES: set[str] = set()
_IID_ALPHA_LABEL = "iid"  # α = ∞; IID-like baseline condition for Regime C


@attrs.define(frozen=True, slots=True)
class BuildOutputs:
    paths: list[Path]


def _result_path(
    base_dir: Path,
    regime: Regime,
    baseline: Baseline,
    seed: int,
    alpha: str | None = None,
) -> Path:
    loc = ExperimentLocator.for_main(base_dir, regime)
    alpha_float: float | None = None
    if alpha is not None:
        alpha_float = math.inf if alpha == "iid" else float(alpha)
    return loc.result(baseline, seed, alpha_float) / METRICS_FILE


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(
            f"[reporting] Missing metrics artifact. Expected: {path}. Got: absent."
        )
    payload = json.loads(path.read_text(encoding="utf-8"))
    _REPORTING_SOURCES.add(str(path))
    failures = validate_metrics_payload(payload, module="reporting")
    if failures:
        raise ValueError("; ".join(failures) + f". Artifact: {path}.")
    return payload


def _payload_alpha(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, str) and value.lower() in {"iid", "inf"}:
        return math.inf
    return float(value)


def _client_metrics_from_payload(payload: dict[str, Any]) -> list[ClientMetrics]:
    clients: list[ClientMetrics] = []
    for client_id, row in client_rows(payload):
        confusion = row[CONFUSION_MATRIX_KEY]
        missing = [
            key
            for key in (CONFUSION_TP, CONFUSION_FP, CONFUSION_TN, CONFUSION_FN)
            if key not in confusion
        ]
        if missing:
            raise ValueError(
                f"[reporting] Missing confusion counts. Expected: tp/fp/tn/fn for {client_id}. Got: missing={missing}."
            )
        tp = int(confusion[CONFUSION_TP])
        fp = int(confusion[CONFUSION_FP])
        tn = int(confusion[CONFUSION_TN])
        fn = int(confusion[CONFUSION_FN])
        if "n_benign" in row and int(row["n_benign"]) != fp + tn:
            raise ValueError(
                f"[reporting] Benign denominator mismatch. Expected: fp+tn={fp + tn} for {client_id}. Got: {row['n_benign']}."
            )
        if "n_attack" in row and int(row["n_attack"]) != tp + fn:
            raise ValueError(
                f"[reporting] Attack denominator mismatch. Expected: tp+fn={tp + fn} for {client_id}. Got: {row['n_attack']}."
            )
        bm = recompute_binary_metrics(tp, fp, tn, fn)
        clients.append(
            ClientMetrics(
                client_id=str(client_id),
                fpr=bm.fpr,
                tpr=bm.tpr,
                tnr=bm.tnr,
                fnr=bm.fnr,
                precision=bm.precision,
                recall=bm.recall,
                balanced_accuracy=bm.balanced_accuracy,
                macro_f1=bm.macro_f1,
                confusion_matrix={
                    CONFUSION_TP: tp,
                    CONFUSION_FP: fp,
                    CONFUSION_TN: tn,
                    CONFUSION_FN: fn,
                },
                n_benign=fp + tn,
                n_attack=tp + fn,
            )
        )
    return clients


def _assert_metric_matches(
    payload: dict[str, Any],
    _result: EvaluationResult,
    key: str,
    value: float,
    metric_tol: float,
) -> None:
    saved_raw = payload.get(key)
    if saved_raw is None:
        raise ValueError(
            f"[reporting] Missing metric field. Expected: {key}. Got: absent."
        )
    saved = float(saved_raw)
    if np.isnan(saved) and np.isnan(value):
        return
    if np.isnan(saved) != np.isnan(value):
        raise ValueError(
            f"[reporting] Metric schema mismatch. Expected: {key}={value}. Got: {saved}."
        )
    if abs(saved - value) > metric_tol:
        raise ValueError(
            f"[reporting] Metric schema mismatch. Expected: {key}={value:.12g} from canonical counts. Got: {saved:.12g}."
        )


def _evaluation_from_payload(
    payload: dict[str, Any], metric_tol: float
) -> EvaluationResult:
    per_client = _client_metrics_from_payload(payload)
    eligible_ids = [str(client_id) for client_id in payload["eligible_ids"]]
    pending_ids = [str(client_id) for client_id in payload["pending_ids"]]
    eval_incomplete_ids = [
        str(client_id) for client_id in payload["eval_incomplete_ids"]
    ]
    result = build_evaluation_result(
        baseline=Baseline(str(payload["baseline"])),
        regime=Regime(str(payload["regime"])),
        seed=int(payload["seed"]),
        alpha=_payload_alpha(payload.get("alpha")),
        per_client=per_client,
        eligible_ids=eligible_ids,
        pending_ids=pending_ids,
        eval_incomplete_ids=eval_incomplete_ids,
    )
    _assert_metric_matches(
        payload, result, COVERAGE_RATIO_KEY, result.coverage_ratio, metric_tol
    )
    _assert_metric_matches(
        payload, result, MetricName.CV_FPR.value, result.cv_fpr, metric_tol
    )
    _assert_metric_matches(
        payload, result, MetricName.MEAN_FPR.value, result.mean_fpr, metric_tol
    )
    _assert_metric_matches(
        payload, result, MetricName.STD_FPR.value, result.std_fpr, metric_tol
    )
    _assert_metric_matches(
        payload, result, MetricName.CV_TPR.value, result.cv_tpr, metric_tol
    )
    _assert_metric_matches(
        payload, result, MetricName.IQR_FPR.value, result.iqr_fpr, metric_tol
    )
    _assert_metric_matches(payload, result, "iqr_tpr", result.iqr_tpr, metric_tol)
    _assert_metric_matches(
        payload,
        result,
        MetricName.WORST_CLIENT_FPR.value,
        result.worst_client_fpr,
        metric_tol,
    )
    _assert_metric_matches(payload, result, "worst_ba", result.worst_ba, metric_tol)
    _assert_metric_matches(
        payload, result, "p10_macro_f1", result.p10_macro_f1, metric_tol
    )
    if int(payload["eligible_count"]) != result.eligible_count:
        raise ValueError(
            f"[reporting] Eligibility count mismatch. Expected: {result.eligible_count}. Got: {payload['eligible_count']}."
        )
    if int(payload["client_count"]) != result.client_count:
        raise ValueError(
            f"[reporting] Client count mismatch. Expected: {result.client_count}. Got: {payload['client_count']}."
        )
    return result


def _load_results(
    base_dir: Path,
    regime: Regime,
    baselines: tuple[str, ...],
    alpha: str | None = None,
    *,
    seeds: tuple[int, ...],
    metric_tol: float,
) -> dict[str, list[EvaluationResult]]:
    loaded: dict[str, list[EvaluationResult]] = {}
    for baseline in baselines:
        loaded[baseline] = []
        for seed in seeds:
            path = _result_path(base_dir, regime, Baseline(baseline), seed, alpha)
            try:
                loaded[baseline].append(
                    _evaluation_from_payload(_load_json(path), metric_tol)
                )
            except ValueError as exc:
                raise ValueError(f"{exc} Artifact: {path}.") from exc
    return loaded


def _cv_fpr(result: EvaluationResult) -> float:
    return float(result.cv_fpr)


def _eligible_fprs(result: EvaluationResult) -> dict[str, float]:
    eligible = set(result.eligible_ids)
    return {c.client_id: c.fpr for c in result.per_client if c.client_id in eligible}


def _eligible_intersection_fprs(
    left: EvaluationResult, right: EvaluationResult
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    left_map = _eligible_fprs(left)
    right_map = _eligible_fprs(right)
    ids = sorted(set(left_map) & set(right_map))
    if not ids:
        raise ValueError(
            f"[reporting] No eligible-client intersection. Expected: shared eligible clients for {left.baseline} vs {right.baseline}. Got: empty."
        )
    left_missing = sorted(set(left_map) - set(ids))
    right_missing = sorted(set(right_map) - set(ids))
    if left_missing or right_missing:
        raise ValueError(
            f"[reporting] Eligible-client set mismatch. Expected: identical eligible-client sets for controlled comparison. Got: left_only={left_missing}, right_only={right_missing}."
        )
    return (
        np.array([left_map[cid] for cid in ids], dtype=np.float64),
        np.array([right_map[cid] for cid in ids], dtype=np.float64),
        ids,
    )


def _bootstrap_payload(
    deltas: np.ndarray, n_bootstrap: int, ci: float, bootstrap_seed: int
) -> dict[str, Any]:
    result = bootstrap_ci(deltas, n_bootstrap=n_bootstrap, ci=ci, seed=bootstrap_seed)
    return {
        "per_seed_deltas": [float(x) for x in deltas],
        "mean_delta": result.mean_delta,
        "ci_lower": result.ci_lower,
        "ci_upper": result.ci_upper,
        "ci": ci,
        "excludes_zero": result.excludes_zero,
        "n_bootstrap": result.n_bootstrap,
        "n_seeds": result.n_seeds,
    }


def _paired_deltas(
    results: dict[str, list[EvaluationResult]],
    left: str,
    right: str,
) -> np.ndarray:
    return np.array(
        [
            _cv_fpr(results[left][idx]) - _cv_fpr(results[right][idx])
            for idx in range(len(results[left]))
        ]
    )


def _pooled_intersection_fprs(
    results: dict[str, list[EvaluationResult]],
    left: str,
    right: str,
) -> tuple[np.ndarray, np.ndarray]:
    left_arrays: list[np.ndarray] = []
    right_arrays: list[np.ndarray] = []
    for idx in range(len(results[left])):
        left_arr, right_arr, _ = _eligible_intersection_fprs(
            results[left][idx], results[right][idx]
        )
        left_arrays.append(left_arr)
        right_arrays.append(right_arr)
    return np.concatenate(left_arrays), np.concatenate(right_arrays)


def _common_eligible_fprs(
    results: dict[str, list[EvaluationResult]], baselines: tuple[str, ...]
) -> dict[str, list[np.ndarray]]:
    out: dict[str, list[np.ndarray]] = {baseline: [] for baseline in baselines}
    n_seeds = len(results[baselines[0]])
    for idx in range(n_seeds):
        maps = {
            baseline: _eligible_fprs(results[baseline][idx]) for baseline in baselines
        }
        ids = sorted(set.intersection(*(set(maps[baseline]) for baseline in baselines)))
        if not ids:
            raise ValueError(
                f"[reporting] No eligible-client intersection. Expected: shared eligible clients for {baselines}. Got: empty."
            )
        for baseline in baselines:
            missing = sorted(set(maps[baseline]) - set(ids))
            if missing:
                raise ValueError(
                    f"[reporting] Eligible-client set mismatch. Expected: identical eligible-client sets for {baselines}. Got: baseline={baseline} extra={missing}."
                )
            out[baseline].append(
                np.array([maps[baseline][cid] for cid in ids], dtype=np.float64)
            )
    return out


def _write_figure_data(output_dir: Path, stem: str, payload: dict[str, Any]) -> Path:
    return write_json_atomic(output_dir / f"{stem}_data.json", payload)


def _check_heterogeneity_context(
    bootstrap_payload: dict[str, Any],
    regime_a: dict[str, list[EvaluationResult]],
    base_dir: Path,
    practical_significance_threshold: float,
    seeds: tuple[int, ...],
    metric_tol: float,
) -> dict[str, Any]:
    """Evaluate Regime C IID context; the primary endpoint is Regime A B1-minus-B2 CV(FPR) bootstrap CI."""
    primary_ci_excludes_zero: bool = bool(
        bootstrap_payload["primary_endpoint"]["excludes_zero"]
    )
    b1_natural_mean = (
        float(np.mean([_cv_fpr(r) for r in regime_a["b1"]]))
        if regime_a.get("b1")
        else float("nan")
    )

    b1_iid_mean: float | None = None
    iid_data_available = False
    try:
        iid_results = _load_results(
            base_dir,
            Regime.C,
            ("b1",),
            alpha=_IID_ALPHA_LABEL,
            seeds=seeds,
            metric_tol=metric_tol,
        )
        b1_iid_cv_fprs = [_cv_fpr(r) for r in iid_results["b1"]]
        if b1_iid_cv_fprs:
            b1_iid_mean = float(np.mean(b1_iid_cv_fprs))
            iid_data_available = True
    except (FileNotFoundError, ValueError):
        pass

    if b1_iid_mean is None:
        natural_minus_iid: float | None = None
        practical_significance_met = False
    else:
        natural_minus_iid = b1_natural_mean - b1_iid_mean
        practical_significance_met = (
            natural_minus_iid >= practical_significance_threshold
        )

    if primary_ci_excludes_zero and practical_significance_met:
        context_result = "CONTEXT_SUPPORTS_HETEROGENEITY"
    elif primary_ci_excludes_zero or practical_significance_met:
        context_result = "PARTIAL_CONTEXT"
    else:
        context_result = "CONTEXT_NOT_AVAILABLE_OR_WEAK"

    return {
        "condition": (
            "Regime C and IID comparisons are heterogeneity context/support checks, "
            "not the confirmatory endpoint."
        ),
        "b1_cv_fpr_regime_a_mean": b1_natural_mean,
        "b1_cv_fpr_iid_mean": b1_iid_mean,
        "natural_minus_iid": natural_minus_iid,
        "practical_significance_threshold": practical_significance_threshold,
        "practical_significance_met": practical_significance_met,
        "iid_data_available": iid_data_available,
        "primary_endpoint_ci_excludes_zero": primary_ci_excludes_zero,
        "context_result": context_result,
        "note": (
            "Primary endpoint: Regime A, B1 vs B2, CV(FPR), per-seed bootstrap CI. "
            "Regime C and IID comparisons are heterogeneity context/support checks, not the confirmatory endpoint."
        ),
    }


def _convergence_summary_warnings(base_dir: Path, seeds: tuple[int, ...]) -> list[str]:
    warnings_list: list[str] = []
    for regime in (Regime.A, Regime.B):
        loc = ExperimentLocator.for_main(base_dir, regime)
        for seed in seeds:
            ckpt_dir = loc.checkpoint(seed)
            model_pt = ckpt_dir / MODEL_CHECKPOINT
            summary = ckpt_dir / "convergence_summary.json"
            if model_pt.exists() and not summary.exists():
                warnings_list.append(
                    f"[reporting] Missing convergence_summary.json for {regime.value} seed {seed}. "
                    f"Expected: {summary}. Got: absent."
                )
    return warnings_list


def build_stats(base_dir: Path, cfg: DatpConfig) -> BuildOutputs:
    seeds = tuple(cfg.experiment.seeds)
    regime_c_alphas = tuple(
        alpha_label(alpha) or "" for alpha in cfg.experiment.regime_c_alphas
    )
    n_bootstrap = cfg.statistics.n_bootstrap
    bootstrap_seed = cfg.statistics.bootstrap_seed
    ci = cfg.statistics.ci_level
    metric_tol = cfg.reporting.metric_tol

    analysis_dir = base_dir / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)

    regime_a = _load_results(
        base_dir, Regime.A, _STATS_BASELINES_A, seeds=seeds, metric_tol=metric_tol
    )
    regime_b = _load_results(
        base_dir, Regime.B, _STATS_BASELINES_B, seeds=seeds, metric_tol=metric_tol
    )

    payload: dict[str, Any] = {
        "primary_endpoint": {
            "condition": "Primary endpoint: Regime A, B1 vs B2, CV(FPR), per-seed bootstrap CI.",
            **_bootstrap_payload(
                _paired_deltas(regime_a, "b1", "b2"), n_bootstrap, ci, bootstrap_seed
            ),
        },
        "secondary_regime_a": {
            "b1_vs_b4": _bootstrap_payload(
                _paired_deltas(regime_a, "b1", "b4"), n_bootstrap, ci, bootstrap_seed
            ),
            "b4_vs_b2": _bootstrap_payload(
                _paired_deltas(regime_a, "b4", "b2"), n_bootstrap, ci, bootstrap_seed
            ),
        },
        "secondary_regime_b": {
            "b1_vs_b2": _bootstrap_payload(
                _paired_deltas(regime_b, "b1", "b2"), n_bootstrap, ci, bootstrap_seed
            ),
            "b1_vs_b4": _bootstrap_payload(
                _paired_deltas(regime_b, "b1", "b4"), n_bootstrap, ci, bootstrap_seed
            ),
        },
        "regime_c": {},
    }

    regime_c_p_values: list[float] = []
    for alpha in regime_c_alphas:
        results = _load_results(
            base_dir,
            Regime.C,
            _REGIME_C_BASELINES,
            alpha=alpha,
            seeds=seeds,
            metric_tol=metric_tol,
        )
        b1_b2 = _paired_deltas(results, "b1", "b2")
        b1_b4 = _paired_deltas(results, "b1", "b4")
        b1_fpr, b2_fpr = _pooled_intersection_fprs(results, "b1", "b2")
        wilcoxon = wilcoxon_test(b1_fpr, b2_fpr)
        regime_c_p_values.append(wilcoxon.p_value)
        cliff = cliffs_delta(b1_fpr, b2_fpr)
        payload["regime_c"][alpha] = {
            "b1_vs_b2": _bootstrap_payload(b1_b2, n_bootstrap, ci, bootstrap_seed),
            "b1_vs_b4": _bootstrap_payload(b1_b4, n_bootstrap, ci, bootstrap_seed),
            "paired_client_fpr_policy": "eligible-client intersection within each seed, pooled across seeds",
            "wilcoxon_b1_vs_b2": attrs.asdict(wilcoxon),
            "cliffs_delta_b1_vs_b2": attrs.asdict(cliff),
        }

    bonferroni = bonferroni_correct(
        regime_c_p_values, alpha=cfg.statistics.significance_alpha
    )
    payload["regime_c_bonferroni_b1_vs_b2"] = attrs.asdict(bonferroni)

    payload["heterogeneity_context_check"] = _check_heterogeneity_context(
        payload,
        regime_a,
        base_dir,
        practical_significance_threshold=cfg.statistics.dispersion_threshold,
        seeds=seeds,
        metric_tol=metric_tol,
    )

    json_path = write_json_atomic(analysis_dir / "bootstrap_cis.json", payload)
    csv_path = analysis_dir / "bootstrap_cis.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "scope",
                "comparison",
                "mean_delta",
                "ci_lower",
                "ci_upper",
                "excludes_zero",
            ]
        )
        writer.writerow(
            [
                "primary_endpoint",
                "b1_vs_b2",
                payload["primary_endpoint"]["mean_delta"],
                payload["primary_endpoint"]["ci_lower"],
                payload["primary_endpoint"]["ci_upper"],
                payload["primary_endpoint"]["excludes_zero"],
            ]
        )
        for scope in ("secondary_regime_a", "secondary_regime_b"):
            for comparison, stats in payload[scope].items():
                writer.writerow(
                    [
                        scope,
                        comparison,
                        stats["mean_delta"],
                        stats["ci_lower"],
                        stats["ci_upper"],
                        stats["excludes_zero"],
                    ]
                )
        for alpha, stats_by_comparison in payload["regime_c"].items():
            for comparison in ("b1_vs_b2", "b1_vs_b4"):
                stats = stats_by_comparison[comparison]
                writer.writerow(
                    [
                        f"regime_c_alpha_{alpha}",
                        comparison,
                        stats["mean_delta"],
                        stats["ci_lower"],
                        stats["ci_upper"],
                        stats["excludes_zero"],
                    ]
                )

    return BuildOutputs(paths=[json_path, csv_path])


def _calibration_errors_for_devices(
    base_dir: Path, seed: int, device_ids: list[str], max_points: int, rng_seed: int
) -> dict[str, np.ndarray]:
    errors: dict[str, np.ndarray] = {}
    rng = np.random.default_rng(rng_seed)
    loc = ExperimentLocator.for_main(base_dir, Regime.A)
    for device_id in device_ids:
        path = loc.score(seed, stage=ScoringStage.CAL, client_id=device_id)
        values = read_artifact(path).to_numpy()[:, 0].astype(np.float64, copy=False)
        if values.size > max_points:
            values = rng.choice(values, size=max_points, replace=False)
        errors[device_id] = values
    return errors


def build_figures(base_dir: Path, cfg: DatpConfig) -> BuildOutputs:
    """Generate Figures 1–4 from completed result and score artifacts."""
    seeds = tuple(cfg.experiment.seeds)
    regime_c_alphas = tuple(
        alpha_label(alpha) or "" for alpha in cfg.experiment.regime_c_alphas
    )
    metric_tol = cfg.reporting.metric_tol
    figure2_max_points = cfg.reporting.figure2_max_points
    style = cfg.reporting.style

    figures_dir = base_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []

    regime_a = _load_results(
        base_dir, Regime.A, _STATS_BASELINES_A, seeds=seeds, metric_tol=metric_tol
    )
    seed0_b1 = regime_a["b1"][0]
    seed0_b2 = regime_a["b2"][0]
    b1_seed0_fpr, b2_seed0_fpr, figure1_ids = _eligible_intersection_fprs(
        seed0_b1, seed0_b2
    )
    figure1_payload = {
        "figure": "figure_1",
        "title": "Per-device FPR: B1 vs B2, Regime A — representative seed, descriptive only",
        "dataset": "nbaiot",
        "regime": Regime.A.value,
        "seed": seed0_b1.seed,
        "seeds": [seed0_b1.seed],
        "source_metrics_files": [
            str(_result_path(base_dir, Regime.A, Baseline.B1, seed0_b1.seed)),
            str(_result_path(base_dir, Regime.A, Baseline.B2, seed0_b2.seed)),
        ],
        "run_ids": [
            f"{Regime.A.value}_b1_seed{seed0_b1.seed}",
            f"{Regime.A.value}_b2_seed{seed0_b2.seed}",
        ],
        "alphas": [],
        "eligible_counts": {
            Baseline.B1.value: seed0_b1.eligible_count,
            Baseline.B2.value: seed0_b2.eligible_count,
        },
        "client_counts": {
            Baseline.B1.value: seed0_b1.client_count,
            Baseline.B2.value: seed0_b2.client_count,
        },
        "coverage_ratios": {
            Baseline.B1.value: seed0_b1.coverage_ratio,
            Baseline.B2.value: seed0_b2.coverage_ratio,
        },
        "metric_names": ["fpr"],
        "evidence_role": "descriptive",
        "seed_scope": "representative_seed",
        "not_confirmatory_warning": "Representative seed only; descriptive evidence, not confirmatory.",
        "validation_status": "PASS",
        "baselines": [Baseline.B1.value, Baseline.B2.value],
        "baseline_order": [Baseline.B1.value, Baseline.B2.value],
        "eligibility_policy": "eligible-client intersection",
        "axis_labels": {"x": "Device", "y": "FPR"},
        "clients": [
            {
                "client_id": cid,
                Baseline.B1.value: float(b1),
                Baseline.B2.value: float(b2),
            }
            for cid, b1, b2 in zip(figure1_ids, b1_seed0_fpr, b2_seed0_fpr, strict=True)
        ],
    }
    paths.append(_write_figure_data(figures_dir, "figure_1", figure1_payload))

    fig1_png = generate_figure1(
        dict(zip(figure1_ids, b1_seed0_fpr, strict=True)),
        dict(zip(figure1_ids, b2_seed0_fpr, strict=True)),
        figures_dir,
        seed=seed0_b1.seed,
        style=style,
    )
    fig1_std = figures_dir / "figure_1.png"
    shutil.copyfile(fig1_png, fig1_std)
    fig1_pdf = figures_dir / "figure_1.pdf"
    shutil.copyfile(fig1_png.with_suffix(".pdf"), fig1_pdf)
    paths.extend([fig1_png, fig1_std, fig1_pdf])

    seed0_b1_fprs = _eligible_fprs(seed0_b1)
    sorted_devices = sorted(
        seed0_b1_fprs, key=lambda device_id: seed0_b1_fprs[device_id]
    )
    representative = [
        sorted_devices[0],
        sorted_devices[len(sorted_devices) // 2],
        sorted_devices[-1],
    ]
    rep_seed = seed0_b1.seed
    cal_errors = _calibration_errors_for_devices(
        base_dir,
        seed=rep_seed,
        device_ids=representative,
        max_points=figure2_max_points,
        rng_seed=cfg.reporting.figure2_rng_seed,
    )
    tau_global = float(
        _load_json(_result_path(base_dir, Regime.A, Baseline.B1, rep_seed))[
            "tau_global"
        ]
    )
    paths.append(
        _write_figure_data(
            figures_dir,
            "figure_2",
            {
                "figure": "figure_2",
                "title": "Calibration-error ECDF for three representative N-BaIoT clients with B1 client-averaged threshold \u2014 representative seed, descriptive only",
                "dataset": "nbaiot",
                "regime": Regime.A.value,
                "seed": rep_seed,
                "seeds": [rep_seed],
                "source_metrics_files": [
                    str(_result_path(base_dir, Regime.A, Baseline.B1, rep_seed))
                ],
                "source_score_manifests": [
                    str(
                        ExperimentLocator.for_main(base_dir, Regime.A).score(rep_seed)
                        / SCORING_MANIFEST_FILE
                    )
                ],
                "run_ids": [f"{Regime.A.value}_b1_seed{rep_seed}"],
                "alphas": [],
                "eligible_counts": {Baseline.B1.value: seed0_b1.eligible_count},
                "client_counts": {Baseline.B1.value: seed0_b1.client_count},
                "coverage_ratios": {Baseline.B1.value: seed0_b1.coverage_ratio},
                "metric_names": ["reconstruction_error", "threshold_value"],
                "evidence_role": "descriptive",
                "seed_scope": "representative_seed",
                "not_confirmatory_warning": "Representative seed only; descriptive evidence, not confirmatory.",
                "validation_status": "PASS",
                "baselines": [Baseline.B1.value],
                "baseline_order": [Baseline.B1.value],
                "eligibility_policy": f"selected eligible clients from B1 seed {rep_seed}",
                "axis_labels": {"x": "Reconstruction Error", "y": "Density"},
                "tau_global": tau_global,
                "client_ids": representative,
                "max_points_per_client": figure2_max_points,
            },
        )
    )
    fig2_png = generate_figure2(
        cal_errors, tau_global, representative, figures_dir, style=style
    )
    fig2_std = figures_dir / "figure_2.png"
    shutil.copyfile(fig2_png, fig2_std)
    fig2_pdf = figures_dir / "figure_2.pdf"
    shutil.copyfile(fig2_png.with_suffix(".pdf"), fig2_pdf)
    paths.extend([fig2_png, fig2_std, fig2_pdf])

    fpr_by_baseline = _common_eligible_fprs(
        regime_a, (Baseline.B1.value, Baseline.B2.value, Baseline.B4.value)
    )
    paths.append(
        _write_figure_data(
            figures_dir,
            "figure_3",
            {
                "figure": "figure_3",
                "title": "Per-client FPR distribution, Regime A",
                "dataset": "nbaiot",
                "regime": Regime.A.value,
                "source_metrics_files": [
                    str(_result_path(base_dir, Regime.A, Baseline(b), seed))
                    for b in (Baseline.B1.value, Baseline.B2.value, Baseline.B4.value)
                    for seed in seeds
                ],
                "run_ids": [
                    f"{Regime.A.value}_{b}_seed{seed}"
                    for b in (Baseline.B1.value, Baseline.B2.value, Baseline.B4.value)
                    for seed in seeds
                ],
                "seeds": list(seeds),
                "alphas": [],
                "eligible_counts": {
                    b: [r.eligible_count for r in regime_a[b]]
                    for b in (Baseline.B1.value, Baseline.B2.value, Baseline.B4.value)
                },
                "client_counts": {
                    b: [r.client_count for r in regime_a[b]]
                    for b in (Baseline.B1.value, Baseline.B2.value, Baseline.B4.value)
                },
                "coverage_ratios": {
                    b: [r.coverage_ratio for r in regime_a[b]]
                    for b in (Baseline.B1.value, Baseline.B2.value, Baseline.B4.value)
                },
                "metric_names": ["fpr", "cv_fpr_delta_b1_b2"],
                "evidence_role": "descriptive_with_confirmatory_sidecar_delta",
                "seed_scope": "all_seed",
                "validation_status": "PASS",
                "baselines": [Baseline.B1.value, Baseline.B2.value, Baseline.B4.value],
                "paired_seed_cv_fpr_delta_b1_minus_b2": [
                    float(x)
                    for x in _paired_deltas(
                        regime_a, Baseline.B1.value, Baseline.B2.value
                    )
                ],
                "seed_aggregation_policy": "eligible-client FPR values pooled across configured seeds after intersection",
                "baseline_order": [
                    Baseline.B1.value,
                    Baseline.B2.value,
                    Baseline.B4.value,
                ],
                "eligibility_policy": "eligible-client intersection within each seed",
                "axis_labels": {"x": "Baseline", "y": "FPR"},
                "values": {
                    baseline: [[float(x) for x in arr] for arr in arrays]
                    for baseline, arrays in fpr_by_baseline.items()
                },
            },
        )
    )
    fig3_png = generate_figure3(fpr_by_baseline, figures_dir, style=style)
    fig3_std = figures_dir / "figure_3.png"
    shutil.copyfile(fig3_png, fig3_std)
    fig3_pdf = figures_dir / "figure_3.pdf"
    shutil.copyfile(fig3_png.with_suffix(".pdf"), fig3_pdf)
    paths.extend([fig3_png, fig3_std, fig3_pdf])

    cv_fpr_by_baseline: dict[str, dict[str, list[float]]] = {}
    regime_c_loaded: dict[str, dict[str, list[EvaluationResult]]] = {}
    for baseline in _REGIME_C_BASELINES:
        cv_fpr_by_baseline[baseline] = {}
        regime_c_loaded[baseline] = {}
        for alpha in regime_c_alphas:
            results = _load_results(
                base_dir,
                Regime.C,
                (baseline,),
                alpha=alpha,
                seeds=seeds,
                metric_tol=metric_tol,
            )[baseline]
            regime_c_loaded[baseline][alpha] = results
            cv_fpr_by_baseline[baseline][alpha] = [_cv_fpr(r) for r in results]
    paths.append(
        _write_figure_data(
            figures_dir,
            "figure_4",
            {
                "figure": "figure_4",
                "title": "CV(FPR) vs Dirichlet alpha, Regime C",
                "dataset": "nbaiot",
                "regime": Regime.C.value,
                "source_metrics_files": [
                    str(_result_path(base_dir, Regime.C, Baseline(b), seed, alpha))
                    for b in _REGIME_C_BASELINES
                    for alpha in regime_c_alphas
                    for seed in seeds
                ],
                "run_ids": [
                    f"{Regime.C.value}_{b}_seed{seed}_alpha{alpha}"
                    for b in _REGIME_C_BASELINES
                    for alpha in regime_c_alphas
                    for seed in seeds
                ],
                "seeds": list(seeds),
                "alphas": list(regime_c_alphas),
                "eligible_counts": {
                    b: {
                        a: [r.eligible_count for r in regime_c_loaded[b][a]]
                        for a in regime_c_alphas
                    }
                    for b in _REGIME_C_BASELINES
                },
                "client_counts": {
                    b: {
                        a: [r.client_count for r in regime_c_loaded[b][a]]
                        for a in regime_c_alphas
                    }
                    for b in _REGIME_C_BASELINES
                },
                "coverage_ratios": {
                    b: {
                        a: [r.coverage_ratio for r in regime_c_loaded[b][a]]
                        for a in regime_c_alphas
                    }
                    for b in _REGIME_C_BASELINES
                },
                "metric_names": ["cv_fpr"],
                "evidence_role": "secondary",
                "seed_scope": "all_seed",
                "validation_status": "PASS",
                "baselines": list(_REGIME_C_BASELINES),
                "seed_aggregation_policy": "mean with one-standard-deviation band across configured seeds",
                "baseline_order": list(_REGIME_C_BASELINES),
                "eligibility_policy": "eligible clients only per result row",
                "axis_labels": {"x": "Dirichlet alpha", "y": "CV(FPR)"},
                "values": {
                    baseline: {
                        str(alpha): [float(x) for x in values]
                        for alpha, values in alpha_map.items()
                    }
                    for baseline, alpha_map in cv_fpr_by_baseline.items()
                },
            },
        )
    )
    fig4_png = generate_figure4(cv_fpr_by_baseline, figures_dir, style=style)
    fig4_std = figures_dir / "figure_4.png"
    shutil.copyfile(fig4_png, fig4_std)
    fig4_pdf = figures_dir / "figure_4.pdf"
    shutil.copyfile(fig4_png.with_suffix(".pdf"), fig4_pdf)
    paths.extend([fig4_png, fig4_std, fig4_pdf])
    return BuildOutputs(paths=paths)


def build_tables(base_dir: Path, cfg: DatpConfig) -> BuildOutputs:
    """Generate Tables 3–4 from completed result artifacts."""
    seeds = tuple(cfg.experiment.seeds)
    metric_tol = cfg.reporting.metric_tol
    baseline_labels = cfg.reporting.style.baseline_labels
    tables_dir = base_dir / "tables"
    table3 = generate_table3(
        _load_results(
            base_dir, Regime.A, _REGIME_A_BASELINES, seeds=seeds, metric_tol=metric_tol
        ),
        tables_dir,
        baseline_labels=baseline_labels,
    )
    table4 = generate_table4(
        _load_results(
            base_dir, Regime.B, _REGIME_B_BASELINES, seeds=seeds, metric_tol=metric_tol
        ),
        tables_dir,
        baseline_labels=baseline_labels,
    )
    return BuildOutputs(
        paths=[
            table3,
            table3.with_suffix(".csv"),
            table4,
            table4.with_suffix(".csv"),
        ]
    )


def validate_results(base_dir: Path, cfg: DatpConfig) -> BuildOutputs:
    seeds = tuple(cfg.experiment.seeds)
    regime_c_alphas = tuple(
        alpha_label(alpha) or "" for alpha in cfg.experiment.regime_c_alphas
    )
    metric_tol = cfg.reporting.metric_tol
    paths: list[Path] = []
    _load_results(
        base_dir, Regime.A, _REGIME_A_BASELINES, seeds=seeds, metric_tol=metric_tol
    )
    _load_results(
        base_dir, Regime.B, _REGIME_B_BASELINES, seeds=seeds, metric_tol=metric_tol
    )
    for alpha in regime_c_alphas:
        _load_results(
            base_dir,
            Regime.C,
            _REGIME_C_BASELINES,
            alpha=alpha,
            seeds=seeds,
            metric_tol=metric_tol,
        )
    validation_path = write_json_atomic(
        base_dir / "analysis" / "metrics_schema_validation.json",
        {
            "status": "PASS",
            "source": "canonical per-client confusion-count reconstruction",
            "validated_regimes": [Regime.A.value, Regime.B.value, Regime.C.value],
            "seeds": list(seeds),
            "regime_c_alphas": list(regime_c_alphas),
        },
    )
    paths.append(validation_path)
    return BuildOutputs(paths=paths)


_REPRESENTATIVE_SEED_FIGURES = {"figure_1", "figure_2"}


def _validate_figure_sidecars(figures_dir: Path) -> list[str]:
    errors: list[str] = []
    for fig_name in _REPRESENTATIVE_SEED_FIGURES:
        sidecar = figures_dir / f"{fig_name}_data.json"
        if not sidecar.exists():
            errors.append(f"[reporting] Missing figure sidecar: {sidecar}")
            continue
        try:
            data = json.loads(sidecar.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"[reporting] Unreadable figure sidecar {sidecar}: {exc}")
            continue
        if data.get("seed_scope") != "representative_seed":
            errors.append(
                f"[reporting] {fig_name} sidecar missing seed_scope=representative_seed. Got: {data.get('seed_scope')!r}."
            )
        if data.get("evidence_role") != "descriptive":
            errors.append(
                f"[reporting] {fig_name} sidecar missing evidence_role=descriptive. Got: {data.get('evidence_role')!r}."
            )
        if not data.get("not_confirmatory_warning"):
            errors.append(
                f"[reporting] {fig_name} sidecar missing not_confirmatory_warning field."
            )
        title = data["title"]
        if "representative seed" not in title.lower():
            errors.append(
                f"[reporting] {fig_name} sidecar title does not include 'representative seed'. Got: {title!r}."
            )
    return errors


def build_all(base_dir: Path, cfg: DatpConfig) -> BuildOutputs:
    """Build analysis, figures, and tables."""
    _REPORTING_SOURCES.clear()
    paths: list[Path] = []
    failures: list[str] = []
    for step in (validate_results, build_stats, build_figures, build_tables):
        try:
            paths.extend(step(base_dir, cfg).paths)
        except Exception as exc:
            failures.append(str(exc))
            break
    sidecar_errors = _validate_figure_sidecars(base_dir / "figures")
    failures.extend(sidecar_errors)
    conv_warnings = _convergence_summary_warnings(base_dir, tuple(cfg.experiment.seeds))
    audit_path = write_json_atomic(
        base_dir / "analysis" / REPORTING_AUDIT_FILE,
        {
            "schema_version": "1",
            "generated_tables": [
                str(path)
                for path in paths
                if path.suffix in {".tex", ".csv"} and "table" in path.name
            ],
            "generated_figures": [
                str(path)
                for path in paths
                if path.suffix in {".pdf", ".png", ".json"} and "figure" in path.name
            ],
            "source_metrics_files": sorted(_REPORTING_SOURCES),
            "source_score_manifests": sorted(
                str(
                    ExperimentLocator.for_main(base_dir, Regime.A).score(seed, None)
                    / SCORING_MANIFEST_FILE
                )
                for seed in cfg.experiment.seeds
            ),
            "source_run_ids_or_artifact_paths": sorted(_REPORTING_SOURCES),
            "validation_results": "FAIL" if failures else "PASS",
            "recomputation_checks": "canonical confusion-matrix recomputation during load",
            "coverage_checks": "explicit eligible_ids/pending_ids/eval_incomplete_ids required",
            "missing_field_checks": "validate_metrics_payload",
            "stale_artifact_checks": "schema/provenance/sidecar checks",
            "descriptive_figure_checks": f"representative-seed sidecar validation for {sorted(_REPRESENTATIVE_SEED_FIGURES)}",
            "convergence_metadata_checks": "warn if convergence_summary.json absent alongside model.pt",
            "figure_table_output_paths": [str(path) for path in paths],
            "warnings": conv_warnings,
            "failures": failures,
        },
    )
    paths.append(audit_path)
    if failures:
        raise ValueError(
            f"[reporting] reporting_audit contains failures. Expected: none. Got: {failures}."
        )
    return BuildOutputs(paths=paths)
