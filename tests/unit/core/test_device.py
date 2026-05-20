from __future__ import annotations

from unittest.mock import patch

import pytest
import torch

from datp.core.device import get_device


class TestGetDevice:
    def test_returns_cuda_device_when_available(self):
        device = get_device()
        assert device == torch.device("cuda")

    def test_raises_when_cuda_unavailable(self):
        with patch("datp.core.device.torch.cuda.is_available", return_value=False):
            with pytest.raises(RuntimeError, match="CUDA is required"):
                get_device()

    def test_error_message_format(self):
        with patch("datp.core.device.torch.cuda.is_available", return_value=False):
            with pytest.raises(RuntimeError, match="Expected.*Got"):
                get_device()
