"""B0 — Centralized reference comparator; violates FL by pooling all data. Not part of the controlled B1–B4 ladder and never described as a guaranteed upper bound."""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import polars as pl
import torch

from datp.artifacts.constants import MANIFEST_FILE, MODEL_B0_CHECKPOINT
from datp.artifacts.markers import write_metrics_atomic
from datp.baselines.common.data_loading import (
    compute_reconstruction_errors,
    df_to_tensor,
    discover_client_dirs,
    load_client_artifact,
    release_freed_heap,
)
from datp.baselines.common.thresholds import percentile_threshold
from datp.baselines.common.training import train_ae
from datp.baselines.common.types import B0Result, ClientEvalResult
from datp.baselines.common.metrics_serialization import (
    METRIC_SCHEMA_VERSION,
    METRICS_SCHEMA_VERSION,
    THRESHOLD_SCHEMA_VERSION,
)
from datp.core.device import get_device
from datp.core.enums import (
    THRESHOLD_AGGREGATION_BY_BASELINE,
    B0NormalizationMode,
    Baseline,
    NormalizationScope,
    Regime,
)
from datp.core.errors import fmt
from datp.core.logging import get_logger
from datp.core.provenance import (
    git_commit,
    hash_file,
    hash_jsonable,
    source_hash,
    utc_timestamp,
)
from datp.core.seeds import set_seeds
from datp.core.tracking import log_artifact, log_metrics, tracking_run
from datp.data.scaling import apply_scaler, fit_scaler
from datp.data.splits import Split
from datp.data.regimes.catalog import dataset_for_regime
from datp.evaluation.metric_keys import MetricName
from datp.evaluation.metrics import (
    ClientMetrics,
    build_evaluation_result,
    compute_client_metrics,
)
from datp.evaluation.ranking import compute_binary_ranking_metrics
from datp.models.autoencoder import Autoencoder

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class B0RunRequest:
    prepared_dir: Path
    output_dir: Path
    seed: int
    input_dim: int
    hidden_dims: list[int]
    n_min: int
    q: float
    epochs: int
    patience: int
    lr: float
    batch_size: int
    val_fraction: float
    activation: str
    use_bn: bool
    training_progress_interval: int
    regime: Regime


def _validate_b0_regime(regime: Regime) -> None:
    if regime not in (Regime.A, Regime.B):
        raise ValueError(
            fmt(
                "baselines.b0",
                "B0 is Regime A and B only",
                "regime a or b",
                repr(regime),
            )
        )


def _normalization_scope(normalization_mode: B0NormalizationMode) -> NormalizationScope:
    if normalization_mode == B0NormalizationMode.POOLED_ZSCORE:
        return NormalizationScope.POOLED_ZSCORE
    return NormalizationScope.PER_CLIENT_ZSCORE


def _run_b0_impl(
    request: B0RunRequest,
    *,
    normalization_mode: B0NormalizationMode,
) -> B0Result:
    prepared_dir = request.prepared_dir
    output_dir = request.output_dir
    seed = request.seed
    input_dim = request.input_dim
    hidden_dims = request.hidden_dims
    n_min = request.n_min
    q = request.q
    epochs = request.epochs
    patience = request.patience
    lr = request.lr
    batch_size = request.batch_size
    val_fraction = request.val_fraction
    activation = request.activation
    use_bn = request.use_bn
    training_progress_interval = request.training_progress_interval
    regime = request.regime

    _validate_b0_regime(regime)
    norm_scope = _normalization_scope(normalization_mode)
    run_name = (
        f"{Baseline.B0.value}_{normalization_mode.value}_{regime.value}_seed{seed}"
    )
    with tracking_run(
        run_name=run_name,
        params={
            "baseline": Baseline.B0,
            "regime": regime,
            "seed": seed,
            "epochs": epochs,
            "patience": patience,
            "learning_rate": lr,
            "batch_size": batch_size,
            "q": q,
            "n_min": n_min,
            "normalization_mode": normalization_mode.value,
        },
        tags={"baseline": Baseline.B0, "pipeline": "isolated"},
        nested=None,
    ):
        set_seeds(seed)

        device = get_device()
        client_dirs = discover_client_dirs(prepared_dir)
        logger.info(
            "found clients",
            baseline=Baseline.B0,
            n_clients=len(client_dirs),
            path=str(prepared_dir),
        )

        train_frames: list[pl.DataFrame] = []
        cal_frames: list[pl.DataFrame] = []
        client_cal_counts: dict[str, int] = {}

        for cd in client_dirs:
            client_id = cd.name
            train_frames.append(load_client_artifact(cd, Split.TRAIN))
            cal_df = load_client_artifact(cd, Split.CAL)
            client_cal_counts[client_id] = len(cal_df)
            cal_frames.append(cal_df)

        pooled_train = pl.concat(train_frames, how="vertical")
        pooled_cal = pl.concat(cal_frames, how="vertical")

        if pooled_train.shape[1] != input_dim:
            raise ValueError(
                fmt(
                    "baselines.b0",
                    "input_dim mismatch",
                    f"{input_dim} columns",
                    f"{pooled_train.shape[1]} columns",
                )
            )

        global_scaler = None
        if normalization_mode == B0NormalizationMode.POOLED_ZSCORE:
            global_scaler = fit_scaler(pooled_train)
            pooled_train = apply_scaler(pooled_train, global_scaler)
            pooled_cal = apply_scaler(pooled_cal, global_scaler)

        n_total = len(pooled_train)
        n_val = max(1, int(n_total * val_fraction))
        indices = np.random.default_rng(seed).permutation(n_total)
        val_idx, train_idx = indices[:n_val], indices[n_val:]

        pooled_train_np = pooled_train.to_numpy()
        train_tensor = df_to_tensor(pooled_train_np[train_idx], device)
        val_tensor = df_to_tensor(pooled_train_np[val_idx], device)
        del pooled_train_np, pooled_train, train_frames
        release_freed_heap()

        model = Autoencoder(
            input_dim=input_dim,
            hidden_dims=hidden_dims,
            activation=activation,
            use_bn=use_bn,
        )
        model, epochs_run = train_ae(
            model,
            train_tensor,
            val_tensor,
            epochs=epochs,
            patience=patience,
            lr=lr,
            batch_size=batch_size,
            device=device,
            tracking_namespace=f"{Baseline.B0}.train",
            training_progress_interval=training_progress_interval,
        )

        cal_tensor = df_to_tensor(pooled_cal, device)
        cal_errors = compute_reconstruction_errors(model, cal_tensor)
        n_cal_errors = len(cal_errors)
        tau_b0 = percentile_threshold(cal_errors, q=q)
        del cal_tensor, cal_errors, pooled_cal, cal_frames
        release_freed_heap()
        logger.info(
            "b0 threshold computed",
            baseline=Baseline.B0,
            tau_b0=tau_b0,
            q=q,
            n_cal=n_cal_errors,
        )

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        ckpt_path = output_dir / MODEL_B0_CHECKPOINT
        torch.save(model.state_dict(), ckpt_path)
        b0_ckpt_hash = hash_file(ckpt_path)
        logger.info("b0 checkpoint saved", path=str(ckpt_path), hash=b0_ckpt_hash)

        per_client: dict[str, ClientEvalResult] = {}
        all_test_errors: list[np.ndarray] = []

        for client_dir in client_dirs:
            client_id = client_dir.name
            tb = load_client_artifact(client_dir, Split.TEST_BENIGN)
            ta = load_client_artifact(client_dir, Split.TEST_ATTACK)
            if global_scaler is not None:
                tb = apply_scaler(tb, global_scaler)
                ta = apply_scaler(ta, global_scaler)

            errors_benign = compute_reconstruction_errors(
                model, df_to_tensor(tb, device)
            )
            errors_attack = compute_reconstruction_errors(
                model, df_to_tensor(ta, device)
            )

            client_metrics_obj = compute_client_metrics(
                client_id, errors_benign, errors_attack, tau_b0
            )

            per_client[client_id] = ClientEvalResult(
                fpr=client_metrics_obj.fpr,
                tpr=client_metrics_obj.tpr,
                balanced_accuracy=client_metrics_obj.balanced_accuracy,
                macro_f1=client_metrics_obj.macro_f1,
                n_benign=client_metrics_obj.n_benign,
                n_attack=client_metrics_obj.n_attack,
                confusion_matrix=client_metrics_obj.confusion_matrix,
            )

            all_test_errors.extend([errors_benign, errors_attack])
            del tb, ta, errors_benign, errors_attack
            release_freed_heap()

        benign_arrays = all_test_errors[0::2]
        attack_arrays = all_test_errors[1::2]
        pooled_benign = (
            np.concatenate(benign_arrays)
            if benign_arrays
            else np.empty(0, dtype=np.float64)
        )
        pooled_attack = (
            np.concatenate(attack_arrays)
            if attack_arrays
            else np.empty(0, dtype=np.float64)
        )
        ranking = compute_binary_ranking_metrics(pooled_benign, pooled_attack)
        auroc = ranking.auroc
        pr_auc = ranking.pr_auc
        logger.info(
            "b0 pooled auroc",
            baseline=Baseline.B0,
            auroc=auroc,
            normalization_mode=normalization_mode.value,
        )

        cal_pending_clients = [
            cid for cid, cal_count in client_cal_counts.items() if cal_count < n_min
        ]
        pending_set = set(cal_pending_clients)
        per_client = {
            cid: metrics.model_copy(
                update={
                    "benign_count": metrics.n_benign,
                    "attack_count": metrics.n_attack,
                    "calibration_pending": cid in pending_set,
                    "evaluation_incomplete": metrics.n_attack == 0,
                    "threshold_value": tau_b0,
                    "threshold_source": THRESHOLD_AGGREGATION_BY_BASELINE[
                        Baseline.B0
                    ].value,
                }
            )
            for cid, metrics in per_client.items()
        }
        canonical_eval = build_evaluation_result(
            baseline=Baseline.B0,
            regime=regime,
            seed=seed,
            alpha=None,
            per_client=[
                ClientMetrics(
                    client_id=cid,
                    **metrics.model_dump(
                        exclude={
                            "benign_count",
                            "attack_count",
                            "calibration_pending",
                            "evaluation_incomplete",
                            "threshold_value",
                            "threshold_source",
                        }
                    ),
                )
                for cid, metrics in per_client.items()
            ],
            eligible_ids=[cid for cid in per_client if cid not in pending_set],
            pending_ids=cal_pending_clients,
            eval_incomplete_ids=[
                cid for cid, metrics in per_client.items() if metrics.n_attack == 0
            ],
        )

        result = B0Result(
            schema_version=METRICS_SCHEMA_VERSION,
            metric_schema_version=METRIC_SCHEMA_VERSION,
            threshold_schema_version=THRESHOLD_SCHEMA_VERSION,
            run_id=f"{regime.value}_{Baseline.B0.value}_seed{seed}",
            baseline=Baseline.B0,
            regime=regime,
            seed=seed,
            dataset=dataset_for_regime(regime).value,
            tau_b0=tau_b0,
            tau_global=tau_b0,
            threshold_scope=THRESHOLD_AGGREGATION_BY_BASELINE[Baseline.B0].value,
            threshold_strategy_name=Baseline.B0.value,
            q=q,
            n_min=n_min,
            eligible_ids=canonical_eval.eligible_ids,
            pending_ids=canonical_eval.pending_ids,
            eval_incomplete_ids=canonical_eval.eval_incomplete_ids,
            eligible_count=canonical_eval.eligible_count,
            pending_count=len(cal_pending_clients),
            eval_incomplete_count=len(canonical_eval.eval_incomplete_ids),
            client_count=canonical_eval.client_count,
            coverage_ratio=canonical_eval.coverage_ratio,
            cv_fpr=canonical_eval.cv_fpr,
            mean_fpr=canonical_eval.mean_fpr,
            std_fpr=canonical_eval.std_fpr,
            cv_tpr=canonical_eval.cv_tpr,
            iqr_fpr=canonical_eval.iqr_fpr,
            iqr_tpr=canonical_eval.iqr_tpr,
            max_min_fpr_gap=canonical_eval.max_min_fpr_gap,
            worst_client_fpr=canonical_eval.worst_client_fpr,
            worst_client_id=canonical_eval.worst_client_id,
            worst_ba=canonical_eval.worst_ba,
            p10_macro_f1=canonical_eval.p10_macro_f1,
            auroc=auroc,
            pr_auc=pr_auc,
            aggregate_metrics={
                "cv_fpr": canonical_eval.cv_fpr,
                "mean_fpr": canonical_eval.mean_fpr,
                "std_fpr": canonical_eval.std_fpr,
                "cv_tpr": canonical_eval.cv_tpr,
                "iqr_fpr": canonical_eval.iqr_fpr,
                "iqr_tpr": canonical_eval.iqr_tpr,
                "max_min_fpr_gap": canonical_eval.max_min_fpr_gap,
                "worst_client_fpr": canonical_eval.worst_client_fpr,
                "worst_client_id": canonical_eval.worst_client_id,
                "worst_ba": canonical_eval.worst_ba,
                "p10_client_macro_f1": canonical_eval.p10_macro_f1,
            },
            provenance={
                "config_identity": hash_jsonable(
                    {
                        "input_dim": input_dim,
                        "hidden_dims": hidden_dims,
                        "n_min": n_min,
                        "q": q,
                        "epochs": epochs,
                        "lr": lr,
                        "batch_size": batch_size,
                    }
                ),
                "split_manifest_identity": hash_file(prepared_dir / MANIFEST_FILE)
                if (prepared_dir / MANIFEST_FILE).exists()
                else "MISSING_MANIFEST_HASH",
                "model_checkpoint_identity": b0_ckpt_hash,
                "model_checkpoint_path": str(ckpt_path),
                "score_artifact_identity": "NOT_APPLICABLE_B0_DIRECT_EVAL",
                "metric_code_version": source_hash([Path(__file__)]),
                "threshold_code_version": git_commit(),
                "package_version": git_commit(),
                "generated_at_utc": utc_timestamp(),
            },
            threshold_mode=THRESHOLD_AGGREGATION_BY_BASELINE[Baseline.B0],
            n_clients=len(client_dirs),
            calibration_pending_clients=cal_pending_clients,
            per_client=per_client,
            normalization_scope=norm_scope,
            normalization_mode=normalization_mode,
        )
        metrics_path = write_metrics_atomic(output_dir, result)
        logger.info(
            "b0 results written",
            baseline=Baseline.B0,
            path=str(metrics_path),
            epochs_run=epochs_run,
        )

        log_metrics(
            {
                "tau": tau_b0,
                MetricName.AUROC.value: math.nan if auroc is None else auroc,
                MetricName.PR_AUC.value: math.nan if pr_auc is None else pr_auc,
                "n_clients": float(len(client_dirs)),
                "epochs_run": float(epochs_run),
                "calibration_pending_count": float(len(cal_pending_clients)),
            },
            step=None,
            prefix=Baseline.B0,
        )
        log_artifact(metrics_path, artifact_path="results")

        return result


def run_b0(request: B0RunRequest) -> B0Result:
    if not isinstance(request.regime, Regime):
        raise TypeError(f"run_b0: regime must be Regime, got {type(request.regime)!r}")
    return _run_b0_impl(
        request,
        normalization_mode=B0NormalizationMode.PER_CLIENT_PREPARED,
    )


def run_b0_pooled_norm(request: B0RunRequest) -> B0Result:
    if not isinstance(request.regime, Regime):
        raise TypeError(
            f"run_b0_pooled_norm: regime must be Regime, got {type(request.regime)!r}"
        )
    return _run_b0_impl(
        request,
        normalization_mode=B0NormalizationMode.POOLED_ZSCORE,
    )
