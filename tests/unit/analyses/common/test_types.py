"""Unit tests for shared analysis model types."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from datp.analyses.common.types import FrozenModel


class ExampleFrozenModel(FrozenModel):
    value: int


def test_frozen_model_forbids_extra_fields() -> None:
    with pytest.raises(ValidationError):
        ExampleFrozenModel.model_validate({"value": 1, "extra": "blocked"})


def test_frozen_model_is_immutable() -> None:
    model = ExampleFrozenModel(value=1)

    with pytest.raises(ValidationError):
        model.value = 2
