from __future__ import annotations
from datp.artifacts.names import ArtifactFile

import json
from pathlib import Path

import pytest

from datp.validation.constants import (
    CELL_VERDICT_JSON,
    CELL_VERDICTS_JSON,
)
from datp.validation.metric_reproducer import (
    BaselineReproductionResult,
    CellReproductionResult,
    MetricCheckCode,
)
from datp.validation.schemas import ValidationCheck
from datp.validation.score_manifest import (
    ScoreCellVerification,
    ScoreCheckCode,
)
from datp.validation.verdicts import (
    CellVerdict,
    compute_all_verdicts,
    compute_reuse_verdict,
)
from datp.validation.enums import AuditStatus, ReuseVerdict
from datp.core.enums import Baseline, Regime
from datp.core.identity import ScoreCellId, TrainingCellId

from tests.unit.validation.test_metric_reproducer import _seed_results


# --- Synthetic builders --------------------------------------------------------------------------


def _manifest(
    overall_status: AuditStatus,
    *,
    seed: int = 0,
    extra_checks: tuple[ValidationCheck, ...] = (),
) -> ScoreCellVerification:
    pass_check = ValidationCheck(
        code=ScoreCheckCode.MANIFEST_PRESENT,
        status=AuditStatus.PASS,
    )
    return ScoreCellVerification(
        cell=ScoreCellId(cell=TrainingCellId(regime=Regime.A, seed=seed, alpha=None)),
        expected_client_ids=["d1", "d2"],
        expected_splits=["cal", "test_benign", "test_attack"],
        checks=[pass_check, *extra_checks],
        overall_status=overall_status,
    )


def _reproduction(
    overall_status: AuditStatus,
    *,
    seed: int = 0,
    failing_checks: tuple[tuple[Baseline, ValidationCheck], ...] = (),
    missing_baselines: tuple[Baseline, ...] = (),
) -> CellReproductionResult:
    baselines: list[BaselineReproductionResult] = []
    grouped: dict[Baseline, list[ValidationCheck]] = {}
    for baseline, check in failing_checks:
        grouped.setdefault(baseline, []).append(check)
    seen: set[Baseline] = set()
    for baseline, checks in grouped.items():
        baselines.append(
            BaselineReproductionResult(
                baseline=baseline,
                status=AuditStatus.FAIL,
                metrics_path=f"fixture://{baseline.value}/metrics.json",
                recomputed={},
                stored={},
                checks=checks,
            )
        )
        seen.add(baseline)
    if not failing_checks:
        # Synthesize one PASS baseline so reproduction has structure.
        baselines.append(
            BaselineReproductionResult(
                baseline=Baseline.B1,
                status=AuditStatus.PASS,
                metrics_path="fixture://b1/metrics.json",
                recomputed={},
                stored={},
                checks=[
                    ValidationCheck(
                        code=MetricCheckCode.SCALAR_WITHIN_TOLERANCE,
                        status=AuditStatus.PASS,
                        detail="field=cv_fpr",
                    )
                ],
            )
        )
    return CellReproductionResult(
        cell=ScoreCellId(cell=TrainingCellId(regime=Regime.A, seed=seed, alpha=None)),
        overall_status=overall_status,
        baselines=baselines,
        missing_baselines=list(missing_baselines),
    )


# --- Pure verdict logic --------------------------------------------------------------------------


def test_both_checks_pass_yields_verified_reuse_safe() -> None:
    verdict = compute_reuse_verdict(
        _manifest(AuditStatus.PASS),
        _reproduction(AuditStatus.PASS),
    )

    assert verdict.verdict == ReuseVerdict.VERIFIED_REUSE_SAFE
    assert verdict.manifest_status == AuditStatus.PASS
    assert verdict.reproduction_status == AuditStatus.PASS
    assert verdict.failed_checks == []
    assert verdict.reason == "all checks passed"


def test_manifest_fail_blocks_reuse_and_names_failure() -> None:
    failing = ValidationCheck(
        code=ScoreCheckCode.CHECKPOINT_HASH_MATCHES,
        status=AuditStatus.FAIL,
        detail="declared=abc, actual=def",
    )
    verdict = compute_reuse_verdict(
        _manifest(AuditStatus.FAIL, extra_checks=(failing,)),
        _reproduction(AuditStatus.PASS),
    )

    assert verdict.verdict == ReuseVerdict.REUSE_BLOCKED_RERUN_REQUIRED
    assert verdict.manifest_status == AuditStatus.FAIL
    codes = [entry.code for entry in verdict.failed_checks]
    assert f"manifest:{ScoreCheckCode.CHECKPOINT_HASH_MATCHES}" in codes
    assert "manifest:checkpoint_hash_matches" in verdict.reason


def test_reproduction_fail_blocks_reuse_and_names_baseline_failure() -> None:
    check = ValidationCheck(
        code=MetricCheckCode.SCALAR_WITHIN_TOLERANCE,
        status=AuditStatus.FAIL,
        detail="field=mean_fpr, abs diff 0.4 > 0.01",
    )
    verdict = compute_reuse_verdict(
        _manifest(AuditStatus.PASS),
        _reproduction(
            AuditStatus.FAIL,
            failing_checks=((Baseline.B2, check),),
        ),
    )

    assert verdict.verdict == ReuseVerdict.REUSE_BLOCKED_RERUN_REQUIRED
    assert verdict.reproduction_status == AuditStatus.FAIL
    codes = [entry.code for entry in verdict.failed_checks]
    assert "reproduction:b2.scalar_within_tolerance" in codes
    assert "reproduction:b2.scalar_within_tolerance" in verdict.reason


def test_both_fail_concatenates_reasons() -> None:
    manifest_fail = ValidationCheck(
        code=ScoreCheckCode.PARQUET_SCHEMA_VALID,
        status=AuditStatus.FAIL,
        detail="schema error",
    )
    metric_fail = ValidationCheck(
        code=MetricCheckCode.ELIGIBLE_COUNT_EXACT,
        status=AuditStatus.FAIL,
        detail="field=eligible_count, expected=8, actual=7",
    )
    verdict = compute_reuse_verdict(
        _manifest(AuditStatus.FAIL, extra_checks=(manifest_fail,)),
        _reproduction(
            AuditStatus.FAIL,
            failing_checks=((Baseline.B1, metric_fail),),
        ),
    )

    assert verdict.verdict == ReuseVerdict.REUSE_BLOCKED_RERUN_REQUIRED
    prefixes = {entry.code.split(":")[0] for entry in verdict.failed_checks}
    assert prefixes == {"manifest", "reproduction"}
    assert "manifest:parquet_schema_valid" in verdict.reason
    assert "reproduction:b1.eligible_count_exact" in verdict.reason


def test_manifest_partial_blocks_reuse() -> None:
    missing = ValidationCheck(
        code=ScoreCheckCode.SCORING_SENTINEL_PRESENT,
        status=AuditStatus.MISSING,
        detail="sentinel absent",
    )
    verdict = compute_reuse_verdict(
        _manifest(AuditStatus.PARTIAL, extra_checks=(missing,)),
        _reproduction(AuditStatus.PASS),
    )

    assert verdict.verdict == ReuseVerdict.REUSE_BLOCKED_RERUN_REQUIRED
    assert verdict.manifest_status == AuditStatus.PARTIAL


def test_reproduction_partial_blocks_reuse() -> None:
    verdict = compute_reuse_verdict(
        _manifest(AuditStatus.PASS),
        _reproduction(
            AuditStatus.PARTIAL,
            missing_baselines=(Baseline.B3,),
        ),
    )

    assert verdict.verdict == ReuseVerdict.REUSE_BLOCKED_RERUN_REQUIRED
    assert verdict.reproduction_status == AuditStatus.PARTIAL
    codes = [entry.code for entry in verdict.failed_checks]
    assert "reproduction:b3.metrics_json_missing" in codes


def test_cell_disagreement_raises() -> None:
    with pytest.raises(ValueError, match="disagree on cell"):
        compute_reuse_verdict(
            _manifest(AuditStatus.PASS, seed=0),
            _reproduction(AuditStatus.PASS, seed=1),
        )


# --- Batch (live integration over real T02/T03 paths) --------------------------------------------


def test_compute_all_verdicts_writes_table_and_summary(tmp_path: Path) -> None:
    base_dir = tmp_path / "outputs"
    _seed_results(base_dir, tmp_path, seed=0)
    _seed_results(base_dir, tmp_path, seed=1)

    table = compute_all_verdicts(base_dir, write_reports=True)

    assert len(table.cells) == 2
    assert all(c.verdict == ReuseVerdict.VERIFIED_REUSE_SAFE for c in table.cells)
    assert table.summary.total == 2
    assert table.summary.verified_reuse_safe == 2
    assert table.summary.reuse_blocked_rerun_required == 0
    assert table.summary.by_regime[Regime.A][ReuseVerdict.VERIFIED_REUSE_SAFE] == 2

    index_path = base_dir / "scores" / CELL_VERDICTS_JSON
    assert index_path.is_file()
    payload = json.loads(index_path.read_text())
    assert len(payload["cells"]) == 2
    assert payload["summary"]["verified_reuse_safe"] == 2
    for cell in table.cells:
        cell_dir = (
            base_dir / "scores" / cell.cell.regime.value / f"seed_{cell.cell.seed}"
        )
        assert (cell_dir / CELL_VERDICT_JSON).is_file()


def test_compute_all_verdicts_blocks_when_metrics_drift(tmp_path: Path) -> None:
    base_dir = tmp_path / "outputs"
    _seed_results(base_dir, tmp_path, seed=0)
    # Inject scientific drift into B1 metrics so reproduction FAILs.
    metrics_path = base_dir / "results" / "a" / "b1" / "seed_0" / ArtifactFile.METRICS
    stored = json.loads(metrics_path.read_text())
    stored["mean_fpr"] = float(stored["mean_fpr"]) + 0.5
    metrics_path.write_text(json.dumps(stored), encoding="utf-8")

    table = compute_all_verdicts(base_dir)

    assert len(table.cells) == 1
    cell = table.cells[0]
    assert cell.verdict == ReuseVerdict.REUSE_BLOCKED_RERUN_REQUIRED
    assert cell.reproduction_status == AuditStatus.FAIL
    assert any(
        entry.code == "reproduction:b1.scalar_within_tolerance"
        for entry in cell.failed_checks
    )
    assert table.summary.verified_reuse_safe == 0
    assert table.summary.reuse_blocked_rerun_required == 1


def test_cell_verdict_schema_is_frozen_and_extra_forbid() -> None:
    cell = compute_reuse_verdict(
        _manifest(AuditStatus.PASS),
        _reproduction(AuditStatus.PASS),
    )
    with pytest.raises(Exception):
        CellVerdict(**{**cell.model_dump(), "unknown_field": 1})  # type: ignore[arg-type]
