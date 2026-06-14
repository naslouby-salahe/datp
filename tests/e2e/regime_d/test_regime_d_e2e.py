from __future__ import annotations

import math
from pathlib import Path

import pytest
import torch

from datp.artifacts.layout import ArtifactLayout
from datp.config.compose import compose_config
from datp.core.enums import Baseline, CheckpointProtocolMode, DeviceType, Regime
from datp.core.identity import TrainingCellId
from datp.core.seeds import set_seeds
from datp.data.datasets.edge_iiotset.spec import FEATURE_COUNT
from datp.data.regimes.regime_d import prepare_regime_d
from datp.data.splits import SplitFilename
from datp.evaluation.metrics import evaluate_baseline
from datp.federated.data_loading import TRAINING_SPLITS, load_client_data
from datp.federated.protocols.fedavg import run_fl_training
from datp.scoring.cal_loading import load_main_cal_errors
from datp.thresholding.eligibility import (
    compute_client_thresholds,
    compute_tau_global,
    identify_eligible,
)
from datp.thresholding.thresholds import derive_threshold

pytestmark = [pytest.mark.e2e]

_N_MIN = 5
_SEED = 0


@pytest.fixture()
def regime_d_artifacts(edge_iiotset_tiny_raw: Path, tmp_path: Path) -> dict:
    set_seeds(_SEED)

    processed_dir = tmp_path / "processed"
    output_dir = tmp_path / "outputs"

    summary = prepare_regime_d(
        raw_dir=edge_iiotset_tiny_raw,
        output_dir=processed_dir,
        regime=Regime.D,
        n_min=_N_MIN,
        seed=_SEED,
        balanced_test=False,
    )
    prepared_dir = processed_dir

    _base = compose_config(regime=Regime.D, baseline=Baseline.B1, seed=_SEED)
    cfg = _base.model_copy(
        update={
            "threshold": _base.threshold.model_copy(update={"n_min": _N_MIN}),
            "dataset": _base.dataset.model_copy(update={"n_min": _N_MIN}),
            "federation": _base.federation.model_copy(
                update={
                    "convergence": _base.federation.convergence.model_copy(
                        update={"rounds_max": 2, "rounds_initial": 2}
                    ),
                    "local_epochs": 1,
                }
            ),
            "checkpoint_protocol": _base.checkpoint_protocol.model_copy(
                update={"mode": CheckpointProtocolMode.DISABLED}
            ),
        }
    )

    client_data = load_client_data(
        prepared_dir, device=torch.device(DeviceType.CPU), splits=TRAINING_SPLITS
    )
    training_result = run_fl_training(
        cfg,
        client_data,
        _SEED,
        base_dir=output_dir,
        prepared_dir=prepared_dir,
    )

    return {
        "processed_dir": processed_dir,
        "prepared_dir": prepared_dir,
        "output_dir": output_dir,
        "cfg": cfg,
        "training_result": training_result,
        "summary": summary,
    }


class TestRegimeDe2e:
    def test_prepare_creates_client_dirs(self, regime_d_artifacts: dict) -> None:
        prepared_dir: Path = regime_d_artifacts["prepared_dir"]
        client_dirs = [d for d in prepared_dir.iterdir() if d.is_dir()]
        assert len(client_dirs) >= 2, f"Expected >= 2 clients, got {len(client_dirs)}"

    def test_parquet_artifacts_per_client(self, regime_d_artifacts: dict) -> None:
        prepared_dir: Path = regime_d_artifacts["prepared_dir"]
        for cdir in sorted(prepared_dir.iterdir()):
            if not cdir.is_dir():
                continue
            for name in (
                SplitFilename.TRAIN,
                SplitFilename.CAL,
                SplitFilename.TEST_BENIGN,
                SplitFilename.TEST_ATTACK,
            ):
                assert (cdir / name).exists(), f"Missing artifact: {cdir / name}"

    def test_no_csv_artifacts(self, regime_d_artifacts: dict) -> None:
        prepared_dir: Path = regime_d_artifacts["prepared_dir"]
        csvs = list(prepared_dir.rglob("*.csv"))
        assert csvs == [], f"CSV artifacts found (forbidden): {csvs}"

    def test_checkpoint_exists(self, regime_d_artifacts: dict) -> None:
        ckpt_dir = regime_d_artifacts["training_result"].checkpoint_dir
        assert (ckpt_dir / "model.pt").exists()

    def test_score_artifacts_exist(self, regime_d_artifacts: dict) -> None:
        score_dir = regime_d_artifacts["training_result"].score_dir
        for stage in ("cal", "test_benign", "test_attack"):
            stage_dir = score_dir / stage
            assert stage_dir.exists(), f"Missing score stage dir: {stage_dir}"
            parquets = list(stage_dir.glob("*.parquet"))
            assert len(parquets) >= 2, (
                f"Expected >= 2 client parquets in {stage_dir}, got {len(parquets)}"
            )

    def test_b1_threshold_and_evaluation(self, regime_d_artifacts: dict) -> None:
        output_dir: Path = regime_d_artifacts["output_dir"]
        cfg = regime_d_artifacts["cfg"]
        n_min = cfg.threshold.n_min
        q = cfg.threshold.q

        client_errors = load_main_cal_errors(Regime.D, _SEED, None, output_dir, checkpoint_round=None)
        eligible, _ = identify_eligible(client_errors, n_min=n_min)
        client_taus = compute_client_thresholds(client_errors, eligible, q=q)
        tau_global = compute_tau_global(client_taus)

        threshold_result = derive_threshold(
            Baseline.B1,
            client_errors,
            n_min,
            q,
            tau_global,
            Regime.D,
            threshold_cfg=cfg.threshold,
        )

        assert threshold_result.run.baseline.value == "b1"
        assert threshold_result.eligible_count >= 1
        assert threshold_result.tau_global > 0

        eval_result = evaluate_baseline(
            threshold_result.client_thresholds,
            ArtifactLayout(base_dir=output_dir, regime=Regime.D)
            .score_cell(TrainingCellId(regime=Regime.D, seed=_SEED, alpha=None))
            .score_dir,
            Regime.D,
            _SEED,
            None,
            score_provider=None,
        )

        assert not math.isnan(eval_result.cv_fpr)
        assert eval_result.coverage_ratio > 0
        assert len(eval_result.clients) >= 2

    def test_b2_threshold_and_evaluation(self, regime_d_artifacts: dict) -> None:
        output_dir: Path = regime_d_artifacts["output_dir"]
        cfg = regime_d_artifacts["cfg"]
        n_min = cfg.threshold.n_min
        q = cfg.threshold.q

        client_errors = load_main_cal_errors(Regime.D, _SEED, None, output_dir, checkpoint_round=None)
        eligible, _ = identify_eligible(client_errors, n_min=n_min)
        client_taus = compute_client_thresholds(client_errors, eligible, q=q)
        tau_global = compute_tau_global(client_taus)

        threshold_result = derive_threshold(
            Baseline.B2,
            client_errors,
            n_min,
            q,
            tau_global,
            Regime.D,
            threshold_cfg=cfg.threshold,
        )
        assert threshold_result.run.baseline.value == "b2"

        eval_result = evaluate_baseline(
            threshold_result.client_thresholds,
            ArtifactLayout(base_dir=output_dir, regime=Regime.D)
            .score_cell(TrainingCellId(regime=Regime.D, seed=_SEED, alpha=None))
            .score_dir,
            Regime.D,
            _SEED,
            None,
            score_provider=None,
        )

        assert eval_result.cv_fpr is not None
        assert len(eval_result.clients) >= 2

    def test_input_dim_58(self, regime_d_artifacts: dict) -> None:
        cfg = regime_d_artifacts["cfg"]
        assert cfg.model.input_dim == FEATURE_COUNT
        assert cfg.dataset.feature_count == FEATURE_COUNT

    def test_no_aborted_marker(self, regime_d_artifacts: dict) -> None:
        output_dir: Path = regime_d_artifacts["output_dir"]
        aborted_files = list(output_dir.rglob("ABORTED.txt"))
        assert aborted_files == [], f"ABORTED.txt found: {aborted_files}"
