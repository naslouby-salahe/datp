"""Unit tests for shared analysis runner helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from datp.analyses.common.runners import analysis_runner


def test_analysis_runner_resolves_base_dir_and_passes_config(tmp_path: Path) -> None:
    config = object()
    seen: dict[str, Any] = {}

    @analysis_runner()
    def run(base_dir: Path, *, config: object, marker: str) -> str:
        seen["base_dir"] = base_dir
        seen["config"] = config
        seen["marker"] = marker
        return "ok"

    result = run(tmp_path, config=config, marker="value")

    assert result == "ok"
    assert seen == {
        "base_dir": tmp_path.resolve(),
        "config": config,
        "marker": "value",
    }


def test_analysis_runner_calls_writer_when_enabled(tmp_path: Path) -> None:
    calls: list[tuple[str, Path]] = []

    def writer(result: str, base_dir: Path) -> None:
        calls.append((result, base_dir))

    @analysis_runner(writer_func=writer)
    def run(base_dir: Path, *, config: object) -> str:
        assert base_dir == tmp_path.resolve()
        assert config is not None
        return "written"

    assert run(tmp_path, config=object(), write_outputs=True) == "written"
    assert calls == [("written", tmp_path.resolve())]
