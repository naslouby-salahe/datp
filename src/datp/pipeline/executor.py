"""B1/B2/B3/B4 all derive thresholds from the same shared score artifacts produced by one FL training run per (regime, seed, alpha)."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from datp.artifacts.constants import MANIFEST_FILE, METRICS_FILE, MODEL_CHECKPOINT, SCORING_MANIFEST_FILE
from datp.artifacts.markers import RunLifecycle, write_metrics_atomic
from datp.artifacts.paths import ExperimentLocator
from datp.core.provenance import hash_file, hash_jsonable
from datp.baselines.common.eligibility import (
    compute_client_thresholds,
    compute_tau_global,
    identify_eligible,
)
from datp.baselines.common.metrics_serialization import SweepMetrics, build_metrics_dict
from datp.baselines.common.scoring import load_main_cal_errors
from datp.baselines.common.thresholds import derive_threshold
from datp.core.enums import Baseline
from datp.core.errors import fmt
from datp.core.logging import get_logger
from datp.core.tracking import log_metrics
from datp.evaluation.metrics import evaluate_baseline
from datp.evaluation.score_loading import ScoreProvider
from datp.pipeline.enums import SweepStep
from datp.pipeline.models import PipelineRequest, SharedPipelineContext
from datp.pipeline.training import ensure_fl_checkpoint

logger = get_logger(__name__)


class SharedTrainingExecutor:
    def __init__(
        self,
        *,
        step_fn: Callable[[SweepStep, str], None] | None,
        checkpoint_status_fn: Callable[[bool, Path], None] | None,
    ) -> None:
        self._step_fn = step_fn
        self._checkpoint_status_fn = checkpoint_status_fn

    def _step(self, step: SweepStep, detail: str = "") -> None:
        if self._step_fn is not None:
            self._step_fn(step, detail)

    def build_context(self, request: PipelineRequest) -> SharedPipelineContext:
        """Train once then load all shared per-group artifacts; caller must set seeds before calling."""
        key = request.key
        cfg = request.cfg

        ensure_fl_checkpoint(
            request,
            step_fn=self._step_fn,
            checkpoint_status_fn=self._checkpoint_status_fn,
            lock_timeout=cfg.runtime.lock_timeout_seconds,
        )

        self._step(SweepStep.LOAD_CAL_SCORES)
        client_errors = load_main_cal_errors(
            key.regime, key.seed, key.alpha, request.base_dir,
        )

        self._step(SweepStep.COMPUTE_ELIGIBILITY)
        eligible, pending = identify_eligible(client_errors, n_min=cfg.threshold.n_min)

        self._step(SweepStep.COMPUTE_TAU_GLOBAL)
        client_taus = compute_client_thresholds(client_errors, eligible, q=cfg.threshold.q)
        tau_global = compute_tau_global(client_taus)

        self._step(SweepStep.INIT_SCORE_PROVIDER)
        score_provider = ScoreProvider(
            ExperimentLocator.for_main(request.base_dir, key.regime).score(key.seed, key.alpha),
        )

        return SharedPipelineContext(
            key=key,
            client_errors=client_errors,
            eligible=eligible,
            pending=pending,
            client_taus=client_taus,
            tau_global=tau_global,
            score_provider=score_provider,
        )


class ThresholdEvaluationExecutor:
    def __init__(self, *, step_fn: Callable[[SweepStep, str], None] | None) -> None:
        self._step_fn = step_fn

    def _step(self, step: SweepStep, detail: str = "") -> None:
        if self._step_fn is not None:
            self._step_fn(step, detail)

    def run(
        self,
        request: PipelineRequest,
        ctx: SharedPipelineContext,
    ) -> SweepMetrics:
        baseline = request.baseline
        cfg = request.cfg
        res_dir = ExperimentLocator.for_main(request.base_dir, ctx.key.regime).result(baseline, ctx.key.seed, ctx.key.alpha)

        metrics: SweepMetrics | None = None
        with RunLifecycle(res_dir, baseline=baseline, seed=ctx.key.seed):
            self._step(SweepStep.DERIVE_THRESHOLD, baseline)
            threshold_result = derive_threshold(
                baseline,
                ctx.client_errors,
                cfg.threshold.n_min,
                cfg.threshold.q,
                ctx.tau_global,
                ctx.key.regime,
                threshold_cfg=cfg.threshold,
            )
            logger.info(
                "threshold derivation complete",
                baseline=baseline,
                tau_global=threshold_result.tau_global,
                eligible=threshold_result.eligible_count,
                pending=threshold_result.pending_count,
            )

            self._step(SweepStep.EVALUATE, baseline)
            eval_result = evaluate_baseline(
                threshold_result.client_thresholds,
                ExperimentLocator.for_main(request.base_dir, ctx.key.regime).score(ctx.key.seed, ctx.key.alpha),
                ctx.key.regime,
                ctx.key.seed,
                ctx.key.alpha,
                score_provider=ctx.score_provider,
            )

            self._step(SweepStep.WRITE_METRICS, baseline)
            loc = ExperimentLocator.for_main(request.base_dir, ctx.key.regime)
            ckpt_file = loc.checkpoint(ctx.key.seed, ctx.key.alpha) / MODEL_CHECKPOINT
            score_manifest = loc.score(ctx.key.seed, ctx.key.alpha) / SCORING_MANIFEST_FILE
            prepared_manifest = request.prepared_dir / MANIFEST_FILE
            metrics = build_metrics_dict(
                eval_result,
                threshold_result,
                config_identity=hash_jsonable(request.cfg.model_dump()),
                split_manifest_identity=hash_file(prepared_manifest) if prepared_manifest.exists() else "MISSING_MANIFEST_HASH",
                model_checkpoint_identity=hash_file(ckpt_file),
                score_artifact_identity=hash_file(score_manifest),
            )
            write_metrics_atomic(res_dir, metrics)
            logger.info("results written", path=str(res_dir / METRICS_FILE))

            log_metrics({
                f"{baseline}_eligible": float(threshold_result.eligible_count),
                f"{baseline}_pending": float(threshold_result.pending_count),
                f"{baseline}_tau_global": threshold_result.tau_global,
            }, step=None, prefix=None)

        if metrics is None:  # pragma: no cover
            raise RuntimeError(
                fmt("pipeline.executor", "metrics not set after RunLifecycle block",
                    "SweepMetrics instance", "None")
            )
        return metrics


class IsolatedBaselineExecutor:
    def __init__(self, *, step_fn: Callable[[SweepStep, str], None] | None) -> None:
        self._step_fn = step_fn

    def _step(self, step: SweepStep, detail: str = "") -> None:
        if self._step_fn is not None:
            self._step_fn(step, detail)

    def run(self, request: PipelineRequest) -> None:
        from datp.baselines.main.b0 import run_b0

        cfg = request.cfg
        key = request.key
        baseline = request.baseline

        model_kwargs = {
            "input_dim": cfg.model.input_dim,
            "hidden_dims": cfg.model.encoder_dims,
            "n_min": cfg.threshold.n_min,
            "q": cfg.threshold.q,
            "epochs": cfg.model.epochs,
            "patience": cfg.model.patience,
            "lr": cfg.model.lr,
            "batch_size": cfg.machine.batch_size_train,
            "activation": cfg.model.activation,
            "use_bn": cfg.model.use_bn,
            "training_progress_interval": cfg.logging.training_progress_interval,
        }

        out_dir = ExperimentLocator.for_main(request.base_dir, key.regime).result(baseline, key.seed, key.alpha)

        if baseline == Baseline.B0:
            self._step(SweepStep.RUN_B0, key.label())
            run_b0(
                prepared_dir=request.prepared_dir,
                output_dir=out_dir,
                seed=key.seed,
                val_fraction=cfg.dataset.b0_val_fraction,
                regime=key.regime,
                **model_kwargs,
            )
        else:
            raise ValueError(
                fmt("pipeline.executor", "Not an isolated baseline", "b0", baseline)
            )
