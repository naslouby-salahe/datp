"""Validates all experiment cells before any training starts; blocked on first config error."""

from __future__ import annotations

from datp.config.compose import ComposeError, compose_config
from datp.config.models import DatpConfig
from datp.core.identity import BaselineRunId


def validate_sweep(
    cells: list[BaselineRunId],
) -> tuple[list[str], dict[tuple, DatpConfig]]:
    errors: list[str] = []
    configs: dict[tuple, DatpConfig] = {}

    for cell in cells:
        label = cell.label()
        try:
            cfg = compose_config(
                regime=cell.regime,
                baseline=cell.baseline,
                seed=cell.seed,
                alpha=cell.alpha,
            )
            configs[(cell.regime, cell.baseline, cell.seed, cell.alpha)] = cfg
        except ComposeError as exc:
            errors.append(f"{label}: {exc}")

    if errors:
        return errors, {}
    return errors, configs
