from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from datp.baselines.main.b0 import (
    B0RunRequest,
    run_b0 as _execute_b0,
    run_b0_pooled_norm as _execute_b0_pooled_norm,
)
from datp.core.enums import B0NormalizationMode, NormalizationScope, Regime


def _make_synthetic_client(
    client_dir: Path,
    n_train: int = 500,
    n_cal: int = 200,
    n_test_benign: int = 100,
    n_test_attack: int = 100,
    n_features: int = 10,
    rng: np.random.Generator | None = None,
    attack_shift: float = 5.0,
) -> None:
    if rng is None:
        rng = np.random.default_rng(42)

    client_dir.mkdir(parents=True, exist_ok=True)
    cols = [f"f{i}" for i in range(n_features)]

    def _benign(n: int) -> pd.DataFrame:
        return pd.DataFrame(rng.normal(0.0, 0.1, size=(n, n_features)), columns=cols)

    def _attack(n: int) -> pd.DataFrame:
        return pd.DataFrame(
            rng.normal(attack_shift, 0.1, size=(n, n_features)), columns=cols
        )

    _benign(n_train).to_parquet(client_dir / "train.parquet", index=False)
    _benign(n_cal).to_parquet(client_dir / "cal.parquet", index=False)
    _benign(n_test_benign).to_parquet(client_dir / "test_benign.parquet", index=False)
    _attack(n_test_attack).to_parquet(client_dir / "test_attack.parquet", index=False)


def _make_prepared_dir(
    base: Path,
    n_clients: int = 3,
    n_features: int = 10,
    attack_shift: float = 5.0,
    n_train: int = 500,
    n_cal: int = 200,
) -> Path:
    rng = np.random.default_rng(42)
    for i in range(n_clients):
        _make_synthetic_client(
            base / f"client_{i}",
            n_features=n_features,
            rng=rng,
            attack_shift=attack_shift,
            n_train=n_train,
            n_cal=n_cal,
        )
    return base


def _run_b0(**kwargs):
    return _execute_b0(B0RunRequest(**kwargs))


def _run_b0_pooled_norm(**kwargs):
    return _execute_b0_pooled_norm(B0RunRequest(**kwargs))


class TestB0AurocThreshold:
    def test_auroc_threshold(self, tmp_path: Path) -> None:
        n_features = 10
        prepared = _make_prepared_dir(
            tmp_path / "prepared",
            n_clients=3,
            n_features=n_features,
            attack_shift=5.0,
        )
        output = tmp_path / "output"

        result = _run_b0(
            prepared_dir=prepared,
            output_dir=output,
            seed=42,
            input_dim=n_features,
            hidden_dims=[8, 4],
            n_min=100,
            q=0.95,
            epochs=50,
            patience=5,
            lr=1e-3,
            batch_size=64,
            val_fraction=0.1,
            activation="relu",
            use_bn=False,
            training_progress_interval=1,
            regime=Regime.A,
        )

        assert result.auroc >= 0.90, (
            f"Gate G2-1 FAILED: AUROC = {result.auroc:.4f} < 0.90"
        )


class TestB0ResultStructure:
    def test_b0_returns_all_required_fields(self, tmp_path: Path) -> None:
        n_features = 10
        prepared = _make_prepared_dir(
            tmp_path / "prepared", n_clients=2, n_features=n_features
        )
        output = tmp_path / "output"

        result = _run_b0(
            prepared_dir=prepared,
            output_dir=output,
            seed=42,
            input_dim=n_features,
            hidden_dims=[8, 4],
            n_min=100,
            q=0.95,
            epochs=20,
            patience=5,
            lr=1e-3,
            batch_size=64,
            val_fraction=0.1,
            activation="relu",
            use_bn=False,
            training_progress_interval=1,
            regime=Regime.A,
        )

        from datp.baselines.common.types import B0Result, ClientEvalResult

        assert isinstance(result, B0Result)
        required_fields = {
            "baseline",
            "regime",
            "seed",
            "tau_b0",
            "q",
            "n_min",
            "auroc",
            "pr_auc",
            "threshold_mode",
            "n_clients",
            "calibration_pending_clients",
            "per_client",
        }
        actual_fields = set(B0Result.model_fields)
        assert required_fields.issubset(actual_fields), (
            f"Missing fields: {required_fields - actual_fields}"
        )
        assert result.baseline == "b0"
        assert result.threshold_mode == "pooled_percentile"
        assert result.seed == 42
        assert result.n_clients == 2

        per_client_required = {
            "fpr",
            "tpr",
            "balanced_accuracy",
            "macro_f1",
            "n_benign",
            "n_attack",
        }
        actual_per_client_fields = set(ClientEvalResult.model_fields)
        assert per_client_required.issubset(actual_per_client_fields), (
            f"ClientEvalResult missing fields: {per_client_required - actual_per_client_fields}"
        )


class TestB0PooledThreshold:
    def test_b0_uses_pooled_threshold(self, tmp_path: Path) -> None:
        n_features = 10
        prepared = _make_prepared_dir(
            tmp_path / "prepared", n_clients=3, n_features=n_features
        )
        output = tmp_path / "output"

        result = _run_b0(
            prepared_dir=prepared,
            output_dir=output,
            seed=42,
            input_dim=n_features,
            hidden_dims=[8, 4],
            n_min=100,
            q=0.95,
            epochs=20,
            patience=5,
            lr=1e-3,
            batch_size=64,
            val_fraction=0.1,
            activation="relu",
            use_bn=False,
            training_progress_interval=1,
            regime=Regime.B,
        )

        assert isinstance(result.tau_b0, float)
        assert result.tau_b0 > 0.0


class TestB0SeparableData:
    def test_b0_on_trivially_separable_data(self, tmp_path: Path) -> None:
        n_features = 10
        prepared = _make_prepared_dir(
            tmp_path / "prepared",
            n_clients=2,
            n_features=n_features,
            attack_shift=10.0,  # very large shift
        )
        output = tmp_path / "output"

        result = _run_b0(
            prepared_dir=prepared,
            output_dir=output,
            seed=42,
            input_dim=n_features,
            hidden_dims=[8, 4],
            n_min=100,
            q=0.95,
            epochs=50,
            patience=5,
            lr=1e-3,
            batch_size=64,
            val_fraction=0.1,
            activation="relu",
            use_bn=False,
            training_progress_interval=1,
            regime=Regime.A,
        )

        assert result.auroc >= 0.95

        for cid, m in result.per_client.items():
            assert m.tpr >= 0.80, f"Client {cid}: TPR = {m.tpr}"
            assert m.fpr <= 0.30, f"Client {cid}: FPR = {m.fpr}"


class TestB0RegimeGuard:
    def test_b0_rejects_regime_c(self, tmp_path: Path) -> None:
        n_features = 10
        prepared = _make_prepared_dir(
            tmp_path / "prepared", n_clients=2, n_features=n_features
        )
        output = tmp_path / "output"

        with pytest.raises(ValueError, match="Regime A and B only"):
            _run_b0(
                prepared_dir=prepared,
                output_dir=output,
                seed=42,
                input_dim=n_features,
                hidden_dims=[8, 4],
                n_min=100,
                q=0.95,
                epochs=10,
                patience=3,
                lr=1e-3,
                batch_size=64,
                val_fraction=0.1,
                activation="relu",
                use_bn=False,
                training_progress_interval=1,
                regime=Regime.C,
            )


class TestB0MetricsFile:
    def test_metrics_json_written(self, tmp_path: Path) -> None:
        n_features = 10
        prepared = _make_prepared_dir(
            tmp_path / "prepared", n_clients=2, n_features=n_features
        )
        output = tmp_path / "output"

        _run_b0(
            prepared_dir=prepared,
            output_dir=output,
            seed=42,
            input_dim=n_features,
            hidden_dims=[8, 4],
            n_min=100,
            q=0.95,
            epochs=10,
            patience=3,
            lr=1e-3,
            batch_size=64,
            val_fraction=0.1,
            activation="relu",
            use_bn=False,
            training_progress_interval=1,
            regime=Regime.A,
        )

        metrics_file = output / "metrics.json"
        assert metrics_file.exists()
        # No .tmp file left behind
        assert not (output / "metrics.json.tmp").exists()


class TestB0CalibrationPending:
    def test_cal_pending_flagged(self, tmp_path: Path) -> None:
        n_features = 10
        prepared = tmp_path / "prepared"
        rng = np.random.default_rng(42)

        _make_synthetic_client(
            prepared / "client_ok",
            n_cal=200,
            n_features=n_features,
            rng=rng,
        )
        _make_synthetic_client(
            prepared / "client_small",
            n_cal=50,
            n_features=n_features,
            rng=rng,
        )

        output = tmp_path / "output"
        result = _run_b0(
            prepared_dir=prepared,
            output_dir=output,
            seed=42,
            input_dim=n_features,
            hidden_dims=[8, 4],
            n_min=100,
            q=0.95,
            epochs=10,
            patience=3,
            lr=1e-3,
            batch_size=64,
            val_fraction=0.1,
            activation="relu",
            use_bn=False,
            training_progress_interval=1,
            regime=Regime.A,
        )

        assert "client_small" in result.calibration_pending_clients
        assert "client_ok" not in result.calibration_pending_clients


class TestB0NormalizationScope:
    def test_run_b0_persists_per_client_zscore(self, tmp_path: Path) -> None:
        n_features = 10
        prepared = _make_prepared_dir(
            tmp_path / "prepared", n_clients=2, n_features=n_features
        )
        result = _run_b0(
            prepared_dir=prepared,
            output_dir=tmp_path / "out",
            seed=0,
            input_dim=n_features,
            hidden_dims=[8],
            n_min=10,
            q=0.95,
            epochs=5,
            patience=3,
            lr=1e-3,
            batch_size=32,
            val_fraction=0.1,
            activation="relu",
            use_bn=False,
            training_progress_interval=1,
            regime=Regime.A,
        )
        assert result.normalization_scope == NormalizationScope.PER_CLIENT_ZSCORE
        assert result.normalization_mode == B0NormalizationMode.PER_CLIENT_PREPARED

    def test_run_b0_pooled_norm_persists_pooled_zscore(self, tmp_path: Path) -> None:
        n_features = 10
        prepared = _make_prepared_dir(
            tmp_path / "prepared", n_clients=2, n_features=n_features
        )
        result = _run_b0_pooled_norm(
            prepared_dir=prepared,
            output_dir=tmp_path / "out",
            seed=0,
            input_dim=n_features,
            hidden_dims=[8],
            n_min=10,
            q=0.95,
            epochs=5,
            patience=3,
            lr=1e-3,
            batch_size=32,
            val_fraction=0.1,
            activation="relu",
            use_bn=False,
            training_progress_interval=1,
            regime=Regime.A,
        )
        assert result.normalization_scope == NormalizationScope.POOLED_ZSCORE
        assert result.normalization_mode == B0NormalizationMode.POOLED_ZSCORE


class TestB0PooledNormDiagnostic:
    def test_pooled_norm_uses_global_scaler_on_train(self, tmp_path: Path) -> None:
        n_features = 4
        prepared = _make_prepared_dir(
            tmp_path / "prepared", n_clients=2, n_features=n_features
        )
        result = _run_b0_pooled_norm(
            prepared_dir=prepared,
            output_dir=tmp_path / "out",
            seed=0,
            input_dim=n_features,
            hidden_dims=[4],
            n_min=10,
            q=0.95,
            epochs=5,
            patience=3,
            lr=1e-3,
            batch_size=32,
            val_fraction=0.1,
            activation="relu",
            use_bn=False,
            training_progress_interval=1,
            regime=Regime.A,
        )
        assert result.per_client
        for client_id, metrics in result.per_client.items():
            assert 0.0 <= metrics.fpr <= 1.0

    def test_pooled_norm_per_client_metrics_present(self, tmp_path: Path) -> None:
        n_features = 4
        prepared = _make_prepared_dir(
            tmp_path / "prepared", n_clients=2, n_features=n_features
        )
        result = _run_b0_pooled_norm(
            prepared_dir=prepared,
            output_dir=tmp_path / "out",
            seed=0,
            input_dim=n_features,
            hidden_dims=[4],
            n_min=10,
            q=0.95,
            epochs=5,
            patience=3,
            lr=1e-3,
            batch_size=32,
            val_fraction=0.1,
            activation="relu",
            use_bn=False,
            training_progress_interval=1,
            regime=Regime.A,
        )
        assert result.tau_b0 > 0
        assert result.normalization_scope == NormalizationScope.POOLED_ZSCORE
        assert result.n_clients == 2
        assert len(result.per_client) == 2

    def test_pooled_norm_metrics_json_written(self, tmp_path: Path) -> None:
        n_features = 4
        prepared = _make_prepared_dir(
            tmp_path / "prepared", n_clients=2, n_features=n_features
        )
        out = tmp_path / "out"
        _run_b0_pooled_norm(
            prepared_dir=prepared,
            output_dir=out,
            seed=0,
            input_dim=n_features,
            hidden_dims=[4],
            n_min=10,
            q=0.95,
            epochs=5,
            patience=3,
            lr=1e-3,
            batch_size=32,
            val_fraction=0.1,
            activation="relu",
            use_bn=False,
            training_progress_interval=1,
            regime=Regime.A,
        )
        assert (out / "metrics.json").exists()
        import json  # noqa: PLC0415

        m = json.loads((out / "metrics.json").read_text())
        assert m.get("normalization_scope") == "pooled_zscore"
        assert m.get("normalization_mode") == "pooled_zscore"


class TestB0Auditability:
    def test_checkpoint_file_written(self, tmp_path: Path) -> None:
        from datp.artifacts.constants import MODEL_B0_CHECKPOINT

        n_features = 4
        prepared = _make_prepared_dir(
            tmp_path / "prepared", n_clients=2, n_features=n_features
        )
        out = tmp_path / "out"

        _run_b0(
            prepared_dir=prepared,
            output_dir=out,
            seed=0,
            input_dim=n_features,
            hidden_dims=[4],
            n_min=10,
            q=0.95,
            epochs=5,
            patience=3,
            lr=1e-3,
            batch_size=32,
            val_fraction=0.1,
            activation="relu",
            use_bn=False,
            training_progress_interval=1,
            regime=Regime.A,
        )
        assert (out / MODEL_B0_CHECKPOINT).exists(), (
            f"Expected {MODEL_B0_CHECKPOINT} in {out}, but it does not exist."
        )

    def test_checkpoint_hash_in_provenance(self, tmp_path: Path) -> None:
        import json
        import re

        n_features = 4
        prepared = _make_prepared_dir(
            tmp_path / "prepared", n_clients=2, n_features=n_features
        )
        out = tmp_path / "out"

        _run_b0(
            prepared_dir=prepared,
            output_dir=out,
            seed=0,
            input_dim=n_features,
            hidden_dims=[4],
            n_min=10,
            q=0.95,
            epochs=5,
            patience=3,
            lr=1e-3,
            batch_size=32,
            val_fraction=0.1,
            activation="relu",
            use_bn=False,
            training_progress_interval=1,
            regime=Regime.A,
        )

        m = json.loads((out / "metrics.json").read_text())
        provenance = m.get("provenance", {})
        identity = provenance.get("model_checkpoint_identity", "")
        assert identity != "NOT_APPLICABLE_B0_OWN_MODEL", (
            "model_checkpoint_identity must be the actual SHA hash, not the old placeholder."
        )
        assert re.fullmatch(r"[0-9a-f]{64}", identity), (
            f"model_checkpoint_identity must be a 64-hex SHA-256 hash, got: {identity!r}"
        )

    def test_checkpoint_path_in_provenance(self, tmp_path: Path) -> None:
        import json
        from datp.artifacts.constants import MODEL_B0_CHECKPOINT

        n_features = 4
        prepared = _make_prepared_dir(
            tmp_path / "prepared", n_clients=2, n_features=n_features
        )
        out = tmp_path / "out"

        _run_b0(
            prepared_dir=prepared,
            output_dir=out,
            seed=0,
            input_dim=n_features,
            hidden_dims=[4],
            n_min=10,
            q=0.95,
            epochs=5,
            patience=3,
            lr=1e-3,
            batch_size=32,
            val_fraction=0.1,
            activation="relu",
            use_bn=False,
            training_progress_interval=1,
            regime=Regime.A,
        )

        m = json.loads((out / "metrics.json").read_text())
        provenance = m.get("provenance", {})
        ckpt_path = provenance.get("model_checkpoint_path", "")
        assert MODEL_B0_CHECKPOINT in ckpt_path, (
            f"model_checkpoint_path must end with {MODEL_B0_CHECKPOINT}, got: {ckpt_path!r}"
        )
