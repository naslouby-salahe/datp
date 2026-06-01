from __future__ import annotations

from unittest.mock import patch

import pytest
import torch

from datp.core.device import resolve_device
from datp.core.enums import DeviceType


class TestResolveDevice:
    def test_returns_cuda_when_available_and_required(self) -> None:
        assert resolve_device(require_cuda=True) == torch.device(DeviceType.CUDA)

    def test_returns_cpu_when_not_required_even_with_cuda(self) -> None:
        assert resolve_device(require_cuda=False) == torch.device(DeviceType.CPU)

    def test_raises_when_cuda_required_but_missing(self) -> None:
        with patch("datp.core.device.torch.cuda.is_available", return_value=False):
            with pytest.raises(RuntimeError, match="CUDA required"):
                resolve_device(require_cuda=True)

    def test_falls_back_to_cpu_when_not_required_and_cuda_missing(self) -> None:
        with patch("datp.core.device.torch.cuda.is_available", return_value=False):
            assert resolve_device(require_cuda=False) == torch.device(DeviceType.CPU)

    def test_error_message_uses_fmt_format(self) -> None:
        with patch("datp.core.device.torch.cuda.is_available", return_value=False):
            with pytest.raises(RuntimeError, match=r"\[core\.device\].*Expected.*Got"):
                resolve_device(require_cuda=True)
