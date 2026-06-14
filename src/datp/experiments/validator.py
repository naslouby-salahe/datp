"""Validates all experiment cells before any training starts; blocked on first config error."""

from __future__ import annotations

from datp.config.compose import ComposeError, compose_config
from datp.config.models import DatpConfig
from datp.core.identity import BaselineRunId


def validate_sweep(
    cells: list[BaselineRunId],
) -> tuple[list[str], dict[BaselineRunId, DatpConfig]]:
    errors: list[str] = []
    configs: dict[BaselineRunId, DatpConfig] = {}

    for cell in cells:
        label = cell.label()
        try:
            cfg = compose_config(
                regime=cell.regime,
                baseline=cell.baseline,
                seed=cell.seed,
                alpha=cell.alpha,
            )
            configs[cell] = cfg
        except ComposeError as exc:
            errors.append(f"{label}: {exc}")

    if errors:
        return errors, {}
    return errors, configs
