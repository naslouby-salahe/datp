from __future__ import annotations

import pytest

from datp.core.enums import Regime
from datp.core.identity import TrainingCellId


class TestTrainingCellId:
    def test_label_without_alpha(self) -> None:
        key = TrainingCellId(regime=Regime.A, seed=42, alpha=None)
        label = key.label()
        assert "regime=a" in label
        assert "seed=42" in label
        assert "alpha" not in label

    def test_label_with_alpha(self) -> None:
        key = TrainingCellId(regime=Regime.B, seed=7, alpha=0.5)
        label = key.label()
        assert "regime=b" in label
        assert "seed=7" in label
        assert "alpha=0.5" in label

    def test_label_with_alpha_zero(self) -> None:
        key = TrainingCellId(regime=Regime.C, seed=1, alpha=0.0)
        label = key.label()
        assert "alpha=0" in label

    def test_immutable(self) -> None:
        key = TrainingCellId(regime=Regime.A, seed=42, alpha=None)
        with pytest.raises((AttributeError, TypeError)):
            key.regime = Regime.B  # type: ignore[misc]

    def test_equality(self) -> None:
        k1 = TrainingCellId(regime=Regime.A, seed=1, alpha=0.3)
        k2 = TrainingCellId(regime=Regime.A, seed=1, alpha=0.3)
        assert k1 == k2

    def test_inequality_different_seed(self) -> None:
        k1 = TrainingCellId(regime=Regime.A, seed=1, alpha=None)
        k2 = TrainingCellId(regime=Regime.A, seed=2, alpha=None)
        assert k1 != k2

    def test_alpha_default_is_none(self) -> None:
        key = TrainingCellId(regime=Regime.A, seed=0, alpha=None)
        assert key.alpha is None

    def test_hashable(self) -> None:
        k1 = TrainingCellId(regime=Regime.A, seed=1, alpha=0.5)
        k2 = TrainingCellId(regime=Regime.A, seed=2, alpha=None)
        s: set[TrainingCellId] = {k1, k2}
        assert len(s) == 2

    def test_regime_is_enum(self) -> None:
        key = TrainingCellId(regime=Regime.A, seed=1, alpha=None)
        assert key.regime == Regime.A
