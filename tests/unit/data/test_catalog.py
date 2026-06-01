"""Tests for datp.data.catalog — enums, dataclasses, and registry functions."""

from __future__ import annotations

import pytest

from datp.data.catalog import (
    CapPolicy,
    CapStrategy,
    ClientIdentity,
    DatasetID,
    DatasetSpec,
    SplitPolicy,
    dataset_display_name,
    dataset_processed_slug,
    dataset_spec,
    get_datasets,
)


class TestDatasetID:
    def test_all_members_present(self) -> None:
        assert set(DatasetID) == {
            DatasetID.NBAIOT,
            DatasetID.CICIOT2023,
            DatasetID.EDGE_IIOTSET,
        }

    def test_values_are_lowercase_slugs(self) -> None:
        for member in DatasetID:
            assert member.value == member.value.lower()
            assert " " not in member.value


class TestClientIdentity:
    def test_all_members_present(self) -> None:
        assert set(ClientIdentity) == {
            ClientIdentity.DEVICE_DIRECTORY,
            ClientIdentity.MERGED_FILE,
        }

    def test_values_are_snake_case(self) -> None:
        for member in ClientIdentity:
            assert "_" in member.value or member.value.islower()


class TestCapStrategy:
    def test_all_members_present(self) -> None:
        assert set(CapStrategy) == {
            CapStrategy.ATTACK_PRESERVING,
            CapStrategy.RANDOM,
        }


class TestSplitPolicy:
    def test_construction(self) -> None:
        sp = SplitPolicy(
            name="chronological",
            calibration_benign_only=True,
            chronological=True,
            contiguous_gaps=False,
            ratios={"train": 0.6, "cal": 0.2},
        )
        assert sp.name == "chronological"
        assert sp.calibration_benign_only is True
        assert sp.chronological is True
        assert sp.contiguous_gaps is False
        assert sp.ratios == {"train": 0.6, "cal": 0.2}

    def test_frozen(self) -> None:
        sp = SplitPolicy(
            name="test",
            calibration_benign_only=False,
            chronological=False,
            contiguous_gaps=False,
            ratios={},
        )
        with pytest.raises(Exception):
            sp.name = "other"  # type: ignore[misc]


class TestCapPolicy:
    def test_construction(self) -> None:
        cp = CapPolicy(
            total=50000,
            attack_reserve=10000,
            strategy=CapStrategy.ATTACK_PRESERVING,
        )
        assert cp.total == 50000
        assert cp.attack_reserve == 10000
        assert cp.strategy == CapStrategy.ATTACK_PRESERVING

    def test_frozen(self) -> None:
        cp = CapPolicy(total=100, attack_reserve=10, strategy=CapStrategy.RANDOM)
        with pytest.raises(Exception):
            cp.total = 200  # type: ignore[misc]


class TestDatasetSpec:
    def test_minimal_construction(self) -> None:
        spec = DatasetSpec(
            id=DatasetID.NBAIOT,
            display_name="Test",
            processed_slug="test",
            feature_count=10,
            feature_columns=None,
            label_column=None,
            benign_label=None,
            client_identity=ClientIdentity.DEVICE_DIRECTORY,
            raw_root_slug="test_raw",
            split_policy=SplitPolicy(
                name="simple",
                calibration_benign_only=True,
                chronological=False,
                contiguous_gaps=False,
                ratios={"train": 0.7, "cal": 0.3},
            ),
            cap_policy=None,
            family_map=None,
            device_ids=(),
            attack_family_dirs=(),
            expected_client_count=None,
        )
        assert spec.id == DatasetID.NBAIOT
        assert spec.feature_count == 10
        assert spec.cap_policy is None

    def test_frozen(self) -> None:
        spec = DatasetSpec(
            id=DatasetID.NBAIOT,
            display_name="T",
            processed_slug="t",
            feature_count=1,
            feature_columns=None,
            label_column=None,
            benign_label=None,
            client_identity=ClientIdentity.DEVICE_DIRECTORY,
            raw_root_slug="t",
            split_policy=SplitPolicy(
                name="t",
                calibration_benign_only=False,
                chronological=False,
                contiguous_gaps=False,
                ratios={},
            ),
            cap_policy=None,
            family_map=None,
            device_ids=(),
            attack_family_dirs=(),
            expected_client_count=None,
        )
        with pytest.raises(Exception):
            spec.feature_count = 99  # type: ignore[misc]


class TestGetDatasets:
    def test_returns_all_three_datasets(self) -> None:
        datasets = get_datasets()
        assert set(datasets) == {
            DatasetID.NBAIOT,
            DatasetID.CICIOT2023,
            DatasetID.EDGE_IIOTSET,
        }

    def test_caches_result(self) -> None:
        a = get_datasets()
        b = get_datasets()
        assert a is b

    def test_every_spec_has_valid_id(self) -> None:
        for did, spec in get_datasets().items():
            assert spec.id == did

    def test_nbaiot_has_expected_properties(self) -> None:
        spec = get_datasets()[DatasetID.NBAIOT]
        assert spec.feature_count == 115
        assert spec.client_identity == ClientIdentity.DEVICE_DIRECTORY
        assert spec.cap_policy is None
        assert spec.family_map is not None

    def test_ciciot2023_has_expected_properties(self) -> None:
        spec = get_datasets()[DatasetID.CICIOT2023]
        assert spec.feature_count == 39
        assert spec.client_identity == ClientIdentity.MERGED_FILE
        assert spec.cap_policy is not None
        assert spec.cap_policy.strategy == CapStrategy.ATTACK_PRESERVING

    def test_edge_iiotset_has_expected_properties(self) -> None:
        spec = get_datasets()[DatasetID.EDGE_IIOTSET]
        assert spec.feature_count == 58
        assert spec.client_identity == ClientIdentity.DEVICE_DIRECTORY
        assert spec.cap_policy is None
        assert spec.family_map is None


class TestDatasetSpecHelper:
    def test_returns_correct_spec(self) -> None:
        spec = dataset_spec(DatasetID.NBAIOT)
        assert spec.id == DatasetID.NBAIOT
        assert spec.display_name == "N-BaIoT"

    def test_raises_keyerror_for_invalid_id(self) -> None:
        with pytest.raises(KeyError):
            dataset_spec("not_an_enum")  # type: ignore[arg-type]


class TestDatasetDisplayName:
    def test_nbaiot(self) -> None:
        assert dataset_display_name(DatasetID.NBAIOT) == "N-BaIoT"

    def test_ciciot2023(self) -> None:
        assert dataset_display_name(DatasetID.CICIOT2023) == "CICIoT2023"

    def test_edge_iiotset(self) -> None:
        assert dataset_display_name(DatasetID.EDGE_IIOTSET) == "Edge-IIoTset"


class TestDatasetProcessedSlug:
    def test_nbaiot(self) -> None:
        assert dataset_processed_slug(DatasetID.NBAIOT) == "nbaiot"

    def test_ciciot2023(self) -> None:
        assert dataset_processed_slug(DatasetID.CICIOT2023) == "ciciot2023"

    def test_edge_iiotset(self) -> None:
        assert dataset_processed_slug(DatasetID.EDGE_IIOTSET) == "edge_iiotset"
