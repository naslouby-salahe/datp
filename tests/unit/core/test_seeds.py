import random

import numpy as np
import torch

from datp.core.seeds import set_seeds


def test_set_seeds_makes_python_random_deterministic() -> None:
    set_seeds(0)
    first = [random.random() for _ in range(8)]
    set_seeds(0)
    second = [random.random() for _ in range(8)]
    assert first == second


def test_set_seeds_makes_numpy_deterministic() -> None:
    set_seeds(0)
    first = np.random.rand(4)
    set_seeds(0)
    second = np.random.rand(4)
    assert np.array_equal(first, second)


def test_set_seeds_makes_torch_deterministic() -> None:
    set_seeds(0)
    first = torch.randn(4)
    set_seeds(0)
    second = torch.randn(4)
    assert torch.equal(first, second)


def test_set_seeds_sets_cudnn_flags() -> None:
    set_seeds(0)
    assert torch.backends.cudnn.deterministic is True
    assert torch.backends.cudnn.benchmark is False
