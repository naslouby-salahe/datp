from __future__ import annotations

import math
from pathlib import Path

import numpy as np
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
from datp.config.compose import compose_config
from datp.core.enums import (
    Baseline,
    Regime,
)
from datp.core.seeds import set_seeds
from datp.data.datasets.nbaiot import prepare_nbaiot
from datp.evaluation.metrics import evaluate_baseline
from datp.federated.protocols.fedavg import run_fl_training

pytestmark = [pytest.mark.e2e]

_TINY_DATA_N_MIN = 5
_SEED = 0


@pytest.fixture()
def regime_a_artifacts(nbaiot_tiny_raw: Path, tmp_path: Path) -> dict:
    set_seeds(_SEED)

    processed_dir = tmp_path / "processed"
    output_dir = tmp_path / "outputs"

    summary = prepare_nbaiot(
        raw_dir=nbaiot_tiny_raw,
        output_dir=processed_dir,
        n_min=_TINY_DATA_N_MIN,
        seed=_SEED,
        balanced_test=False,
    )
    prepared_dir = processed_dir

    _base = compose_config(regime=Regime.A, baseline=Baseline.B1, seed=_SEED)
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


class TestRegimeAE2E:
    def test_prepare_creates_parquet(self, regime_a_artifacts: dict) -> None:
        prepared_dir: Path = regime_a_artifacts["prepared_dir"]
        for device_dir in sorted(prepared_dir.iterdir()):
            if not device_dir.is_dir():
                continue
            for name in (
                "train.parquet",
                "cal.parquet",
                "test_benign.parquet",
                "test_attack.parquet",
            ):
                artifact = device_dir / name
                assert artifact.exists(), f"Missing artifact: {artifact}"

    def test_no_csv_artifacts(self, regime_a_artifacts: dict) -> None:
        prepared_dir: Path = regime_a_artifacts["prepared_dir"]
        csvs = list(prepared_dir.rglob("*.csv"))
        assert csvs == [], f"CSV artifacts found (forbidden): {csvs}"

    def test_checkpoint_exists(self, regime_a_artifacts: dict) -> None:
        ckpt_dir = regime_a_artifacts["training_result"].checkpoint_dir
        assert (ckpt_dir / "model.pt").exists()

    def test_score_artifacts_exist(self, regime_a_artifacts: dict) -> None:
        score_dir = regime_a_artifacts["training_result"].score_dir
        for stage in ("cal", "test_benign", "test_attack"):
            stage_dir = score_dir / stage
            assert stage_dir.exists(), f"Missing score stage dir: {stage_dir}"
            parquets = list(stage_dir.glob("*.parquet"))
            assert len(parquets) >= 2, (
                f"Expected >= 2 client parquets in {stage_dir}, got {len(parquets)}"
            )

    def test_score_artifacts_are_parquet(self, regime_a_artifacts: dict) -> None:
        score_dir = regime_a_artifacts["training_result"].score_dir
        csvs = list(score_dir.rglob("*.csv"))
        assert csvs == [], f"CSV score artifacts found: {csvs}"

    def test_b1_threshold_and_evaluation(self, regime_a_artifacts: dict) -> None:
        output_dir: Path = regime_a_artifacts["output_dir"]
        cfg = regime_a_artifacts["cfg"]
        n_min = cfg.threshold.n_min
        q = cfg.threshold.q

        client_errors = load_main_cal_errors(Regime.A, _SEED, None, output_dir)
        eligible, _ = identify_eligible(client_errors, n_min=n_min)
        client_taus = compute_client_thresholds(client_errors, eligible, q=q)
        tau_global = compute_tau_global(client_taus)

        threshold_result = derive_threshold(
            Baseline.B1,
            client_errors,
            n_min,
            q,
            tau_global,
            Regime.A,
            threshold_cfg=cfg.threshold,
        )

        assert threshold_result.run.baseline.value == "b1"
        assert threshold_result.eligible_count >= 1
        assert threshold_result.tau_global > 0

        eval_result = evaluate_baseline(
            threshold_result.client_thresholds,
            ExperimentLocator.for_main(output_dir, Regime.A).score(_SEED, None),
            Regime.A,
            _SEED,
            None,
            score_provider=None,
        )

        assert not math.isnan(eval_result.cv_fpr)
        assert eval_result.coverage_ratio > 0
        assert len(eval_result.per_client) >= 2

    def test_b2_threshold_and_evaluation(self, regime_a_artifacts: dict) -> None:
        output_dir: Path = regime_a_artifacts["output_dir"]
        cfg = regime_a_artifacts["cfg"]
        n_min = cfg.threshold.n_min
        q = cfg.threshold.q

        client_errors = load_main_cal_errors(Regime.A, _SEED, None, output_dir)
        eligible, _ = identify_eligible(client_errors, n_min=n_min)
        client_taus = compute_client_thresholds(client_errors, eligible, q=q)
        tau_global = compute_tau_global(client_taus)

        threshold_result = derive_threshold(
            Baseline.B2,
            client_errors,
            n_min,
            q,
            tau_global,
            Regime.A,
            threshold_cfg=cfg.threshold,
        )

        assert threshold_result.run.baseline.value == "b2"

        eval_result = evaluate_baseline(
            threshold_result.client_thresholds,
            ExperimentLocator.for_main(output_dir, Regime.A).score(_SEED, None),
            Regime.A,
            _SEED,
            None,
            score_provider=None,
        )

        assert eval_result.cv_fpr is not None
        assert len(eval_result.per_client) >= 2

    def test_no_aborted_marker(self, regime_a_artifacts: dict) -> None:
        output_dir: Path = regime_a_artifacts["output_dir"]
        aborted_files = list(output_dir.rglob("ABORTED.txt"))
        assert aborted_files == [], f"ABORTED.txt found: {aborted_files}"

    def test_determinism(self, nbaiot_tiny_raw: Path, tmp_path: Path) -> None:
        seed = 42

        def run_pipeline(base: Path) -> dict[str, float]:
            set_seeds(seed)
            processed = base / "processed"
            outputs = base / "outputs"
            prepare_nbaiot(
                raw_dir=nbaiot_tiny_raw,
                output_dir=processed,
                n_min=_TINY_DATA_N_MIN,
                seed=seed,
                balanced_test=False,
            )
            _base = compose_config(regime=Regime.A, baseline=Baseline.B1, seed=seed)
            cfg = _base.model_copy(
                update={
                    "threshold": _base.threshold.model_copy(
                        update={"n_min": _TINY_DATA_N_MIN}
                    ),
                    "dataset": _base.dataset.model_copy(
                        update={"n_min": _TINY_DATA_N_MIN}
                    ),
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
                processed, device=torch.device("cpu"), splits=TRAINING_SPLITS
            )
            run_fl_training(
                fl_cfg, client_data, seed, base_dir=outputs, prepared_dir=processed
            )
            errors = load_main_cal_errors(Regime.A, seed, None, outputs)
            return {k: float(np.mean(v)) for k, v in errors.items()}

        result_a = run_pipeline(tmp_path / "run_a")
        result_b = run_pipeline(tmp_path / "run_b")

        assert result_a.keys() == result_b.keys()
        for cid in result_a:
            assert result_a[cid] == pytest.approx(result_b[cid], abs=1e-6), (
                f"Determinism failure for {cid}: {result_a[cid]} != {result_b[cid]}"
            )
