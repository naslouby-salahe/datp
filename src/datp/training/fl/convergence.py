# SPDX-License-Identifier: Proprietary
"""Convergence criterion: relative change in FedAvg-weighted benign validation loss over last N rounds < threshold."""

from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datp.config.models import DatpConfig

from datp.core.errors import fmt
from datp.core.logging import get_logger

logger = get_logger(__name__)

_MODULE = "training.fl.convergence"


class ConvergenceMonitor:
    def __init__(
        self,
        rounds_initial: int,
        rounds_max: int,
        relative_threshold: float,
        window: int,
    ) -> None:
        if rounds_initial < 1:
            raise ValueError(
                fmt(_MODULE, "rounds_initial must be >= 1", ">= 1", str(rounds_initial))
            )
        if rounds_max < rounds_initial:
            raise ValueError(
                fmt(
                    _MODULE,
                    "rounds_max must be >= rounds_initial",
                    f">= {rounds_initial}",
                    str(rounds_max),
                )
            )
        if window < 2:
            raise ValueError(fmt(_MODULE, "window must be >= 2", ">= 2", str(window)))
        self._rounds_initial = rounds_initial
        self._rounds_max = rounds_max
        self._relative_threshold = relative_threshold
        self._window = window
        self._losses: deque[float] = deque(maxlen=rounds_max)
        self._converged_round: int | None = None
        self._latest_relative_change: float | None = None

    @property
    def converged_round(self) -> int | None:
        return self._converged_round

    @property
    def num_recorded(self) -> int:
        return len(self._losses)

    @property
    def loss_history(self) -> list[float]:
        return list(self._losses)

    @property
    def latest_relative_change(self) -> float | None:
        return self._latest_relative_change

    def record(self, server_round: int, weighted_loss: float) -> None:
        self._losses.append(weighted_loss)
        logger.debug(
            "loss recorded",
            round=server_round,
            weighted_val_loss=weighted_loss,
            n_recorded=len(self._losses),
        )

    def should_stop(self, server_round: int) -> bool:
        """Returns True when rounds_initial met and relative change in last window rounds < threshold, or rounds_max reached."""
        if self._converged_round is not None:
            return True

        if server_round >= self._rounds_max:
            logger.info(
                "reached rounds_max, stopping",
                round=server_round,
                rounds_max=self._rounds_max,
            )
            return True

        if server_round < self._rounds_initial:
            return False

        if len(self._losses) < self._window:
            return False

        recent = list(self._losses)[-self._window :]
        start_loss = recent[0]
        end_loss = recent[-1]

        if abs(start_loss) < 1e-12:
            # Avoid division by near-zero; loss is effectively zero → converged
            rel_change = 0.0
        else:
            rel_change = abs(end_loss - start_loss) / abs(start_loss)
        self._latest_relative_change = rel_change

        if rel_change < self._relative_threshold:
            self._converged_round = server_round
            logger.info(
                "convergence detected",
                round=server_round,
                rel_change=rel_change,
                threshold=self._relative_threshold,
                window=self._window,
            )
            return True

        return False

    @classmethod
    def from_config(cls, cfg: "DatpConfig") -> "ConvergenceMonitor":
        conv = cfg.federation.convergence
        return cls(
            rounds_initial=conv.rounds_initial,
            rounds_max=conv.rounds_max,
            relative_threshold=conv.relative_threshold,
            window=conv.window,
        )
