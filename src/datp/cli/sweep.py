from pathlib import Path

import typer
from rich.console import Console

from datp.core.enums import Regime
from datp.data.paths import DEFAULT_BASE_DIR
from datp.sweep.run_sweep import run_sweep

_stderr = Console(stderr=True)


def sweep(
    dry_run: bool = typer.Option(False, "--dry-run/--no-dry-run", help="Enumerate and validate without launching"),
    regime: Regime | None = typer.Option(None, help="Run only cells for this regime (a, b, c)"),
    base_dir: Path = typer.Option(..., help="Root output directory"),
    data_root: Path = typer.Option(DEFAULT_BASE_DIR, help="Project data root (where data/raw/ lives)"),
) -> None:
    """Enumerate, validate, and run experiment cells."""
    try:
        run_sweep(dry_run=dry_run, base_dir=base_dir, regime=regime, data_root=data_root)
    except SystemExit as exc:
        _stderr.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc
