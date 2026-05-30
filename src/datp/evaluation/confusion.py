"""Atomic write of per-client confusion matrices; Regime C filenames include alpha to prevent cross-alpha overwriting."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from datp.artifacts.names import ArtifactDir
from datp.evaluation.metric_keys import (
    ALPHA_KEY,
    BASELINE_KEY,
    CLIENT_ID_KEY,
    CONFUSION_MATRIX_KEY,
    COVERAGE_RATIO_KEY,
    PER_CLIENT_KEY,
    REGIME_KEY,
    SEED_KEY,
)
from datp.evaluation.metrics import EvaluationResult

_CM_KEYS = (CLIENT_ID_KEY, CONFUSION_MATRIX_KEY, "n_benign", "n_attack")
_PAYLOAD_KEYS = (BASELINE_KEY, REGIME_KEY, SEED_KEY, ALPHA_KEY, COVERAGE_RATIO_KEY)


def save_confusion_matrices(eval_result: EvaluationResult, base_dir: Path) -> Path:
    base_dir = Path(base_dir)
    cm_dir = base_dir / ArtifactDir.CONFUSION_MATRICES / eval_result.regime

    filename = f"{eval_result.baseline}_seed{eval_result.seed}"
    if eval_result.alpha is not None:
        filename += f"_alpha{eval_result.alpha}"
    filename += ".json"

    out_path = cm_dir / filename
    out_path.parent.mkdir(parents=True, exist_ok=True)

    payload: dict[str, object] = {
        BASELINE_KEY: eval_result.baseline.value,
        REGIME_KEY: eval_result.regime.value,
        SEED_KEY: eval_result.seed,
        ALPHA_KEY: eval_result.alpha,
        COVERAGE_RATIO_KEY: eval_result.coverage_ratio,
    }
    payload[PER_CLIENT_KEY] = [
        {
            CLIENT_ID_KEY: cr.client_id,
            CONFUSION_MATRIX_KEY: {
                "tp": cr.confusion.tp,
                "fp": cr.confusion.fp,
                "tn": cr.confusion.tn,
                "fn": cr.confusion.fn,
            },
            "n_benign": cr.n_benign,
            "n_attack": cr.n_attack,
        }
        for cr in eval_result.clients
    ]

    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    fd, tmp = tempfile.mkstemp(dir=out_path.parent, suffix=".tmp.json")
    try:
        with open(fd, "w", encoding="utf-8") as f:
            f.write(text)
        Path(tmp).replace(out_path)
    except Exception:
        Path(tmp).unlink(missing_ok=True)
        raise

    return out_path
