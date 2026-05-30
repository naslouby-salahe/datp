from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import polars as pl
import pytest

from datp.artifacts.names import ArtifactFile
from datp.scoring.schema import SCORE_COLUMN
from datp.validation.constants import (
    COVERAGE_RATIO_TOLERANCE,
    RECOMPUTED_METRICS_INDEX_JSON,
    RECOMPUTED_METRICS_JSON,
    SCALAR_METRIC_TOLERANCE,
)
from datp.validation.metric_reproducer import (
    BaselineReproductionResult,
    CellReproductionResult,
    MetricCheckCode,
    reproduce_all_cells,
    reproduce_cell_metrics,
)
from datp.thresholding.thresholds import derive_threshold
from datp.config.compose import compose_config
from datp.validation.enums import AuditStatus
from datp.core.enums import (
    SCORING_STAGES,
    Baseline,
    ConfusionKey,
    Regime,
    ScoringStage,
)
from datp.data.common.storage import write_artifact
from datp.data.datasets.nbaiot.spec import NBAIOT_SPEC
from datp.evaluation.metrics import (
    build_evaluation_result,
    compute_client_record,
)
from datp.scoring.loading import ScoreProvider


CLIENTS: tuple[str, ...] = NBAIOT_SPEC.device_ids
REGIME_A_BASELINES: tuple[Baseline, ...] = (
    Baseline.B1,
    Baseline.B2,
    Baseline.B3,
    Baseline.B4,
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_scores(path: Path, values: np.ndarray) -> None:
    write_artifact(pl.DataFrame({SCORE_COLUMN: values.astype(np.float32)}), path)


def _deterministic_scores(
    seed: int, client_idx: int, stage: ScoringStage
) -> np.ndarray:
    rng = np.random.default_rng(1000 * seed + 7 * client_idx + hash(stage.value) % 50)
    if stage == ScoringStage.CAL:
        return rng.uniform(0.01, 0.10, size=300).astype(np.float32)
    if stage == ScoringStage.TEST_BENIGN:
        return rng.uniform(0.01, 0.12, size=200).astype(np.float32)
    return rng.uniform(0.20, 0.80, size=400).astype(np.float32)


def _build_score_cell(
    *,
    base_dir: Path,
    data_root: Path,
    seed: int = 0,
    clients: tuple[str, ...] = CLIENTS,
) -> Path:
    """Create one Regime A score cell with calibration + test data on disk."""
    cell_dir = base_dir / "scores" / Regime.A.value / f"seed_{seed}"
    cell_dir.mkdir(parents=True, exist_ok=True)

    for stage in SCORING_STAGES:
        stage_dir = cell_dir / stage.value
        stage_dir.mkdir(parents=True, exist_ok=True)
        for idx, cid in enumerate(clients):
            _write_scores(
                stage_dir / f"{cid}.parquet", _deterministic_scores(seed, idx, stage)
            )

    partition_root = data_root / "data" / "processed" / "nbaiot"
    partition_root.mkdir(parents=True, exist_ok=True)
    (partition_root / "manifest.json").write_text(
        json.dumps(
            {
                "dataset": "nbaiot",
                "file_hashes": {"fixture": "abc"},
                "metadata": {
                    "n_features": 115,
                    "n_devices": len(clients),
                    "n_clients": None,
                },
                "created": "2026-04-26T00:00:00+00:00",
            }
        ),
        encoding="utf-8",
    )
    for cid in clients:
        (partition_root / cid).mkdir(parents=True, exist_ok=True)

    ckpt = base_dir / "checkpoints" / Regime.A.value / f"seed_{seed}" / ArtifactFile.MODEL_CHECKPOINT
    ckpt.parent.mkdir(parents=True, exist_ok=True)
    ckpt.write_bytes(b"fixture-checkpoint-bytes")
    ckpt_hash = _sha256(ckpt)

    manifest = {
        "schema_version": "1",
        "dataset": "nbaiot",
        "regime": Regime.A.value,
        "seed": seed,
        "alpha": None,
        "model_checkpoint_path": str(ckpt.relative_to(data_root))
        if data_root in ckpt.parents
        else str(ckpt),
        "model_checkpoint_hash": ckpt_hash,
        "scoring_code_version": "fixture",
        "score_column_name": SCORE_COLUMN,
        "expected_client_ids": sorted(clients),
        "expected_splits": [s.value for s in SCORING_STAGES],
        "actual_client_ids": sorted(clients),
        "actual_splits": sorted(s.value for s in SCORING_STAGES),
        "records": [
            {"client_id": cid, "split": s.value}
            for cid in clients
            for s in SCORING_STAGES
        ],
        "completion_status": "complete",
        "generated_at_utc": "2026-04-26T00:00:00+00:00",
    }
    (cell_dir / ArtifactFile.SCORING_MANIFEST).write_text(
        json.dumps(manifest), encoding="utf-8"
    )
    (cell_dir / ArtifactFile.SCORING_SENTINEL).write_text("done\n", encoding="utf-8")
    return cell_dir


def _expected_metrics_for_baseline(
    base_dir: Path,
    seed: int,
    baseline: Baseline,
    clients: tuple[str, ...],
) -> dict[str, object]:
    """Compute the metrics that the reproducer should output, using canonical helpers directly."""
    cfg = compose_config(regime=Regime.A, baseline=baseline, seed=seed, alpha=None)
    cal_errors: dict[str, np.ndarray] = {}
    score_root = base_dir / "scores" / Regime.A.value / f"seed_{seed}"
    for cid in clients:
        cal_errors[cid] = (
            pl.read_parquet(score_root / "cal" / f"{cid}.parquet")
            .get_column(SCORE_COLUMN)
            .to_numpy()
            .astype(np.float64)
        )
    b1_result = derive_threshold(
        Baseline.B1,
        cal_errors,
        n_min=cfg.threshold.n_min,
        q=cfg.threshold.q,
        tau_global=0.0,
        regime=Regime.A,
        threshold_cfg=cfg.threshold,
    )
    tau_global_b1 = float(b1_result.tau_global)
    threshold_result = derive_threshold(
        baseline,
        cal_errors,
        n_min=cfg.threshold.n_min,
        q=cfg.threshold.q,
        tau_global=tau_global_b1,
        regime=Regime.A,
        threshold_cfg=cfg.threshold,
    )

    provider = ScoreProvider(score_root)
    per_client_metrics = []
    eligible_ids: list[str] = []
    pending_ids: list[str] = []
    eval_incomplete: list[str] = []
    client_thresholds: dict[str, float] = {}
    for ct in threshold_result.client_thresholds:
        benign, attack = provider.load_test_scores(ct.client_id)
        per_client_metrics.append(
            compute_client_record(ct.client_id, benign, attack, ct)
        )
        client_thresholds[ct.client_id] = float(ct.threshold)
        (pending_ids if ct.calibration_pending else eligible_ids).append(ct.client_id)
        if attack.size == 0:
            eval_incomplete.append(ct.client_id)

    evaluation = build_evaluation_result(
        baseline=baseline,
        regime=Regime.A,
        seed=seed,
        alpha=None,
        clients=tuple(per_client_metrics),
        eligible_ids=tuple(eligible_ids),
        pending_ids=tuple(pending_ids),
        incomplete_ids=tuple(eval_incomplete),
    )

    return {
        "baseline": baseline.value,
        "regime": Regime.A.value,
        "seed": seed,
        "alpha": None,
        "dataset": "nbaiot",
        "tau_global": float(threshold_result.tau_global),
        "coverage_ratio": evaluation.coverage_ratio,
        "cv_fpr": evaluation.cv_fpr,
        "cv_tpr": evaluation.cv_tpr,
        "mean_fpr": evaluation.mean_fpr,
        "std_fpr": evaluation.std_fpr,
        "iqr_fpr": evaluation.iqr_fpr,
        "iqr_tpr": evaluation.iqr_tpr,
        "max_min_fpr_gap": evaluation.max_min_fpr_gap,
        "worst_client_fpr": evaluation.worst_client_fpr,
        "worst_ba": evaluation.worst_ba,
        "p10_macro_f1": evaluation.p10_macro_f1,
        "client_count": evaluation.client_count,
        "eligible_count": evaluation.eligible_count,
        "pending_count": len(evaluation.pending_ids),
        "eligible_ids": list(evaluation.eligible_ids),
        "pending_ids": list(evaluation.pending_ids),
        "per_client": {
            cm.client_id: {
                "fpr": cm.metrics.fpr,
                "tpr": cm.metrics.tpr,
                "balanced_accuracy": cm.metrics.balanced_accuracy,
                "macro_f1": cm.metrics.macro_f1,
                "n_benign": cm.n_benign,
                "n_attack": cm.n_attack,
                "confusion_matrix": {
                    ConfusionKey.TP.value: cm.confusion.tp,
                    ConfusionKey.FP.value: cm.confusion.fp,
                    ConfusionKey.TN.value: cm.confusion.tn,
                    ConfusionKey.FN.value: cm.confusion.fn,
                },
                "threshold_value": client_thresholds[cm.client_id],
                "calibration_pending": False,
                "evaluation_incomplete": cm.client_id in eval_incomplete,
            }
            for cm in per_client_metrics
        },
    }


def _write_metrics_json(
    base_dir: Path, seed: int, baseline: Baseline, payload: dict
) -> Path:
    out = (
        base_dir
        / "results"
        / Regime.A.value
        / baseline.value
        / f"seed_{seed}"
        / ArtifactFile.METRICS
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload), encoding="utf-8")
    return out


def _seed_results(base_dir: Path, data_root: Path, seed: int = 0) -> Path:
    """Build a score cell + per-baseline metrics.json files that mirror real production output."""
    cell = _build_score_cell(base_dir=base_dir, data_root=data_root, seed=seed)
    for baseline in REGIME_A_BASELINES:
        expected = _expected_metrics_for_baseline(base_dir, seed, baseline, CLIENTS)
        per_client_map: dict[str, dict[str, object]] = expected["per_client"]  # type: ignore[assignment]
        per_client_list = [
            dict(values, client_id=cid) for cid, values in per_client_map.items()
        ]
        stored = dict(expected)
        stored["per_client"] = per_client_list
        _write_metrics_json(base_dir, seed, baseline, stored)
    return cell


def _baseline_result(
    result: CellReproductionResult, baseline: Baseline
) -> BaselineReproductionResult:
    for br in result.baselines:
        if br.baseline == baseline:
            return br
    raise AssertionError(f"baseline {baseline} not in result")


def test_reproduction_passes_when_stored_matches(tmp_path: Path) -> None:
    base_dir = tmp_path / "outputs"
    cell = _seed_results(base_dir, tmp_path)

    result = reproduce_cell_metrics(cell, base_dir)

    assert result.overall_status == AuditStatus.PASS, [
        (
            b.baseline,
            b.status,
            [c.model_dump() for c in b.checks if c.status != AuditStatus.PASS],
        )
        for b in result.baselines
    ]
    assert {b.baseline for b in result.baselines} == set(REGIME_A_BASELINES)
    assert result.missing_baselines == []


def test_scalar_metric_tolerance_breach_fails(tmp_path: Path) -> None:
    base_dir = tmp_path / "outputs"
    _seed_results(base_dir, tmp_path)
    metrics_path = base_dir / "results" / "a" / "b1" / "seed_0" / ArtifactFile.METRICS
    stored = json.loads(metrics_path.read_text())
    stored["mean_fpr"] = float(stored["mean_fpr"]) + 0.5  # well outside 0.01
    metrics_path.write_text(json.dumps(stored), encoding="utf-8")

    result = reproduce_cell_metrics(base_dir / "scores" / "a" / "seed_0", base_dir)

    b1 = _baseline_result(result, Baseline.B1)
    assert b1.status == AuditStatus.FAIL
    mean_fpr_checks = [c for c in b1.checks if "field=mean_fpr" in c.detail]
    assert mean_fpr_checks and mean_fpr_checks[0].status == AuditStatus.FAIL
    assert f"tol={SCALAR_METRIC_TOLERANCE:.4g}" in mean_fpr_checks[0].detail
    assert result.overall_status == AuditStatus.FAIL


def test_eligible_count_exact_mismatch_fails(tmp_path: Path) -> None:
    base_dir = tmp_path / "outputs"
    _seed_results(base_dir, tmp_path)
    metrics_path = base_dir / "results" / "a" / "b2" / "seed_0" / ArtifactFile.METRICS
    stored = json.loads(metrics_path.read_text())
    stored["eligible_count"] = int(stored["eligible_count"]) + 1
    metrics_path.write_text(json.dumps(stored), encoding="utf-8")

    result = reproduce_cell_metrics(base_dir / "scores" / "a" / "seed_0", base_dir)

    b2 = _baseline_result(result, Baseline.B2)
    elig = [c for c in b2.checks if c.code == MetricCheckCode.ELIGIBLE_COUNT_EXACT]
    assert elig and elig[0].status == AuditStatus.FAIL
    assert b2.status == AuditStatus.FAIL


def test_eligible_ids_set_mismatch_fails(tmp_path: Path) -> None:
    base_dir = tmp_path / "outputs"
    _seed_results(base_dir, tmp_path)
    metrics_path = base_dir / "results" / "a" / "b1" / "seed_0" / ArtifactFile.METRICS
    stored = json.loads(metrics_path.read_text())
    stored["eligible_ids"] = sorted(set(stored["eligible_ids"]) - {CLIENTS[0]}) + [
        "phantom_device"
    ]
    metrics_path.write_text(json.dumps(stored), encoding="utf-8")

    result = reproduce_cell_metrics(base_dir / "scores" / "a" / "seed_0", base_dir)

    b1 = _baseline_result(result, Baseline.B1)
    elig_ids = [c for c in b1.checks if c.code == MetricCheckCode.ELIGIBLE_IDS_EXACT]
    assert elig_ids and elig_ids[0].status == AuditStatus.FAIL


def test_confusion_total_mismatch_fails(tmp_path: Path) -> None:
    base_dir = tmp_path / "outputs"
    _seed_results(base_dir, tmp_path)
    metrics_path = base_dir / "results" / "a" / "b1" / "seed_0" / ArtifactFile.METRICS
    stored = json.loads(metrics_path.read_text())
    stored["per_client"][0]["confusion_matrix"]["tp"] += 17
    metrics_path.write_text(json.dumps(stored), encoding="utf-8")

    result = reproduce_cell_metrics(base_dir / "scores" / "a" / "seed_0", base_dir)

    b1 = _baseline_result(result, Baseline.B1)
    cm = [c for c in b1.checks if c.code == MetricCheckCode.PER_CLIENT_CONFUSION_EXACT]
    assert cm and cm[0].status == AuditStatus.FAIL


def test_coverage_ratio_tolerance_just_inside_passes(tmp_path: Path) -> None:
    base_dir = tmp_path / "outputs"
    _seed_results(base_dir, tmp_path)
    metrics_path = base_dir / "results" / "a" / "b1" / "seed_0" / ArtifactFile.METRICS
    stored = json.loads(metrics_path.read_text())
    stored["coverage_ratio"] = (
        float(stored["coverage_ratio"]) - COVERAGE_RATIO_TOLERANCE * 0.5
    )
    metrics_path.write_text(json.dumps(stored), encoding="utf-8")

    result = reproduce_cell_metrics(base_dir / "scores" / "a" / "seed_0", base_dir)

    b1 = _baseline_result(result, Baseline.B1)
    cov = [
        c
        for c in b1.checks
        if c.code == MetricCheckCode.COVERAGE_RATIO_WITHIN_TOLERANCE
    ]
    assert cov and cov[0].status == AuditStatus.PASS
    assert f"tol={COVERAGE_RATIO_TOLERANCE:.4g}" in cov[0].detail


def test_coverage_ratio_tolerance_just_outside_fails(tmp_path: Path) -> None:
    base_dir = tmp_path / "outputs"
    _seed_results(base_dir, tmp_path)
    metrics_path = base_dir / "results" / "a" / "b1" / "seed_0" / ArtifactFile.METRICS
    stored = json.loads(metrics_path.read_text())
    stored["coverage_ratio"] = (
        float(stored["coverage_ratio"]) - COVERAGE_RATIO_TOLERANCE * 2
    )
    metrics_path.write_text(json.dumps(stored), encoding="utf-8")

    result = reproduce_cell_metrics(base_dir / "scores" / "a" / "seed_0", base_dir)

    b1 = _baseline_result(result, Baseline.B1)
    cov = [
        c
        for c in b1.checks
        if c.code == MetricCheckCode.COVERAGE_RATIO_WITHIN_TOLERANCE
    ]
    assert cov and cov[0].status == AuditStatus.FAIL


def test_missing_metrics_json_returns_missing_baselines(tmp_path: Path) -> None:
    base_dir = tmp_path / "outputs"
    cell = _seed_results(base_dir, tmp_path)
    # Remove B3's metrics.json — the cell still has B1/B2/B4.
    (base_dir / "results" / "a" / "b3" / "seed_0" / ArtifactFile.METRICS).unlink()

    result = reproduce_cell_metrics(cell, base_dir)

    assert Baseline.B3 in result.missing_baselines
    assert {b.baseline for b in result.baselines} == {
        Baseline.B1,
        Baseline.B2,
        Baseline.B4,
    }
    # Overall is PARTIAL (no FAILs but missing data).
    assert result.overall_status == AuditStatus.PARTIAL


def test_no_results_for_cell_reports_all_baselines_missing(tmp_path: Path) -> None:
    base_dir = tmp_path / "outputs"
    cell = _build_score_cell(base_dir=base_dir, data_root=tmp_path)
    # Score cell exists but no results/* at all.
    result = reproduce_cell_metrics(cell, base_dir)

    assert result.baselines == []
    assert set(result.missing_baselines) == set(REGIME_A_BASELINES)
    assert result.overall_status in (AuditStatus.PARTIAL, AuditStatus.MISSING)


def test_missing_cal_directory_raises(tmp_path: Path) -> None:
    base_dir = tmp_path / "outputs"
    cell = _seed_results(base_dir, tmp_path)
    cal_dir = cell / ScoringStage.CAL.value
    for f in cal_dir.glob("*.parquet"):
        f.unlink()
    cal_dir.rmdir()

    with pytest.raises(FileNotFoundError):
        reproduce_cell_metrics(cell, base_dir)


def test_reproduce_all_cells_writes_index(tmp_path: Path) -> None:
    base_dir = tmp_path / "outputs"
    _seed_results(base_dir, tmp_path, seed=0)
    _seed_results(base_dir, tmp_path, seed=1)

    results = reproduce_all_cells(base_dir, write_reports=True)

    assert len(results) == 2
    for r in results:
        cell_dir = base_dir / "scores" / r.cell.regime.value / f"seed_{r.cell.seed}"
        assert (cell_dir / RECOMPUTED_METRICS_JSON).is_file()
    assert (base_dir / "scores" / RECOMPUTED_METRICS_INDEX_JSON).is_file()
    payload = json.loads(
        (base_dir / "scores" / RECOMPUTED_METRICS_INDEX_JSON).read_text(),
    )
    assert len(payload["cells"]) == 2


def test_scalar_constants_match_pre_coding_plan_table() -> None:
    """PRE_CODING_PLAN §5.1 fixes these tolerances; constants must equal them exactly."""
    assert SCALAR_METRIC_TOLERANCE == pytest.approx(0.01, abs=0.0)
    assert COVERAGE_RATIO_TOLERANCE == pytest.approx(0.001, abs=0.0)
