from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock

import datp.data.paths as data_paths
from datp.artifacts.constants import (
    MANIFEST_FILE,
    SCALER_FILE,
)
from datp.config.compose import BASE_CONFIG
from datp.core.enums import Regime
from datp.data.manifests import create_manifest
from datp.data.splits import Split, filename_for_split
from datp.experiments.stages.prepare_data import PreparedDataRequest, ensure_prepared_data


def _write_raw_file(raw_dir: Path) -> Path:
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_file = raw_dir / "raw.csv"
    raw_file.write_text("x\n1\n")
    return raw_file


def _write_processed_client(prepared_dir: Path) -> None:
    client_dir = prepared_dir / "client_0"
    client_dir.mkdir(parents=True, exist_ok=True)
    for split in Split:
        (client_dir / filename_for_split(split)).write_text("placeholder")
    (client_dir / SCALER_FILE).write_bytes(b"scaler")


def _write_manifest(prepared_dir: Path, raw_dir: Path, raw_file: Path) -> None:
    create_manifest(
        dataset="nbaiot",
        raw_files=[raw_file],
        raw_base_dir=raw_dir,
        metadata={"n_devices": 1, "n_features": 2},
        manifest_path=prepared_dir / MANIFEST_FILE,
    )


def test_existing_processed_data_is_verified_and_reused(
    tmp_path: Path,
    monkeypatch,
) -> None:
    raw_dir = tmp_path / "raw"
    raw_file = _write_raw_file(raw_dir)
    prepared_dir = tmp_path / "processed" / "nbaiot"
    _write_processed_client(prepared_dir)
    _write_manifest(prepared_dir, raw_dir, raw_file)

    prepare = Mock()
    monkeypatch.setattr(
        data_paths, "prepared_root_for_regime", lambda *a, **kw: prepared_dir
    )
    monkeypatch.setattr(data_paths, "processed_root", lambda *a, **kw: prepared_dir)

    result = ensure_prepared_data(
        PreparedDataRequest(
            cfg=BASE_CONFIG,
            regime=Regime.A,
            seed=0,
            nbaiot_raw_dir=raw_dir,
            base_dir=tmp_path,
            alpha=None,
            ciciot_raw_dir=None,
        )
    )

    assert result == prepared_dir
    prepare.assert_not_called()


def test_missing_processed_data_runs_preparation_then_verifies(
    tmp_path: Path,
    monkeypatch,
) -> None:
    raw_dir = tmp_path / "raw"
    raw_file = _write_raw_file(raw_dir)
    prepared_dir = tmp_path / "processed" / "nbaiot"

    def prepare(*, regime, raw_dir, output_dir, **kwargs) -> None:
        assert regime == Regime.A
        _write_processed_client(prepared_dir)
        _write_manifest(prepared_dir, raw_dir, raw_file)

    import datp.experiments.stages.prepare_data as prepare_data_mod

    prepare_mock = Mock(side_effect=prepare)
    monkeypatch.setattr(
        data_paths, "prepared_root_for_regime", lambda *a, **kw: prepared_dir
    )
    monkeypatch.setattr(data_paths, "processed_root", lambda *a, **kw: prepared_dir)
    monkeypatch.setattr(prepare_data_mod, "prepare_regime_data", prepare_mock)

    result = ensure_prepared_data(
        PreparedDataRequest(
            cfg=BASE_CONFIG,
            regime=Regime.A,
            seed=0,
            nbaiot_raw_dir=raw_dir,
            base_dir=tmp_path,
            alpha=None,
            ciciot_raw_dir=None,
        )
    )

    assert result == prepared_dir
    prepare_mock.assert_called_once()
