from __future__ import annotations

import os

import pytest

from datp.config.compose import BASE_CONFIG
from datp.training.fl.resources import (
    derive_max_concurrent,
    ensure_ray_memory_threshold,
    get_ray_memory_threshold,
)


class TestRayMemoryThreshold:
    def test_ray_memory_threshold_value(self) -> None:
        assert (
            get_ray_memory_threshold(BASE_CONFIG.runtime.ray_memory_threshold) == 0.90
        )

    def test_ray_memory_threshold_enforced(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("RAY_memory_usage_threshold", raising=False)
        ensure_ray_memory_threshold(BASE_CONFIG.runtime.ray_memory_threshold)
        assert os.environ["RAY_memory_usage_threshold"] == "0.9"

    def test_ray_memory_threshold_rejects_high(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("RAY_memory_usage_threshold", "0.99")
        with pytest.raises(RuntimeError, match="too high"):
            ensure_ray_memory_threshold(BASE_CONFIG.runtime.ray_memory_threshold)

    def test_ray_memory_threshold_accepts_lower(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("RAY_memory_usage_threshold", "0.85")
        ensure_ray_memory_threshold(
            BASE_CONFIG.runtime.ray_memory_threshold
        )  # should not raise
        assert os.environ["RAY_memory_usage_threshold"] == "0.85"

    def test_ray_memory_threshold_rejects_invalid(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("RAY_memory_usage_threshold", "not-a-number")
        with pytest.raises(RuntimeError, match="not a valid float"):
            ensure_ray_memory_threshold(BASE_CONFIG.runtime.ray_memory_threshold)


# max_concurrent derivation


class TestDeriveMaxConcurrent:
    def test_derive_max_concurrent_from_ram(self) -> None:
        assert derive_max_concurrent(16.0, per_client_ram_gb=0.6, reserve_gb=2.0) == 23

    def test_derive_max_concurrent_low_ram(self) -> None:
        assert derive_max_concurrent(3.0, per_client_ram_gb=0.6, reserve_gb=2.0) == 1

    def test_derive_max_concurrent_never_zero(self) -> None:
        result = derive_max_concurrent(1.0, per_client_ram_gb=0.6, reserve_gb=2.0)
        assert result == 1
        assert result >= 1

    def test_derive_max_concurrent_zero_ram(self) -> None:
        assert derive_max_concurrent(0.0, per_client_ram_gb=0.6, reserve_gb=2.0) == 1

    def test_derive_max_concurrent_rejects_bad_per_client(self) -> None:
        with pytest.raises(ValueError, match="per_client_ram_gb must be > 0"):
            derive_max_concurrent(16.0, per_client_ram_gb=0.0, reserve_gb=2.0)
