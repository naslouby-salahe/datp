# SPDX-License-Identifier: Proprietary
"""FedAvg strategy weighted by local benign dataset size; convergence monitoring."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from flwr.common import (
    EvaluateIns,
    FitIns,
    NDArrays,
    Parameters,
    Scalar,
    parameters_to_ndarrays,
)
from flwr.server.client_proxy import ClientProxy
from flwr.server.strategy import FedAvg

from datp.config.models import DatpConfig
from datp.core.logging import get_logger
from datp.training.convergence import ConvergenceMonitor

logger = get_logger(__name__)

_PROC_SELF_STATUS = Path("/proc/self/status")
_KIB_PER_MIB = 1024
_RSS_UNAVAILABLE = -1.0


def _get_rss_mb() -> float:
    try:
        with _PROC_SELF_STATUS.open() as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1]) / _KIB_PER_MIB
    except (OSError, ValueError):
        return _RSS_UNAVAILABLE
    return _RSS_UNAVAILABLE


class DatpFedAvg(FedAvg):
    def __init__(
        self,
        convergence_monitor: ConvergenceMonitor,
        round_timeout_s: float,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._monitor = convergence_monitor
        self._round_timeout_s = round_timeout_s
        self._round_start_time: float | None = None
        self._stopped = False
        self._latest_parameters: NDArrays | None = None

    @property
    def convergence_monitor(self) -> ConvergenceMonitor:
        return self._monitor

    @property
    def stopped(self) -> bool:
        return self._stopped

    @property
    def latest_parameters(self) -> NDArrays | None:
        return self._latest_parameters

    def aggregate_fit(
        self,
        server_round: int,
        results: list[tuple[ClientProxy, Any]],
        failures: list[tuple[ClientProxy, Any] | BaseException],
    ) -> tuple[Parameters | None, dict[str, Scalar]]:
        if failures:
            raise RuntimeError(
                f"FL round {server_round}: {len(failures)} client(s) failed during fit. "
                f"Full participation required — aborting."
            )
        aggregated = super().aggregate_fit(server_round, results, failures)
        if aggregated is not None:
            params, _ = aggregated
            if params is not None:
                self._latest_parameters = parameters_to_ndarrays(params)
        return aggregated

    def configure_fit(
        self,
        server_round: int,
        parameters: Parameters,
        client_manager: Any,
    ) -> list[tuple[ClientProxy, FitIns]]:
        if self._stopped:
            logger.info("convergence reached, skipping fit", round=server_round)
            return []

        self._round_start_time = time.monotonic()
        return super().configure_fit(server_round, parameters, client_manager)

    def configure_evaluate(
        self,
        server_round: int,
        parameters: Parameters,
        client_manager: Any,
    ) -> list[tuple[ClientProxy, EvaluateIns]]:
        if self._stopped:
            logger.info("convergence reached, skipping evaluate", round=server_round)
            return []

        return super().configure_evaluate(server_round, parameters, client_manager)

    def aggregate_evaluate(
        self,
        server_round: int,
        results: list[tuple[ClientProxy, Any]],
        failures: list[tuple[ClientProxy, Any] | BaseException],
    ) -> tuple[float | None, dict[str, Scalar]]:
        if failures:
            raise RuntimeError(
                f"FL round {server_round}: {len(failures)} client(s) failed during evaluate. "
                f"Full participation required — aborting."
            )
        if not results:
            logger.warning("no evaluate results received", round=server_round)
            return None, {}

        if self._round_start_time is not None:
            elapsed = time.monotonic() - self._round_start_time
            rss_mb = _get_rss_mb()
            logger.info(
                "round complete",
                round=server_round,
                elapsed_s=round(elapsed, 1),
                rss_mb=round(rss_mb, 0),
            )
            if elapsed > self._round_timeout_s:
                logger.warning(
                    "round exceeded timeout",
                    round=server_round,
                    elapsed_s=round(elapsed, 1),
                    timeout_s=self._round_timeout_s,
                )

        total_examples = 0
        weighted_loss_sum = 0.0
        for _client, evaluate_res in results:
            num_examples = evaluate_res.num_examples
            loss = evaluate_res.loss
            weighted_loss_sum += loss * num_examples
            total_examples += num_examples

        if total_examples == 0:
            logger.warning("total_examples=0 in aggregate_evaluate", round=server_round)
            return None, {}

        weighted_loss = weighted_loss_sum / total_examples

        self._monitor.record(server_round, weighted_loss)

        if self._monitor.should_stop(server_round):
            self._stopped = True
            logger.info(
                "convergence signal, requesting stop",
                round=server_round,
                converged_round=self._monitor.converged_round,
            )

        return weighted_loss, {"weighted_val_loss": weighted_loss}

    @classmethod
    def from_config(
        cls,
        cfg: DatpConfig,
        initial_parameters: Parameters,
        num_clients: int,
    ) -> "DatpFedAvg":
        monitor = ConvergenceMonitor.from_config(cfg)
        round_timeout_s = cfg.federation.convergence.round_timeout_s

        return cls(
            convergence_monitor=monitor,
            round_timeout_s=round_timeout_s,
            fraction_fit=1.0,
            fraction_evaluate=1.0,
            min_fit_clients=num_clients,
            min_evaluate_clients=num_clients,
            min_available_clients=num_clients,
            initial_parameters=initial_parameters,
        )
