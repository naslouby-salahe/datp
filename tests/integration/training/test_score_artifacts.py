from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
import torch

from datp.artifacts.constants import SCORING_MANIFEST_FILE
from datp.artifacts.paths import ExperimentLocator
from datp.config.compose import BASE_CONFIG
from datp.config.models import (
    ConvergenceConfig,
    DatpConfig,
    FederationConfig,
)
from datp.core.device import get_device
from datp.core.enums import Regime, ScoringStage
from datp.core.seeds import set_seeds
from datp.training.protocols.fedavg import run_fl_training
from datp.training.scoring import ClientData, validate_scoring_manifest

_N_FEATURES = 10
_N_TRAIN = 200
_N_VAL = 50
_N_TEST = 50
_SEED = 42
_STAGES = (ScoringStage.CAL, ScoringStage.TEST_BENIGN, ScoringStage.TEST_ATTACK)


def _make_client_data(n_clients: int, seed: int = _SEED) -> dict[str, ClientData]:
    device = get_device()
    rng = torch.Generator().manual_seed(seed)
    data = {}
    for i in range(n_clients):
        data[f"client_{i}"] = ClientData(
            train=torch.randn(_N_TRAIN, _N_FEATURES, generator=rng).to(device),
            val=torch.randn(_N_VAL, _N_FEATURES, generator=rng).to(device),
            test_benign=torch.randn(_N_TEST, _N_FEATURES, generator=rng).to(device),
            test_attack=(torch.randn(_N_TEST, _N_FEATURES, generator=rng) + 5.0).to(
                device
            ),
        )
    return data


def _make_cfg(
    regime: Regime = Regime.A,
    n_features: int = _N_FEATURES,
    rounds: int = 2,
) -> DatpConfig:
    return BASE_CONFIG.model_copy(
        update={
            "regime": regime,
            "model": BASE_CONFIG.model.model_copy(
                update={
                    "input_dim": n_features,
                    "encoder_dims": [8, 4],
                }
            ),
            "dataset": BASE_CONFIG.dataset.model_copy(
                update={
                    "feature_count": n_features,
                }
            ),
            "machine": BASE_CONFIG.machine.model_copy(
                update={
                    "batch_size_train": 64,
                }
            ),
            "federation": FederationConfig(
                local_epochs=1,
                convergence=ConvergenceConfig(
                    rounds_initial=1,
                    rounds_max=rounds,
                    relative_threshold=0.001,
                    window=2,
                    round_timeout_s=300.0,
                ),
            ),
        }
    )


@pytest.mark.integration
def test_artifacts_written(tmp_path) -> None:
    set_seeds(_SEED)
    cfg = _make_cfg(regime=Regime.A, rounds=2)
    client_data = _make_client_data(n_clients=2)
    client_ids = sorted(client_data.keys())

    run_fl_training(
        cfg=cfg,
        client_data=client_data,
        seed=_SEED,
        alpha=None,
        base_dir=tmp_path,
    )

    for cid in client_ids:
        for stage in _STAGES:
            expected = ExperimentLocator.for_main(tmp_path, Regime.A).score(
                _SEED, alpha=None, stage=stage, client_id=cid
            )
            assert expected.exists(), (
                f"Missing score artifact: {expected} (client={cid}, stage={stage})"
            )
    manifest = validate_scoring_manifest(
        ExperimentLocator.for_main(tmp_path, Regime.A).score(_SEED)
    )
    assert manifest["completion_status"] == "complete"
    assert manifest["expected_client_ids"] == client_ids
    assert len(manifest["records"]) == len(client_ids) * len(_STAGES)


@pytest.mark.integration
def test_artifact_schema(tmp_path) -> None:
    set_seeds(_SEED)
    cfg = _make_cfg(regime=Regime.A, rounds=2)
    client_data = _make_client_data(n_clients=2)
    first_cid = sorted(client_data.keys())[0]

    run_fl_training(
        cfg=cfg,
        client_data=client_data,
        seed=_SEED,
        alpha=None,
        base_dir=tmp_path,
    )

    parquet_file = ExperimentLocator.for_main(tmp_path, Regime.A).score(
        _SEED, alpha=None, stage=ScoringStage.CAL, client_id=first_cid
    )
    df = pd.read_parquet(parquet_file)

    assert list(df.columns) == ["reconstruction_error"], (
        f"Expected single column 'reconstruction_error', got {list(df.columns)}"
    )
    assert df["reconstruction_error"].dtype == np.float32, (
        f"Expected float32, got {df['reconstruction_error'].dtype}"
    )


def test_scoring_manifest_validation_fails_when_missing(tmp_path) -> None:
    score_base = ExperimentLocator.for_main(tmp_path, Regime.A).score(_SEED)
    score_base.mkdir(parents=True)
    (score_base / SCORING_MANIFEST_FILE).write_text(
        '{"schema_version":"1","completion_status":"complete","expected_client_ids":["c1"],'
        '"expected_splits":["cal"],"records":[]}',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="Scoring manifest incomplete"):
        validate_scoring_manifest(score_base)
