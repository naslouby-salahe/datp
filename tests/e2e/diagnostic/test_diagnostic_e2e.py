from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from datp.artifacts.paths import ExperimentLocator
from datp.baselines.common.data_loading import load_client_data
from datp.baselines.common.eligibility import (
    compute_client_thresholds,
    compute_tau_global,
    identify_eligible,
)
from datp.baselines.common.scoring import load_main_cal_errors
from datp.baselines.common.thresholds import derive_threshold
from datp.config.compose import compose_config
from datp.core.enums import (
    Baseline,
    Regime,
)
from datp.core.seeds import set_seeds
from datp.data.datasets.nbaiot import prepare_nbaiot
from datp.evaluation.metrics import evaluate_baseline
from datp.training.fl.runner import run_fl_training

pytestmark = [pytest.mark.e2e]

_N_MIN = 5
_SEED = 0


def _write_contingency_decision(
    diag_dir: Path,
    eval_b1: object,
    eval_b2: object,
) -> Path:
    decision = {
        "decision": "proceed" if not math.isnan(eval_b1.cv_fpr) else "contingency",
        "cv_fpr_b1": eval_b1.cv_fpr if not math.isnan(eval_b1.cv_fpr) else None,
        "cv_fpr_b2": eval_b2.cv_fpr if not math.isnan(eval_b2.cv_fpr) else None,
        "seed": _SEED,
        "regime": "a",
    }
    path = diag_dir / "contingency_decision.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(decision, f, indent=2)
    return path


@pytest.fixture()
def diagnostic_artifacts(nbaiot_tiny_raw: Path, tmp_path: Path) -> dict:
    set_seeds(_SEED)

    processed_dir = tmp_path / "processed"
    output_dir = tmp_path / "outputs"
    diag_dir = output_dir / "phase3_diagnostic"

    prepare_nbaiot(raw_dir=nbaiot_tiny_raw, output_dir=processed_dir, n_min=_N_MIN)
    prepared_dir = processed_dir

    _base = compose_config(regime="a", baseline="b1", seed=_SEED)
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
        }
    )
    fl_cfg = cfg
    client_data = load_client_data(prepared_dir)
    run_fl_training(fl_cfg, client_data, _SEED, base_dir=output_dir)

    n_min = cfg.threshold.n_min
    q = cfg.threshold.q
    client_errors = load_main_cal_errors(Regime.A, _SEED, None, output_dir)
    eligible, pending = identify_eligible(client_errors, n_min=n_min)
    client_taus = compute_client_thresholds(client_errors, eligible, q=q)
    tau_global = compute_tau_global(client_taus)

    tr_b1 = derive_threshold(
        Baseline.B1,
        client_errors,
        n_min,
        q,
        tau_global,
        Regime.A,
        threshold_cfg=cfg.threshold,
    )
    eval_b1 = evaluate_baseline(
        tr_b1.client_thresholds,
        ExperimentLocator.for_main(output_dir, Regime.A).score(_SEED, None),
        Regime.A,
        _SEED,
        None,
    )

    tr_b2 = derive_threshold(
        Baseline.B2,
        client_errors,
        n_min,
        q,
        tau_global,
        Regime.A,
        threshold_cfg=cfg.threshold,
    )
    eval_b2 = evaluate_baseline(
        tr_b2.client_thresholds,
        ExperimentLocator.for_main(output_dir, Regime.A).score(_SEED, None),
        Regime.A,
        _SEED,
        None,
    )

    contingency_path = _write_contingency_decision(diag_dir, eval_b1, eval_b2)

    return {
        "processed_dir": processed_dir,
        "output_dir": output_dir,
        "cfg": cfg,
        "contingency_path": contingency_path,
    }


class TestDiagnosticE2E:
    def test_contingency_decision_exists(self, diagnostic_artifacts: dict) -> None:
        path: Path = diagnostic_artifacts["contingency_path"]
        assert path.exists()

    def test_contingency_decision_keys(self, diagnostic_artifacts: dict) -> None:
        path: Path = diagnostic_artifacts["contingency_path"]
        with open(path) as f:
            decision = json.load(f)
        assert "decision" in decision
        assert "cv_fpr_b1" in decision
        assert "cv_fpr_b2" in decision

    def test_no_aborted_marker(self, diagnostic_artifacts: dict) -> None:
        output_dir: Path = diagnostic_artifacts["output_dir"]
        aborted_files = list(output_dir.rglob("ABORTED.txt"))
        assert aborted_files == [], f"ABORTED.txt found: {aborted_files}"
