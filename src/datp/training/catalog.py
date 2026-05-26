# SPDX-License-Identifier: Proprietary
"""TrainingClientCatalog — single source of truth for client identity during training."""

from __future__ import annotations

from pathlib import Path

import torch

from datp.artifacts.constants import SCALER_FILE
from datp.baselines.common.data_loading import ALL_SPLITS, discover_client_dirs, load_client_data
from datp.core.errors import fmt
from datp.data.splits import Split, filename_for_split
from datp.training.types import ClientData

_MODULE = "training.catalog"


class TrainingClientCatalog:
    """Discovers and validates the deterministic ordered list of client IDs.

    Works in two modes:
      - prepared_dir mode: discovers client IDs from on-disk directories.
      - in-memory mode: extracts client IDs from the provided client_data dict.

    At least one source must be non-empty. When both are provided, the prepared_dir
    source wins (in-memory data is used only for scoring afterward).
    """

    def __init__(
        self,
        *,
        client_data: dict[str, ClientData] | None = None,
        prepared_dir: Path | None = None,
    ) -> None:
        self._prepared_dir = prepared_dir
        if prepared_dir is not None:
            dirs = discover_client_dirs(prepared_dir)
            if not dirs:
                raise ValueError(
                    fmt(
                        _MODULE,
                        "prepared_dir contains no client directories",
                        "at least one client directory",
                        f"empty: {prepared_dir}",
                    )
                )
            self._client_ids = sorted(d.name for d in dirs)
        elif client_data:
            self._client_ids = sorted(client_data.keys())
        else:
            raise ValueError(
                fmt(
                    _MODULE,
                    "No client source provided",
                    "non-empty client_data or valid prepared_dir",
                    "both None/empty",
                )
            )

    @property
    def client_ids(self) -> list[str]:
        return list(self._client_ids)

    @property
    def num_clients(self) -> int:
        return len(self._client_ids)

    @property
    def prepared_dir(self) -> Path | None:
        return self._prepared_dir

    def validate_against(self, client_data: dict[str, ClientData]) -> None:
        """Verify that in-memory client_data keys match the catalog."""
        data_ids = sorted(client_data.keys())
        if data_ids != self._client_ids:
            raise ValueError(
                fmt(
                    _MODULE,
                    "client_data keys do not match catalog",
                    f"keys={self._client_ids}",
                    f"keys={data_ids}",
                )
            )

    def validate_prepared_splits(self) -> None:
        """Validate that all required split files exist for every client in prepared_dir."""
        if self._prepared_dir is None:
            return
        required = tuple(filename_for_split(s) for s in Split) + (SCALER_FILE,)
        for cid in self._client_ids:
            client_dir = self._prepared_dir / cid
            if not client_dir.is_dir():
                raise FileNotFoundError(
                    fmt(
                        _MODULE,
                        f"Client directory missing: {cid}",
                        f"directory at {client_dir}",
                        "not found",
                    )
                )
            missing = [name for name in required if not (client_dir / name).exists()]
            if missing:
                raise FileNotFoundError(
                    fmt(
                        _MODULE,
                        f"Missing prepared artifacts for {cid}",
                        ", ".join(required),
                        f"missing: {', '.join(missing)}",
                    )
                )

    def validate_feature_dim(self, expected_dim: int) -> None:
        """Validate feature dimension of prepared data by sampling the first client's train split."""
        if self._prepared_dir is None:
            return
        if not self._client_ids:
            return
        first_cid = self._client_ids[0]
        train_path = self._prepared_dir / first_cid / filename_for_split(Split.TRAIN)
        if not train_path.exists():
            raise FileNotFoundError(
                fmt(
                    _MODULE,
                    f"Cannot validate feature dim: train file missing for {first_cid}",
                    str(train_path),
                    "not found",
                )
            )
        import polars as pl

        df = pl.read_parquet(train_path)
        actual_dim = df.width
        if actual_dim != expected_dim:
            raise ValueError(
                fmt(
                    _MODULE,
                    f"Feature dimension mismatch for {first_cid}",
                    f"expected_dim={expected_dim}",
                    f"actual_dim={actual_dim}",
                )
            )

    def load_scoring_data(self, device: torch.device) -> dict[str, ClientData]:
        """Load all splits for scoring from prepared_dir or raise if not available."""
        if self._prepared_dir is None:
            raise ValueError(
                fmt(_MODULE, "Cannot load scoring data without prepared_dir", "prepared_dir set", "None")
            )
        return load_client_data(self._prepared_dir, device=device, splits=ALL_SPLITS)
