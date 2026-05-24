from pathlib import Path
from typing import Callable

import typer
from rich.console import Console

from datp.config.compose import BASE_CONFIG
from datp.config.models import DatpConfig
from datp.reporting.build import BuildOutputs, build_all, build_figures, build_stats, build_tables, validate_results

app = typer.Typer(help="Build analysis, figures, and tables from completed results.")
console = Console()

_ROOT_OUTPUT_HELP = "Root output directory"


def _print_paths(paths: list[Path]) -> None:
    for path in paths:
        console.print(f"[green]wrote[/green] {path}")


def _run_report_step(fn: Callable[[Path, DatpConfig], BuildOutputs], base_dir: Path) -> None:
    try:
        result = fn(base_dir, BASE_CONFIG)
        _print_paths(result.paths)
    except (FileNotFoundError, ValueError) as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc


@app.command("stats")
def stats(
    base_dir: Path = typer.Option(..., help=_ROOT_OUTPUT_HELP),
) -> None:
    """Compute bootstrap CIs and secondary statistics."""
    _run_report_step(build_stats, base_dir)


@app.command("validate")
def validate(
    base_dir: Path = typer.Option(..., help=_ROOT_OUTPUT_HELP),
) -> None:
    """Validate result metrics against the canonical schema and recomputation path."""
    _run_report_step(validate_results, base_dir)


@app.command("figures")
def figures(
    base_dir: Path = typer.Option(..., help=_ROOT_OUTPUT_HELP),
) -> None:
    """Generate main-body figures."""
    _run_report_step(build_figures, base_dir)


@app.command("tables")
def tables(
    base_dir: Path = typer.Option(..., help=_ROOT_OUTPUT_HELP),
) -> None:
    """Generate main-body tables."""
    _run_report_step(build_tables, base_dir)


@app.command("all")
def all_outputs(
    base_dir: Path = typer.Option(..., help=_ROOT_OUTPUT_HELP),
) -> None:
    """Generate analysis, figures, and tables."""
    _run_report_step(build_all, base_dir)
