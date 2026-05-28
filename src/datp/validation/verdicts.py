"""T04 — Reuse verdict checker.

Combines T02 manifest verification (`ScoreCellVerification`) and T03 metric reproduction
(`CellReproductionResult`) into a single per-cell verdict:

- `VERIFIED_REUSE_SAFE` iff both inputs have ``overall_status == AuditStatus.PASS``.
- `REUSE_BLOCKED_RERUN_REQUIRED` otherwise.

Does not retrain, re-score, re-derive thresholds, or decide rerun policy.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from datp.artifacts.directories import SCORES_DIR
from datp.validation.constants import (
    CELL_VERDICT_JSON,
    CELL_VERDICTS_JSON,
)
from datp.validation.discovery import iter_score_cells
from datp.validation.metric_reproducer import (
    CellReproductionResult,
    reproduce_cell_metrics,
)
from datp.validation.score_manifest import (
    ScoreCellVerification,
    verify_score_cell,
)
from datp.validation.writers import write_json
from datp.config.models import DatpConfig
from datp.validation.enums import AuditStatus, ReuseVerdict
from datp.core.enums import Regime

_REASON_ALL_PASS = "all checks passed"
_MANIFEST_PREFIX = "manifest"
_REPRODUCTION_PREFIX = "reproduction"


class VerdictReasonEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    source: str
    code: str
    status: AuditStatus
    detail: str = ""


class CellVerdict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    cell_dir: str
    regime: Regime
    seed: int
    alpha: str | None
    dataset: str
    verdict: ReuseVerdict
    manifest_status: AuditStatus
    reproduction_status: AuditStatus
    reason: str
    failed_checks: list[VerdictReasonEntry] = Field(default_factory=list)


class VerdictSummary(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    total: int
    verified_reuse_safe: int
    reuse_blocked_rerun_required: int
    by_regime: dict[Regime, dict[ReuseVerdict, int]]


class VerdictTable(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    cells: list[CellVerdict]
    summary: VerdictSummary


def _failing_manifest_entries(
    manifest_report: ScoreCellVerification,
) -> list[VerdictReasonEntry]:
    return [
        VerdictReasonEntry(
            source=_MANIFEST_PREFIX,
            code=check.code.value,
            status=check.status,
            detail=check.detail,
        )
        for check in manifest_report.checks
        if check.status != AuditStatus.PASS
    ]


def _failing_reproduction_entries(
    reproduction_result: CellReproductionResult,
) -> list[VerdictReasonEntry]:
    entries: list[VerdictReasonEntry] = []
    for baseline_result in reproduction_result.baselines:
        for check in baseline_result.checks:
            if check.status == AuditStatus.PASS:
                continue
            entries.append(
                VerdictReasonEntry(
                    source=_REPRODUCTION_PREFIX,
                    code=f"{baseline_result.baseline.value}.{check.code.value}",
                    status=check.status,
                    detail=check.detail or check.field,
                )
            )
    for missing_baseline in reproduction_result.missing_baselines:
        entries.append(
            VerdictReasonEntry(
                source=_REPRODUCTION_PREFIX,
                code=f"{missing_baseline.value}.metrics_json_missing",
                status=AuditStatus.MISSING,
                detail=f"metrics.json absent for baseline {missing_baseline.value}",
            )
        )
    return entries


def _summarize_reason(failed_checks: list[VerdictReasonEntry]) -> str:
    if not failed_checks:
        return _REASON_ALL_PASS
    codes = [
        f"{entry.source}:{entry.code}({entry.status.value})" for entry in failed_checks
    ]
    if len(codes) <= 5:
        return "; ".join(codes)
    head = "; ".join(codes[:5])
    return f"{head}; +{len(codes) - 5} more"


def compute_reuse_verdict(
    manifest_report: ScoreCellVerification,
    reproduction_result: CellReproductionResult,
) -> CellVerdict:
    """Emit `VERIFIED_REUSE_SAFE` iff both inputs are AuditStatus.PASS; else BLOCKED.

    Both inputs must describe the same cell. ``cell_dir``, ``regime``, ``seed``, and
    ``alpha`` are taken from ``manifest_report`` and cross-checked against ``reproduction_result``.
    """
    if manifest_report.cell_dir != reproduction_result.cell_dir:
        raise ValueError(
            f"verdict inputs disagree on cell_dir: "
            f"manifest={manifest_report.cell_dir!r}, reproduction={reproduction_result.cell_dir!r}"
        )

    manifest_status = manifest_report.overall_status
    reproduction_status = reproduction_result.overall_status
    failed: list[VerdictReasonEntry] = []
    failed.extend(_failing_manifest_entries(manifest_report))
    failed.extend(_failing_reproduction_entries(reproduction_result))

    both_pass = (
        manifest_status == AuditStatus.PASS and reproduction_status == AuditStatus.PASS
    )
    verdict = (
        ReuseVerdict.VERIFIED_REUSE_SAFE
        if both_pass
        else ReuseVerdict.REUSE_BLOCKED_RERUN_REQUIRED
    )

    return CellVerdict(
        cell_dir=manifest_report.cell_dir,
        regime=manifest_report.regime,
        seed=manifest_report.seed,
        alpha=manifest_report.alpha,
        dataset=manifest_report.dataset,
        verdict=verdict,
        manifest_status=manifest_status,
        reproduction_status=reproduction_status,
        reason=_summarize_reason(failed),
        failed_checks=failed,
    )


def _summarize(cells: list[CellVerdict]) -> VerdictSummary:
    by_regime: dict[Regime, dict[ReuseVerdict, int]] = {
        regime: dict.fromkeys(ReuseVerdict, 0) for regime in Regime
    }
    safe = 0
    blocked = 0
    for cell in cells:
        by_regime[cell.regime][cell.verdict] += 1
        if cell.verdict == ReuseVerdict.VERIFIED_REUSE_SAFE:
            safe += 1
        else:
            blocked += 1
    return VerdictSummary(
        total=len(cells),
        verified_reuse_safe=safe,
        reuse_blocked_rerun_required=blocked,
        by_regime=by_regime,
    )


def compute_all_verdicts(
    base_dir: Path,
    *,
    data_root: Path | None = None,
    config: DatpConfig | None = None,
    write_reports: bool = False,
) -> VerdictTable:
    """Iterate every discoverable score cell, run T02 + T03, and produce the verdict table.

    When ``write_reports`` is True, writes ``cell_verdict.json`` per cell and a canonical
    ``cell_verdicts.json`` under ``<base_dir>/scores/`` with summary counts and per-cell entries.
    """
    resolved_base = base_dir.resolve()
    resolved_data_root = (data_root or resolved_base.parent).resolve()
    cells: list[CellVerdict] = []

    for location in iter_score_cells(resolved_base):
        manifest_report = verify_score_cell(
            location.cell_dir,
            resolved_base,
            data_root=resolved_data_root,
        )
        reproduction_result = reproduce_cell_metrics(
            location.cell_dir,
            resolved_base,
            config=config,
        )
        cell_verdict = compute_reuse_verdict(manifest_report, reproduction_result)
        cells.append(cell_verdict)
        if write_reports:
            write_json(
                location.cell_dir / CELL_VERDICT_JSON,
                cell_verdict.model_dump(mode="json"),
            )

    table = VerdictTable(cells=cells, summary=_summarize(cells))
    if write_reports:
        write_json(
            resolved_base / SCORES_DIR / CELL_VERDICTS_JSON,
            table.model_dump(mode="json"),
        )
    return table
