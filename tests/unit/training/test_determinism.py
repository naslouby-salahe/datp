from __future__ import annotations

from pathlib import Path

import pytest
import ray

# Synthetic / test-only constants — identical to the smoke test (T0-7).
_SMOKE_INPUT_DIM = 8
_SMOKE_HIDDEN_DIM = 4
_SMOKE_N_SAMPLES = 200
_SMOKE_NUM_CLIENTS = 2
_SMOKE_NUM_ROUNDS = 2


def _run_experiment(seed: int | None, run_dir: Path) -> Path:
    import numpy as np
    import torch
    import torch.nn as nn
    from flwr.client import NumPyClient
    from flwr.common import Context, ndarrays_to_parameters
    from flwr.server import ServerConfig
    from flwr.server.strategy import FedAvg
    from flwr.simulation import start_simulation

    from datp.artifacts.markers import write_metrics_atomic
    from datp.core.seeds import set_seeds

    if seed is not None:
        set_seeds(seed)

    # Minimal test-only AE — defined inside the function so Ray workers
    # can pickle the closure without importing the test module.
    class _SmokeAE(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.encoder = nn.Linear(_SMOKE_INPUT_DIM, _SMOKE_HIDDEN_DIM)
            self.decoder = nn.Linear(_SMOKE_HIDDEN_DIM, _SMOKE_INPUT_DIM)

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            return self.decoder(torch.relu(self.encoder(x)))

    def _get_params(model: nn.Module) -> list[np.ndarray]:
        return [p.detach().cpu().numpy() for p in model.parameters()]

    def _set_params(model: nn.Module, params: list[np.ndarray]) -> None:
        with torch.no_grad():
            for p, arr in zip(model.parameters(), params):
                p.copy_(torch.from_numpy(arr))

    client_data = {
        str(i): torch.randn(_SMOKE_N_SAMPLES, _SMOKE_INPUT_DIM)
        for i in range(_SMOKE_NUM_CLIENTS)
    }

    class _SmokeClient(NumPyClient):
        def __init__(self, cid: str) -> None:
            self.cid = cid
            self.model = _SmokeAE()
            self.data = client_data[cid]

        def get_parameters(self, config):
            return _get_params(self.model)

        def fit(self, parameters, config):
            _set_params(self.model, parameters)
            optimizer = torch.optim.SGD(self.model.parameters(), lr=0.01)
            self.model.train()
            for _ in range(1):
                pred = self.model(self.data)
                loss = nn.functional.mse_loss(pred, self.data)
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
            return _get_params(self.model), len(self.data), {}

        def evaluate(self, parameters, config):  # type: ignore[override]
            _set_params(self.model, parameters)
            self.model.eval()
            with torch.no_grad():
                pred = self.model(self.data)
                loss = nn.functional.mse_loss(pred, self.data).item()
            return float(loss), len(self.data), {"loss": float(loss)}

    def client_fn(context: Context):
        cid = str(context.node_config["partition-id"])
        return _SmokeClient(cid).to_client()

    init_model = _SmokeAE()
    initial_params = _get_params(init_model)

    strategy = FedAvg(
        fraction_fit=1.0,
        fraction_evaluate=1.0,
        min_fit_clients=_SMOKE_NUM_CLIENTS,
        min_evaluate_clients=_SMOKE_NUM_CLIENTS,
        min_available_clients=_SMOKE_NUM_CLIENTS,
        initial_parameters=ndarrays_to_parameters(initial_params),
    )

    history = start_simulation(
        client_fn=client_fn,
        num_clients=_SMOKE_NUM_CLIENTS,
        config=ServerConfig(num_rounds=_SMOKE_NUM_ROUNDS),
        strategy=strategy,
        ray_init_args={"num_cpus": 2, "include_dashboard": False},
    )

    # Build metrics dict from history
    metrics = {
        "losses_distributed": [
            {"round": entry[0], "loss": entry[1]}
            for entry in history.losses_distributed  # type: ignore[attr-defined]
        ],
    }

    return write_metrics_atomic(run_dir, metrics)


@pytest.mark.integration
def test_determinism_same_seed_identical_metrics(tmp_path: Path) -> None:
    dir_a = tmp_path / "run_a"
    path_a = _run_experiment(seed=42, run_dir=dir_a)

    ray.shutdown()

    dir_b = tmp_path / "run_b"
    path_b = _run_experiment(seed=42, run_dir=dir_b)

    ray.shutdown()

    bytes_a = path_a.read_bytes()
    bytes_b = path_b.read_bytes()
    assert bytes_a == bytes_b, (
        "metrics.json files differ between two runs with the same seed.\n"
        f"Run A:\n{bytes_a.decode()}\n"
        f"Run B:\n{bytes_b.decode()}"
    )


@pytest.mark.integration
def test_determinism_guard_no_seeds_differ(tmp_path: Path) -> None:
    dir_a = tmp_path / "run_a"
    path_a = _run_experiment(seed=42, run_dir=dir_a)

    ray.shutdown()

    dir_b = tmp_path / "run_b"
    path_b = _run_experiment(seed=99, run_dir=dir_b)

    ray.shutdown()

    bytes_a = path_a.read_bytes()
    bytes_b = path_b.read_bytes()
    assert bytes_a != bytes_b, (
        "metrics.json files are identical despite different seeds — "
        "the determinism test is not sensitive to seed state."
    )
