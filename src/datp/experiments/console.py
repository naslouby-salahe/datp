# SPDX-License-Identifier: Proprietary
"""Rich console utilities for diagnostic and sweep experiment output."""

from __future__ import annotations

import time
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Iterator

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from datp.core.enums import Baseline, Regime
from datp.experiments.enums import DiagnosticStep, SweepStep

if TYPE_CHECKING:
    from datp.experiments.sweep import SweepResult

console = Console()

# ---------------------------------------------------------------------------
# Diagnostic step labels and helpers
# ---------------------------------------------------------------------------

_DIAGNOSTIC_STEP_LABELS: dict[DiagnosticStep, str] = {
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
    label = (
        _DIAGNOSTIC_STEP_LABELS[step] if step in _DIAGNOSTIC_STEP_LABELS else step.value
    )
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


# ---------------------------------------------------------------------------
# Sweep step labels and helpers
# ---------------------------------------------------------------------------

_SWEEP_STEP_LABELS: dict[SweepStep, str] = {
    SweepStep.BUILD_MATRIX: "Build experiment matrix",
    SweepStep.VALIDATE_MATRIX: "Validate sweep matrix",
    SweepStep.CHECK_CHECKPOINT: "Check FL checkpoint",
    SweepStep.TRAIN_FL: "Train FL model",
    SweepStep.LOAD_CAL_SCORES: "Load calibration scores",
    SweepStep.COMPUTE_ELIGIBILITY: "Compute client eligibility",
    SweepStep.COMPUTE_TAU_GLOBAL: "Compute tau_global",
    SweepStep.INIT_SCORE_PROVIDER: "Initialize score provider",
    SweepStep.DERIVE_THRESHOLD: "Derive threshold",
    SweepStep.EVALUATE: "Evaluate baseline",
    SweepStep.WRITE_METRICS: "Write metrics",
    SweepStep.RUN_B0: "Run B0 (centralized reference)",
    SweepStep.SWEEP_COMPLETE: "Sweep complete",
}

_STATUS_SYMBOLS: dict[str, str] = {
    "done": "[green]\u2713[/green]",
    "skipped": "[dim]\u2192[/dim]",
    "failed": "[red]\u2717[/red]",
}


def print_sweep_banner(
    regime: Regime | None,
    cell_count: int,
    base_dir: str,
) -> None:
    regime_display = "ALL" if regime is None else regime.upper()
    lines = [
        f"Regime: [cyan]{regime_display}[/cyan]  Cells: [cyan]{cell_count}[/cyan]",
        f"Output: [dim]{base_dir}[/dim]",
    ]
    console.print(
        Panel("\n".join(lines), title="[bold]DATP Sweep[/bold]", border_style="cyan")
    )


def print_dry_run_summary(regime_counts: dict[Regime, int], total_cells: int) -> None:
    table = Table(title="Sweep Matrix", border_style="cyan")
    table.add_column("Regime", style="bold")
    table.add_column("Cells", justify="right")

    for regime in sorted(regime_counts):
        table.add_row(f"Regime {regime.upper()}", str(regime_counts[regime]))
    table.add_row("Overall", str(total_cells), style="bold")
    console.print(table)
    console.print("[dim]Dry run only. No training launched.[/dim]")


def print_step(step: SweepStep, detail: str) -> None:
    label = _SWEEP_STEP_LABELS[step] if step in _SWEEP_STEP_LABELS else step.value
    detail_str = f"  [dim]{detail}[/dim]" if detail else ""
    console.print(f"  [dim][{step.value}][/dim] [bold]{label}[/bold]{detail_str}")


def print_group_header(
    regime: Regime,
    seed: int,
    alpha: float | None,
    group_size: int,
    current: int,
    total: int,
) -> None:
    alpha_str = f" \u03b1={alpha:g}" if alpha is not None else ""
    progress = f"[{current}/{total}]"
    console.print(
        f"\n[bold yellow]{'─' * 56}[/bold yellow]\n"
        f"[bold yellow]  Group {progress}[/bold yellow]"
        f"  regime={regime.upper()} seed={seed}{alpha_str}"
        f"  [dim]({group_size} cells)[/dim]",
    )


def print_baseline_result(
    baseline: Baseline,
    status: str,
    elapsed_s: float,
) -> None:
    symbol = _STATUS_SYMBOLS[status] if status in _STATUS_SYMBOLS else status
    elapsed_str = f"[dim]({elapsed_s:.1f}s)[/dim]" if elapsed_s > 0 else ""
    console.print(f"    {symbol} [bold]{baseline.upper()}[/bold] {elapsed_str}")


def print_checkpoint_status(found: bool, ckpt_path: Path) -> None:
    if found:
        console.print(
            f"    [green]\u2713 checkpoint found[/green]  [dim]{ckpt_path}[/dim]"
        )
    else:
        console.print(
            f"    [yellow]\u25cb no checkpoint — will train[/yellow]  [dim]{ckpt_path}[/dim]"
        )


def print_sweep_summary(result: "SweepResult", elapsed_s: float) -> None:
    table = Table(title="Sweep Summary", border_style="green")
    table.add_column("Metric", style="bold")
    table.add_column("Value")
    table.add_row("Total", str(result.total))
    table.add_row("Completed", f"[green]{result.completed}[/green]")
    table.add_row("Skipped", f"[dim]{result.skipped}[/dim]")
    failed_style = "red" if result.failed > 0 else ""
    table.add_row(
        "Failed",
        f"[{failed_style}]{result.failed}[/{failed_style}]"
        if failed_style
        else str(result.failed),
    )
    table.add_row("Duration", f"{elapsed_s:.1f}s")
    console.print(table)
