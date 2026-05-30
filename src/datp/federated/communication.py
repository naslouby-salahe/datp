# SPDX-License-Identifier: Proprietary
"""Threshold calibration communication overhead.

Accounting model: **server-aggregated payload bytes**.
- uplink_bytes = total bytes received by the server from all clients in one round/phase.
- downlink_bytes = total bytes sent by the server to all clients in one round/phase.
All payloads are 32-bit (4-byte) floats.
"""

from __future__ import annotations

from dataclasses import dataclass

from datp.core.enums import CONTROLLED_BASELINES, Baseline
from datp.core.errors import fmt

_BYTES_PER_SCALAR = 4
_MODULE = "training.communication"


@dataclass(frozen=True, slots=True)
class RoundComm:
    round_num: int
    server_uplink_payload_bytes: int
    server_downlink_payload_bytes: int


@dataclass(frozen=True, slots=True)
class ThresholdComm:
    baseline: Baseline
    server_uplink_payload_bytes: int
    server_downlink_payload_bytes: int


def compute_model_bytes(param_count: int) -> int:
    return param_count * _BYTES_PER_SCALAR


def compute_round_comm(
    round_num: int,
    model_bytes: int,
    num_clients: int,
) -> RoundComm:
    return RoundComm(
        round_num=round_num,
        server_uplink_payload_bytes=model_bytes * num_clients,
        server_downlink_payload_bytes=model_bytes * num_clients,
    )


def compute_threshold_comm(
    baseline: Baseline,
    k_eligible: int,
    n_families: int,
) -> ThresholdComm:
    if baseline == Baseline.B1:
        return ThresholdComm(
            baseline=baseline,
            server_uplink_payload_bytes=_BYTES_PER_SCALAR * k_eligible,
            server_downlink_payload_bytes=_BYTES_PER_SCALAR * k_eligible,
        )
    if baseline == Baseline.B2:
        # B2 computes the per-client threshold locally from calibration scores — no inter-client
        # threshold communication is required; each client applies only its own quantile.
        return ThresholdComm(
            baseline=baseline,
            server_uplink_payload_bytes=0,
            server_downlink_payload_bytes=0,
        )
    if baseline == Baseline.B3:
        return ThresholdComm(
            baseline=baseline,
            server_uplink_payload_bytes=_BYTES_PER_SCALAR * k_eligible,
            server_downlink_payload_bytes=_BYTES_PER_SCALAR * n_families,
        )
    if baseline == Baseline.B4:
        # B4 uplink: each eligible client uploads its 4-dimensional fingerprint
        # [mean_e, std_e, skew_e, p95_e] = 4 floats per client.
        # B4 downlink: server returns 2 floats per eligible client (cluster assignment
        # + cluster-level threshold).
        return ThresholdComm(
            baseline=baseline,
            server_uplink_payload_bytes=4 * _BYTES_PER_SCALAR * k_eligible,
            server_downlink_payload_bytes=2 * _BYTES_PER_SCALAR * k_eligible,
        )
    raise ValueError(
        fmt(
            _MODULE,
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
    for bl in CONTROLLED_BASELINES:
        tc = compute_threshold_comm(bl, k_eligible, n_families)
        threshold_comms[bl] = {
            "server_uplink_payload_bytes": tc.server_uplink_payload_bytes,
            "server_downlink_payload_bytes": tc.server_downlink_payload_bytes,
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
