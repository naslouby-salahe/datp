from __future__ import annotations

import contextlib
import dataclasses
import json
import traceback
from pathlib import Path
from types import TracebackType
from typing import Any

from pydantic import BaseModel

from datp.artifacts.constants import (
    ABORTED_MARKER,
    DONE_MARKER,
    IN_PROGRESS_MARKER,
    METRICS_FILE,
    METRICS_TMP_FILE,
)
from datp.artifacts.enums import RunState
from datp.core.enums import (
    Baseline,
)


def _get_logger() -> Any:
    """Lazy import to avoid circular dependency with logging setup."""
    from datp.core.logging import get_logger

    return get_logger(__name__)


def check_run_state(run_dir: Path) -> RunState:
    """Absent or conflicting markers → CORRUPT."""
    has_in_progress = (run_dir / IN_PROGRESS_MARKER).exists()
    has_done = (run_dir / DONE_MARKER).exists()
    has_aborted = (run_dir / ABORTED_MARKER).exists()

    marker_count = sum([has_in_progress, has_done, has_aborted])
    if marker_count != 1:
        # No markers at all, or conflicting markers → corrupt
        return RunState.CORRUPT

    if has_done:
        return RunState.DONE
    if has_aborted:
        return RunState.ABORTED
    return RunState.IN_PROGRESS


class RunLifecycle:
    def __init__(
        self,
        run_dir: Path,
        *,
        baseline: Baseline | None = None,
        seed: int | None = None,
    ) -> None:
        self.run_dir = run_dir
        self.baseline = baseline
        self.seed = seed
        self.last_completed_round: int | None = None

    def __enter__(self) -> "RunLifecycle":
        self.run_dir.mkdir(parents=True, exist_ok=True)
        (self.run_dir / ABORTED_MARKER).unlink(missing_ok=True)
        (self.run_dir / IN_PROGRESS_MARKER).touch()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        in_progress_path = self.run_dir / IN_PROGRESS_MARKER

        if exc_type is None:
            in_progress_path.unlink(missing_ok=True)
            (self.run_dir / DONE_MARKER).write_text("Run completed successfully.\n")
        else:
            in_progress_path.unlink(missing_ok=True)
            try:
                self._write_aborted(exc_type, exc_val, exc_tb)
            except Exception as inner:  # noqa: BLE001 - best-effort abort marker
                with contextlib.suppress(Exception):
                    _get_logger().error(
                        "artifacts.abort_marker_write_failed",
                        run_dir=str(self.run_dir),
                        error=str(inner),
                    )

        return False

    def _write_aborted(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        lines = [
            f"last_completed_round: {self.last_completed_round}",
            f"baseline: {str(self.baseline) if self.baseline is not None else 'None'}",
            f"seed: {self.seed}",
            f"exception_type: {exc_type.__name__ if exc_type else 'None'}",
            f"exception_message: {exc_val}",
        ]
        if exc_tb is not None:
            tb_lines = traceback.format_tb(exc_tb)
            lines.append("traceback:")
            lines.extend(f"  {line.rstrip()}" for line in tb_lines)

        (self.run_dir / ABORTED_MARKER).write_text("\n".join(lines) + "\n")


def write_json_atomic(path: Path, data: dict[str, Any] | BaseModel) -> Path:
    """Atomically writes JSON via tmp→rename; never pre-creates a placeholder."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    if isinstance(data, BaseModel):
        payload = data.model_dump(mode="json")
    elif dataclasses.is_dataclass(data) and not isinstance(data, type):
        payload = dataclasses.asdict(data)  # type: ignore[arg-type]
    else:
        payload = data
    tmp.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n")
    tmp.replace(path)
    return path


def write_metrics_atomic(run_dir: Path, metrics: Any) -> Path:
    """Atomically writes metrics.json via tmp→rename; never pre-creates a placeholder."""
    run_dir.mkdir(parents=True, exist_ok=True)
    tmp_path = run_dir / METRICS_TMP_FILE
    final_path = run_dir / METRICS_FILE

    if isinstance(metrics, BaseModel):
        payload = metrics.model_dump(mode="json")
    elif dataclasses.is_dataclass(metrics) and not isinstance(metrics, type):
        payload = dataclasses.asdict(metrics)  # type: ignore[arg-type]
    else:
        payload = metrics

    tmp_path.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n")
    tmp_path.replace(final_path)

    return final_path
