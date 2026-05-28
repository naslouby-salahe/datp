from __future__ import annotations

import math
from pathlib import Path

import pytest

from datp.artifacts.paths import ExperimentLocator
import torch

from datp.federated.data_loading import TRAINING_SPLITS, load_client_data
from datp.thresholding.eligibility import (
    compute_client_thresholds,
    compute_tau_global,
    identify_eligible,
)
from datp.scoring.cal_loading import load_main_cal_errors
from datp.thresholding.thresholds import derive_threshold
from datp.config.compose import BASE_CONFIG, compose_config
from datp.core.enums import (
    Baseline,
    Regime,
)
from datp.core.seeds import set_seeds
from datp.data.regimes.regime_c import partition_regime_c
from datp.evaluation.metrics import evaluate_baseline
from datp.federated.protocols.fedavg import run_fl_training

pytestmark = [pytest.mark.e2e]

_TINY_DATA_N_MIN = 3
_SEED = 0
_ALPHA = 1.0
_N_CLIENTS = 3  # tiny client count
_TRAIN_FRAC = BASE_CONFIG.dataset.regime_c_train_fraction
_CAL_FRAC = BASE_CONFIG.dataset.regime_c_cal_fraction


@pytest.fixture()
def regime_c_artifacts(nbaiot_tiny_raw: Path, tmp_path: Path) -> dict:
    set_seeds(_SEED)

    processed_dir = tmp_path / "processed"
    output_dir = tmp_path / "outputs"

    summary = partition_regime_c(
        raw_nbaiot_dir=nbaiot_tiny_raw,
        output_dir=processed_dir,
        alpha=_ALPHA,
        seed=_SEED,
        n_clients=_N_CLIENTS,
        n_min=_TINY_DATA_N_MIN,
        train_frac=_TRAIN_FRAC,
        cal_frac=_CAL_FRAC,
    )
    prepared_dir = processed_dir / "regime_c" / f"alpha_{_ALPHA:g}" / f"seed_{_SEED}"

    _base = compose_config(
        regime=Regime.C, baseline=Baseline.B1, seed=_SEED, alpha=_ALPHA
    )
    cfg = _base.model_copy(
        update={
            "threshold": _base.threshold.model_copy(update={"n_min": _TINY_DATA_N_MIN}),
            "dataset": _base.dataset.model_copy(update={"n_min": _TINY_DATA_N_MIN}),
            "federation": _base.federation.model_copy(
                update={
                    "convergence": _base.federation.convergence.model_copy(
                        update={"rounds_max": 2, "rounds_initial": 2}
                    ),
                    "local_epochs": 1,
                }
            ),
        }
    )

    fl_cfg = cfg
    client_data = load_client_data(
        prepared_dir, device=torch.device("cpu"), splits=TRAINING_SPLITS
    )

    training_result = run_fl_training(
        fl_cfg,
        client_data,
        _SEED,
        alpha=_ALPHA,
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


class TestRegimeCE2E:
    def test_partition_creates_client_dirs(self, regime_c_artifacts: dict) -> None:
        prepared_dir: Path = regime_c_artifacts["prepared_dir"]
        client_dirs = [d for d in prepared_dir.iterdir() if d.is_dir()]
        assert len(client_dirs) == _N_CLIENTS, (
            f"Expected {_N_CLIENTS} virtual clients, got {len(client_dirs)}"
        )

    def test_parquet_artifacts_per_client(self, regime_c_artifacts: dict) -> None:
        prepared_dir: Path = regime_c_artifacts["prepared_dir"]
        for cdir in sorted(prepared_dir.iterdir()):
            if not cdir.is_dir():
                continue
            for name in (
                "train.parquet",
                "cal.parquet",
                "test_benign.parquet",
                "test_attack.parquet",
            ):
                artifact = cdir / name
                assert artifact.exists(), f"Missing artifact: {artifact}"

    def test_js_divergence_saved(self, regime_c_artifacts: dict) -> None:
        prepared_dir: Path = regime_c_artifacts["prepared_dir"]
        js_file = prepared_dir / "js_divergence.json"
        assert js_file.exists(), f"Missing JS divergence file: {js_file}"

    def test_checkpoint_exists(self, regime_c_artifacts: dict) -> None:
        ckpt_dir = regime_c_artifacts["training_result"].checkpoint_dir
        assert (ckpt_dir / "model.pt").exists()

    def test_score_artifacts_exist(self, regime_c_artifacts: dict) -> None:
        score_dir = regime_c_artifacts["training_result"].score_dir
        for stage in ("cal", "test_benign", "test_attack"):
            stage_dir = score_dir / stage
            assert stage_dir.exists(), f"Missing score stage dir: {stage_dir}"
            parquets = list(stage_dir.glob("*.parquet"))
            assert len(parquets) >= _N_CLIENTS, (
                f"Expected >= {_N_CLIENTS} parquets in {stage_dir}, got {len(parquets)}"
            )

    def test_b1_threshold_and_evaluation(self, regime_c_artifacts: dict) -> None:
        output_dir: Path = regime_c_artifacts["output_dir"]
        cfg = regime_c_artifacts["cfg"]
        n_min = cfg.threshold.n_min
        q = cfg.threshold.q

        client_errors = load_main_cal_errors(Regime.C, _SEED, _ALPHA, output_dir)
        eligible, _ = identify_eligible(client_errors, n_min=n_min)
        client_taus = compute_client_thresholds(client_errors, eligible, q=q)
        tau_global = compute_tau_global(client_taus)

        threshold_result = derive_threshold(
            Baseline.B1,
            client_errors,
            n_min,
            q,
            tau_global,
            Regime.C,
            threshold_cfg=cfg.threshold,
        )

        assert threshold_result.strategy == "b1"
        assert threshold_result.eligible_count >= 1

        eval_result = evaluate_baseline(
            threshold_result.client_thresholds,
            ExperimentLocator.for_main(output_dir, Regime.C).score(_SEED, _ALPHA),
            Regime.C,
            _SEED,
            _ALPHA,
            score_provider=None,
        )

        assert not math.isnan(eval_result.cv_fpr)
        assert len(eval_result.per_client) >= _N_CLIENTS

    def test_b2_threshold_and_evaluation(self, regime_c_artifacts: dict) -> None:
        output_dir: Path = regime_c_artifacts["output_dir"]
        cfg = regime_c_artifacts["cfg"]
        n_min = cfg.threshold.n_min
        q = cfg.threshold.q

        client_errors = load_main_cal_errors(Regime.C, _SEED, _ALPHA, output_dir)
        eligible, _ = identify_eligible(client_errors, n_min=n_min)
        client_taus = compute_client_thresholds(client_errors, eligible, q=q)
        tau_global = compute_tau_global(client_taus)

        threshold_result = derive_threshold(
            Baseline.B2,
            client_errors,
            n_min,
            q,
            tau_global,
            Regime.C,
            threshold_cfg=cfg.threshold,
        )
        assert threshold_result.strategy == "b2"

    def test_no_aborted_marker(self, regime_c_artifacts: dict) -> None:
        output_dir: Path = regime_c_artifacts["output_dir"]
        aborted_files = list(output_dir.rglob("ABORTED.txt"))
        assert aborted_files == [], f"ABORTED.txt found: {aborted_files}"
