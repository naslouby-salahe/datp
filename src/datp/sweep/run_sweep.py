"""Sweep orchestration: enumerate, validate, and run experiment cells; completed runs are skipped."""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from datp.artifacts.paths import ExperimentLocator
from datp.artifacts.results import results_exist
from datp.config.compose import BASE_CONFIG, write_resolved_config
from datp.config.models import DatpConfig
from datp.core.enums import (
    ISOLATED_BASELINES,
    REGIME_BASELINES,
    Baseline,
    Regime,
)
from datp.core.identity import ExperimentKey, RunIdentity
from datp.core.logging import get_logger
from datp.core.seeds import set_seeds
from datp.core.tracking import init_tracking, log_metrics, tracking_run
from datp.data.paths import prepared_root_for_regime
from datp.pipeline import (
    IsolatedBaselineExecutor,
    PipelineRequest,
    SharedTrainingExecutor,
    ThresholdEvaluationExecutor,
)
from datp.pipeline.enums import SweepStep
from datp.sweep import _console as console
from datp.sweep.data_preparation import (
    PreparedDataRequest,
    ensure_prepared_data,
)
from datp.sweep.validator import validate_sweep

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class _RegimeSpec:
    regime: Regime
    has_alpha: bool


_REGIME_SPEC: list[_RegimeSpec] = [
    _RegimeSpec(regime=Regime.A, has_alpha=False),
    _RegimeSpec(regime=Regime.B, has_alpha=False),
    _RegimeSpec(regime=Regime.C, has_alpha=True),
    _RegimeSpec(regime=Regime.D, has_alpha=False),
]


def build_experiment_matrix() -> list[RunIdentity]:
    seeds = list(BASE_CONFIG.experiment.seeds)
    regime_c_alphas = BASE_CONFIG.experiment.regime_c_alphas
    cells: list[RunIdentity] = []
    for spec in _REGIME_SPEC:
        regime = spec.regime
        alphas: list[float | None] = list(regime_c_alphas) if spec.has_alpha else [None]
        for baseline in sorted(REGIME_BASELINES[regime]):
            for alpha in alphas:
                for seed in seeds:
                    cells.append(
                        RunIdentity(
                            regime=regime, baseline=baseline, seed=seed, alpha=alpha
                        )
                    )
    return cells


@dataclass(slots=True)
class SweepResult:
    total: int = 0
    completed: int = 0
    skipped: int = 0
    failed: int = 0


def run_sweep(
    *,
    dry_run: bool,
    base_dir: Path,
    regime: Regime | None,
    data_root: Path | None = None,
) -> SweepResult:
    """Orchestrate a full experiment sweep; blocks and exits on pre-validation failure."""
    t_start = time.monotonic()

    init_tracking(
        experiment_name=BASE_CONFIG.tracking.experiment_name,
        tracking_uri=BASE_CONFIG.tracking.tracking_uri,
    )

    console.print_step(SweepStep.BUILD_MATRIX, detail="")
    cells = build_experiment_matrix()

    if regime is not None:
        cells = [c for c in cells if c.regime == regime]

    result = SweepResult(total=len(cells))

    regime_label = "all" if regime is None else regime
    console.print_sweep_banner(regime_label, len(cells), str(base_dir))

    console.print_step(SweepStep.VALIDATE_MATRIX, detail="")
    errors, pre_composed_configs = validate_sweep(cells)
    if errors:
        for err in errors:
            logger.error("pre-validation failure", error=str(err))
        raise SystemExit(f"Sweep blocked: {len(errors)} config validation error(s)")

    if dry_run:
        _print_dry_run_summary(cells)
        return result

    groups: dict[tuple, list[RunIdentity]] = defaultdict(list)
    for cell in cells:
        groups[cell.shared_training_key()].append(cell)

    _data_root = data_root if data_root is not None else base_dir
    total_groups = len(groups)
    for group_idx, (key, group_cells) in enumerate(
        sorted(groups.items(), key=lambda kv: _sort_key(kv[0])),
        start=1,
    ):
        grp_regime, grp_seed, grp_alpha = key
        with tracking_run(
            run_name=f"{grp_regime}_seed{grp_seed}"
            + (f"_alpha{grp_alpha}" if grp_alpha is not None else ""),
            params={"regime": grp_regime, "seed": grp_seed, "alpha": grp_alpha},
            tags=None,
            nested=None,
        ):
            _process_group(
                key,
                group_cells,
                pre_composed_configs,
                base_dir,
                result,
                group_idx,
                total_groups,
                data_root=_data_root,
            )

    total_elapsed = time.monotonic() - t_start
    log_metrics(
        {
            "sweep_total": float(result.total),
            "sweep_completed": float(result.completed),
            "sweep_skipped": float(result.skipped),
            "sweep_failed": float(result.failed),
            "sweep_elapsed_s": total_elapsed,
        },
        step=None,
        prefix=None,
    )
    console.print_sweep_summary(result, total_elapsed)
    return result


def _cell_is_done(cell: RunIdentity, base_dir: Path) -> bool:
    return results_exist(
        cell.baseline, cell.regime, cell.seed, cell.alpha, base_dir=base_dir
    )


def _account_skip(cell: RunIdentity, result: SweepResult) -> None:
    logger.info("skipping completed cell", cell=cell.label())
    result.skipped += 1
    console.print_baseline_result(cell.baseline, "skipped", 0.0)


def _process_group(
    key: tuple,
    group_cells: list[RunIdentity],
    pre_composed_configs: dict[tuple, DatpConfig],
    base_dir: Path,
    result: SweepResult,
    group_idx: int,
    total_groups: int,
    data_root: Path | None = None,
) -> None:
    _data_root = data_root if data_root is not None else base_dir
    grp_regime, grp_seed, grp_alpha = key
    console.print_group_header(
        grp_regime, grp_seed, grp_alpha, len(group_cells), group_idx, total_groups
    )

    pending_cells = [cell for cell in group_cells if not _cell_is_done(cell, base_dir)]
    if not pending_cells:
        for cell in group_cells:
            _account_skip(cell, result)
        return

    if not _prepare_group_data(
        grp_regime,
        grp_seed,
        grp_alpha,
        pending_cells,
        group_cells,
        base_dir,
        result,
        data_root=_data_root,
    ):
        return

    isolated_executor = IsolatedBaselineExecutor(step_fn=console.print_step)
    pending_fl: list[RunIdentity] = []

    for cell in group_cells:
        if _cell_is_done(cell, base_dir):
            _account_skip(cell, result)
            continue
        if cell.baseline in ISOLATED_BASELINES:
            _run_isolated_with_accounting(
                cell,
                pre_composed_configs,
                base_dir,
                result,
                isolated_executor,
                data_root=_data_root,
            )
        else:
            pending_fl.append(cell)

    if pending_fl:
        completed, failed = _run_shared_fl_group(
            pending_fl, pre_composed_configs, base_dir, data_root=_data_root
        )
        result.completed += completed
        result.failed += failed


def _prepare_group_data(
    regime: Regime,
    seed: int,
    alpha: float | None,
    pending_cells: list[RunIdentity],
    group_cells: list[RunIdentity],
    base_dir: Path,
    result: SweepResult,
    data_root: Path | None = None,
) -> bool:
    _data_root = data_root if data_root is not None else base_dir
    try:
        ensure_prepared_data(
            PreparedDataRequest(
                regime=regime,
                seed=seed,
                alpha=alpha,
                cfg=BASE_CONFIG,
                base_dir=_data_root,
            )
        )
        return True
    except Exception:
        logger.exception(
            "prepared data setup failed",
            regime=regime,
            seed=seed,
            alpha=alpha,
            n_failed=len(pending_cells),
        )
        for cell in pending_cells:
            result.failed += 1
            console.print_baseline_result(cell.baseline, "failed", 0.0)
        for cell in group_cells:
            if cell not in pending_cells:
                _account_skip(cell, result)
        return False


def _run_isolated_with_accounting(
    cell: RunIdentity,
    pre_composed_configs: dict[tuple, DatpConfig],
    base_dir: Path,
    result: SweepResult,
    executor: IsolatedBaselineExecutor,
    data_root: Path | None = None,
) -> None:
    _data_root = data_root if data_root is not None else base_dir
    t0 = time.monotonic()
    cfg = pre_composed_configs[(cell.regime, cell.baseline, cell.seed, cell.alpha)]
    prepared_dir = _prepared_dir_for_regime(
        cell.regime, _data_root, seed=cell.seed, alpha=cell.alpha
    )
    request = PipelineRequest(
        key=ExperimentKey(regime=cell.regime, seed=cell.seed, alpha=cell.alpha),
        baseline=cell.baseline,
        cfg=cfg,
        base_dir=base_dir,
        prepared_dir=prepared_dir,
    )
    _write_cell_resolved_config(cell, cfg, base_dir)
    try:
        executor.run(request)
        result.completed += 1
        console.print_baseline_result(cell.baseline, "done", time.monotonic() - t0)
    except Exception:
        logger.exception("cell failed", cell=cell.label())
        result.failed += 1
        console.print_baseline_result(cell.baseline, "failed", time.monotonic() - t0)


def _sort_key(k: tuple) -> tuple[Regime, int, float]:
    regime, seed, alpha = k
    return (regime, seed, alpha if alpha is not None else -1.0)


def _run_shared_fl_group(
    group_cells: list[RunIdentity],
    pre_composed_configs: dict[tuple, DatpConfig],
    base_dir: Path,
    data_root: Path | None = None,
) -> tuple[int, int]:
    """Run shared FL training once for this group; all cells share the same checkpoint (train-once rule)."""
    _data_root = data_root if data_root is not None else base_dir
    first_cell = group_cells[0]
    regime = first_cell.regime
    seed = first_cell.seed
    alpha = first_cell.alpha
    cfg = pre_composed_configs[
        (first_cell.regime, first_cell.baseline, first_cell.seed, first_cell.alpha)
    ]
    prepared_dir = _prepared_dir_for_regime(regime, _data_root, seed=seed, alpha=alpha)

    for cell in group_cells:
        cell_cfg = pre_composed_configs[
            (cell.regime, cell.baseline, cell.seed, cell.alpha)
        ]
        _write_cell_resolved_config(cell, cell_cfg, base_dir)

    key = ExperimentKey(regime=regime, seed=seed, alpha=alpha)
    # Use B1 as the representative baseline for context building;
    # the baseline field is irrelevant for training and score loading.
    context_request = PipelineRequest(
        key=key,
        baseline=Baseline.B1,
        cfg=cfg,
        base_dir=base_dir,
        prepared_dir=prepared_dir,
    )

    set_seeds(seed)
    trainer = SharedTrainingExecutor(
        step_fn=console.print_step,
        checkpoint_status_fn=console.print_checkpoint_status,
    )
    evaluator = ThresholdEvaluationExecutor(step_fn=console.print_step)

    try:
        ctx = trainer.build_context(context_request)
    except Exception:
        logger.exception(
            "shared group setup failed",
            regime=regime,
            seed=seed,
            alpha=alpha,
            n_failed=len(group_cells),
        )
        for cell in group_cells:
            console.print_baseline_result(cell.baseline, "failed", 0.0)
        return 0, len(group_cells)

    completed = 0
    failed = 0
    for cell in group_cells:
        t0 = time.monotonic()
        cell_cfg = pre_composed_configs[
            (cell.regime, cell.baseline, cell.seed, cell.alpha)
        ]
        cell_request = PipelineRequest(
            key=key,
            baseline=cell.baseline,
            cfg=cell_cfg,
            base_dir=base_dir,
            prepared_dir=prepared_dir,
        )
        try:
            evaluator.run(cell_request, ctx)
            completed += 1
            console.print_baseline_result(cell.baseline, "done", time.monotonic() - t0)
        except Exception:
            logger.exception(
                "cell failed",
                baseline=cell.baseline,
                regime=regime,
                seed=seed,
                alpha=alpha,
            )
            failed += 1
            console.print_baseline_result(
                cell.baseline, "failed", time.monotonic() - t0
            )

    return completed, failed


def _prepared_dir_for_regime(
    regime: Regime,
    base_dir: Path,
    *,
    seed: int | None = None,
    alpha: float | None = None,
) -> Path:
    return prepared_root_for_regime(regime, base_dir=base_dir, seed=seed, alpha=alpha)


def _write_cell_resolved_config(
    cell: RunIdentity, cfg: DatpConfig, base_dir: Path
) -> Path:
    output_dir = ExperimentLocator.for_main(base_dir, cell.regime).result(
        cell.baseline, cell.seed, cell.alpha
    )
    return write_resolved_config(cfg, output_dir)


def _print_dry_run_summary(cells: list[RunIdentity]) -> None:
    regime_counts: dict[str, int] = {}
    for cell in cells:
        if cell.regime not in regime_counts:
            regime_counts[cell.regime] = 0
        regime_counts[cell.regime] += 1
    console.print_dry_run_summary(regime_counts, len(cells))
