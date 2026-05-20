# SPDX-License-Identifier: Proprietary
"""Threshold calibration communication overhead; formulas assume 32-bit (4-byte) float payloads."""

from __future__ import annotations

from dataclasses import dataclass

from datp.core.enums import Baseline
from datp.core.errors import fmt
from datp.core.logging import get_logger

logger = get_logger(__name__)

_BYTES_PER_SCALAR = 4


@dataclass(frozen=True, slots=True)
class RoundComm:
    round_num: int
    uplink_bytes: int
    downlink_bytes: int


@dataclass(frozen=True, slots=True)
class ThresholdComm:
    baseline: Baseline
    uplink_bytes: int
    downlink_bytes: int


def compute_model_bytes(param_count: int) -> int:
    return param_count * _BYTES_PER_SCALAR


def compute_round_comm(
    round_num: int,
    model_bytes: int,
    num_clients: int,
) -> RoundComm:
    """Per-round FL training communication — identical for B1–B4 (fraction_fit=1.0)."""
    return RoundComm(
        round_num=round_num,
        uplink_bytes=model_bytes * num_clients,
        downlink_bytes=model_bytes * num_clients,
    )


def compute_threshold_comm(
    baseline: Baseline,
    k_eligible: int,
    n_families: int,
) -> ThresholdComm:
    if isinstance(baseline, str):
        try:
            baseline = Baseline(baseline.lower())
        except ValueError:
            raise ValueError(
                fmt(
                    "fl.comm",
                    "Unknown baseline for comm overhead",
                    "one of ['b1', 'b2', 'b3', 'b4']",
                    repr(baseline),
                )
            )
    if baseline == Baseline.B1:
        # 1 scalar per eligible client uplink; 1 scalar broadcast downlink
        return ThresholdComm(
            baseline=baseline,
            uplink_bytes=_BYTES_PER_SCALAR * k_eligible,
            downlink_bytes=_BYTES_PER_SCALAR * k_eligible,
        )
    elif baseline == Baseline.B2:
        # Zero uplink, zero downlink (local only)
        return ThresholdComm(
            baseline=baseline,
            uplink_bytes=0,
            downlink_bytes=0,
        )
    elif baseline == Baseline.B3:
        # 1 scalar per eligible client uplink; 1 scalar per family broadcast
        return ThresholdComm(
            baseline=baseline,
            uplink_bytes=_BYTES_PER_SCALAR * k_eligible,
            downlink_bytes=_BYTES_PER_SCALAR * n_families,
        )
    elif baseline == Baseline.B4:
        # 4 scalars uplink (fingerprint); 2 scalars downlink (τ_c + cluster_id)
        return ThresholdComm(
            baseline=baseline,
            uplink_bytes=4 * _BYTES_PER_SCALAR * k_eligible,
            downlink_bytes=2 * _BYTES_PER_SCALAR * k_eligible,
        )
    else:
        raise ValueError(
            fmt(
                "fl.comm",
                "Unknown baseline for comm overhead",
                "one of ['b1', 'b2', 'b3', 'b4']",
                repr(baseline),
            )
        )


def build_comm_summary(
    total_rounds: int,
    model_bytes: int,
    num_clients: int,
    k_eligible: int,
    n_families: int,
) -> dict:
    training_uplink = model_bytes * num_clients * total_rounds
    training_downlink = model_bytes * num_clients * total_rounds

    threshold_comms = {}
    for bl in (Baseline.B1, Baseline.B2, Baseline.B3, Baseline.B4):
        tc = compute_threshold_comm(bl, k_eligible, n_families)
        threshold_comms[bl] = {
            "uplink_bytes": tc.uplink_bytes,
            "downlink_bytes": tc.downlink_bytes,
        }

    return {
        "communication": {
            "training": {
                "model_bytes": model_bytes,
                "total_rounds": total_rounds,
                "num_clients": num_clients,
                "uplink_bytes_per_round": model_bytes * num_clients,
                "downlink_bytes_per_round": model_bytes * num_clients,
                "total_uplink_bytes": training_uplink,
                "total_downlink_bytes": training_downlink,
            },
            "threshold_calibration": threshold_comms,
        }
    }
