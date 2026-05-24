from dataclasses import dataclass, field
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from datp.artifacts.constants import ABORTED_MARKER
from datp.artifacts.paths import ExperimentLocator
from datp.artifacts.results import results_exist
from datp.core.enums import Regime
from datp.sweep.run_sweep import build_experiment_matrix

console = Console()


@dataclass(slots=True)
class RegimeReport:
    regime: Regime
    complete: list = field(default_factory=list)
    missing: list = field(default_factory=list)
    aborted: list = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.complete) + len(self.missing) + len(self.aborted)

    @property
    def complete_count(self) -> int:
        return len(self.complete)

    @property
    def missing_count(self) -> int:
        return len(self.missing)

    @property
    def aborted_count(self) -> int:
        return len(self.aborted)


@dataclass(slots=True)
class StatusReport:
    regime_reports: dict[str, RegimeReport] = field(default_factory=dict)

    def summary_rows(self) -> list[tuple[str, int, int, int, int]]:
        rows: list[tuple[str, int, int, int, int]] = []
        total_complete = 0
        total_missing = 0
        total_aborted = 0
        total_all = 0

        for name in sorted(self.regime_reports):
            report = self.regime_reports[name]
            rows.append(
                (
                    f"Regime {name.upper()}",
                    report.complete_count,
                    report.missing_count,
                    report.aborted_count,
                    report.total,
                )
            )
            total_complete += report.complete_count
            total_missing += report.missing_count
            total_aborted += report.aborted_count
            total_all += report.total

        rows.append(
            ("Overall", total_complete, total_missing, total_aborted, total_all)
        )
        return rows

    def summary_lines(self) -> list[str]:
        lines: list[str] = []
        for label, complete, missing, aborted, total in self.summary_rows():
            lines.append(
                f"{label}:  complete={complete}  "
                f"missing={missing}  "
                f"aborted={aborted}  "
                f"(total={total})"
            )
        return lines

    def render_table(self) -> Table:
        table = Table(title="DATP Status", border_style="cyan")
        table.add_column("Scope", style="bold")
        table.add_column("Complete", justify="right", style="green")
        table.add_column("Missing", justify="right", style="yellow")
        table.add_column("Aborted", justify="right", style="red")
        table.add_column("Total", justify="right")

        for label, complete, missing, aborted, total in self.summary_rows():
            style = "bold" if label == "Overall" else ""
            table.add_row(
                f"[{style}]{label}[/{style}]" if style else label,
                str(complete),
                str(missing),
                str(aborted),
                str(total),
            )
        return table


def get_status(
    regime: Regime | None,
    base_dir: Path,
) -> StatusReport:
    cells = build_experiment_matrix()

    if regime is not None:
        cells = [c for c in cells if c.regime == regime]

    report = StatusReport()

    for cell in cells:
        regime_key = cell.regime
        if regime_key not in report.regime_reports:
            report.regime_reports[regime_key] = RegimeReport(regime=regime_key)

        rr = report.regime_reports[regime_key]

        rp = ExperimentLocator.for_main(base_dir, cell.regime).result(
            cell.baseline, cell.seed, cell.alpha
        )

        aborted_file = rp / ABORTED_MARKER
        if aborted_file.is_file():
            rr.aborted.append(cell)
        elif results_exist(
            cell.baseline,
            cell.regime,
            cell.seed,
            cell.alpha,
            base_dir=base_dir,
        ):
            rr.complete.append(cell)
        else:
            rr.missing.append(cell)

    return report


def status(
    regime: Regime | None = typer.Option(
        None, help="Show status for this regime only (a, b, c)"
    ),
    base_dir: Path = typer.Option(..., help="Root output directory"),
) -> None:
    """Report experiment cell completion status."""
    report = get_status(regime=regime, base_dir=base_dir)
    console.print(report.render_table())
