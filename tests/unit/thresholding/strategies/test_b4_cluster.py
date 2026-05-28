from __future__ import annotations

import numpy as np
import pytest

from datp.thresholding.strategies.b4_cluster import compute
from datp.core.enums import Regime


def _make_errors(n: int, seed: int = 0) -> np.ndarray:
    return np.random.default_rng(seed).exponential(scale=0.3, size=n).astype(np.float32)


@pytest.fixture()
def eligible_errors() -> dict[str, np.ndarray]:
    rng = np.random.default_rng(42)
    errors: dict[str, np.ndarray] = {
        f"c{i}": rng.exponential(scale=0.2 + i * 0.15, size=200).astype(np.float32)
        for i in range(5)
    }
    errors["pending"] = _make_errors(10, seed=99)
    return errors


N_MIN = 100


class TestB4FixedMode:
    def test_fixed_k3_returns_k3(self, eligible_errors: dict[str, np.ndarray]) -> None:
        result = compute(
            eligible_errors,
            n_min=N_MIN,
            tau_global=0.5,
            regime=Regime.A,
            q=0.95,
            random_state=42,
            k_regime_a=3,
            k_candidates=[2, 3, 4, 5],
            n_init=10,
        )
        assert result.b4_metadata is not None
        assert result.b4_metadata.k == 3

    def test_fixed_k_pending_excluded(
        self, eligible_errors: dict[str, np.ndarray]
    ) -> None:
        result = compute(
            eligible_errors,
            n_min=N_MIN,
            tau_global=0.5,
            regime=Regime.A,
            q=0.95,
            random_state=42,
            k_regime_a=3,
            k_candidates=[2, 3, 4, 5],
            n_init=10,
        )
        assert result.b4_metadata is not None
        assert "pending" not in result.b4_metadata.fingerprints


class TestB4SilhouetteMode:
    def test_silhouette_selects_valid_k(
        self, eligible_errors: dict[str, np.ndarray]
    ) -> None:
        result = compute(
            eligible_errors,
            n_min=N_MIN,
            tau_global=0.5,
            regime=Regime.A,
            q=0.95,
            random_state=42,
            k_regime_a=0,
            k_candidates=[2, 3, 4, 5],
            n_init=10,
        )
        assert result.b4_metadata is not None
        assert result.b4_metadata.k in {2, 3, 4, 5}

    def test_silhouette_scores_non_empty(
        self, eligible_errors: dict[str, np.ndarray]
    ) -> None:
        result = compute(
            eligible_errors,
            n_min=N_MIN,
            tau_global=0.5,
            regime=Regime.A,
            q=0.95,
            random_state=42,
            k_regime_a=0,
            k_candidates=[2, 3, 4],
            n_init=10,
        )
        assert result.b4_metadata is not None
        assert len(result.b4_metadata.silhouette_scores) > 0

    def test_invalid_k_skipped(self) -> None:
        errors = {f"c{i}": _make_errors(200, seed=i) for i in range(3)}
        result = compute(
            errors,
            n_min=N_MIN,
            tau_global=0.5,
            regime=Regime.B,
            q=0.95,
            random_state=42,
            k_regime_a=0,
            k_candidates=[2, 3, 100],  # k=100 >= n_eligible=3, will be skipped
            n_init=10,
        )
        assert result.b4_metadata is not None
        assert result.b4_metadata.k in {2, 3}


class TestB4FingerprintRobustness:
    def test_constant_errors_skew_is_zero(self) -> None:
        from datp.thresholding.strategies.b4_cluster import compute_fingerprints

        errors = {
            "c0": np.full(200, 0.5, dtype=np.float32),
            "c1": np.full(200, 0.3, dtype=np.float32),
        }
        fps = compute_fingerprints(errors, ["c0", "c1"], q=0.95)
        for cid, fp in fps.items():
            assert np.isfinite(fp).all(), (
                f"fingerprint for {cid} contains NaN/inf: {fp}"
            )
            # skew is the 3rd element (index 2)
            assert fp[2] == pytest.approx(0.0), (
                f"skew for {cid} should be 0.0, got {fp[2]}"
            )

    def test_near_constant_errors_finite_fingerprint(self) -> None:
        from datp.thresholding.strategies.b4_cluster import compute_fingerprints

        rng = np.random.default_rng(0)
        errors = {
            "c0": np.full(200, 0.01, dtype=np.float32)
            + rng.standard_normal(200).astype(np.float32) * 1e-7,
            "c1": np.full(200, 0.05, dtype=np.float32)
            + rng.standard_normal(200).astype(np.float32) * 1e-7,
        }
        fps = compute_fingerprints(errors, ["c0", "c1"], q=0.95)
        for cid, fp in fps.items():
            assert np.isfinite(fp).all(), (
                f"fingerprint for {cid} contains NaN/inf: {fp}"
            )

    def test_constant_errors_do_not_block_compute(self) -> None:
        from datp.thresholding.strategies.b4_cluster import (
            compute_fingerprints,
            _validate_fingerprint_matrix,
        )

        errors = {
            "c0": np.full(200, 0.5, dtype=np.float32),
            "c1": np.full(200, 0.5, dtype=np.float32),  # identical to c0
        }
        fps = compute_fingerprints(errors, ["c0", "c1"], q=0.95)
        fp_matrix = np.array([fps["c0"], fps["c1"]])
        # All identical → degenerate, should raise ValueError but not NaN-related
        with pytest.raises(ValueError, match="Degenerate fingerprints"):
            _validate_fingerprint_matrix(fp_matrix)

    def test_pending_client_excluded_from_fingerprints(self) -> None:
        from datp.thresholding.strategies.b4_cluster import compute_fingerprints

        errors = {
            "eligible": np.random.default_rng(0)
            .exponential(0.3, size=200)
            .astype(np.float32),
            "pending": _make_errors(5, seed=99),  # 5 samples < n_min=100 → pending
        }
        fps = compute_fingerprints(errors, ["eligible"], q=0.95)
        assert "pending" not in fps
        assert "eligible" in fps

    def test_one_eligible_client_raises_before_clustering(self) -> None:
        errors = {
            "only_one": np.random.default_rng(0)
            .exponential(0.3, size=200)
            .astype(np.float32)
        }
        with pytest.raises(ValueError, match="Cannot cluster"):
            compute(
                errors,
                n_min=N_MIN,
                tau_global=0.5,
                regime=Regime.B,
                q=0.95,
                random_state=42,
                k_regime_a=0,
                k_candidates=[2, 3],
                n_init=10,
            )

    def test_calibration_pending_uses_tau_global(self) -> None:
        rng = np.random.default_rng(42)
        errors: dict[str, np.ndarray] = {
            f"c{i}": rng.exponential(scale=0.2 + i * 0.15, size=200).astype(np.float32)
            for i in range(4)
        }
        errors["pending"] = _make_errors(10, seed=99)
        tau_global = 0.99

        result = compute(
            errors,
            n_min=N_MIN,
            tau_global=tau_global,
            regime=Regime.B,
            q=0.95,
            random_state=42,
            k_regime_a=0,
            k_candidates=[2, 3],
            n_init=10,
        )
        pending_ct = next(
            ct for ct in result.client_thresholds if ct.calibration_pending
        )
        assert pending_ct.threshold == pytest.approx(tau_global)
