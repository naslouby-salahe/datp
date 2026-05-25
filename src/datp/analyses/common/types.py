"""Shared typed models for DATP analyses."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class FrozenModel(BaseModel):
    """Strict, immutable Pydantic base for analysis row and result models."""

    model_config = ConfigDict(extra="forbid", frozen=True)
