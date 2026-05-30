"""Shared plotting functions for DATP analyses."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import numpy as np

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from matplotlib.axes import Axes
from matplotlib.figure import Figure

__all__ = ["plt", "saved_figure", "saved_scatter"]


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


@contextmanager
def saved_scatter(
    path: Path,
    xs: np.ndarray,
    ys: np.ndarray,
    *,
    xlabel: str,
    ylabel: str,
    title: str,
    figsize: tuple[float, float] = (5, 4),
    alpha: float = 0.7,
    marker_size: float = 40,
    dpi: int = 150,
) -> Iterator[tuple[Figure, Axes]]:
    """Yield ``(fig, ax)`` with a pre-filled scatter plot, then save and close."""
    fig, ax = plt.subplots(figsize=figsize)
    try:
        ax.scatter(xs, ys, alpha=alpha, s=marker_size)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.axhline(y=0, color="gray", linestyle="--", linewidth=0.5)
        ax.axvline(x=0, color="gray", linestyle="--", linewidth=0.5)
        yield fig, ax
        fig.tight_layout()
        fig.savefig(path, dpi=dpi)
    finally:
        plt.close(fig)
