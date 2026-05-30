"""Atomic write of per-client confusion matrices; Regime C filenames include alpha to prevent cross-alpha overwriting."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from datp.artifacts.names import ArtifactDir
from datp.core.enums import (
    PayloadKey,
)
from datp.evaluation.metrics import EvaluationResult

_CM_KEYS = (PayloadKey.CLIENT_ID, PayloadKey.CONFUSION_MATRIX, "n_benign", "n_attack")
_PAYLOAD_KEYS = (PayloadKey.BASELINE, PayloadKey.REGIME, PayloadKey.SEED, PayloadKey.ALPHA, PayloadKey.COVERAGE_RATIO)


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
        PayloadKey.BASELINE: eval_result.baseline.value,
        PayloadKey.REGIME: eval_result.regime.value,
        PayloadKey.SEED: eval_result.seed,
        PayloadKey.ALPHA: eval_result.alpha,
        PayloadKey.COVERAGE_RATIO: eval_result.coverage_ratio,
    }
    payload[PayloadKey.PER_CLIENT] = [
        {
            PayloadKey.CLIENT_ID: cr.client_id,
            PayloadKey.CONFUSION_MATRIX: {
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
