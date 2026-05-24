"""Pydantic v2 config models — single source of truth for all scientific defaults.

Every scientific parameter lives here. No module-level constants for
scientific parameters downstream.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from datp.core.enums import (
    Baseline,
    Regime,
)


class SafetyBounds(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    max_batch_size_train: int


class ConvergenceConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    rounds_initial: int
    rounds_max: int
    relative_threshold: float
    window: int
    round_timeout_s: float


class ModelConfig(BaseModel):
    """Autoencoder architecture config.

    ``encoder_dims`` is the canonical layer-width spec: the encoder path's
    hidden-layer dimensions including the bottleneck. The decoder is built
    as the mirror of the encoder inside ``Autoencoder``. There is no full
    symmetric ``layer_widths`` — that dual representation was removed to
    eliminate drift.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)
    input_dim: int
    encoder_dims: list[int]
    lr: float
    epochs: int
    patience: int
    activation: str
    use_bn: bool


class DatasetConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    feature_count: int
    n_min: int
    cap: int
    b0_val_fraction: float
    regime_c_train_fraction: float
    regime_c_cal_fraction: float
    attack_reserve_fraction: float
    nbaiot_balanced_test: bool


class MachineConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    batch_size_train: int = Field(gt=0)
    per_client_ram_gb: float = Field(gt=0)
    reserve_ram_gb: float = Field(ge=0)
    max_concurrent_override: int | None = Field(gt=0, default=None)
    ray_object_store_mb: int = Field(gt=0)
    cache_maxsize: int = Field(gt=0)
    safety_bounds: SafetyBounds


class FederationConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    convergence: ConvergenceConfig
    local_epochs: int


class ThresholdConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    n_min: int
    q: float
    b4_regime_a_mode: Literal["fixed", "silhouette"]
    b4_k_regime_a: int
    b4_k_candidates: list[int]
    b4_n_init: int
    b4_random_state: int


class ExperimentConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    seeds: list[int]
    regime_c_alphas: list[float]
    regime_c_n_clients: int


class StatisticsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    n_bootstrap: int
    ci_level: float
    bootstrap_seed: int
    significance_alpha: float
    # GO if CV(FPR)[B1, Regime A single-seed] > this value (Phase 3 preliminary diagnostic only).
    dispersion_threshold: float


class QualityGateConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    b0_sanity_min: float
    b3_dispersion_threshold: float
    ciciot_homogeneity_threshold: float
    js_divergence_n_bins: int


class StyleConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    dpi: int
    font_size: int
    figsize_single_col: tuple[float, float]
    figsize_double_col: tuple[float, float]
    baseline_colors: dict[Baseline, str]
    baseline_labels: dict[Baseline, str]


class LoggingConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    level: str
    json_format: bool
    max_bytes: int
    backup_count: int
    training_progress_interval: int


class RuntimeConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    lock_timeout_seconds: float
    ray_memory_threshold: float


class TrackingConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    experiment_name: str
    tracking_uri: str


class ReportingConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    figure2_max_points: int
    figure2_rng_seed: int
    metric_tol: float
    style: StyleConfig



class AnalysisConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    q_grid: list[float]
    cal_sweep_n_cal: list[int]
    cal_sweep_n_repeats: int
    cal_sweep_seed_base: int
    tau_shrink_lambdas: list[float]
    fedstats_k_min: float
    fedstats_k_max: float
    fedstats_k_step: float
    fedstats_target_exceedance: float


class DatpConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, protected_namespaces=())

    model: ModelConfig
    dataset: DatasetConfig
    machine: MachineConfig
    federation: FederationConfig
    threshold: ThresholdConfig
    experiment: ExperimentConfig
    statistics: StatisticsConfig
    quality_gates: QualityGateConfig
    reporting: ReportingConfig
    analysis: AnalysisConfig
    runtime: RuntimeConfig
    logging: LoggingConfig
    tracking: TrackingConfig

    regime: Regime | None = None
    baseline: Baseline | None = None
    seed: int | None = None
    alpha: float | None = None

    @model_validator(mode="after")
    def check_input_dim_matches_features(self) -> "DatpConfig":
        if self.model.input_dim != self.dataset.feature_count:
            raise ValueError(
                f"model.input_dim ({self.model.input_dim}) != "
                f"dataset.feature_count ({self.dataset.feature_count})"
            )
        return self

    @model_validator(mode="after")
    def check_n_min_consistent(self) -> "DatpConfig":
        if self.dataset.n_min != self.threshold.n_min:
            raise ValueError(
                f"dataset.n_min ({self.dataset.n_min}) != "
                f"threshold.n_min ({self.threshold.n_min})"
            )
        return self

    @model_validator(mode="after")
    def check_batch_size_within_bounds(self) -> "DatpConfig":
        if self.machine.batch_size_train > self.machine.safety_bounds.max_batch_size_train:
            raise ValueError(
                f"machine.batch_size_train ({self.machine.batch_size_train}) exceeds "
                f"machine.safety_bounds.max_batch_size_train "
                f"({self.machine.safety_bounds.max_batch_size_train})"
            )
        return self
