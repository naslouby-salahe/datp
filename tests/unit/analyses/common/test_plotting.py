"""Unit tests for shared analysis plotting helpers."""

from __future__ import annotations

from pathlib import Path

from datp.analyses.common.plotting import plt, saved_figure


def test_saved_figure_writes_and_closes_png(tmp_path: Path) -> None:
    out = tmp_path / "figure.png"

    with saved_figure(out, figsize=(2, 2)) as (fig, ax):
        ax.plot([0, 1], [1, 0])
        number = fig.number

    assert out.is_file()
    assert not plt.fignum_exists(number)
