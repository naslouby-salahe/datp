from __future__ import annotations

import csv
from pathlib import Path

import attrs
import numpy as np

from datp.core.enums import Baseline
from datp.evaluation.metrics import EvaluationResult
from datp.reporting.engine import format_mean_std as _format_mean_std
from datp.reporting.engine import render
from datp.reporting.validation import validate_main_body_role

MANDATORY_FOOTNOTE = "† Eligible clients only."


@attrs.define(frozen=True, slots=True)
class TableRow:
    baseline: Baseline
    cv_fpr_mean: float
    cv_fpr_std: float
    cv_tpr_mean: float
    cv_tpr_std: float
    worst_ba_mean: float
    worst_ba_std: float
    macro_f1_mean: float
    macro_f1_std: float
    eligible_count: int
    pending_count: int
    coverage_ratio: float


@attrs.define(frozen=True, slots=True)
class LatexTableRow:
    label: str
    cv_fpr: str
    cv_tpr: str
    worst_ba: str
    macro_f1: str
    coverage: str


def _format_coverage_count(
    coverage_ratio: float, eligible_count: int, total_count: int
) -> str:
    return f"{coverage_ratio:.2f} ({eligible_count}/{total_count})"


def _baseline_label(baseline: Baseline, baseline_labels: dict[Baseline, str]) -> str:
    return baseline_labels[baseline]


@attrs.define(slots=True)
class ResultTable:
    title: str
    baseline_labels: dict[Baseline, str]
    rows: list[TableRow] = attrs.Factory(list)
    footnote: str = MANDATORY_FOOTNOTE

    def to_latex(self) -> str:
        non_b0 = [r for r in self.rows if r.baseline != Baseline.B0]
        best_cv_fpr = (
            min(non_b0, key=lambda r: r.cv_fpr_mean).baseline if non_b0 else None
        )
        best_cv_tpr = (
            min(non_b0, key=lambda r: r.cv_tpr_mean).baseline if non_b0 else None
        )

        template_rows: list[LatexTableRow] = []
        for row in self.rows:
            label = _baseline_label(row.baseline, self.baseline_labels)
            template_rows.append(
                LatexTableRow(
                    label=label,
                    cv_fpr=_format_mean_std(
                        row.cv_fpr_mean,
                        row.cv_fpr_std,
                        bold=(row.baseline == best_cv_fpr),
                    )
                    + f" ({row.eligible_count}/{row.eligible_count + row.pending_count})",
                    cv_tpr=_format_mean_std(
                        row.cv_tpr_mean,
                        row.cv_tpr_std,
                        bold=(row.baseline == best_cv_tpr),
                    ),
                    worst_ba=_format_mean_std(
                        row.worst_ba_mean, row.worst_ba_std, bold=False
                    ),
                    macro_f1=_format_mean_std(
                        row.macro_f1_mean, row.macro_f1_std, bold=False
                    ),
                    coverage=_format_coverage_count(
                        row.coverage_ratio,
                        row.eligible_count,
                        row.eligible_count + row.pending_count,
                    ),
                )
            )

        eligible_counts = ", ".join(
            f"{_baseline_label(r.baseline, self.baseline_labels)}: {r.eligible_count}"
            for r in self.rows
        )
        pending_counts = ", ".join(
            f"{_baseline_label(r.baseline, self.baseline_labels)}: {r.pending_count}"
            for r in self.rows
        )

        return render(
            "table_main.tex.j2",
            title=self.title,
            caption=self.title,
            header=(
                "Baseline & CV(FPR)$\\dagger$ & CV(TPR)$\\dagger$ "
                "& Worst BA & P10 client Macro-F1 & Coverage"
            ),
            rows=template_rows,
            footnote=self.footnote,
            comments=[
                f"Eligible counts: {eligible_counts}",
                f"Calibration-Pending counts: {pending_counts}",
            ],
        )

    def to_csv(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "Baseline",
                    "CV(FPR) mean",
                    "CV(FPR) std",
                    "CV(TPR) mean",
                    "CV(TPR) std",
                    "Worst BA mean",
                    "Worst BA std",
                    "P10 client Macro-F1 mean",
                    "P10 client Macro-F1 std",
                    "Eligible",
                    "Pending",
                    "Coverage",
                ]
            )
            for row in self.rows:
                label = _baseline_label(row.baseline, self.baseline_labels)
                writer.writerow(
                    [
                        label,
                        f"{row.cv_fpr_mean:.4f}",
                        f"{row.cv_fpr_std:.4f}",
                        f"{row.cv_tpr_mean:.4f}",
                        f"{row.cv_tpr_std:.4f}",
                        f"{row.worst_ba_mean:.4f}",
                        f"{row.worst_ba_std:.4f}",
                        f"{row.macro_f1_mean:.4f}",
                        f"{row.macro_f1_std:.4f}",
                        row.eligible_count,
                        row.pending_count,
                        f"{row.coverage_ratio:.4f}",
                    ]
                )
            writer.writerow([f"# {self.footnote}"])
        return path


def _build_table_row(
    baseline: Baseline,
    results: list[EvaluationResult],
) -> TableRow:
    cv_fprs = [r.cv_fpr for r in results]
    cv_tprs = [r.cv_tpr for r in results]
    worst_bas = [r.worst_ba for r in results]
    macro_f1s = [r.p10_macro_f1 for r in results]

    eligible_count = len(results[0].eligible_ids)
    pending_count = len(results[0].pending_ids)
    coverage = results[0].coverage_ratio
    for result in results:
        if not np.isfinite(result.coverage_ratio):
            raise ValueError(
                f"[reporting] Coverage ratio missing. Expected: finite coverage for {baseline}. Got: {result.coverage_ratio}."
            )
        if (
            len(result.eligible_ids) != eligible_count
            or len(result.pending_ids) != pending_count
        ):
            raise ValueError(
                f"[reporting] Coverage count mismatch. Expected: stable eligible/pending counts for {baseline}. Got: seed={result.seed} eligible={len(result.eligible_ids)} pending={len(result.pending_ids)}."
            )

    return TableRow(
        baseline=baseline,
        cv_fpr_mean=float(np.mean(cv_fprs)),
        cv_fpr_std=float(np.std(cv_fprs, ddof=1)) if len(cv_fprs) > 1 else 0.0,
        cv_tpr_mean=float(np.mean(cv_tprs)),
        cv_tpr_std=float(np.std(cv_tprs, ddof=1)) if len(cv_tprs) > 1 else 0.0,
        worst_ba_mean=float(np.mean(worst_bas)),
        worst_ba_std=float(np.std(worst_bas, ddof=1)) if len(worst_bas) > 1 else 0.0,
        macro_f1_mean=float(np.mean(macro_f1s)),
        macro_f1_std=float(np.std(macro_f1s, ddof=1)) if len(macro_f1s) > 1 else 0.0,
        eligible_count=eligible_count,
        pending_count=pending_count,
        coverage_ratio=coverage,
    )


def _generate_table(
    title: str,
    results_by_baseline: dict[str, list[EvaluationResult]],
    output_dir: Path,
    filename_stem: str,
    baseline_labels: dict[Baseline, str],
) -> Path:
    validate_main_body_role(list(results_by_baseline.keys()))

    table = ResultTable(title=title, baseline_labels=baseline_labels)
    for baseline_key in sorted(results_by_baseline.keys()):
        baseline = Baseline(baseline_key)
        table.rows.append(_build_table_row(baseline, results_by_baseline[baseline_key]))

    output_dir.mkdir(parents=True, exist_ok=True)

    tex_path = output_dir / f"{filename_stem}.tex"
    tex_path.write_text(table.to_latex(), encoding="utf-8")

    csv_path = output_dir / f"{filename_stem}.csv"
    table.to_csv(csv_path)

    return tex_path


def generate_table3(
    results_by_baseline: dict[str, list[EvaluationResult]],
    output_dir: Path,
    baseline_labels: dict[Baseline, str],
) -> Path:
    return _generate_table(
        title="Table 3: N-BaIoT Main Results",
        results_by_baseline=results_by_baseline,
        output_dir=output_dir,
        filename_stem="table3_nbaiot",
        baseline_labels=baseline_labels,
    )


def generate_table4(
    results_by_baseline: dict[str, list[EvaluationResult]],
    output_dir: Path,
    baseline_labels: dict[Baseline, str],
) -> Path:
    return _generate_table(
        title="Table 4: CICIoT2023 External Validation Results",
        results_by_baseline=results_by_baseline,
        output_dir=output_dir,
        filename_stem="table4_ciciot",
        baseline_labels=baseline_labels,
    )
