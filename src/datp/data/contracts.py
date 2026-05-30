from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


@dataclass(frozen=True, slots=True)
class ClientPartitionRecord:
    """Per-client partition summary as a frozen domain contract."""

    client_id: str
    benign_train_count: int
    benign_cal_count: int
    test_benign_count: int
    test_attack_count: int
    calibration_pending: bool
    evaluation_incomplete: bool
    attack_classes: tuple[str, ...]


class PartitionResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    benign_train_count: int
    benign_cal_count: int
    test_benign_count: int
    test_attack_count: int
    calibration_pending: bool
    evaluation_incomplete: bool = False
    attack_classes: list[str] = Field(default_factory=list)
    attack_categories: list[str] = Field(default_factory=list)
    total_benign_pre_cap: Optional[int] = None
    total_attack_pre_cap: Optional[int] = None
    split_indices: Optional[dict[str, tuple[int, int]]] = None


class RegimeCClientSummary(BaseModel):
    model_config = ConfigDict(frozen=True)

    client_id: str
    train_count: int
    cal_count: int
    test_benign_count: int
    test_attack_count: int
    calibration_pending: bool
    device_mixture_proportions: dict[str, float] = Field(default_factory=dict)


class RegimeCResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    alpha: float
    seed: int
    n_clients: int
    js_divergence: float | None
    n_eligible: int
    n_calibration_pending: int
    coverage: str
    clients: list[RegimeCClientSummary]


class RegimeCManifestMetadata(BaseModel):
    """Manifest metadata block consumed by validation audit (datasets.py).

    Mirrors the subset of the Regime C manifest JSON that the audit reads.
    Extra keys present in the manifest (dataset_display_name, n_features,
    alpha, seed) are ignored by Pydantic v2 default behaviour.
    """

    model_config = ConfigDict(frozen=True)

    n_clients: int
    js_divergence: float | None = None
    client_summaries: list[RegimeCClientSummary]
