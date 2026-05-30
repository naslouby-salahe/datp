from pathlib import Path

import typer
from rich.console import Console

from datp.artifacts.layout import ArtifactLayout
from datp.artifacts.names import ArtifactDir
from datp.config.compose import ComposeError, compose_config, write_resolved_config
from datp.core.enums import (
    Baseline,
    Regime,
)
from datp.core.identity import BaselineRunId, TrainingCellId

app = typer.Typer(help="Configuration commands.")

_stdout = Console()
_stderr = Console(stderr=True)


def _build_output_path(cfg) -> Path:
    run = BaselineRunId(
        cell=TrainingCellId(regime=cfg.regime, seed=cfg.seed, alpha=cfg.alpha),
        baseline=cfg.baseline,
    )
    return (
        ArtifactLayout(base_dir=Path(ArtifactDir.OUTPUTS), regime=cfg.regime)
        .baseline_run(run)
        .result_dir
    )


def preview_config(
    *,
    regime: str,
    baseline: str,
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
