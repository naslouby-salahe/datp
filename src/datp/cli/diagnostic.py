from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from datp.config.compose import BASE_CONFIG
from datp.core.enums import Regime
from datp.core.logging import get_logger
from datp.data.catalog import DatasetID
from datp.data.datasets.nbaiot import prepare_nbaiot
from datp.data.paths import (
    DEFAULT_BASE_DIR,
    assert_no_root_conflict,
    prepared_root_for_regime,
    raw_root,
)
from datp.data.regimes.catalog import dataset_for_regime
from datp.data.regimes.regime_b import prepare_regime_b
from datp.data.regimes.regime_c import partition_regime_c
from datp.pipeline import print_banner
from datp.pipeline.diagnostic import DiagnosticRequest, make_regime_a_extras, run_diagnostic

logger = get_logger(__name__)

_DATA_ROOT_HELP = "Project data root (used to resolve raw and prepared dirs when not explicitly specified)"

_Seed = Annotated[int | None, typer.Option(help="Random seed")]
_DataRoot = Annotated[Path, typer.Option(help=_DATA_ROOT_HELP)]


def _dispatch(request: DiagnosticRequest) -> None:
    try:
        run_diagnostic(request)
    except Exception as exc:
        logger.exception(
            "diagnostic pipeline failed",
            regime=request.regime, seed=request.seed, alpha=request.alpha,
        )
        raise typer.Exit(code=1) from exc







def diagnostic(
    raw_dir: Annotated[Path | None, typer.Option(help="Path to raw N-BaIoT data")] = None,
    output_dir: Path = typer.Option(..., help="Root output directory"),
    data_root: _DataRoot = DEFAULT_BASE_DIR,
    seed: _Seed = None,
    skip_prepare: bool = typer.Option(False, "--skip-prepare/--no-skip-prepare", help="Skip data prep"),
) -> None:
    """Run Phase 3 diagnostic (N-BaIoT, Regime A, single seed)."""
    regime = Regime.A
    assert_no_root_conflict(data_root, dataset_for_regime(regime))
    actual_seed = seed if seed is not None else BASE_CONFIG.experiment.seeds[0]
    actual_output_dir = output_dir
    actual_raw_dir = raw_dir if raw_dir is not None else raw_root(DatasetID.NBAIOT, base_dir=data_root)

    run_dir = actual_output_dir / f"regime_a_seed{actual_seed}"
    prepared_dir = prepared_root_for_regime(Regime.A, base_dir=data_root)

    print_banner(regime, actual_seed, str(actual_output_dir))

    def _prepare() -> None:
        logger.info("preparing N-BaIoT data", raw_dir=str(actual_raw_dir), prepared_dir=str(prepared_dir))
        prepare_nbaiot(
            actual_raw_dir,
            prepared_dir,
            n_min=BASE_CONFIG.threshold.n_min,
            seed=actual_seed,
            balanced_test=BASE_CONFIG.dataset.nbaiot_balanced_test,
        )

    _dispatch(DiagnosticRequest(
        regime=regime, seed=actual_seed,
        output_dir=actual_output_dir, run_dir=run_dir, alpha=None,
        prepared_dir=prepared_dir, prepare_fn=_prepare,
        skip_prepare=skip_prepare,
        diagnostic_tag="regime_a_b1_vs_b2",
        extras_fn=make_regime_a_extras(phase3_dir=actual_output_dir / "phase3_diagnostic"),
    ))
    logger.info("diagnostic complete", output_dir=str(run_dir))


def diagnostic_b(
    raw_dir: Annotated[Path | None, typer.Option(help="Path to raw CICIoT2023 data")] = None,
    output_dir: Path = typer.Option(..., help="Root output directory"),
    data_root: _DataRoot = DEFAULT_BASE_DIR,
    seed: _Seed = None,
    skip_prepare: bool = typer.Option(False, "--skip-prepare/--no-skip-prepare", help="Skip data prep"),
) -> None:
    """Run Regime B diagnostic (CICIoT2023, single seed)."""
    regime = Regime.B
    assert_no_root_conflict(data_root, dataset_for_regime(regime))
    actual_seed = seed if seed is not None else BASE_CONFIG.experiment.seeds[0]
    actual_output_dir = output_dir
    actual_raw_dir = raw_dir if raw_dir is not None else raw_root(DatasetID.CICIOT2023, base_dir=data_root)

    run_dir = actual_output_dir / f"regime_b_seed{actual_seed}"
    prepared_dir = prepared_root_for_regime(Regime.B, base_dir=data_root)

    print_banner(regime, actual_seed, str(actual_output_dir))

    def _prepare() -> None:
        logger.info("preparing CICIoT2023 data", raw_dir=str(actual_raw_dir), prepared_dir=str(prepared_dir))
        prepare_regime_b(
            raw_dir=actual_raw_dir,
            output_dir=prepared_dir,
            regime=Regime.B,
            n_min=BASE_CONFIG.threshold.n_min,
            cap=BASE_CONFIG.dataset.cap,
            seed=actual_seed,
            attack_reserve_fraction=BASE_CONFIG.dataset.attack_reserve_fraction,
        )

    _dispatch(DiagnosticRequest(
        regime=regime, seed=actual_seed,
        output_dir=actual_output_dir, run_dir=run_dir, alpha=None,
        prepared_dir=prepared_dir, prepare_fn=_prepare,
        skip_prepare=skip_prepare,
        diagnostic_tag="regime_b_b1_vs_b2",
    ))
    logger.info("diagnostic-b complete", output_dir=str(run_dir))


def diagnostic_c(
    raw_dir: Annotated[Path | None, typer.Option(help="Path to raw N-BaIoT data")] = None,
    output_dir: Path = typer.Option(..., help="Root output directory"),
    data_root: _DataRoot = DEFAULT_BASE_DIR,
    seed: _Seed = None,
    alpha: Annotated[float | None, typer.Option(help="Dirichlet concentration parameter")] = None,
    skip_prepare: bool = typer.Option(False, "--skip-prepare/--no-skip-prepare", help="Skip data prep"),
) -> None:
    """Run Regime C diagnostic (N-BaIoT Dirichlet repartition, single seed+alpha)."""
    regime = Regime.C
    assert_no_root_conflict(data_root, dataset_for_regime(regime))
    actual_seed = seed if seed is not None else BASE_CONFIG.experiment.seeds[0]
    actual_output_dir = output_dir
    actual_raw_dir = raw_dir if raw_dir is not None else raw_root(DatasetID.NBAIOT, base_dir=data_root)
    actual_alpha = alpha if alpha is not None else BASE_CONFIG.experiment.regime_c_alphas[0]

    run_dir = actual_output_dir / f"regime_c_alpha{actual_alpha:g}_seed{actual_seed}"

    n_clients = BASE_CONFIG.experiment.regime_c_n_clients
    prepared_dir = prepared_root_for_regime(Regime.C, base_dir=data_root, alpha=actual_alpha, seed=actual_seed)

    print_banner(regime, actual_seed, str(actual_output_dir), alpha=actual_alpha)

    def _prepare() -> None:
        logger.info(
            "Preparing Regime C data",
            raw_dir=str(actual_raw_dir), prepared_dir=str(prepared_dir),
            alpha=actual_alpha, seed=actual_seed,
        )
        partition_regime_c(
            raw_nbaiot_dir=actual_raw_dir,
            output_dir=prepared_root_for_regime(Regime.A, base_dir=data_root),
            alpha=actual_alpha,
            seed=actual_seed,
            n_clients=n_clients,
            n_min=BASE_CONFIG.threshold.n_min,
            train_frac=BASE_CONFIG.dataset.regime_c_train_fraction,
            cal_frac=BASE_CONFIG.dataset.regime_c_cal_fraction,
        )

    _dispatch(DiagnosticRequest(
        regime=regime, seed=actual_seed,
        output_dir=actual_output_dir, run_dir=run_dir, alpha=actual_alpha,
        prepared_dir=prepared_dir, prepare_fn=_prepare,
        skip_prepare=skip_prepare,
        diagnostic_tag=f"regime_c_alpha{actual_alpha:g}_b1_vs_b2",
    ))
    logger.info("diagnostic-c complete", output_dir=str(run_dir))
