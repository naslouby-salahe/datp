from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from datp.artifacts.constants import (
    MANIFEST_FILE,
    SCALER_FILE,
)
from datp.config.models import DatpConfig
from datp.core.enums import Regime
from datp.core.errors import fmt
from datp.core.logging import get_logger
from datp.data.catalog import DatasetID
from datp.data.common.storage import assert_no_csv_artifacts
from datp.data.datasets.ciciot2023.spec import merged_csv_root
from datp.data.manifests import PartitionManifest
from datp.data.paths import assert_no_root_conflict, prepared_root_for_regime, processed_root, raw_root
from datp.data.regimes.catalog import dataset_for_regime
from datp.data.regimes.prepare import prepare_regime_data
from datp.data.splits import Split, filename_for_split, split_path

logger = get_logger(__name__)

_REQUIRED_CLIENT_ARTIFACTS = tuple(filename_for_split(s) for s in Split) + (SCALER_FILE,)


@dataclass(frozen=True, slots=True)
class PreparedDataRequest:
    regime: Regime
    seed: int
    cfg: DatpConfig
    base_dir: Path
    alpha: float | None = None
    nbaiot_raw_dir: Path | None = None
    ciciot_raw_dir: Path | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.base_dir, Path):
            raise TypeError("PreparedDataRequest.base_dir must be a Path, not implicit")


_VERIFIED: set[tuple[Regime, str, str]] = set()


def ensure_prepared_data(request: PreparedDataRequest) -> Path:
    assert_no_root_conflict(request.base_dir, dataset_for_regime(request.regime))

    prepared_dir = prepared_root_for_regime(
        request.regime, base_dir=request.base_dir, seed=request.seed, alpha=request.alpha,
    )
    manifest_file = prepared_dir / MANIFEST_FILE
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
    _nbaiot_raw = request.nbaiot_raw_dir if request.nbaiot_raw_dir is not None else raw_root(DatasetID.NBAIOT, base_dir=request.base_dir)
    _ciciot_raw = request.ciciot_raw_dir if request.ciciot_raw_dir is not None else raw_root(DatasetID.CICIOT2023, base_dir=request.base_dir)
    raw_dir = _ciciot_raw if request.regime == Regime.B else _nbaiot_raw
    prepare_regime_data(
        regime=request.regime,
        raw_dir=raw_dir,
        output_dir=processed_root(dataset_for_regime(request.regime), base_dir=request.base_dir),
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
    raw_base_dir = _manifest_raw_base_dir(request)
    cache_key = (request.regime, str(prepared_dir), str(raw_base_dir))
    if cache_key in _VERIFIED:
        logger.info("processed data already verified; reusing", prepared_dir=str(prepared_dir))
        return

    manifest = PartitionManifest.load(manifest_file)
    manifest.verify_hashes(raw_base_dir)
    _verify_client_artifacts(prepared_dir)
    assert_no_csv_artifacts(prepared_dir)
    _VERIFIED.add(cache_key)
    logger.info(
        "processed data verified; reusing",
        regime=request.regime,
        seed=request.seed,
        alpha=request.alpha,
        prepared_dir=str(prepared_dir),
    )


def _manifest_raw_base_dir(request: PreparedDataRequest) -> Path:
    if request.regime == Regime.B:
        ciciot_raw = request.ciciot_raw_dir if request.ciciot_raw_dir is not None else raw_root(DatasetID.CICIOT2023, base_dir=request.base_dir)
        return merged_csv_root(ciciot_raw)
    if request.nbaiot_raw_dir is not None:
        return request.nbaiot_raw_dir
    return raw_root(DatasetID.NBAIOT, base_dir=request.base_dir)


def _verify_client_artifacts(prepared_dir: Path) -> None:
    if not prepared_dir.is_dir():
        raise RuntimeError(
            fmt("sweep.data", "Prepared directory missing", str(prepared_dir), "not found")
        )

    client_dirs = sorted(
        d for d in prepared_dir.iterdir()
        if d.is_dir() and split_path(d, Split.TRAIN).exists()
    )
    if not client_dirs:
        raise RuntimeError(
            fmt("sweep.data", "Prepared clients missing", "at least one client directory", "0")
        )

    for client_dir in client_dirs:
        missing = [
            name for name in _REQUIRED_CLIENT_ARTIFACTS
            if not (client_dir / name).exists()
        ]
        if missing:
            raise RuntimeError(
                fmt(
                    "sweep.data",
                    f"Prepared client {client_dir.name} incomplete",
                    ", ".join(_REQUIRED_CLIENT_ARTIFACTS),
                    ", ".join(missing),
                )
            )
