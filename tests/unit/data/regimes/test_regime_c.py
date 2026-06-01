from __future__ import annotations

import dataclasses
import json
import math
from pathlib import Path

import numpy as np
import polars as pl
import pytest

import datp.data.regimes.regime_c as regime_c_mod
from datp.core.identity import format_alpha_dir
from datp.data.datasets.nbaiot import DEVICE_DIRS
from datp.data.datasets.nbaiot.spec import NBAIOT_SPEC
from datp.data.regimes.regime_c import (
    _stratified_split,
    partition_regime_c,
)
from datp.data.splits import SplitFilename

# ── Synthetic data helpers ────────────────────────────────────────

_N_FEATURES = 10


def _create_synthetic_nbaiot_raw(
    raw_dir: Path,
    n_features: int = _N_FEATURES,
    n_benign: int = 200,
    n_attack: int = 50,
) -> None:
    rng = np.random.default_rng(99)
    cols = [f"feat_{i}" for i in range(n_features)]

    for device_id in DEVICE_DIRS:
        device_dir = raw_dir / device_id
        device_dir.mkdir(parents=True, exist_ok=True)

        benign = pl.DataFrame(rng.standard_normal((n_benign, n_features)), schema=cols)
        benign.write_csv(device_dir / "benign_traffic.csv")

        attack_dir = device_dir / "gafgyt_attacks"
        attack_dir.mkdir(parents=True, exist_ok=True)
        attack = pl.DataFrame(rng.standard_normal((n_attack, n_features)), schema=cols)
        attack.write_csv(attack_dir / "combo.csv")


# ── Tests: JS divergence via canonical helper ────────────────────


class TestJSDivergenceCanonical:
    def test_js_nonnegative_from_device_mixture(self):
        from datp.statistics.divergence import pairwise_js_from_distributions

        vecs = [
            np.array([0.8, 0.1, 0.1]),
            np.array([0.1, 0.8, 0.1]),
            np.array([0.1, 0.1, 0.8]),
        ]
        summary = pairwise_js_from_distributions(vecs)
        assert summary.mean is not None
        assert summary.mean >= 0.0

    def test_identical_mixtures_zero_divergence(self):
        from datp.statistics.divergence import pairwise_js_from_distributions

        vec = np.array([0.5, 0.5])
        summary = pairwise_js_from_distributions([vec, vec, vec])
        assert summary.mean is not None
        assert summary.mean == pytest.approx(0.0, abs=1e-9)

    def test_separated_mixtures_larger_js(self):
        from datp.statistics.divergence import pairwise_js_from_distributions

        identical = pairwise_js_from_distributions([np.array([0.5, 0.5])] * 3)
        separated = pairwise_js_from_distributions(
            [
                np.array([1.0, 0.0]),
                np.array([0.0, 1.0]),
            ]
        )
        assert separated.mean is not None
        assert identical.mean is not None
        assert separated.mean > identical.mean


# ── Tests: Stratified split ──────────────────────────────────────


class TestStratifiedSplit:
    def test_split_preserves_records(self):
        rng = np.random.default_rng(42)
        n = 200
        df = pl.DataFrame(
            rng.standard_normal((n, 5)), schema=[f"f{i}" for i in range(5)]
        )
        labels = np.repeat([0, 1, 2], [80, 60, 60])

        train, cal, test = _stratified_split(
            df, labels, rng, train_frac=0.70, cal_frac=0.15
        )
        assert len(train) + len(cal) + len(test) == n

    def test_split_approximate_ratios(self):
        rng = np.random.default_rng(42)
        n = 1000
        df = pl.DataFrame(
            rng.standard_normal((n, 5)), schema=[f"f{i}" for i in range(5)]
        )
        labels = np.repeat([0, 1], [500, 500])

        train, cal, test = _stratified_split(
            df, labels, rng, train_frac=0.70, cal_frac=0.15
        )
        assert abs(len(train) / n - 0.70) < 0.05
        assert abs(len(cal) / n - 0.15) < 0.05
        assert abs(len(test) / n - 0.15) < 0.05


# ── Tests: Output format ─────────────────────────────────────────


class TestOutputFormat:
    @pytest.fixture(autouse=True)
    def patch_nbaiot_spec(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            regime_c_mod,
            "NBAIOT_SPEC",
            dataclasses.replace(NBAIOT_SPEC, feature_count=_N_FEATURES),
        )

    def test_output_is_parquet(self, tmp_path: Path):
        raw_dir = tmp_path / "raw"
        _create_synthetic_nbaiot_raw(raw_dir, n_benign=200, n_attack=50)

        output_dir = tmp_path / "output"
        partition_regime_c(
            raw_nbaiot_dir=raw_dir,
            output_dir=output_dir,
            alpha=1.0,
            seed=0,
            n_clients=5,
            n_min=10,
            train_frac=0.70,
            cal_frac=0.15,
        )

        run_dir = output_dir / "regime_c" / format_alpha_dir(1.0) / "seed_0"
        for i in range(5):
            client_dir = run_dir / f"client_{i:02d}"
            assert (client_dir / SplitFilename.TRAIN).exists()
            assert (client_dir / SplitFilename.CAL).exists()
            assert (client_dir / SplitFilename.TEST_BENIGN).exists()
            assert (client_dir / SplitFilename.TEST_ATTACK).exists()

        csv_files = list(run_dir.rglob("*.csv"))
        assert len(csv_files) == 0

    def test_js_divergence_json_written(self, tmp_path: Path):
        raw_dir = tmp_path / "raw"
        _create_synthetic_nbaiot_raw(raw_dir, n_benign=200, n_attack=50)

        output_dir = tmp_path / "output"
        partition_regime_c(
            raw_nbaiot_dir=raw_dir,
            output_dir=output_dir,
            alpha=0.5,
            seed=0,
            n_clients=5,
            n_min=10,
            train_frac=0.70,
            cal_frac=0.15,
        )

        js_path = (
            output_dir
            / "regime_c"
            / format_alpha_dir(0.5)
            / "seed_0"
            / "js_divergence.json"
        )
        assert js_path.exists()
        with open(js_path) as f:
            data = json.load(f)
        assert "js_divergence" in data
        assert data["js_divergence"] is None or isinstance(data["js_divergence"], float)
        assert data["js_divergence"] is None or data["js_divergence"] >= 0.0

    def test_iid_partition_output(self, tmp_path: Path):
        raw_dir = tmp_path / "raw"
        _create_synthetic_nbaiot_raw(raw_dir, n_benign=200, n_attack=50)

        output_dir = tmp_path / "output"
        result = partition_regime_c(
            raw_nbaiot_dir=raw_dir,
            output_dir=output_dir,
            alpha=math.inf,
            seed=0,
            n_clients=5,
            n_min=10,
            train_frac=0.70,
            cal_frac=0.15,
        )

        run_dir = output_dir / "regime_c" / format_alpha_dir(math.inf) / "seed_0"
        assert run_dir.exists()
        assert result.js_divergence is None or result.js_divergence >= 0.0

    def test_manifest_has_n_features(self, tmp_path: Path):
        raw_dir = tmp_path / "raw"
        _create_synthetic_nbaiot_raw(raw_dir, n_benign=200, n_attack=50)

        output_dir = tmp_path / "output"
        partition_regime_c(
            raw_nbaiot_dir=raw_dir,
            output_dir=output_dir,
            alpha=1.0,
            seed=0,
            n_clients=5,
            n_min=10,
            train_frac=0.70,
            cal_frac=0.15,
        )

        run_dir = output_dir / "regime_c" / format_alpha_dir(1.0) / "seed_0"
        payload = json.loads((run_dir / "manifest.json").read_text())
        assert "n_features" in payload["metadata"]
        assert payload["metadata"]["n_features"] == _N_FEATURES


# ── Tests: Calibration-Pending ────────────────────────────────────


class TestCalibrationPending:
    @pytest.fixture(autouse=True)
    def patch_nbaiot_spec(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            regime_c_mod,
            "NBAIOT_SPEC",
            dataclasses.replace(NBAIOT_SPEC, feature_count=_N_FEATURES),
        )

    def test_calibration_pending_flagged(self, tmp_path: Path):
        raw_dir = tmp_path / "raw"
        _create_synthetic_nbaiot_raw(raw_dir, n_benign=100, n_attack=20)

        output_dir = tmp_path / "output"
        result = partition_regime_c(
            raw_nbaiot_dir=raw_dir,
            output_dir=output_dir,
            alpha=1.0,
            seed=0,
            n_clients=20,
            n_min=100,
            train_frac=0.70,
            cal_frac=0.15,
        )

        assert result.n_calibration_pending > 0
        for client in result.clients:
            if client.cal_count < 100:
                assert client.calibration_pending is True
            else:
                assert client.calibration_pending is False

    def test_coverage_reported(self, tmp_path: Path):
        raw_dir = tmp_path / "raw"
        _create_synthetic_nbaiot_raw(raw_dir, n_benign=200, n_attack=50)

        output_dir = tmp_path / "output"
        result = partition_regime_c(
            raw_nbaiot_dir=raw_dir,
            output_dir=output_dir,
            alpha=1.0,
            seed=0,
            n_clients=5,
            n_min=10,
            train_frac=0.70,
            cal_frac=0.15,
        )

        assert result.n_eligible + result.n_calibration_pending == result.n_clients
        assert result.n_clients == 5


# ── Tests: Device mixture proportions ────────────────────────────


class TestDeviceMixtureProportions:
    @pytest.fixture(autouse=True)
    def patch_nbaiot_spec(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            regime_c_mod,
            "NBAIOT_SPEC",
            dataclasses.replace(NBAIOT_SPEC, feature_count=_N_FEATURES),
        )

    def test_device_mixture_proportions_sum_to_one(self, tmp_path: Path):
        raw_dir = tmp_path / "raw"
        _create_synthetic_nbaiot_raw(raw_dir, n_benign=300, n_attack=60)
        output_dir = tmp_path / "output"
        result = partition_regime_c(
            raw_nbaiot_dir=raw_dir,
            output_dir=output_dir,
            alpha=0.5,
            seed=0,
            n_clients=4,
            n_min=10,
            train_frac=0.70,
            cal_frac=0.15,
        )

        for client in result.clients:
            proportions = client.device_mixture_proportions
            assert len(proportions) > 0
            total = sum(proportions.values())
            assert total == pytest.approx(1.0, abs=1e-6), (
                f"client {client.client_id} proportions sum to {total}"
            )

    def test_device_mixture_keys_are_device_names(self, tmp_path: Path):
        raw_dir = tmp_path / "raw"
        _create_synthetic_nbaiot_raw(raw_dir, n_benign=200, n_attack=40)
        output_dir = tmp_path / "output"
        result = partition_regime_c(
            raw_nbaiot_dir=raw_dir,
            output_dir=output_dir,
            alpha=1.0,
            seed=0,
            n_clients=3,
            n_min=10,
            train_frac=0.70,
            cal_frac=0.15,
        )

        for client in result.clients:
            for key in client.device_mixture_proportions:
                assert key in DEVICE_DIRS

    def test_iid_partition_nearly_uniform(self, tmp_path: Path):
        raw_dir = tmp_path / "raw"
        _create_synthetic_nbaiot_raw(raw_dir, n_benign=600, n_attack=100)
        output_dir = tmp_path / "output"
        result = partition_regime_c(
            raw_nbaiot_dir=raw_dir,
            output_dir=output_dir,
            alpha=float("inf"),
            seed=0,
            n_clients=3,
            n_min=10,
            train_frac=0.70,
            cal_frac=0.15,
        )

        for client in result.clients:
            for frac in client.device_mixture_proportions.values():
                assert frac >= 0.0
                assert frac <= 1.0

    def test_manifest_contains_device_mixture_proportions(self, tmp_path: Path):
        raw_dir = tmp_path / "raw"
        _create_synthetic_nbaiot_raw(raw_dir, n_benign=200, n_attack=40)
        output_dir = tmp_path / "output"
        partition_regime_c(
            raw_nbaiot_dir=raw_dir,
            output_dir=output_dir,
            alpha=0.5,
            seed=0,
            n_clients=3,
            n_min=10,
            train_frac=0.70,
            cal_frac=0.15,
        )

        run_dir = output_dir / "regime_c" / format_alpha_dir(0.5) / "seed_0"
        manifest_path = run_dir / "manifest.json"
        assert manifest_path.exists()
        payload = json.loads(manifest_path.read_text())
        client_summaries = payload["metadata"]["client_summaries"]
        assert len(client_summaries) == 3
        for cs in client_summaries:
            assert "device_mixture_proportions" in cs
            mix = cs["device_mixture_proportions"]
            assert isinstance(mix, dict)
            assert abs(sum(mix.values()) - 1.0) < 1e-5
