# SPDX-License-Identifier: Proprietary
"""Tests for TrainingClientCatalog."""

from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest
import torch

from datp.data.common.storage import write_artifact
from datp.data.splits import Split, filename_for_split
from datp.training.catalog import TrainingClientCatalog
from datp.training.types import ClientData


def _write_client_dir(prepared_dir: Path, name: str) -> None:
    client_dir = prepared_dir / name
    client_dir.mkdir(parents=True)
    df = pl.DataFrame({"f0": [1.0], "f1": [2.0]})
    for split in Split:
        write_artifact(df, client_dir / filename_for_split(split))


def _make_client_data(*names: str) -> dict[str, ClientData]:
    return {
        name: ClientData(
            train=torch.zeros(4, 2),
            val=torch.zeros(2, 2),
            test_benign=torch.zeros(2, 2),
            test_attack=torch.zeros(2, 2),
        )
        for name in names
    }


class TestTrainingClientCatalog:
    def test_from_prepared_dir(self, tmp_path: Path) -> None:
        prepared_dir = tmp_path / "prep"
        _write_client_dir(prepared_dir, "client_b")
        _write_client_dir(prepared_dir, "client_a")

        catalog = TrainingClientCatalog(prepared_dir=prepared_dir)

        assert catalog.client_ids == ["client_a", "client_b"]
        assert catalog.num_clients == 2

    def test_from_client_data(self) -> None:
        data = _make_client_data("z_client", "a_client")

        catalog = TrainingClientCatalog(client_data=data)

        assert catalog.client_ids == ["a_client", "z_client"]
        assert catalog.num_clients == 2

    def test_prepared_dir_takes_precedence(self, tmp_path: Path) -> None:
        prepared_dir = tmp_path / "prep"
        _write_client_dir(prepared_dir, "disk_client")
        data = _make_client_data("memory_client")

        catalog = TrainingClientCatalog(client_data=data, prepared_dir=prepared_dir)

        assert catalog.client_ids == ["disk_client"]

    def test_raises_when_both_none(self) -> None:
        with pytest.raises(ValueError, match="No client source"):
            TrainingClientCatalog()

    def test_raises_when_empty_dict(self) -> None:
        with pytest.raises(ValueError, match="No client source"):
            TrainingClientCatalog(client_data={})

    def test_validate_against_matching(self) -> None:
        data = _make_client_data("a", "b")
        catalog = TrainingClientCatalog(client_data=data)

        catalog.validate_against(data)

    def test_validate_against_mismatch(self) -> None:
        data = _make_client_data("a", "b")
        catalog = TrainingClientCatalog(client_data=data)

        other = _make_client_data("a", "c")
        with pytest.raises(ValueError, match="do not match catalog"):
            catalog.validate_against(other)

    def test_client_ids_returns_copy(self) -> None:
        data = _make_client_data("x")
        catalog = TrainingClientCatalog(client_data=data)

        ids = catalog.client_ids
        ids.append("mutation")
        assert catalog.client_ids == ["x"]
