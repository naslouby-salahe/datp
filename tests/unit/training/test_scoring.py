from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
import torch

from datp.artifacts.constants import SCORING_MANIFEST_FILE, SCORING_SENTINEL
from datp.artifacts.paths import ExperimentLocator
from datp.core.enums import Regime
from datp.training.scoring import validate_scoring_manifest

_SEED = 0


def _score_base(tmp_path: Path) -> Path:
    return ExperimentLocator.for_main(tmp_path, Regime.A).score(_SEED)


def _write_sentinel(score_base: Path) -> None:
    score_base.mkdir(parents=True, exist_ok=True)
    (score_base / SCORING_SENTINEL).write_text("Scoring complete: 2 clients.\n")


def _write_valid_manifest(
    score_base: Path, client_ids: list[str], splits: list[str]
) -> None:
    score_base.mkdir(parents=True, exist_ok=True)
    records = []
    for cid in client_ids:
        for split in splits:
            path = score_base / split / f"{cid}.parquet"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"\x00")
            records.append(
                {
                    "client_id": cid,
                    "split": split,
                    "path": str(path),
                    "row_count": 50,
                    "columns": ["reconstruction_error"],
                    "dtypes": {"reconstruction_error": "Float32"},
                    "score_min": 0.1,
                    "score_max": 1.0,
                    "score_nan_count": 0,
                    "file_hash": "abc123",
                }
            )
    manifest = {
        "schema_version": "1",
        "completion_status": "complete",
        "expected_client_ids": sorted(client_ids),
        "expected_splits": sorted(splits),
        "actual_client_ids": sorted(client_ids),
        "actual_splits": sorted(splits),
        "records": records,
    }
    (score_base / SCORING_MANIFEST_FILE).write_text(
        json.dumps(manifest), encoding="utf-8"
    )


def test_validate_scoring_manifest_passes_with_valid_manifest(tmp_path: Path) -> None:
    sb = _score_base(tmp_path)
    _write_valid_manifest(sb, ["c0", "c1"], ["cal", "test_benign", "test_attack"])
    result = validate_scoring_manifest(sb)
    assert result["completion_status"] == "complete"


def test_sentinel_alone_is_not_sufficient(tmp_path: Path) -> None:
    sb = _score_base(tmp_path)
    _write_sentinel(sb)
    with pytest.raises(FileNotFoundError, match="Scoring manifest missing"):
        validate_scoring_manifest(sb)


def test_validate_scoring_manifest_fails_when_manifest_missing(tmp_path: Path) -> None:
    sb = _score_base(tmp_path)
    sb.mkdir(parents=True, exist_ok=True)
    with pytest.raises(FileNotFoundError, match="Scoring manifest missing"):
        validate_scoring_manifest(sb)


def test_validate_scoring_manifest_fails_incomplete_status(tmp_path: Path) -> None:
    sb = _score_base(tmp_path)
    sb.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema_version": "1",
        "completion_status": "incomplete",
        "expected_client_ids": ["c0"],
        "expected_splits": ["cal"],
        "records": [],
    }
    (sb / SCORING_MANIFEST_FILE).write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="Scoring manifest incomplete"):
        validate_scoring_manifest(sb)


def test_validate_scoring_manifest_fails_missing_records(tmp_path: Path) -> None:
    sb = _score_base(tmp_path)
    sb.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema_version": "1",
        "completion_status": "complete",
        "expected_client_ids": ["c0"],
        "expected_splits": ["cal"],
        "actual_client_ids": [],
        "actual_splits": [],
        "records": [],
    }
    (sb / SCORING_MANIFEST_FILE).write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="Scoring manifest incomplete"):
        validate_scoring_manifest(sb)


class TestLoadModelFromCheckpoint:
    """load_model_from_checkpoint must use resolve_device(), not hardcode CUDA."""

    def _write_checkpoint(self, tmp_path: Path) -> None:
        import io

        from datp.config.compose import BASE_CONFIG
        from datp.models.autoencoder import Autoencoder

        model = Autoencoder(
            input_dim=BASE_CONFIG.model.input_dim,
            hidden_dims=BASE_CONFIG.model.encoder_dims,
            activation=BASE_CONFIG.model.activation,
            use_bn=BASE_CONFIG.model.use_bn,
        )
        buf = io.BytesIO()
        torch.save(model.state_dict(), buf)
        (tmp_path / "model.pt").write_bytes(buf.getvalue())

    def test_uses_resolve_device_not_hardcoded_cuda(self, tmp_path: Path) -> None:
        from datp.config.compose import BASE_CONFIG
        from datp.training.scoring import load_model_from_checkpoint

        self._write_checkpoint(tmp_path)
        cpu_device = torch.device("cpu")

        with patch("datp.training.scoring.resolve_device", return_value=cpu_device):
            model = load_model_from_checkpoint(BASE_CONFIG, ckpt_dir=tmp_path, require_cuda=False)

        assert next(model.parameters()).device.type == "cpu"

    def test_fails_clearly_when_device_unavailable(self, tmp_path: Path) -> None:
        from datp.config.compose import BASE_CONFIG
        from datp.training.scoring import load_model_from_checkpoint

        self._write_checkpoint(tmp_path)

        def _raise_cuda_unavailable(require_cuda: bool) -> torch.device:
            raise RuntimeError("CUDA is required but not available")

        with patch("datp.training.scoring.resolve_device", side_effect=_raise_cuda_unavailable):
            with pytest.raises(RuntimeError, match="CUDA"):
                load_model_from_checkpoint(BASE_CONFIG, ckpt_dir=tmp_path, require_cuda=True)


class TestBatchedScoring:
    """Batched scoring must produce identical results to full-tensor scoring."""

    def test_batched_matches_full(self) -> None:
        from datp.models.autoencoder import Autoencoder
        from datp.training.scoring import _compute_errors

        torch.manual_seed(42)
        model = Autoencoder(input_dim=4, hidden_dims=[3, 2], activation="relu", use_bn=False)
        model.eval()
        data = torch.randn(100, 4)

        # Full (large batch)
        errors_full = _compute_errors(model, data, batch_size=10000)
        # Batched with small batch size
        errors_batched = _compute_errors(model, data, batch_size=7)

        import numpy as np
        np.testing.assert_array_almost_equal(errors_full, errors_batched, decimal=5)

    def test_empty_tensor_returns_empty(self) -> None:
        from datp.models.autoencoder import Autoencoder
        from datp.training.scoring import _compute_errors

        model = Autoencoder(input_dim=4, hidden_dims=[3, 2], activation="relu", use_bn=False)
        model.eval()
        data = torch.empty(0, 4)

        errors = _compute_errors(model, data, batch_size=128)
        assert errors.shape == (0,)

    def test_raises_file_not_found_when_checkpoint_missing(self, tmp_path: Path) -> None:
        from datp.config.compose import BASE_CONFIG
        from datp.training.scoring import load_model_from_checkpoint

        with pytest.raises(FileNotFoundError, match="Checkpoint missing"):
            load_model_from_checkpoint(BASE_CONFIG, ckpt_dir=tmp_path, require_cuda=False)
