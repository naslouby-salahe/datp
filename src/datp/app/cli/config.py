from pathlib import Path

import typer
from rich.console import Console

from datp.artifacts.directories import OUTPUTS_DIR
from datp.artifacts.paths import ExperimentLocator
from datp.config.compose import ComposeError, compose_config, write_resolved_config
from datp.core.enums import (
    Baseline,
    Regime,
)

app = typer.Typer(help="Configuration commands.")

_stdout = Console()
_stderr = Console(stderr=True)


def _build_output_path(cfg) -> Path:
    return ExperimentLocator.for_main(Path(OUTPUTS_DIR), cfg.regime).result(
        cfg.baseline, cfg.seed, cfg.alpha
    )


def preview_config(
    *,
    regime: Regime,
    baseline: Baseline,
    seed: int,
    alpha: float | None = None,
    output_dir: Path | None = None,
) -> Path:
    cfg = compose_config(
        regime=regime,
        baseline=baseline,
        seed=seed,
        alpha=alpha,
    )

    if output_dir is None:
        output_dir = _build_output_path(cfg)

    return write_resolved_config(cfg, output_dir)


@app.command("preview")
def preview(
    regime: Regime = typer.Option(..., help="Experiment regime (a, b, c)"),
    baseline: Baseline = typer.Option(..., help="Baseline (b0–b4)"),
    seed: int = typer.Option(..., help="Random seed"),
    alpha: float | None = typer.Option(None, help="Dirichlet alpha (regime c)"),
    output_dir: Path | None = typer.Option(None, help="Override output directory"),
) -> None:
    """Write resolved_config.yaml without launching training."""
    try:
        dest = preview_config(
            regime=regime,
            baseline=baseline,
            seed=seed,
            alpha=alpha,
            output_dir=output_dir,
        )
    except ComposeError as exc:
        _stderr.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    _stdout.print(dest.read_text(), end="", highlight=False)
    _stderr.print(f"[dim]# Written to: {dest}[/dim]")
