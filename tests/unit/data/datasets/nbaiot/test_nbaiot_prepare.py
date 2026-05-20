from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from datp.data.datasets.nbaiot import (
    SPLIT_RATIOS,
    prepare_nbaiot,
)
from datp.data.datasets.nbaiot.prepare import _compute_split_indices
from datp.data.scaling import apply_scaler, fit_scaler, load_scaler, save_scaler

N_FEATURES = 10  # Reduced feature count for fast synthetic tests.
N_BENIGN = 1000  # Large enough to exercise all splits.
N_ATTACK = 200
_SYNTHETIC_DEVICES = ["SynDev_A", "SynDev_B"]


def _make_synthetic_raw(tmp_path: Path, devices: list[str] | None = None) -> Path:
    devices = devices or _SYNTHETIC_DEVICES
    raw_dir = tmp_path / "raw"

    rng = np.random.RandomState(42)

    for dev in devices:
        dev_dir = raw_dir / dev
        dev_dir.mkdir(parents=True)

        # Benign traffic — with header row (like real N-BaIoT data)
        cols = [f"feat_{i}" for i in range(N_FEATURES)]
        benign = pd.DataFrame(rng.randn(N_BENIGN, N_FEATURES), columns=cols)
        benign.to_csv(dev_dir / "benign_traffic.csv", index=False)

        # Attack traffic — with header (like real N-BaIoT attack files)
        atk_dir = dev_dir / "gafgyt_attacks"
        atk_dir.mkdir()
        for atk_name in ("combo", "junk"):
            atk = pd.DataFrame(rng.randn(N_ATTACK // 2, N_FEATURES), columns=cols)
            atk.to_csv(atk_dir / f"{atk_name}.csv", index=False)

    return raw_dir


class TestSplitIndices:
    def test_ratios_match(self) -> None:
        n = N_BENIGN
        splits = _compute_split_indices(n)

        n_train = splits["train"][1] - splits["train"][0]
        n_gap1 = splits["gap1"][1] - splits["gap1"][0]
        n_cal = splits["cal"][1] - splits["cal"][0]
        n_gap2 = splits["gap2"][1] - splits["gap2"][0]
        n_test = splits["test_benign"][1] - splits["test_benign"][0]

        assert n_train == math.floor(n * 0.60)
        assert n_gap1 == math.floor(n * 0.01)
        assert n_cal == math.floor(n * 0.20)
        assert n_gap2 == math.floor(n * 0.01)
        assert n_test == n - n_train - n_gap1 - n_cal - n_gap2
        assert n_train + n_gap1 + n_cal + n_gap2 + n_test == n

    def test_contiguous_gaps(self) -> None:
        splits = _compute_split_indices(N_BENIGN)

        assert splits["gap1"][0] == splits["train"][1]
        assert splits["cal"][0] == splits["gap1"][1]
        assert splits["gap2"][0] == splits["cal"][1]
        assert splits["test_benign"][0] == splits["gap2"][1]

    def test_no_train_test_overlap(self) -> None:
        splits = _compute_split_indices(N_BENIGN)
        train_set = set(range(*splits["train"]))
        test_set = set(range(*splits["test_benign"]))
        assert len(train_set & test_set) == 0

    def test_no_train_cal_overlap(self) -> None:
        splits = _compute_split_indices(N_BENIGN)
        train_set = set(range(*splits["train"]))
        cal_set = set(range(*splits["cal"]))
        assert len(train_set & cal_set) == 0


class TestPrepareNBaIoT:
    @pytest.fixture()
    def prepared(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> tuple[Path, dict]:
        import dataclasses

        raw_dir = _make_synthetic_raw(tmp_path)
        output_dir = tmp_path / "processed"

        import datp.data.datasets.nbaiot.prepare as nbaiot_mod
        from datp.data.datasets.nbaiot.spec import NBAIOT_SPEC

        # Patch DEVICE_DIRS and NBAIOT_SPEC so prepare_nbaiot works with synthetic 10-feature data
        monkeypatch.setattr(nbaiot_mod, "DEVICE_DIRS", _SYNTHETIC_DEVICES)
        monkeypatch.setattr(
            nbaiot_mod,
            "NBAIOT_SPEC",
            dataclasses.replace(NBAIOT_SPEC, feature_count=N_FEATURES),
        )

        result = prepare_nbaiot(
            raw_dir, output_dir, n_min=100, seed=42, balanced_test=False
        )
        return output_dir, result

    def test_output_is_parquet(self, prepared: tuple[Path, dict]) -> None:
        output_dir, _ = prepared
        for dev in _SYNTHETIC_DEVICES:
            dev_dir = output_dir / dev
            for name in (
                "train.parquet",
                "cal.parquet",
                "test_benign.parquet",
                "test_attack.parquet",
            ):
                p = dev_dir / name
                assert p.exists(), f"Missing artifact: {p}"
                assert p.suffix == ".parquet"
            assert (dev_dir / "scaler.pkl").exists()

    def test_chronological_split_ratios(self, prepared: tuple[Path, dict]) -> None:
        _, result = prepared
        for dev in _SYNTHETIC_DEVICES:
            info = result[dev]
            total_benign = (
                info.benign_train_count + info.benign_cal_count + info.test_benign_count
            )
            # Gaps consume rows too — total benign = N_BENIGN minus gaps
            n_gap1 = math.floor(N_BENIGN * SPLIT_RATIOS["gap1"])
            n_gap2 = math.floor(N_BENIGN * SPLIT_RATIOS["gap2"])
            assert total_benign + n_gap1 + n_gap2 == N_BENIGN

            assert info.benign_train_count == math.floor(N_BENIGN * 0.60)
            assert info.benign_cal_count == math.floor(N_BENIGN * 0.20)

    def test_calibration_above_n_min(self, prepared: tuple[Path, dict]) -> None:
        _, result = prepared
        for dev in _SYNTHETIC_DEVICES:
            assert result[dev].benign_cal_count >= 100
            assert result[dev].calibration_pending is False

    def test_calibration_pending_flagged(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        raw_dir = tmp_path / "raw_tiny"
        dev = "TinyDev"
        dev_dir = raw_dir / dev
        dev_dir.mkdir(parents=True)

        rng = np.random.RandomState(99)
        cols = [f"f{i}" for i in range(N_FEATURES)]
        pd.DataFrame(rng.randn(50, N_FEATURES), columns=cols).to_csv(
            dev_dir / "benign_traffic.csv", index=False
        )
        output_dir = tmp_path / "out_tiny"

        import dataclasses

        import datp.data.datasets.nbaiot.prepare as nbaiot_mod
        from datp.data.datasets.nbaiot.spec import NBAIOT_SPEC

        monkeypatch.setattr(nbaiot_mod, "DEVICE_DIRS", [dev])
        monkeypatch.setattr(
            nbaiot_mod,
            "NBAIOT_SPEC",
            dataclasses.replace(NBAIOT_SPEC, feature_count=N_FEATURES),
        )

        result = prepare_nbaiot(
            raw_dir, output_dir, n_min=100, seed=42, balanced_test=False
        )
        assert result[dev].calibration_pending is True

    def test_attack_in_test_only(self, prepared: tuple[Path, dict]) -> None:
        output_dir, result = prepared
        for dev in _SYNTHETIC_DEVICES:
            dev_dir = output_dir / dev
            train = pd.read_parquet(dev_dir / "train.parquet")
            cal = pd.read_parquet(dev_dir / "cal.parquet")
            test_attack = pd.read_parquet(dev_dir / "test_attack.parquet")

            assert result[dev].test_attack_count == N_ATTACK
            assert len(test_attack) == N_ATTACK

            assert len(train) == result[dev].benign_train_count
            assert len(cal) == result[dev].benign_cal_count

    def test_no_train_test_overlap(self, prepared: tuple[Path, dict]) -> None:
        output_dir, _ = prepared
        for dev in _SYNTHETIC_DEVICES:
            dev_dir = output_dir / dev
            train = pd.read_parquet(dev_dir / "train.parquet")
            test_b = pd.read_parquet(dev_dir / "test_benign.parquet")

            # Merge and check for duplicate rows
            merged = pd.merge(train, test_b, how="inner")
            # It's possible (but unlikely with random data) to have identical rows.
            # The structural guarantee is index-based; for synthetic random data,
            # inner merge being empty is a strong practical check.
            assert len(merged) == 0, (
                f"Train/test_benign overlap in {dev}: {len(merged)} rows"
            )


class TestSplitNonOverlap:
    def test_all_pair_overlaps_empty(self) -> None:
        n = 1000
        splits = _compute_split_indices(n)
        sets = {
            name: set(range(start, end))
            for name, (start, end) in splits.items()
            if name not in ("gap1", "gap2")
        }
        pairs = [("train", "cal"), ("train", "test_benign"), ("cal", "test_benign")]
        for a, b in pairs:
            overlap = sets[a] & sets[b]
            assert len(overlap) == 0, f"{a} ∩ {b} = {len(overlap)} rows"

    def test_contiguous_and_gap_non_overlap(self) -> None:
        n = 1000
        splits = _compute_split_indices(n)
        train_set = set(range(*splits["train"]))
        gap1_set = set(range(*splits["gap1"]))
        cal_set = set(range(*splits["cal"]))
        gap2_set = set(range(*splits["gap2"]))
        test_set = set(range(*splits["test_benign"]))

        assert len(train_set & gap1_set) == 0
        assert len(gap1_set & cal_set) == 0
        assert len(cal_set & gap2_set) == 0
        assert len(gap2_set & test_set) == 0

    def test_all_rows_covered_exactly_once(self) -> None:
        n = 1000
        splits = _compute_split_indices(n)
        all_blocks = (
            set(range(*splits["train"]))
            | set(range(*splits["gap1"]))
            | set(range(*splits["cal"]))
            | set(range(*splits["gap2"]))
            | set(range(*splits["test_benign"]))
        )
        assert all_blocks == set(range(n))


class TestSplitIndicesInResult:
    def test_split_indices_present_in_result(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        raw_dir = _make_synthetic_raw(tmp_path)
        out = tmp_path / "processed"
        import dataclasses

        import datp.data.datasets.nbaiot.prepare as nbaiot_mod
        from datp.data.datasets.nbaiot.spec import NBAIOT_SPEC

        monkeypatch.setattr(nbaiot_mod, "DEVICE_DIRS", _SYNTHETIC_DEVICES)
        monkeypatch.setattr(
            nbaiot_mod,
            "NBAIOT_SPEC",
            dataclasses.replace(NBAIOT_SPEC, feature_count=N_FEATURES),
        )
        result = prepare_nbaiot(raw_dir, out, n_min=100, seed=42, balanced_test=False)
        for dev in _SYNTHETIC_DEVICES:
            si = result[dev].split_indices
            assert si is not None
            for key in ("train", "gap1", "cal", "gap2", "test_benign"):
                assert key in si
                start, end = si[key]
                assert end >= start

    def test_split_indices_in_manifest(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import json

        raw_dir = _make_synthetic_raw(tmp_path)
        out = tmp_path / "processed"
        import dataclasses

        import datp.data.datasets.nbaiot.prepare as nbaiot_mod
        from datp.data.datasets.nbaiot.spec import NBAIOT_SPEC

        monkeypatch.setattr(nbaiot_mod, "DEVICE_DIRS", _SYNTHETIC_DEVICES)
        monkeypatch.setattr(
            nbaiot_mod,
            "NBAIOT_SPEC",
            dataclasses.replace(NBAIOT_SPEC, feature_count=N_FEATURES),
        )
        prepare_nbaiot(raw_dir, out, n_min=100, seed=42, balanced_test=False)
        manifest = json.loads((out / "manifest.json").read_text())
        assert "split_indices" in manifest["metadata"]
        for dev in _SYNTHETIC_DEVICES:
            assert dev in manifest["metadata"]["split_indices"]


class TestBalancedTest:
    def _make_raw_with_few_attacks(self, tmp_path: Path, devices: list[str]) -> Path:
        raw_dir = tmp_path / "raw"
        rng = np.random.RandomState(42)
        cols = [f"feat_{i}" for i in range(N_FEATURES)]
        for dev in devices:
            dev_dir = raw_dir / dev
            dev_dir.mkdir(parents=True)
            pd.DataFrame(rng.randn(N_BENIGN, N_FEATURES), columns=cols).to_csv(
                dev_dir / "benign_traffic.csv", index=False
            )
            atk_dir = dev_dir / "gafgyt_attacks"
            atk_dir.mkdir()
            # Only 10 attack rows so test_benign (≈180) >> test_attack
            pd.DataFrame(rng.randn(10, N_FEATURES), columns=cols).to_csv(
                atk_dir / "small_attack.csv", index=False
            )
        return raw_dir

    def test_balanced_test_produces_equal_counts(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        raw_dir = self._make_raw_with_few_attacks(tmp_path, _SYNTHETIC_DEVICES)
        out = tmp_path / "processed_balanced"
        import dataclasses

        import datp.data.datasets.nbaiot.prepare as nbaiot_mod
        from datp.data.datasets.nbaiot.spec import NBAIOT_SPEC

        monkeypatch.setattr(nbaiot_mod, "DEVICE_DIRS", _SYNTHETIC_DEVICES)
        monkeypatch.setattr(
            nbaiot_mod,
            "NBAIOT_SPEC",
            dataclasses.replace(NBAIOT_SPEC, feature_count=N_FEATURES),
        )
        result = prepare_nbaiot(raw_dir, out, n_min=100, seed=42, balanced_test=True)
        for dev in _SYNTHETIC_DEVICES:
            r = result[dev]
            # test_benign should be subsampled to match test_attack (10 rows)
            assert r.test_attack_count == 10
            assert r.test_benign_count == 10, (
                f"{dev}: balanced test expected benign={r.test_attack_count}, "
                f"got benign={r.test_benign_count}"
            )

    def test_default_is_not_balanced(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        raw_dir = self._make_raw_with_few_attacks(tmp_path, _SYNTHETIC_DEVICES)
        out = tmp_path / "processed_default"
        import dataclasses

        import datp.data.datasets.nbaiot.prepare as nbaiot_mod
        from datp.data.datasets.nbaiot.spec import NBAIOT_SPEC

        monkeypatch.setattr(nbaiot_mod, "DEVICE_DIRS", _SYNTHETIC_DEVICES)
        monkeypatch.setattr(
            nbaiot_mod,
            "NBAIOT_SPEC",
            dataclasses.replace(NBAIOT_SPEC, feature_count=N_FEATURES),
        )
        result = prepare_nbaiot(raw_dir, out, n_min=100, seed=42, balanced_test=False)
        for dev in _SYNTHETIC_DEVICES:
            r = result[dev]
            # Without balancing, benign test >> attack test
            assert r.test_benign_count > r.test_attack_count


class TestScaler:
    def test_scaler_fitted_on_train_only(self, tmp_path: Path) -> None:
        rng = np.random.default_rng(7)
        cols = [f"f{i}" for i in range(5)]
        train_df = pd.DataFrame(rng.standard_normal((200, 5)) * 3 + 10, columns=cols)
        other_df = pd.DataFrame(rng.standard_normal((100, 5)) * 0.5 - 5, columns=cols)

        scaler = fit_scaler(train_df)

        # Scaler mean/std should match train, not other
        np.testing.assert_allclose(
            scaler.mean_, train_df.values.mean(axis=0), atol=1e-10
        )
        np.testing.assert_allclose(
            scaler.scale_, train_df.values.std(axis=0, ddof=0), atol=1e-10
        )

        # Applying to train should give ~zero mean, ~unit std
        scaled_train = apply_scaler(train_df, scaler)
        np.testing.assert_allclose(
            scaled_train.to_numpy().mean(axis=0), 0.0, atol=1e-10
        )
        np.testing.assert_allclose(
            scaled_train.to_numpy().std(axis=0, ddof=0), 1.0, atol=1e-10
        )

        # Applying to other should NOT give zero mean (different distribution)
        scaled_other = apply_scaler(other_df, scaler)
        assert not np.allclose(scaled_other.to_numpy().mean(axis=0), 0.0, atol=0.5)

    def test_scaler_round_trip(self, tmp_path: Path) -> None:
        rng = np.random.default_rng(8)
        cols = [f"f{i}" for i in range(5)]
        train_df = pd.DataFrame(rng.standard_normal((100, 5)), columns=cols)

        scaler = fit_scaler(train_df)
        path = tmp_path / "scaler.pkl"
        save_scaler(scaler, path)
        loaded = load_scaler(path)

        np.testing.assert_allclose(loaded.mean_, scaler.mean_)
        np.testing.assert_allclose(loaded.scale_, scaler.scale_)

    def test_apply_preserves_columns(self) -> None:
        cols = ["alpha", "beta", "gamma"]
        df = pd.DataFrame(np.ones((10, 3)), columns=cols)
        scaler = fit_scaler(df)
        result = apply_scaler(df, scaler)
        assert list(result.columns) == cols
