from __future__ import annotations

import json
from pathlib import Path

from datp.artifacts.constants import METRICS_FILE
from datp.artifacts.paths import ExperimentLocator
from datp.core.enums import (
    Baseline,
    Regime,
)
from datp.evaluation.artifact_validation import validate_metrics_payload


def results_exist(
    baseline: Baseline,
    regime: Regime,
    seed: int,
    alpha: float | None,
    *,
    base_dir: Path,
) -> bool:
    """True only if metrics.json is valid and per-client entries include confusion_matrix; missing it → stale, reruns cell."""
    rp = ExperimentLocator.for_main(base_dir, regime).result(baseline, seed, alpha)
    metrics_file = rp / METRICS_FILE
    if not (metrics_file.is_file() and metrics_file.stat().st_size > 0):
        return False
    try:
        data = json.loads(metrics_file.read_text())
        violations = validate_metrics_payload(data, module="artifacts.results")
        if violations:
            return False
        per_client = data["per_client"]
        clients: list[object] = (
            list(per_client.values())
            if isinstance(per_client, dict)
            else list(per_client)
        )
        if clients and "confusion_matrix" not in clients[0]:  # type: ignore[operator]
            return False
    except (json.JSONDecodeError, KeyError, IndexError, TypeError, AttributeError):
        return False
    return True
