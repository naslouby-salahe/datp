from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from datp.artifacts.names import ArtifactFile


def serialize_json_payload(data: dict[str, Any] | BaseModel | Any) -> Any:
    if isinstance(data, BaseModel):
        return data.model_dump(mode="json")
    if dataclasses.is_dataclass(data) and not isinstance(data, type):
        return dataclasses.asdict(data)
    return data


def write_json_atomic(path: Path, data: dict[str, Any] | BaseModel) -> Path:
    """Atomically writes JSON via tmp->rename; never pre-creates a placeholder."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    payload = serialize_json_payload(data)
    tmp.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n")
    tmp.replace(path)
    return path


def write_metrics_atomic(run_dir: Path, metrics: Any) -> Path:
    """Atomically writes metrics.json via tmp->rename; never pre-creates a placeholder."""
    return write_json_atomic(run_dir / ArtifactFile.METRICS, metrics)
