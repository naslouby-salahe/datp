"""Hydra-backed config composition with Pydantic validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any, NoReturn

from hydra import compose as hydra_compose
from hydra import initialize_config_module
from hydra.core.global_hydra import GlobalHydra
from omegaconf import DictConfig, OmegaConf
from pydantic import BaseModel, ConfigDict, ValidationError, model_validator

from datp.config.models import DatpConfig
from datp.core.enums import (
    Baseline,
    Regime,
)
from datp.core.errors import fmt

_CONFIG_MODULE = "datp.conf"
_CONFIG_NAME = "config"


class ComposeError(Exception):
    """Raised when config composition encounters invalid parameters."""


class ComposeRequest(BaseModel):
    """External request to compose an experiment config."""
    model_config = ConfigDict(frozen=True)
    regime: Regime
    baseline: Baseline
    seed: int
    alpha: float | None = None

    @model_validator(mode="before")
    @classmethod
    def preprocess(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Coerce to lowercase for consistent enum parsing.
            if "regime" in data and isinstance(data["regime"], str):
                data["regime"] = data["regime"].lower()
            if "baseline" in data and isinstance(data["baseline"], str):
                data["baseline"] = data["baseline"].lower()
        return data

    @model_validator(mode="after")
    def validate_scientific_constraints(self) -> 'ComposeRequest':
        if self.regime == Regime.C and self.alpha is None:
            raise ValueError(fmt("config", "alpha is required for regime c", "a float", "None"))
        if self.baseline == Baseline.B3 and self.regime != Regime.A:
            raise ValueError(fmt("config", "B3 is only valid for regime a", "regime=a", f"regime={self.regime!r}"))
        if self.baseline == Baseline.B0 and self.regime == Regime.C:
            raise ValueError(fmt("config", "B0 is not valid for regime c", "regime a or b", f"regime={self.regime!r}"))
        return self


def _validate_seed(seed: object) -> int:
    """Return seed as int or raise ComposeError."""
    if isinstance(seed, int):
        return seed
    if isinstance(seed, str) and seed.isdigit():
        return int(seed)
    raise ComposeError(fmt("config", "seed must be an integer", "int", type(seed).__name__))


def _raise_compose_error_from_validation(
    exc: ValidationError,
    regime_input: object,
    baseline_input: object,
) -> NoReturn:
    """Inspect Pydantic ValidationError and raise the appropriate ComposeError."""
    for err in exc.errors():
        if err["type"] == "enum":
            if "regime" in err["loc"]:
                valid_regimes = sorted(r.value for r in Regime)
                raise ComposeError(
                    fmt("config", "Invalid regime", f"one of {valid_regimes}", repr(regime_input))
                ) from exc
            if "baseline" in err["loc"]:
                valid_baselines = sorted(b.value for b in Baseline)
                raise ComposeError(
                    fmt("config", "Invalid baseline", f"one of {valid_baselines}", repr(baseline_input))
                ) from exc
        if err["type"] == "value_error":
            raise ComposeError(err["msg"]) from exc
    raise ComposeError(str(exc)) from exc


def _normalize_request(
    *,
    regime: Regime,
    baseline: Baseline,
    seed: int,
    alpha: float | None,
) -> tuple[Regime, Baseline, int, float | None]:
    seed_value = _validate_seed(seed)
    try:
        req = ComposeRequest.model_validate(
            {"regime": regime, "baseline": baseline, "seed": seed_value, "alpha": alpha}
        )
    except ValidationError as exc:
        _raise_compose_error_from_validation(exc, regime, baseline)
    return req.regime, req.baseline, req.seed, req.alpha


def _compose_hydra_config(*, overrides: list[str]) -> DictConfig:
    GlobalHydra.instance().clear()
    with initialize_config_module(config_module=_CONFIG_MODULE, version_base=None):
        return hydra_compose(
            config_name=_CONFIG_NAME,
            overrides=overrides,
            return_hydra_config=False,
        )


def _validate_resolved_config(cfg: DictConfig) -> DatpConfig:
    resolved = OmegaConf.to_container(cfg, resolve=True, enum_to_str=True)
    if not isinstance(resolved, dict):
        raise ComposeError(
            fmt("config", "Resolved config must be a mapping", "dict", type(resolved).__name__)
        )
    try:
        return DatpConfig.model_validate(resolved)
    except ValidationError as exc:
        raise ComposeError(str(exc)) from exc


def _build_overrides(
    *,
    regime: Regime,
    baseline: Baseline,
    seed: int,
    alpha: float | None,
) -> list[str]:
    overrides = [
        f"regime={regime}",
        f"baseline={baseline}",
        f"seed={seed}",
    ]
    if alpha is not None:
        overrides.append(f"alpha={alpha}")
    return overrides


def _compose_and_validate(
    *,
    regime: Regime,
    baseline: Baseline,
    seed: int,
    alpha: float | None,
) -> tuple[DictConfig, DatpConfig]:
    regime_value, baseline_value, seed_value, alpha_value = _normalize_request(
        regime=regime,
        baseline=baseline,
        seed=seed,
        alpha=alpha,
    )
    cfg = _compose_hydra_config(
        overrides=_build_overrides(
            regime=regime_value,
            baseline=baseline_value,
            seed=seed_value,
            alpha=alpha_value,
        )
    )
    return cfg, _validate_resolved_config(cfg)


def compose_resolved_config(
    *,
    regime: Regime,
    baseline: Baseline,
    seed: int,
    alpha: float | None = None,
) -> DictConfig:
    """Compose the resolved Hydra config and validate it with Pydantic."""
    cfg, _ = _compose_and_validate(
        regime=regime,
        baseline=baseline,
        seed=seed,
        alpha=alpha,
    )
    return cfg


def resolved_config_yaml(cfg: DatpConfig | DictConfig) -> str:
    """Render a resolved config model into canonical YAML text."""
    payload = cfg
    if isinstance(cfg, DatpConfig):
        payload = OmegaConf.create(cfg.model_dump(mode="json"))
    return OmegaConf.to_yaml(payload, resolve=True)


def write_resolved_config(
    cfg: DatpConfig | DictConfig,
    output_dir: Path,
) -> Path:
    """Persist ``resolved_config.yaml`` into ``output_dir``."""
    output_dir.mkdir(parents=True, exist_ok=True)
    dest = output_dir / "resolved_config.yaml"
    dest.write_text(resolved_config_yaml(cfg), encoding="utf-8")
    return dest


def compose_config(
    *,
    regime: Regime,
    baseline: Baseline,
    seed: int,
    alpha: float | None = None,
) -> DatpConfig:
    """Build a validated runtime config from Hydra-composed defaults + overrides."""
    _, cfg = _compose_and_validate(
        regime=regime,
        baseline=baseline,
        seed=seed,
        alpha=alpha,
    )
    return cfg


BASE_CONFIG: DatpConfig = _validate_resolved_config(_compose_hydra_config(overrides=[]))
