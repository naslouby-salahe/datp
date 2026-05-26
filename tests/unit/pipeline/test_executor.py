from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from datp.core.enums import (
    ISOLATED_BASELINES,
    Baseline,
    Regime,
    ScoringStage,
)
from datp.core.identity import ExperimentKey
from datp.evaluation.metric_keys import SCORE_COLUMN
from datp.evaluation.score_loading import ScoreProvider
from datp.pipeline.executor import IsolatedBaselineExecutor
from datp.pipeline.models import (
    PipelineRequest,
    SharedPipelineContext,
)
from datp.pipeline.training import ensure_fl_checkpoint, train_once_guard


def _make_request(
    baseline: Baseline,
    tmp_path: Path,
    regime: Regime = Regime.A,
    seed: int = 1,
    alpha: float | None = None,
) -> PipelineRequest:
    cfg = MagicMock()
    cfg.threshold.n_min = 100
    cfg.threshold.q = 0.95
    cfg.model.input_dim = 115
    cfg.model.encoder_dims = [64, 32]
    cfg.model.epochs = 5
    cfg.model.patience = 3
    cfg.model.lr = 1e-3
    cfg.model.activation = "relu"
    cfg.machine.batch_size_train = 256
    cfg.dataset.b0_val_fraction = 0.1
    return PipelineRequest(
        key=ExperimentKey(regime=regime, seed=seed, alpha=alpha),
        baseline=baseline,
        cfg=cfg,
        base_dir=tmp_path,
        prepared_dir=tmp_path / "prepared",
    )


def _make_context(key: ExperimentKey, score_root: Path) -> SharedPipelineContext:
    return SharedPipelineContext(
        key=key,
        client_errors={"c0": np.array([0.05, 0.10]), "c1": np.array([0.08])},
        eligible=["c0", "c1"],
        pending=[],
        client_taus={"c0": 0.09, "c1": 0.07},
        tau_global=0.08,
        score_provider=ScoreProvider(score_root),
    )


def _write_score_artifact(path: Path, values: list[float]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    table = pa.table({SCORE_COLUMN: pa.array(values, type=pa.float32())})
    pq.write_table(table, path)


class TestIsolatedBaselinesConstant:
    def test_does_not_contain_shared_baselines(self) -> None:
        for bl in (Baseline.B1, Baseline.B2, Baseline.B3, Baseline.B4):
            assert bl not in ISOLATED_BASELINES

    def test_is_frozenset(self) -> None:
        assert isinstance(ISOLATED_BASELINES, frozenset)


class TestIsolatedBaselineExecutor:
    def test_raises_for_shared_baseline(self, tmp_path: Path) -> None:
        executor = IsolatedBaselineExecutor(step_fn=None)
        request = _make_request(Baseline.B1, tmp_path)
        with pytest.raises(ValueError):
            executor.run(request)

    def test_raises_for_b2(self, tmp_path: Path) -> None:
        executor = IsolatedBaselineExecutor(step_fn=None)
        request = _make_request(Baseline.B2, tmp_path)
        with pytest.raises(ValueError):
            executor.run(request)

    def test_dispatches_b0(self, tmp_path: Path) -> None:
        executor = IsolatedBaselineExecutor(step_fn=None)
        request = _make_request(Baseline.B0, tmp_path, regime=Regime.A, seed=42)

        with (
            patch(
                "datp.pipeline.executor.ExperimentLocator.for_main",
                return_value=type(
                    "L",
                    (),
                    {
                        "result": lambda *a, **kw: tmp_path / "out",
                        "score": lambda *a, **kw: tmp_path / "scores",
                    },
                )(),
            ),
            patch("datp.baselines.main.b0.run_b0") as mock_b0,
            patch("datp.pipeline.executor.IsolatedBaselineExecutor._step"),
        ):
            executor.run(request)

        mock_b0.assert_called_once()
        _, kwargs = mock_b0.call_args
        assert kwargs.get("seed") == 42 or mock_b0.call_args[0]  # positional or kw

    def test_step_fn_called(self, tmp_path: Path) -> None:
        step_calls: list[tuple[str, str]] = []

        def record_step(step: str, detail: str = "") -> None:
            step_calls.append((step, detail))

        executor = IsolatedBaselineExecutor(step_fn=record_step)
        request = _make_request(Baseline.B0, tmp_path, regime=Regime.A, seed=1)

        with (
            patch(
                "datp.pipeline.executor.ExperimentLocator.for_main",
                return_value=type(
                    "L",
                    (),
                    {
                        "result": lambda *a, **kw: tmp_path / "out",
                        "score": lambda *a, **kw: tmp_path / "scores",
                    },
                )(),
            ),
            patch("datp.baselines.main.b0.run_b0"),
        ):
            executor.run(request)

        assert len(step_calls) >= 1

    def test_no_step_fn_no_error(self, tmp_path: Path) -> None:
        executor = IsolatedBaselineExecutor(step_fn=None)
        request = _make_request(Baseline.B0, tmp_path)

        with (
            patch(
                "datp.pipeline.executor.ExperimentLocator.for_main",
                return_value=type(
                    "L",
                    (),
                    {
                        "result": lambda *a, **kw: tmp_path / "out",
                        "score": lambda *a, **kw: tmp_path / "scores",
                    },
                )(),
            ),
            patch("datp.baselines.main.b0.run_b0"),
        ):
            executor.run(request)  # should not raise


class TestTrainOnceGuard:
    def test_trains_when_checkpoint_missing(self, tmp_path: Path) -> None:
        ckpt = tmp_path / "model.pt"
        trained: list[bool] = []

        def do_train() -> None:
            trained.append(True)
            ckpt.touch()

        assert not ckpt.exists()
        train_once_guard(ckpt, "test.train", do_train, lock_timeout=60.0)
        assert trained == [True]

    def test_skips_when_checkpoint_exists(self, tmp_path: Path) -> None:
        ckpt = tmp_path / "model.pt"
        ckpt.touch()
        trained: list[bool] = []

        def do_train() -> None:
            trained.append(True)

        train_once_guard(ckpt, "test.train", do_train, lock_timeout=60.0)
        assert trained == []

    def test_log_fields_forwarded(self, tmp_path: Path) -> None:
        ckpt = tmp_path / "model.pt"
        ckpt.touch()

        train_once_guard(
            ckpt,
            "test.train",
            lambda: None,
            lock_timeout=60.0,
            seed=42,
            regime=Regime.A,
        )
        # No assertion needed — just verify no TypeError is raised.

    def test_trains_only_once(self, tmp_path: Path) -> None:
        ckpt = tmp_path / "model.pt"
        call_count = [0]

        def do_train() -> None:
            call_count[0] += 1
            ckpt.touch()

        train_once_guard(ckpt, "test.train", do_train, lock_timeout=60.0)
        train_once_guard(ckpt, "test.train", do_train, lock_timeout=60.0)
        assert call_count[0] == 1

    def test_creates_lock_in_checkpoint_directory(self, tmp_path: Path) -> None:
        ckpt = tmp_path / "nested" / "model.pt"
        created_lock_paths: list[str] = []

        class _Lock:
            def __enter__(self) -> "_Lock":
                return self

            def __exit__(self, exc_type, exc, tb) -> None:
                del exc_type, exc, tb

        def fake_filelock(path: str, timeout: float) -> _Lock:
            del timeout
            created_lock_paths.append(path)
            return _Lock()

        with patch("datp.pipeline.training.FileLock", side_effect=fake_filelock):
            train_once_guard(
                ckpt, "test.train", lambda: ckpt.touch(), lock_timeout=60.0
            )

        assert created_lock_paths == [str(ckpt.parent / ".train.lock")]


class TestEnsureFlCheckpoint:
    def test_lock_wraps_score_only_recovery(self, tmp_path: Path) -> None:
        cfg = MagicMock()
        request = PipelineRequest(
            key=ExperimentKey(regime=Regime.A, seed=4),
            baseline=Baseline.B1,
            cfg=cfg,
            base_dir=tmp_path,
            prepared_dir=tmp_path / "prepared",
        )
        ckpt_dir = tmp_path / "checkpoints" / "a" / "seed_4"
        ckpt_dir.mkdir(parents=True, exist_ok=True)
        ckpt = ckpt_dir / "model.pt"
        ckpt.touch()

        score_dir = tmp_path / "scores" / "a" / "seed_4"
        score_dir.mkdir(parents=True, exist_ok=True)

        locator = type(
            "Locator",
            (),
            {
                "checkpoint": staticmethod(lambda seed, alpha=None: ckpt_dir),
                "score": staticmethod(lambda seed, alpha=None: score_dir),
            },
        )()

        class _Lock:
            entered = False

            def __enter__(self) -> "_Lock":
                self.entered = True
                return self

            def __exit__(self, exc_type, exc, tb) -> None:
                del exc_type, exc, tb

        lock = _Lock()
        with (
            patch("datp.pipeline.training.FileLock", return_value=lock),
            patch(
                "datp.pipeline.training.ExperimentLocator.for_main",
                return_value=locator,
            ),
            patch(
                "datp.baselines.common.data_loading.load_client_data",
                return_value={"c1": object()},
            ),
            patch(
                "datp.training.scoring.load_model_from_checkpoint",
                return_value=object(),
            ),
            patch("datp.training.scoring.score_clients") as score_clients,
        ):
            ensure_fl_checkpoint(
                request,
                step_fn=None,
                checkpoint_status_fn=None,
                lock_timeout=60.0,
            )

        assert lock.entered is True
        score_clients.assert_called_once()


class TestScoreProvider:
    def test_missing_benign_raises(self, tmp_path: Path) -> None:
        provider = ScoreProvider(tmp_path)
        with pytest.raises(FileNotFoundError, match="test_benign"):
            provider.load("client_01", ScoringStage.TEST_BENIGN)

    def test_missing_attack_raises(self, tmp_path: Path) -> None:
        provider = ScoreProvider(tmp_path)
        # Write benign so we can isolate the attack-missing case
        _write_score_artifact(
            tmp_path / ScoringStage.TEST_BENIGN / "c1.parquet", [0.1, 0.2]
        )
        with pytest.raises(FileNotFoundError, match="test_attack"):
            provider.load("c1", ScoringStage.TEST_ATTACK)

    def test_reads_score_column_only(self, tmp_path: Path) -> None:
        _write_score_artifact(
            tmp_path / ScoringStage.TEST_BENIGN / "c1.parquet", [0.1, 0.2, 0.3]
        )
        provider = ScoreProvider(tmp_path)
        arr = provider.load("c1", ScoringStage.TEST_BENIGN)
        assert arr.dtype == np.float64
        np.testing.assert_allclose(arr, [0.1, 0.2, 0.3], rtol=1e-5)

    def test_empty_attack_artifact_is_valid(self, tmp_path: Path) -> None:
        _write_score_artifact(tmp_path / ScoringStage.TEST_ATTACK / "c1.parquet", [])
        provider = ScoreProvider(tmp_path)
        arr = provider.load("c1", ScoringStage.TEST_ATTACK)
        assert arr.size == 0
        assert arr.dtype == np.float64

    def test_load_test_scores_returns_tuple(self, tmp_path: Path) -> None:
        _write_score_artifact(
            tmp_path / ScoringStage.TEST_BENIGN / "c1.parquet", [0.1, 0.2]
        )
        _write_score_artifact(
            tmp_path / ScoringStage.TEST_ATTACK / "c1.parquet", [0.5, 0.9]
        )
        provider = ScoreProvider(tmp_path)
        benign, attack = provider.load_test_scores("c1")
        assert benign.size == 2
        assert attack.size == 2

    def test_score_provider_has_no_cache_state(self, tmp_path: Path) -> None:
        provider = ScoreProvider(tmp_path)
        assert not hasattr(provider, "_lru")

    def test_shared_provider_across_baselines(self, tmp_path: Path) -> None:
        _write_score_artifact(tmp_path / ScoringStage.TEST_BENIGN / "c1.parquet", [0.1])
        _write_score_artifact(tmp_path / ScoringStage.TEST_ATTACK / "c1.parquet", [0.5])
        provider = ScoreProvider(tmp_path)
        # Simulate two baselines sharing the provider
        b, a = provider.load_test_scores("c1")
        b2, a2 = provider.load_test_scores("c1")
        np.testing.assert_allclose(b, b2)
        np.testing.assert_allclose(a, a2)


class TestNoProductionAssert:
    def test_no_assert_in_executor_source(self) -> None:
        import inspect

        import datp.pipeline.executor as mod

        source = inspect.getsource(mod)
        # Strip comment lines then check for bare assert statements
        non_comment = "\n".join(
            line for line in source.splitlines() if not line.strip().startswith("#")
        )
        assert "assert " not in non_comment, (
            "Production assert found in pipeline/executor.py"
        )
