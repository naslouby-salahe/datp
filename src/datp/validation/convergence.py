from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from datp.artifacts.constants import CONVERGENCE_CURVE_FILE, CONVERGENCE_SUMMARY_FILE
from datp.validation.enums import ConvergenceStatus


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def status_from_convergence(checkpoint: Path) -> ConvergenceStatus:
    return (
        ConvergenceStatus.BLOCKED_PENDING_RUN
        if checkpoint.exists()
        else ConvergenceStatus.MISSING_CHECKPOINT
    )


def convergence_payload(
    checkpoint: Path,
) -> tuple[int | None, float | None, ConvergenceStatus, str | None]:
    ckpt_dir = checkpoint.parent
    summary_path = ckpt_dir / CONVERGENCE_SUMMARY_FILE
    curve_path = ckpt_dir / CONVERGENCE_CURVE_FILE
    if not summary_path.exists():
        return None, None, status_from_convergence(checkpoint), None
    payload = _load_json(summary_path)
    raw_status = payload["convergence_status"]
    try:
        status = ConvergenceStatus(raw_status)
    except ValueError:
        status = ConvergenceStatus.UNKNOWN
    return (
        payload["convergence_round"],
        payload["convergence_criterion_value"],
        status,
        str(curve_path) if curve_path.exists() else None,
    )
