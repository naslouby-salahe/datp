"""Atomic write of per-client confusion matrices; Regime C filenames include alpha to prevent cross-alpha overwriting."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from datp.artifacts.directories import CONFUSION_MATRICES_DIR
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
    cm_dir = base_dir / CONFUSION_MATRICES_DIR / eval_result.regime

    filename = f"{eval_result.baseline}_seed{eval_result.seed}"
    if eval_result.alpha is not None:
        filename += f"_alpha{eval_result.alpha}"
    filename += ".json"

    out_path = cm_dir / filename
    out_path.parent.mkdir(parents=True, exist_ok=True)

    full = eval_result.model_dump()
    payload = {k: full[k] for k in _PAYLOAD_KEYS}
    payload[PER_CLIENT_KEY] = [
        {k: cm[k] for k in _CM_KEYS}
        for cm in full["per_client"]
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
