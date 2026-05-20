from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


def write_csv(path: Path, records: list[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [record.model_dump(mode="json") if hasattr(record, "model_dump") else record for record in records]
    pd.DataFrame(rows).to_csv(path, index=False)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
