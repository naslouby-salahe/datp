from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, NamedTuple

import pytest

from datp.artifacts.paths import ExperimentLocator
import torch

from datp.baselines.common.data_loading import TRAINING_SPLITS, load_client_data
from datp.baselines.common.calibration_eligibility import (
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
from datp.evaluation.metrics import EvaluationResult, evaluate_baseline
from datp.training.protocols.fedavg import run_fl_training

pytestmark = [pytest.mark.e2e]

_N_MIN = 5
_SEED = 0


class DiagnosticEvaluationContext(NamedTuple):
    client_errors: dict[str, Any]
    tau_global: float
    cfg: Any
    output_dir: Path


def _write_contingency_decision(
    diag_dir: Path,
    eval_b1: EvaluationResult,
    eval_b2: EvaluationResult,
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


def _diagnostic_config():
    base = compose_config(regime=Regime.A, baseline=Baseline.B1, seed=_SEED)
    return base.model_copy(
        update={
            "threshold": base.threshold.model_copy(update={"n_min": _N_MIN}),
            "dataset": base.dataset.model_copy(update={"n_min": _N_MIN}),
            "federation": base.federation.model_copy(
                update={
                    "convergence": base.federation.convergence.model_copy(
                        update={"rounds_max": 2, "rounds_initial": 2}
                    ),
                    "local_epochs": 1,
                }
            ),
        }
    )


def _evaluate_threshold(
    baseline: Baseline,
    context: DiagnosticEvaluationContext,
) -> EvaluationResult:
    threshold = derive_threshold(
        baseline,
        context.client_errors,
        context.cfg.threshold.n_min,
        context.cfg.threshold.q,
        context.tau_global,
        Regime.A,
        threshold_cfg=context.cfg.threshold,
    )
    return evaluate_baseline(
        threshold.client_thresholds,
        ExperimentLocator.for_main(context.output_dir, Regime.A).score(_SEED, None),
        Regime.A,
        _SEED,
        None,
        score_provider=None,
    )


@pytest.fixture()
def diagnostic_artifacts(nbaiot_tiny_raw: Path, tmp_path: Path) -> dict:
    set_seeds(_SEED)

    processed_dir = tmp_path / "processed"
    output_dir = tmp_path / "outputs"
    diag_dir = output_dir / "phase3_diagnostic"

    prepare_nbaiot(
        raw_dir=nbaiot_tiny_raw,
        output_dir=processed_dir,
        n_min=_N_MIN,
        seed=_SEED,
        balanced_test=False,
    )
    prepared_dir = processed_dir

    cfg = _diagnostic_config()
    client_data = load_client_data(
        prepared_dir, device=torch.device("cpu"), splits=TRAINING_SPLITS
    )
    run_fl_training(
        cfg, client_data, _SEED, base_dir=output_dir, prepared_dir=prepared_dir
    )

    client_errors = load_main_cal_errors(Regime.A, _SEED, None, output_dir)
    eligible, _ = identify_eligible(client_errors, n_min=cfg.threshold.n_min)
    client_taus = compute_client_thresholds(client_errors, eligible, q=cfg.threshold.q)
    tau_global = compute_tau_global(client_taus)
    evaluation_context = DiagnosticEvaluationContext(
        client_errors=client_errors,
        tau_global=tau_global,
        cfg=cfg,
        output_dir=output_dir,
    )
    eval_b1 = _evaluate_threshold(Baseline.B1, evaluation_context)
    eval_b2 = _evaluate_threshold(Baseline.B2, evaluation_context)

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
