# SPDX-License-Identifier: Proprietary
"""FedRep-AE stress-test: shared encoder (FedAvg), localized decoder heads.

This is NOT Ditto. It is a recognized shared-representation/local-head
personalization family (FedRep style, adapted to the DATP AE architecture).

The client is a stress test only — never added to the Baseline enum.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import torch

from flwr.common import Parameters

from datp.artifacts.constants import DECODER_CHECKPOINT, MODEL_CHECKPOINT
from datp.artifacts.directories import SCORES_DIR
from datp.baselines.common.data_loading import ALL_SPLITS, load_client_data
from datp.config.models import DatpConfig
from datp.core.identity import format_alpha_dir
from datp.data.regimes.catalog import dataset_for_regime
from datp.models.autoencoder import Autoencoder
from datp.training.catalog import TrainingClientCatalog
from datp.training.clients import DatpClient
from datp.training.factories import build_model
from datp.training.local import train_decoder_only, train_local
from datp.training.parameters import get_parameters, set_parameters
from datp.training.runtime import resolve_device
from datp.training.scoring import score_fedrep_clients
from datp.training.simulation import SimClientConfig, TrainingResult, run_fl_simulation
from datp.training.strategies import DatpFedAvg
from datp.training.types import ClientData


class DatpFedRepClient(DatpClient):
    """FedRep-AE: shared encoder aggregated via FedAvg, decoder personalized per-client.

    During local training:
      1. Encoder params are set from the global model.
      2. Phase 1 (decoder head): encoder frozen, decoder trained for local_epochs.
      3. Phase 2 (full model): both encoder + decoder trained for local_epochs.
      4. Only encoder params are returned to the server.

    The decoder never leaves the client — it is the personalization surface.
    After each fit() call the decoder state is saved atomically to
    decoder_ckpt_dir / cid / DECODER_CHECKPOINT so scoring can use the
    personalized model after the FL loop completes.
    """

    def __init__(
        self,
        cid: str,
        model: Autoencoder,
        train_data: torch.Tensor,
        val_data: torch.Tensor,
        cfg: DatpConfig,
        decoder_ckpt_dir: Path,
    ) -> None:
        super().__init__(cid, model, train_data, val_data, cfg)
        self._decoder_ckpt_dir = decoder_ckpt_dir
        self._load_persisted_decoder()

    def _load_persisted_decoder(self) -> None:
        """Load previously saved decoder state if available (cross-round persistence)."""
        decoder_path = self._decoder_ckpt_dir / self.cid / DECODER_CHECKPOINT
        if decoder_path.exists():
            device = next(self.model.parameters()).device
            state = torch.load(decoder_path, map_location=device, weights_only=True)
            self.model.decoder.load_state_dict(state)

    def get_parameters(self, config: dict[str, Any]) -> list[np.ndarray]:  # noqa: ARG002
        """Return only encoder parameters — decoder is local-only."""
        return [p.detach().cpu().numpy() for p in self.model.encoder.parameters()]

    def fit(
        self,
        parameters: list[np.ndarray],
        config: dict[str, Any],  # noqa: ARG002
    ) -> tuple[list[np.ndarray], int, dict[str, Any]]:
        set_parameters(self.model.encoder, parameters)
        self.model.train()

        n_train = len(self.train_data)

        # Phase 1: train decoder only (encoder frozen).
        train_decoder_only(
            self.model,
            self.train_data,
            epochs=self._local_epochs,
            batch_size=self._batch_size,
            lr=self._lr,
        )

        # Phase 2: train full model (encoder + decoder).
        last_loss = train_local(
            self.model,
            self.train_data,
            epochs=self._local_epochs,
            batch_size=self._batch_size,
            lr=self._lr,
        )

        decoder_path = self._decoder_ckpt_dir / self.cid / DECODER_CHECKPOINT
        decoder_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = decoder_path.with_suffix(".pt.tmp")
        torch.save(self.model.decoder.state_dict(), tmp_path)
        tmp_path.rename(decoder_path)

        return (
            get_parameters(self.model.encoder),
            n_train,
            {"train_loss": last_loss},
        )


def run_fedrep_training(
    cfg: DatpConfig,
    client_data: dict[str, ClientData] | None,
    seed: int,
    *,
    alpha: float | None = None,
    base_dir: Path,
    prepared_dir: Path | None = None,
) -> TrainingResult:
    """Run FedRep-AE training for one seed.

    The FL loop aggregates only encoder parameters (FedAvg).
    Each client personalizes its decoder and saves it to a per-client checkpoint.
    After training, per-client models (aggregated encoder + personalized decoder)
    are used to produce score artifacts.
    """
    from datp.core.errors import fmt as _fmt

    regime = cfg.regime
    if regime is None:
        raise ValueError(
            _fmt(
                "training.protocols.fedrep",
                "regime must be set in config",
                "non-null regime",
                repr(regime),
            )
        )

    def _build_strategy(initial_parameters: Parameters, num_clients: int) -> DatpFedAvg:
        return DatpFedAvg.from_config(
            cfg, initial_parameters=initial_parameters, num_clients=num_clients
        )

    ckpt_base = base_dir / "fedrep" / regime.value
    if alpha is not None:
        ckpt_base = ckpt_base / format_alpha_dir(alpha)
    ckpt_dir = ckpt_base / f"seed_{seed}"
    score_base = ckpt_dir / SCORES_DIR

    result = run_fl_simulation(
        cfg,
        client_data,
        seed,
        alpha,
        model_cls=Autoencoder,
        build_strategy=_build_strategy,
        ckpt_dir=ckpt_dir,
        score_base=score_base,
        label=f"FedRep-AE(seed={seed})",
        prepared_dir=prepared_dir,
        client_config=SimClientConfig(
            client_cls=DatpFedRepClient,
            client_extra_kwargs={"decoder_ckpt_dir": ckpt_dir},
            encoder_only=True,
            score_after=False,
        ),
    )

    catalog = TrainingClientCatalog(
        client_data=client_data,
        prepared_dir=prepared_dir,
    )

    device = resolve_device(cfg.machine.require_cuda)
    encoder_state = torch.load(
        ckpt_dir / MODEL_CHECKPOINT, map_location=device, weights_only=True
    )

    scoring_data: dict[str, ClientData]
    if prepared_dir is not None:
        scoring_data = load_client_data(prepared_dir, device=torch.device("cpu"), splits=ALL_SPLITS)
    elif client_data is not None:
        scoring_data = client_data
    else:
        raise ValueError(
            _fmt(
                "training.protocols.fedrep",
                "No scoring data source for FedRep",
                "client_data or prepared_dir",
                "neither",
            )
        )

    client_models: dict[str, Autoencoder] = {}
    for cid in catalog.client_ids:
        decoder_path = ckpt_dir / cid / DECODER_CHECKPOINT
        if not decoder_path.exists():
            raise FileNotFoundError(
                _fmt(
                    "training.protocols.fedrep",
                    f"Decoder checkpoint missing for client {cid}",
                    str(decoder_path),
                    "not found",
                )
            )
        model = build_model(cfg, Autoencoder)
        model.load_state_dict(encoder_state)
        decoder_state = torch.load(
            decoder_path, map_location=device, weights_only=True
        )
        model.decoder.load_state_dict(decoder_state)
        model.to(device)
        model.eval()
        client_models[cid] = model

    scoring_ids = sorted(scoring_data.keys())
    model_ids = sorted(client_models.keys())
    if scoring_ids != model_ids:
        raise ValueError(
            _fmt(
                "training.protocols.fedrep",
                "client_models keys do not match scoring data",
                f"expected={scoring_ids}",
                f"actual={model_ids}",
            )
        )

    regime = result.regime
    score_fedrep_clients(
        client_models=client_models,
        client_data=scoring_data,
        score_base=score_base,
        regime=regime,
        seed=seed,
        alpha=alpha,
        dataset=dataset_for_regime(regime).value,
        checkpoint_path=ckpt_dir / MODEL_CHECKPOINT,
        scoring_batch_size=cfg.machine.scoring_batch_size,
    )

    return result
