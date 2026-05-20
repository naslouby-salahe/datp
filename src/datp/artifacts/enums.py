from __future__ import annotations

import enum


class RunState(enum.Enum):
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"
    ABORTED = "ABORTED"
    CORRUPT = "CORRUPT"
