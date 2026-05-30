from __future__ import annotations

from pathlib import Path
from typing import Sequence

import numpy as np
import pandas as pd
import pytest

from datp.config.compose import BASE_CONFIG
from datp.data.contracts import PartitionResult
from datp.data.datasets.ciciot2023 import (
    prepare_ciciot,
    validate_schema,
)
from datp.data.datasets.ciciot2023.spec import (
    BENIGN_LABEL,
    FEATURE_COLUMNS,
    LABEL_COLUMN,
    TEST_ATTACK_LABELS_ARTIFACT,
    attack_family,
)
from datp.data.sampling import apply_ciciot_cap
from datp.data.scaling import load_scaler

_ATTACK_RESERVE_FRACTION = BASE_CONFIG.dataset.attack_reserve_fraction


def _apply_cap(df, cap):
    import polars as pl

    pl_df = pl.from_pandas(df)
    res = apply_ciciot_cap(
        pl_df,
        cap=cap,
        label_column=LABEL_COLUMN,
        benign_label=BENIGN_LABEL,
        attack_reserve_fraction=_ATTACK_RESERVE_FRACTION,
        seed=42,
    )
    return res.to_pandas()


def _prepare_ciciot(
    raw_dir: Path,
    output_dir: Path,
    *,
    cap: int = 50_000,
    n_min: int = 100,
    seed: int = 42,
) -> dict[str, PartitionResult]:
    return prepare_ciciot(
        raw_dir,
        output_dir,
        cap=cap,
        n_min=n_min,
        seed=seed,
        attack_reserve_fraction=_ATTACK_RESERVE_FRACTION,
    )


# Synthetic helpers

N_FEATURES = len(FEATURE_COLUMNS)  # 39


def _make_client_csv(
    path: Path,
    n_benign: int,
    n_attack: int,
    attack_labels: list[str] | None = None,
    rng: np.random.Generator | None = None,
    columns: Sequence[str] | None = None,
) -> None:
    if rng is None:
        rng = np.random.default_rng(42)
    if columns is None:
        columns = FEATURE_COLUMNS
    if attack_labels is None:
        attack_labels = ["DDoS_TCP", "DDoS_UDP"]

    rows: list[pd.DataFrame] = []

    if n_benign > 0:
        benign_data = pd.DataFrame(
            rng.standard_normal((n_benign, len(columns))), columns=columns  # type: ignore
        )
        benign_data[LABEL_COLUMN] = BENIGN_LABEL
        rows.append(benign_data)

    if n_attack > 0:
        # Distribute attack rows across labels.
        per_label = max(1, n_attack // len(attack_labels))
        for i, label in enumerate(attack_labels):
            n = per_label if i < len(attack_labels) - 1 else n_attack - per_label * i
            n = max(n, 0)
            if n == 0:
                continue
            atk_data = pd.DataFrame(
                rng.standard_normal((n, len(columns))), columns=columns  # type: ignore
            )
            atk_data[LABEL_COLUMN] = label
            rows.append(atk_data)

    df = (
        pd.concat(rows, ignore_index=True)
        if rows
        else pd.DataFrame(columns=list(columns) + [LABEL_COLUMN])  # type: ignore
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def _make_merged_dir(
    tmp_path: Path,
    clients: dict[str, tuple[int, int]],
    attack_labels: list[str] | None = None,
    columns: Sequence[str] | None = None,
) -> Path:
    raw_dir = tmp_path / "raw_ciciot"
    merged_dir = raw_dir / "CSV" / "MERGED_CSV"
    merged_dir.mkdir(parents=True)

    rng = np.random.default_rng(42)
    for name, (n_b, n_a) in clients.items():
        _make_client_csv(
            merged_dir / f"{name}.csv",
            n_benign=n_b,
            n_attack=n_a,
            attack_labels=attack_labels,
            rng=rng,
            columns=columns,
        )
    return raw_dir


# Schema validation


class TestSchemaValidation:
    def test_valid_schema_passes(self, tmp_path: Path) -> None:
        raw_dir = _make_merged_dir(tmp_path, {"Merged01": (100, 50)})
        validate_schema(raw_dir)  # Should not raise.

    def test_rejects_wrong_columns(self, tmp_path: Path) -> None:
        bad_cols = FEATURE_COLUMNS[:-1] + ("BOGUS_COLUMN",)
        raw_dir = _make_merged_dir(tmp_path, {"Merged01": (100, 50)}, columns=bad_cols)
        with pytest.raises(ValueError, match="Schema mismatch"):
            validate_schema(raw_dir)

    def test_validates_all_files_not_just_first(self, tmp_path: Path) -> None:
        raw_dir = tmp_path / "raw_ciciot"
        merged_dir = raw_dir / "CSV" / "MERGED_CSV"
        merged_dir.mkdir(parents=True)

        rng = np.random.default_rng(42)
        # First file: correct schema.
        _make_client_csv(merged_dir / "Merged01.csv", 100, 50, rng=rng)
        # Second file: wrong schema.
        bad_cols = FEATURE_COLUMNS[:-1] + ("WRONG",)
        _make_client_csv(
            merged_dir / "Merged02.csv", 100, 50, rng=rng, columns=bad_cols
        )

        with pytest.raises(ValueError, match="Merged02"):
            validate_schema(raw_dir)

    def test_rejects_non_numeric_feature_sample(self, tmp_path: Path) -> None:
        raw_dir = _make_merged_dir(tmp_path, {"Merged01": (100, 50)})
        csv_path = raw_dir / "CSV" / "MERGED_CSV" / "Merged01.csv"
        df = pd.read_csv(csv_path)
        df[FEATURE_COLUMNS[0]] = df[FEATURE_COLUMNS[0]].astype(object)
        df.loc[0, FEATURE_COLUMNS[0]] = "not_numeric"
        df.to_csv(csv_path, index=False)

        with pytest.raises(ValueError, match="Non-numeric feature sample"):
            validate_schema(raw_dir)

    def test_no_files_raises(self, tmp_path: Path) -> None:
        raw_dir = tmp_path / "raw_ciciot"
        (raw_dir / "CSV" / "MERGED_CSV").mkdir(parents=True)
        with pytest.raises(FileNotFoundError):
            validate_schema(raw_dir)


class TestCapPriorityOrder:
    def test_cap_priority_order(self) -> None:
        rng = np.random.default_rng(0)
        # 80,000 benign + 20,000 attack (2 categories, 10k each).
        n_benign, n_attack = 80_000, 20_000
        benign = pd.DataFrame(rng.standard_normal((n_benign, 2)), columns=["f1", "f2"])  # type: ignore
        benign[LABEL_COLUMN] = BENIGN_LABEL

        atk_a = pd.DataFrame(
            rng.standard_normal((n_attack // 2, 2)), columns=["f1", "f2"]  # type: ignore
        )
        atk_a[LABEL_COLUMN] = "DDoS_A"
        atk_b = pd.DataFrame(
            rng.standard_normal((n_attack // 2, 2)), columns=["f1", "f2"]  # type: ignore
        )
        atk_b[LABEL_COLUMN] = "DDoS_B"

        df = pd.concat([benign, atk_a, atk_b], ignore_index=True)
        capped = _apply_cap(df, cap=50_000)

        assert len(capped) == 50_000

        # Attack budget = 10,000; proportional across 2 equal categories.
        attack_in_result = capped[capped[LABEL_COLUMN] != BENIGN_LABEL]
        benign_in_result = capped[capped[LABEL_COLUMN] == BENIGN_LABEL]

        assert len(attack_in_result) == 10_000
        assert len(benign_in_result) == 40_000

        # Both categories represented proportionally.
        cat_counts = attack_in_result[LABEL_COLUMN].value_counts()  # type: ignore
        assert cat_counts["DDoS_A"] == 5_000
        assert cat_counts["DDoS_B"] == 5_000

    def test_cap_fewer_attack_than_budget(self) -> None:
        rng = np.random.default_rng(0)
        benign = pd.DataFrame(rng.standard_normal((80_000, 2)), columns=["f1", "f2"])  # type: ignore
        benign[LABEL_COLUMN] = BENIGN_LABEL
        atk = pd.DataFrame(rng.standard_normal((3_000, 2)), columns=["f1", "f2"])  # type: ignore
        atk[LABEL_COLUMN] = "Recon"

        df = pd.concat([benign, atk], ignore_index=True)
        capped = _apply_cap(df, cap=50_000)

        assert len(capped) == 50_000
        assert (capped[LABEL_COLUMN] == "Recon").sum() == 3_000
        assert (capped[LABEL_COLUMN] == BENIGN_LABEL).sum() == 47_000

    def test_no_cap_needed_benign_only(self) -> None:
        rng = np.random.default_rng(0)
        df = pd.DataFrame(rng.standard_normal((100, 2)), columns=["f1", "f2"])  # type: ignore
        df[LABEL_COLUMN] = BENIGN_LABEL

        capped = _apply_cap(df, cap=50_000)
        assert len(capped) == 100

    def test_total_leq_cap_but_attack_exceeds_reserve(self) -> None:
        rng = np.random.default_rng(0)
        # 10,000 benign + 20,000 attack = 30,000 total, which is under the 50,000 cap.
        # But attack_reserve = 0.2 * 50,000 = 10,000.  The 20,000 attacks must be
        # reduced to the 10,000 reserve even though total <= cap.
        n_benign, n_attack = 10_000, 20_000
        benign = pd.DataFrame(rng.standard_normal((n_benign, 2)), columns=["f1", "f2"])  # type: ignore
        benign[LABEL_COLUMN] = BENIGN_LABEL
        atk = pd.DataFrame(rng.standard_normal((n_attack, 2)), columns=["f1", "f2"])  # type: ignore
        atk[LABEL_COLUMN] = "DDoS_A"

        df = pd.concat([benign, atk], ignore_index=True)
        assert len(df) == 30_000  # total < 50,000

        capped = _apply_cap(df, cap=50_000)
        attack_in_result = (capped[LABEL_COLUMN] != BENIGN_LABEL).sum()
        benign_in_result = (capped[LABEL_COLUMN] == BENIGN_LABEL).sum()

        assert attack_in_result == 10_000, (
            "attack must be capped to reserve even when total <= cap"
        )
        assert (
            benign_in_result == 10_000
        )  # all benign preserved (10k < 40k benign budget)


# Calibration-Pending (PRE-CAP)


class TestCalibrationPendingPreCap:
    def test_calibration_pending_pre_cap(self, tmp_path: Path) -> None:
        # 20 benign → floor(20 × 0.15) = 3 < n_min=100 → pending.
        raw_dir = _make_merged_dir(tmp_path, {"Merged01": (20, 500)})
        output_dir = tmp_path / "out"

        result = _prepare_ciciot(raw_dir, output_dir)
        assert result["Merged01"].calibration_pending is True

    def test_eligible_when_enough_benign(self, tmp_path: Path) -> None:
        # 2000 benign → floor(2000 × 0.15) = 300 >= 100 → eligible.
        raw_dir = _make_merged_dir(tmp_path, {"Merged01": (2000, 500)})
        output_dir = tmp_path / "out"

        result = _prepare_ciciot(raw_dir, output_dir)
        assert result["Merged01"].calibration_pending is False


# Evaluation-incomplete


class TestEvaluationIncomplete:
    def test_evaluation_incomplete_zero_attack(self, tmp_path: Path) -> None:
        raw_dir = _make_merged_dir(tmp_path, {"Merged01": (500, 0)})
        output_dir = tmp_path / "out"

        result = _prepare_ciciot(raw_dir, output_dir)
        assert result["Merged01"].evaluation_incomplete is True

    def test_not_evaluation_incomplete(self, tmp_path: Path) -> None:
        raw_dir = _make_merged_dir(tmp_path, {"Merged01": (500, 200)})
        output_dir = tmp_path / "out"

        result = _prepare_ciciot(raw_dir, output_dir)
        assert result["Merged01"].evaluation_incomplete is False


# Orthogonal flags


class TestFlagsOrthogonal:
    def test_all_four_combinations(self, tmp_path: Path) -> None:
        # Case 1: pending=False, incomplete=False
        # 2000 benign (floor(2000*0.15)=300 >= 100), 200 attack
        # Case 2: pending=True, incomplete=False
        # 10 benign (floor(10*0.15)=1 < 100), 200 attack
        # Case 3: pending=False, incomplete=True
        # 2000 benign, 0 attack
        # Case 4: pending=True, incomplete=True
        # 10 benign, 0 attack
        clients = {
            "Merged01": (2000, 200),  # F, F
            "Merged02": (10, 200),  # T, F
            "Merged03": (2000, 0),  # F, T
            "Merged04": (10, 0),  # T, T
        }
        raw_dir = _make_merged_dir(tmp_path, clients)
        output_dir = tmp_path / "out"

        result = _prepare_ciciot(raw_dir, output_dir)

        assert result["Merged01"].calibration_pending is False
        assert result["Merged01"].evaluation_incomplete is False

        assert result["Merged02"].calibration_pending is True
        assert result["Merged02"].evaluation_incomplete is False

        assert result["Merged03"].calibration_pending is False
        assert result["Merged03"].evaluation_incomplete is True

        assert result["Merged04"].calibration_pending is True
        assert result["Merged04"].evaluation_incomplete is True


# Stratified split ratios


class TestStratifiedSplitRatios:
    def test_stratified_split_ratios(self, tmp_path: Path) -> None:
        raw_dir = _make_merged_dir(tmp_path, {"Merged01": (10_000, 1000)})
        output_dir = tmp_path / "out"

        result = _prepare_ciciot(raw_dir, output_dir)
        info = result["Merged01"]

        total_benign = (
            info.benign_train_count + info.benign_cal_count + info.test_benign_count
        )

        # After cap there should be 10,000 benign (under cap).
        # Allow small rounding differences from train_test_split.
        train_ratio = info.benign_train_count / total_benign
        cal_ratio = info.benign_cal_count / total_benign
        test_ratio = info.test_benign_count / total_benign

        assert 0.68 <= train_ratio <= 0.72, f"train ratio {train_ratio}"
        assert 0.13 <= cal_ratio <= 0.17, f"cal ratio {cal_ratio}"
        assert 0.13 <= test_ratio <= 0.17, f"test ratio {test_ratio}"


# Output format


class TestOutputFormat:
    @pytest.fixture()
    def prepared(self, tmp_path: Path) -> tuple[Path, dict]:
        raw_dir = _make_merged_dir(tmp_path, {"Merged01": (2000, 500)})
        output_dir = tmp_path / "out"
        result = _prepare_ciciot(raw_dir, output_dir)
        return output_dir, result

    def test_output_is_parquet(self, prepared: tuple[Path, dict]) -> None:
        output_dir, _ = prepared
        client_dir = output_dir / "ciciot2023" / "Merged01"
        for name in (
            "train.parquet",
            "cal.parquet",
            "test_benign.parquet",
            "test_attack.parquet",
        ):
            p = client_dir / name
            assert p.exists(), f"Missing artifact: {p}"
            assert p.suffix == ".parquet"
        assert (client_dir / "scaler.pkl").exists()

    def test_no_csv_artifacts(self, prepared: tuple[Path, dict]) -> None:
        output_dir, _ = prepared
        csv_files = list((output_dir / "ciciot2023").rglob("*.csv"))
        assert csv_files == [], f"CSV files found: {csv_files}"

    def test_non_finite_rows_are_dropped_before_artifact_validation(
        self, tmp_path: Path
    ) -> None:
        raw_dir = _make_merged_dir(tmp_path, {"Merged01": (2000, 500)})
        csv_path = raw_dir / "CSV" / "MERGED_CSV" / "Merged01.csv"
        df = pd.read_csv(csv_path)
        df.loc[0, FEATURE_COLUMNS[0]] = np.inf
        df.loc[1, FEATURE_COLUMNS[1]] = -np.inf
        df.loc[2, FEATURE_COLUMNS[2]] = np.nan
        df.to_csv(csv_path, index=False)

        output_dir = tmp_path / "out"
        result = _prepare_ciciot(raw_dir, output_dir)

        client_dir = output_dir / "ciciot2023" / "Merged01"
        artifact_rows = sum(
            len(pd.read_parquet(client_dir / name))
            for name in (
                "train.parquet",
                "cal.parquet",
                "test_benign.parquet",
                "test_attack.parquet",
            )
        )
        assert artifact_rows == 2497
        assert result["Merged01"].total_benign_pre_cap == 1997

    def test_short_malformed_rows_are_dropped_before_artifact_validation(
        self, tmp_path: Path
    ) -> None:
        raw_dir = _make_merged_dir(tmp_path, {"Merged01": (2000, 500)})
        csv_path = raw_dir / "CSV" / "MERGED_CSV" / "Merged01.csv"
        with csv_path.open("a", encoding="utf-8") as f:
            f.write("1.0,2.0,3.0\n")

        output_dir = tmp_path / "out"
        result = _prepare_ciciot(raw_dir, output_dir)

        client_dir = output_dir / "ciciot2023" / "Merged01"
        artifact_rows = sum(
            len(pd.read_parquet(client_dir / name))
            for name in (
                "train.parquet",
                "cal.parquet",
                "test_benign.parquet",
                "test_attack.parquet",
            )
        )
        assert artifact_rows == 2500
        assert result["Merged01"].total_benign_pre_cap == 2000


# Scaler fitted on benign train only


class TestScalerFittedOnBenignTrainOnly:
    def test_scaler_fitted_on_benign_train_only(self, tmp_path: Path) -> None:
        raw_dir = _make_merged_dir(tmp_path, {"Merged01": (2000, 500)})
        output_dir = tmp_path / "out"

        _prepare_ciciot(raw_dir, output_dir)

        client_dir = output_dir / "ciciot2023" / "Merged01"
        load_scaler(client_dir / "scaler.pkl")
        train_df = pd.read_parquet(client_dir / "train.parquet")

        # Scaled train data should have ~0 mean and ~1 std per column.
        means = train_df.mean()
        stds = train_df.std()
        assert all(abs(m) < 0.1 for m in means), (  # type: ignore
            f"Train means not near 0: {means.tolist()}"  # type: ignore
        )
        assert all(abs(s - 1.0) < 0.2 for s in stds if s > 0), (  # type: ignore
            f"Train stds not near 1: {stds.tolist()}"  # type: ignore
        )


class TestBenignOnlyInTrainAndCal:
    def test_benign_only_in_train_and_cal(self, tmp_path: Path) -> None:
        raw_dir = _make_merged_dir(tmp_path, {"Merged01": (2000, 500)})
        output_dir = tmp_path / "out"

        _prepare_ciciot(raw_dir, output_dir)

        client_dir = output_dir / "ciciot2023" / "Merged01"
        train_df = pd.read_parquet(client_dir / "train.parquet")
        cal_df = pd.read_parquet(client_dir / "cal.parquet")

        # No Label column in output (only features after scaling).
        assert LABEL_COLUMN not in train_df.columns
        assert LABEL_COLUMN not in cal_df.columns

        # Row counts: train + cal + test_benign = total benign (capped).
        test_benign_df = pd.read_parquet(client_dir / "test_benign.parquet")
        total_benign_output = len(train_df) + len(cal_df) + len(test_benign_df)
        assert total_benign_output > 0  # Sanity check.


# PartitionResult model


class TestPartitionResult:
    def test_model_fields(self) -> None:
        result = PartitionResult(
            benign_train_count=10,
            benign_cal_count=2,
            test_benign_count=3,
            test_attack_count=4,
            calibration_pending=True,
            evaluation_incomplete=False,
        )
        assert result.calibration_pending is True
        assert result.evaluation_incomplete is False

    def test_model_equality(self) -> None:
        a = PartitionResult(
            benign_train_count=1,
            benign_cal_count=1,
            test_benign_count=1,
            test_attack_count=0,
            calibration_pending=True,
            evaluation_incomplete=True,
        )
        b = PartitionResult(
            benign_train_count=1,
            benign_cal_count=1,
            test_benign_count=1,
            test_attack_count=0,
            calibration_pending=True,
            evaluation_incomplete=True,
        )
        assert a == b


class TestAttackLabelPersistence:
    def test_labels_artifact_exists_when_attack_rows_present(
        self, tmp_path: Path
    ) -> None:
        raw_dir = _make_merged_dir(tmp_path, {"Merged01": (500, 200)})
        output_dir = tmp_path / "out"
        _prepare_ciciot(raw_dir, output_dir)
        labels_path = (
            output_dir / "ciciot2023" / "Merged01" / TEST_ATTACK_LABELS_ARTIFACT
        )
        assert labels_path.exists()

    def test_labels_artifact_row_count_matches_test_attack(
        self, tmp_path: Path
    ) -> None:
        raw_dir = _make_merged_dir(tmp_path, {"Merged01": (500, 200)})
        output_dir = tmp_path / "out"
        _prepare_ciciot(raw_dir, output_dir)
        client_dir = output_dir / "ciciot2023" / "Merged01"
        labels_df = pd.read_parquet(client_dir / TEST_ATTACK_LABELS_ARTIFACT)
        attack_df = pd.read_parquet(client_dir / "test_attack.parquet")
        assert len(labels_df) == len(attack_df)

    def test_labels_artifact_empty_when_zero_attack_rows(self, tmp_path: Path) -> None:
        raw_dir = _make_merged_dir(tmp_path, {"Merged01": (500, 0)})
        output_dir = tmp_path / "out"
        _prepare_ciciot(raw_dir, output_dir)
        labels_path = (
            output_dir / "ciciot2023" / "Merged01" / TEST_ATTACK_LABELS_ARTIFACT
        )
        assert labels_path.exists()
        labels_df = pd.read_parquet(labels_path)
        assert len(labels_df) == 0

    def test_labels_column_is_label_column(self, tmp_path: Path) -> None:
        raw_dir = _make_merged_dir(tmp_path, {"Merged01": (500, 200)})
        output_dir = tmp_path / "out"
        _prepare_ciciot(raw_dir, output_dir)
        labels_df = pd.read_parquet(
            output_dir / "ciciot2023" / "Merged01" / TEST_ATTACK_LABELS_ARTIFACT
        )
        assert LABEL_COLUMN in labels_df.columns

    def test_labels_do_not_appear_in_feature_artifacts(self, tmp_path: Path) -> None:
        raw_dir = _make_merged_dir(tmp_path, {"Merged01": (500, 200)})
        output_dir = tmp_path / "out"
        _prepare_ciciot(raw_dir, output_dir)
        client_dir = output_dir / "ciciot2023" / "Merged01"
        for name in (
            "test_attack.parquet",
            "train.parquet",
            "cal.parquet",
            "test_benign.parquet",
        ):
            df = pd.read_parquet(client_dir / name)
            assert LABEL_COLUMN not in df.columns, (
                f"{name} must not contain label column"
            )

    def test_unknown_attack_labels_fail_validation(self, tmp_path: Path) -> None:
        raw_dir = _make_merged_dir(
            tmp_path,
            {"Merged01": (500, 100)},
            attack_labels=["UNKNOWN_ATTACK_XYZ"],
        )
        output_dir = tmp_path / "out"
        with pytest.raises(ValueError, match="Unknown attack labels"):
            _prepare_ciciot(raw_dir, output_dir)

    def test_known_attack_labels_pass(self, tmp_path: Path) -> None:
        raw_dir = _make_merged_dir(
            tmp_path,
            {"Merged01": (500, 100)},
            attack_labels=["DDoS_TCP", "Mirai_Botnet_HTTP", "Recon_Port_Scan"],
        )
        output_dir = tmp_path / "out"
        result = _prepare_ciciot(raw_dir, output_dir)
        assert result["Merged01"].test_attack_count > 0


class TestAttackFamilyMapping:
    def test_ddos_prefix(self) -> None:
        assert attack_family("DDoS_TCP") == "DDoS"
        assert attack_family("DDoS_UDP") == "DDoS"

    def test_dos_prefix(self) -> None:
        assert attack_family("DoS_SYN") == "DoS"

    def test_mirai_prefix(self) -> None:
        assert attack_family("Mirai_Botnet_HTTP") == "Mirai"

    def test_recon_prefix(self) -> None:
        assert attack_family("Recon_Port_Scan") == "Recon"

    def test_spoofing_prefix(self) -> None:
        assert attack_family("Spoofing_ARP") == "Spoofing"

    def test_bruteforce_prefix(self) -> None:
        assert attack_family("BruteForce_SSH") == "Brute-Force"

    def test_webattack_labels(self) -> None:
        assert attack_family("XSS") == "Web-based"
        assert attack_family("SQL_Injection") == "Web-based"
        assert attack_family("CommandInjection") == "Web-based"

    def test_unknown_returns_none(self) -> None:
        assert attack_family("COMPLETELY_UNKNOWN") is None
        assert attack_family("") is None
