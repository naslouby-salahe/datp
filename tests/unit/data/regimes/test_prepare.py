from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from datp.core.enums import Regime
from datp.data.regimes.prepare import prepare_regime_data


def _default_kwargs(**overrides):
    kwargs = {
        "regime": Regime.A,
        "raw_dir": Path("/tmp/raw"),
        "output_dir": Path("/tmp/out"),
        "n_min": 10,
        "seed": 42,
        "cap": 10000,
        "attack_reserve_fraction": 0.2,
        "alpha": None,
        "n_clients": 5,
        "train_frac": 0.6,
        "cal_frac": 0.2,
        "balanced_test": True,
    }
    kwargs.update(overrides)
    return kwargs


class TestPrepareRegimeDataDispatch:
    def test_dispatches_to_regime_a(self):
        with patch(
            "datp.data.regimes.prepare.prepare_regime_a"
        ) as mock_a, patch(
            "datp.data.regimes.prepare.prepare_regime_b"
        ), patch(
            "datp.data.regimes.prepare.partition_regime_c"
        ), patch(
            "datp.data.regimes.prepare.prepare_regime_d"
        ):
            mock_a.return_value = {}
            result = prepare_regime_data(**_default_kwargs(regime=Regime.A))
            mock_a.assert_called_once()
            assert result == {}

    def test_dispatches_to_regime_b(self):
        with patch(
            "datp.data.regimes.prepare.prepare_regime_a"
        ), patch(
            "datp.data.regimes.prepare.prepare_regime_b"
        ) as mock_b, patch(
            "datp.data.regimes.prepare.partition_regime_c"
        ), patch(
            "datp.data.regimes.prepare.prepare_regime_d"
        ):
            mock_b.return_value = {}
            result = prepare_regime_data(**_default_kwargs(regime=Regime.B))
            mock_b.assert_called_once()
            assert result == {}

    def test_dispatches_to_regime_c(self):
        with patch(
            "datp.data.regimes.prepare.prepare_regime_a"
        ), patch(
            "datp.data.regimes.prepare.prepare_regime_b"
        ), patch(
            "datp.data.regimes.prepare.partition_regime_c"
        ) as mock_c, patch(
            "datp.data.regimes.prepare.prepare_regime_d"
        ):
            mock_c.return_value = Mock()
            result = prepare_regime_data(
                **_default_kwargs(regime=Regime.C, alpha=0.5)
            )
            mock_c.assert_called_once()
            assert result is mock_c.return_value

    def test_dispatches_to_regime_d(self):
        with patch(
            "datp.data.regimes.prepare.prepare_regime_a"
        ), patch(
            "datp.data.regimes.prepare.prepare_regime_b"
        ), patch(
            "datp.data.regimes.prepare.partition_regime_c"
        ), patch(
            "datp.data.regimes.prepare.prepare_regime_d"
        ) as mock_d:
            mock_d.return_value = {}
            result = prepare_regime_data(**_default_kwargs(regime=Regime.D))
            mock_d.assert_called_once()
            assert result == {}


class TestPrepareRegimeDataErrors:
    def test_regime_c_without_alpha_raises_valueerror(self):
        with pytest.raises(ValueError, match="alpha is required for Regime C"):
            prepare_regime_data(**_default_kwargs(regime=Regime.C, alpha=None))

    def test_invalid_regime_raises_valueerror(self):
        with pytest.raises(ValueError, match="Unknown regime"):
            prepare_regime_data(**_default_kwargs(regime="x"))  # type: ignore[arg-type]
