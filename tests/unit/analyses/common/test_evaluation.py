"""Unit tests for shared analysis evaluation helpers."""

from __future__ import annotations

import math

import numpy as np

from datp.analyses.common.evaluation import compute_cv


def test_compute_cv_returns_zero_for_single_value() -> None:
    assert compute_cv(np.array([1.0])) == 0.0


def test_compute_cv_returns_zero_for_zero_mean() -> None:
    assert compute_cv(np.array([-1.0, 1.0])) == 0.0


def test_compute_cv_uses_sample_standard_deviation() -> None:
    result = compute_cv(np.array([1.0, 2.0, 3.0]))

    assert math.isclose(result, 0.5)
