from __future__ import annotations

import os

import pytest
import torch

from datp.config.compose import BASE_CONFIG
from datp.federated.runtime import (
    derive_max_concurrent,
    ensure_ray_memory_threshold,
    resolve_device,
)


class TestRayMemoryThreshold:
    def test_ray_memory_threshold_value(self) -> None:
        assert BASE_CONFIG.runtime.ray_memory_threshold == 0.90

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
        ensure_ray_memory_threshold(BASE_CONFIG.runtime.ray_memory_threshold)
        assert os.environ["RAY_memory_usage_threshold"] == "0.85"

    def test_ray_memory_threshold_rejects_invalid(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("RAY_memory_usage_threshold", "not-a-number")
        with pytest.raises(RuntimeError, match="not a valid float"):
            ensure_ray_memory_threshold(BASE_CONFIG.runtime.ray_memory_threshold)


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


class TestResolveDevice:
    def test_returns_cuda_when_available(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(torch.cuda, "is_available", lambda: True)
        assert resolve_device(require_cuda=True) == torch.device("cuda")

    def test_returns_cpu_when_not_required_even_with_cuda(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(torch.cuda, "is_available", lambda: True)
        assert resolve_device(require_cuda=False) == torch.device("cpu")

    def test_raises_when_cuda_required_but_missing(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(torch.cuda, "is_available", lambda: False)
        with pytest.raises(RuntimeError, match="CUDA required"):
            resolve_device(require_cuda=True)

    def test_falls_back_to_cpu_when_not_required(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(torch.cuda, "is_available", lambda: False)
        assert resolve_device(require_cuda=False) == torch.device("cpu")


class TestDeriveClientResources:
    def test_num_gpus_positive_when_cuda_required(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from datp.federated.runtime import derive_client_resources

        monkeypatch.setattr("datp.federated.runtime.get_available_ram_gb", lambda: 16.0)
        monkeypatch.setattr("os.cpu_count", lambda: 8)
        result = derive_client_resources(
            per_client_ram_gb=1.5,
            reserve_ram_gb=3.5,
            max_concurrent_override=None,
            ray_object_store_mb=256,
            require_cuda=True,
            ray_num_gpus_per_client=0.5,
        )
        assert result["num_gpus"] == 0.5

    def test_num_gpus_zero_when_cpu_mode(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from datp.federated.runtime import derive_client_resources

        monkeypatch.setattr("datp.federated.runtime.get_available_ram_gb", lambda: 16.0)
        monkeypatch.setattr("os.cpu_count", lambda: 8)
        result = derive_client_resources(
            per_client_ram_gb=1.5,
            reserve_ram_gb=3.5,
            max_concurrent_override=None,
            ray_object_store_mb=256,
            require_cuda=False,
            ray_num_gpus_per_client=0.5,
        )
        assert result["num_gpus"] == 0.0

    def test_device_and_resources_agree_cuda(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from datp.federated.runtime import derive_client_resources

        monkeypatch.setattr(torch.cuda, "is_available", lambda: True)
        monkeypatch.setattr("datp.federated.runtime.get_available_ram_gb", lambda: 16.0)
        monkeypatch.setattr("os.cpu_count", lambda: 8)
        device = resolve_device(require_cuda=True)
        resources = derive_client_resources(
            per_client_ram_gb=1.5,
            reserve_ram_gb=3.5,
            max_concurrent_override=None,
            ray_object_store_mb=256,
            require_cuda=True,
            ray_num_gpus_per_client=0.5,
        )
        assert device.type == "cuda"
        assert resources["num_gpus"] > 0

    def test_device_and_resources_agree_cpu(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from datp.federated.runtime import derive_client_resources

        monkeypatch.setattr(torch.cuda, "is_available", lambda: False)
        monkeypatch.setattr("datp.federated.runtime.get_available_ram_gb", lambda: 16.0)
        monkeypatch.setattr("os.cpu_count", lambda: 8)
        device = resolve_device(require_cuda=False)
        resources = derive_client_resources(
            per_client_ram_gb=1.5,
            reserve_ram_gb=3.5,
            max_concurrent_override=None,
            ray_object_store_mb=256,
            require_cuda=False,
            ray_num_gpus_per_client=0.5,
        )
        assert device.type == "cpu"
        assert resources["num_gpus"] == 0.0
