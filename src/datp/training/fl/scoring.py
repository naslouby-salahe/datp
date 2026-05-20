# SPDX-License-Identifier: Proprietary
"""Score artifacts have no baseline subdirectory — they are shared across B1/B2/B3/B4."""

from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

import numpy as np
import polars as pl
import torch

from datp.artifacts.constants import (
    MODEL_CHECKPOINT,
    SCORING_MANIFEST_FILE,
    SCORING_SENTINEL,
)
from datp.artifacts.markers import write_json_atomic
from datp.core.device import get_device
from datp.core.enums import (
    SCORING_STAGES,
    Regime,
    ScoringStage,
)
from datp.core.errors import fmt
from datp.core.logging import get_logger
from datp.core.provenance import git_commit, hash_file, utc_timestamp
from datp.data.common.storage import write_artifact
from datp.evaluation.metric_keys import SCORE_COLUMN
from datp.models.autoencoder import Autoencoder

logger = get_logger(__name__)


class ClientData(NamedTuple):
    """All tensors are 2-D: (n_samples, input_dim)."""

    train: torch.Tensor
    val: torch.Tensor
    test_benign: torch.Tensor
    test_attack: torch.Tensor


def _compute_errors(model: Autoencoder, data: torch.Tensor) -> np.ndarray:
    model.eval()
    with torch.inference_mode():
        errors = model.reconstruction_error(data)
    return errors.cpu().numpy().astype(np.float32)


def _errors_to_dataframe(errors: np.ndarray) -> pl.DataFrame:
    return pl.DataFrame({SCORE_COLUMN: errors})


def _score_record(path: Path, client_id: str, stage: ScoringStage, errors: np.ndarray) -> dict[str, object]:
    finite = errors[np.isfinite(errors)]
    return {
        "client_id": client_id,
        "split": stage.value,
        "path": str(path),
        "row_count": int(errors.size),
        "columns": [SCORE_COLUMN],
        "dtypes": {SCORE_COLUMN: "Float32"},
        "score_min": float(finite.min()) if finite.size else None,
        "score_max": float(finite.max()) if finite.size else None,
        "score_nan_count": int(np.isnan(errors).sum()),
        "file_hash": hash_file(path),
    }


def validate_scoring_manifest(score_base: Path) -> dict[str, object]:
    manifest_path = Path(score_base) / SCORING_MANIFEST_FILE
    if not manifest_path.exists():
        raise FileNotFoundError(
            fmt("training.fl.scoring", "Scoring manifest missing", str(manifest_path), "missing file")
        )
    import json

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    records = manifest["records"]
    expected = {(cid, split) for cid in manifest["expected_client_ids"] for split in manifest["expected_splits"]}
    actual = {(str(row["client_id"]), str(row["split"])) for row in records}
    missing = sorted(expected - actual)
    missing_files = sorted(str(row["path"]) for row in records if not Path(str(row["path"])).exists())
    completion_status = manifest["completion_status"]
    if completion_status != "complete" or missing or missing_files:
        raise ValueError(
            fmt(
                "training.fl.scoring",
                "Scoring manifest incomplete",
                "complete manifest with all expected score files",
                f"status={completion_status}, missing={missing}, missing_files={missing_files}",
            )
        )
    return manifest


def score_clients(
    model: Autoencoder,
    client_data: dict[str, ClientData],
    *,
    score_base: Path,
    regime: Regime | None,
    seed: int | None,
    alpha: float | None,
    dataset: str,
    checkpoint_path: Path | None,
) -> None:
    model.eval()
    n_clients = len(client_data)
    logger.info("scoring clients", n_clients=n_clients, score_base=str(score_base))

    # `val` tensor stores calibration data (used as FL validation during training).
    stage_tensor_map = {
        ScoringStage.CAL: "val",
        ScoringStage.TEST_BENIGN: "test_benign",
        ScoringStage.TEST_ATTACK: "test_attack",
    }

    records: list[dict[str, object]] = []
    for cid, splits in client_data.items():
        for stage in SCORING_STAGES:
            tensor_attr = stage_tensor_map[stage]
            data = getattr(splits, tensor_attr)
            model_device = next(model.parameters()).device
            if data.device != model_device:
                data = data.to(model_device, non_blocking=True)
            errors = _compute_errors(model, data)
            df = _errors_to_dataframe(errors)

            out_path = score_base / stage / f"{cid}.parquet"
            write_artifact(df, out_path)
            records.append(_score_record(out_path, cid, stage, errors))
            logger.debug(
                "wrote scores",
                n_scores=len(errors), path=str(out_path), client=cid, stage=stage,
            )

    manifest = {
        "schema_version": "1",
        "dataset": dataset,
        "regime": regime.value if regime is not None else "NOT_PROVIDED",
        "seed": seed,
        "alpha": alpha,
        "model_checkpoint_path": str(checkpoint_path) if checkpoint_path is not None else "NOT_PROVIDED",
        "model_checkpoint_hash": hash_file(checkpoint_path) if checkpoint_path is not None else "NOT_PROVIDED",
        "scoring_code_version": git_commit(),
        "score_column_name": SCORE_COLUMN,
        "expected_client_ids": sorted(client_data.keys()),
        "expected_splits": [stage.value for stage in SCORING_STAGES],
        "actual_client_ids": sorted({str(row["client_id"]) for row in records}),
        "actual_splits": sorted({str(row["split"]) for row in records}),
        "records": records,
        "completion_status": "complete",
        "generated_at_utc": utc_timestamp(),
    }
    write_json_atomic(score_base / SCORING_MANIFEST_FILE, manifest)
    validate_scoring_manifest(score_base)

    sentinel = score_base / SCORING_SENTINEL
    sentinel.parent.mkdir(parents=True, exist_ok=True)
    sentinel.write_text(f"Scoring complete: {n_clients} clients.\n")
    logger.info("scoring complete, sentinel written", score_base=str(score_base), path=str(sentinel))


def load_model_from_checkpoint(
    cfg,
    *,
    ckpt_dir: Path,
) -> Autoencoder:
    ckpt_file = ckpt_dir / MODEL_CHECKPOINT
    if not ckpt_file.exists():
        raise FileNotFoundError(
            fmt("training.fl.scoring", "Checkpoint missing", str(ckpt_file), "missing file")
        )

    model = Autoencoder(
        input_dim=cfg.model.input_dim,
        hidden_dims=cfg.model.encoder_dims,
        activation=cfg.model.activation,
        use_bn=cfg.model.use_bn,
    )
    state_dict = torch.load(ckpt_file, map_location="cuda", weights_only=True)
    model.load_state_dict(state_dict)
    device = get_device()
    model.to(device)
    model.eval()
    logger.info("loaded checkpoint", path=str(ckpt_file), device=str(device))
    return model
