from __future__ import annotations

from collections.abc import Sequence

from datp.core.enums import MAIN_BODY_BASELINES


def validate_main_body_role(baselines: Sequence[str]) -> None:
    for b in baselines:
        if b not in MAIN_BODY_BASELINES:
            raise ValueError(
                f"[reporting] Baseline '{b}' is not permitted in main-body "
                f"figures/tables. "
                f"Allowed: {sorted(b.value for b in MAIN_BODY_BASELINES)}"
            )
