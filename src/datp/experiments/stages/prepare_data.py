from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from datp.artifacts.names import ArtifactFile
from datp.config.models import DatpConfig
from datp.core.enums import Regime
from datp.core.errors import fmt
from datp.core.logging import get_logger
from datp.data.common.storage import assert_no_csv_artifacts
from datp.data.manifests import PartitionManifest
from datp.data.paths import (
    prepared_root_for_regime,
    processed_root,
    raw_root,
)
from datp.data.regimes.catalog import dataset_for_regime
from datp.data.regimes.prepare import prepare_regime_data
from datp.data.splits import Split, filename_for_split, split_path

logger = get_logger(__name__)

_MODULE = "experiments.stages.prepare_data"

_REQUIRED_CLIENT_ARTIFACTS = tuple(filename_for_split(s) for s in Split) + (
    str(ArtifactFile.SCALER),
)


@dataclass(frozen=True, slots=True)
class PreparedDataRequest:
    """Minimal resolved request for ensuring prepared data exists for a (regime, seed, alpha) cell."""

    regime: Regime
    seed: int
    cfg: DatpConfig
    base_dir: Path
    alpha: float | None


def ensure_prepared_data(request: PreparedDataRequest) -> Path:
    prepared_dir = prepared_root_for_regime(
        request.regime,
        base_dir=request.base_dir,
        seed=request.seed,
        alpha=request.alpha,
    )
    manifest_file = prepared_dir / ArtifactFile.MANIFEST
    if manifest_file.exists():
        _verify_existing_prepared_data(request, prepared_dir, manifest_file)
        return prepared_dir

    logger.info(
        "processed data missing; running preparation",
        regime=request.regime,
        seed=request.seed,
        alpha=request.alpha,
        prepared_dir=str(prepared_dir),
    )
    _prepare(request)
    _verify_existing_prepared_data(request, prepared_dir, manifest_file)
    return prepared_dir


def _prepare(request: PreparedDataRequest) -> None:
    cfg = request.cfg
    dataset_id = dataset_for_regime(request.regime)
    raw_dir = raw_root(dataset_id, base_dir=request.base_dir)
    prepare_regime_data(
        regime=request.regime,
        raw_dir=raw_dir,
        output_dir=processed_root(dataset_id, base_dir=request.base_dir),
        n_min=cfg.threshold.n_min,
        seed=request.seed,
        cap=cfg.dataset.cap,
        attack_reserve_fraction=cfg.dataset.attack_reserve_fraction,
        alpha=request.alpha,
        n_clients=cfg.experiment.regime_c_n_clients,
        train_frac=cfg.dataset.regime_c_train_fraction,
        cal_frac=cfg.dataset.regime_c_cal_fraction,
        balanced_test=cfg.dataset.nbaiot_balanced_test,
    )


def _verify_existing_prepared_data(
    request: PreparedDataRequest,
    prepared_dir: Path,
    manifest_file: Path,
) -> None:
    manifest = PartitionManifest.load(manifest_file)
    raw_base_dir = raw_root(
        dataset_for_regime(request.regime), base_dir=request.base_dir
    )
    manifest.verify_hashes(raw_base_dir)
    _verify_client_artifacts(prepared_dir)
    assert_no_csv_artifacts(prepared_dir)
    logger.info(
        "processed data verified; reusing",
        regime=request.regime,
        seed=request.seed,
        alpha=request.alpha,
        prepared_dir=str(prepared_dir),
    )


def _verify_client_artifacts(prepared_dir: Path) -> None:
    if not prepared_dir.is_dir():
        raise RuntimeError(
            fmt(_MODULE, "Prepared directory missing", str(prepared_dir), "not found")
        )

    client_dirs = sorted(
        d
        for d in prepared_dir.iterdir()
        if d.is_dir() and split_path(d, Split.TRAIN).exists()
    )
    if not client_dirs:
        raise RuntimeError(
            fmt(
                _MODULE,
                "Prepared clients missing",
                "at least one client directory",
                "0",
            )
        )

    for client_dir in client_dirs:
        missing = [
            name
            for name in _REQUIRED_CLIENT_ARTIFACTS
            if not (client_dir / name).exists()
        ]
        if missing:
            raise RuntimeError(
                fmt(
                    _MODULE,
                    f"Prepared client {client_dir.name} incomplete",
                    ", ".join(_REQUIRED_CLIENT_ARTIFACTS),
                    ", ".join(missing),
                )
            )
