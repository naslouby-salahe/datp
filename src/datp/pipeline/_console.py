from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Iterator

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from datp.core.enums import Regime
from datp.pipeline.enums import DiagnosticStep

console = Console()

_STEP_LABELS: dict[DiagnosticStep, str] = {
    DiagnosticStep.COMPOSE_CONFIG: "Compose config",
    DiagnosticStep.VALIDATE_CONFIG: "Validate config",
    DiagnosticStep.PREPARE_DATA: "Prepare data",
    DiagnosticStep.SET_SEEDS: "Set seeds",
    DiagnosticStep.FL_TRAINING: "FL training",
    DiagnosticStep.LOAD_SCORES: "Load score artifacts",
    DiagnosticStep.DERIVE_THRESHOLDS: "Derive thresholds (B1 + B2)",
    DiagnosticStep.EVALUATE: "Evaluate baselines",
    DiagnosticStep.WRITE_METRICS: "Write metrics",
    DiagnosticStep.CONTINGENCY_DECISION: "Contingency decision",
    DiagnosticStep.SUMMARY: "Summary",
}


def print_banner(
    regime: Regime,
    seed: int,
    output_dir: str,
    *,
    alpha: float | None = None,
) -> None:
    lines = [f"Regime: [cyan]{regime.value.upper()}[/cyan]  Seed: [cyan]{seed}[/cyan]"]
    if alpha is not None:
        lines.append(f"Alpha: [cyan]{alpha:g}[/cyan]")
    lines.append(f"Output: [dim]{output_dir}[/dim]")
    console.print(
        Panel(
            "\n".join(lines), title="[bold]DATP Diagnostic[/bold]", border_style="cyan"
        )
    )


@contextmanager
def step_context(step: DiagnosticStep) -> Iterator[None]:
    label = _STEP_LABELS[step] if step in _STEP_LABELS else step.value
    ordinal = list(DiagnosticStep).index(step) + 1
    console.print(f"  [dim][{ordinal:>2}][/dim] [bold]{label}[/bold] ...", end="")
    t0 = time.monotonic()
    try:
        yield
    except Exception:
        elapsed = time.monotonic() - t0
        console.print(f" [red]\u2717 FAILED[/red] [dim]({elapsed:.1f}s)[/dim]")
        raise
    elapsed = time.monotonic() - t0
    console.print(f" [green]\u2713[/green] [dim]({elapsed:.1f}s)[/dim]")


def print_section_header(title: str) -> None:
    console.print(Panel(f"[bold]{title}[/bold]", border_style="cyan"))


def print_step_start(label: str) -> None:
    console.print(f"[bold]→[/bold] {label}")


def print_step_error(label: str, exc: BaseException) -> None:
    console.print(f"[red]✗[/red] {label}: [red]{exc}[/red]")


def print_completion(label: str) -> None:
    console.print(f"[green]✓[/green] {label}")


def print_summary(
    regime: Regime,
    seed: int,
    b1_cv_fpr: float,
    b2_cv_fpr: float,
    coverage: tuple[int, int],
    output_dir: str,
    total_elapsed: float,
    *,
    alpha: float | None = None,
    contingency: str | None = None,
) -> None:
    title = f"Regime {regime.value.upper()}"
    if alpha is not None:
        title += f" (\u03b1={alpha:g})"
    title += f", seed {seed}"

    delta = b1_cv_fpr - b2_cv_fpr
    eligible, total = coverage

    table = Table(title=title, border_style="green")
    table.add_column("Metric", style="bold")
    table.add_column("Value")
    table.add_row("B1 CV(FPR)", f"{b1_cv_fpr:.4f}  (coverage: {eligible}/{total})")
    table.add_row("B2 CV(FPR)", f"{b2_cv_fpr:.4f}  (coverage: {eligible}/{total})")
    table.add_row("\u0394 CV(FPR)", f"{delta:.4f}")
    if contingency is not None:
        table.add_row("Contingency", contingency.upper())
    table.add_row("Duration", f"{total_elapsed:.1f}s")
    table.add_row("Output", f"{output_dir}/")
    console.print(table)
