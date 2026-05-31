"""Filesystem and artifact I/O helpers for DATP analyses."""

from __future__ import annotations

import csv
import json
from collections.abc import Mapping, Sequence
from pathlib import Path

import numpy as np
from pydantic import BaseModel

from datp.artifacts.names import ArtifactDir
from datp.validation.constants import CELL_VERDICTS_JSON
from datp.core.enums import ScoringStage
from datp.core.errors import fmt
from datp.scoring.loading import load_parquets_from_dir

from datp.analyses.cells import CellEntry

_MODULE = __name__


def load_cell_verdicts(base_dir: Path) -> list[CellEntry]:
    path = base_dir / ArtifactDir.SCORES / CELL_VERDICTS_JSON
    if not path.is_file():
        raise FileNotFoundError(
            fmt(
                _MODULE,
                f"Cell verdicts not found at {path}",
                "cell_verdicts.json from T04",
                "absent",
            )
        )
    return [
        CellEntry.model_validate(c)
        for c in json.loads(path.read_text(encoding="utf-8"))["cells"]
    ]


def load_cal_errors(score_root: Path) -> dict[str, np.ndarray]:
    return load_parquets_from_dir(
        score_root / ScoringStage.CAL.value, allow_empty=False
    )


def load_test_benign_errors(score_root: Path) -> dict[str, np.ndarray]:
    return load_parquets_from_dir(score_root / ScoringStage.TEST_BENIGN.value)


def ensure_analysis_dir(base_dir: Path) -> Path:
    out = base_dir / ArtifactDir.ANALYSIS
    out.mkdir(parents=True, exist_ok=True)
    return out


def write_analysis_csv(
    base_dir: Path,
    filename: str,
    rows: Sequence[BaseModel],
    row_model: type[BaseModel],
) -> Path:
    """Write analysis CSV to ``<base_dir>/analysis/<filename>``."""
    out_path = ensure_analysis_dir(base_dir) / filename
    fieldnames = list(row_model.model_fields)
    with out_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row.model_dump(mode="json"))
    return out_path


def write_analysis_json(
    base_dir: Path,
    filename: str,
    payload: BaseModel | Mapping[str, object] | Sequence[object],
) -> Path:
    """Write analysis JSON to ``<base_dir>/analysis/<filename>``."""
    out_path = ensure_analysis_dir(base_dir) / filename
    if isinstance(payload, BaseModel):
        text = payload.model_dump_json(indent=2)
    else:
        text = json.dumps(payload, indent=2, default=str)
    out_path.write_text(text, encoding="utf-8")
    return out_path
