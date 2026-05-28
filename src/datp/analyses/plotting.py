"""Shared plotting functions for DATP analyses."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from matplotlib.axes import Axes
from matplotlib.figure import Figure

__all__ = ["plt", "saved_figure"]


@contextmanager
def saved_figure(
    path: Path,
    *,
    figsize: tuple[float, float],
    dpi: int = 150,
    savefig_kwargs: Mapping[str, Any] | None = None,
) -> Iterator[tuple[Figure, Axes]]:
    """Yield ``(fig, ax)``, then save and close the figure."""
    fig, ax = plt.subplots(figsize=figsize)
    try:
        yield fig, ax
        fig.tight_layout()
        fig.savefig(path, dpi=dpi, **(dict(savefig_kwargs or {})))
    finally:
        plt.close(fig)
