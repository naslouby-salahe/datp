# SPDX-License-Identifier: Proprietary
"""Tests for Edge-IIoTset dataset spec and preprocessing (T21)."""

from __future__ import annotations

from datp.core.enums import ConfusionKey
from datp.core.enums import (
    FeasibilityOutcome,
    Regime,
)
from datp.data.catalog import DatasetID, dataset_spec
from datp.data.datasets.edge_iiotset.spec import (
    ALL_COLUMNS,
    ATTACK_TYPE_COLUMN,
    BENIGN_LABEL,
    CLIENT_ID_COLUMN,
    FEATURE_COLUMNS,
    FEATURE_COUNT,
    LABEL_COLUMN,
    NORMAL_SENSOR_DIRS,
    SPLIT_RATIOS,
    TIMESTAMP_COLUMN,
    EDGE_IIOTSET_SPEC,
)
from datp.data.regimes.catalog import dataset_for_regime


class TestEdgeIIoTsetSpec:
    """Dataset spec integrity."""

    def test_feature_count_matches_columns(self) -> None:
        assert len(FEATURE_COLUMNS) == FEATURE_COUNT
        assert FEATURE_COUNT == 58

    def test_all_columns_includes_metadata_and_features(self) -> None:
        assert len(ALL_COLUMNS) == 63
        assert TIMESTAMP_COLUMN in ALL_COLUMNS
        assert CLIENT_ID_COLUMN in ALL_COLUMNS
        assert LABEL_COLUMN in ALL_COLUMNS
        assert ATTACK_TYPE_COLUMN in ALL_COLUMNS
        for col in FEATURE_COLUMNS:
            assert col in ALL_COLUMNS

    def test_metadata_not_in_features(self) -> None:
        metadata = {
            TIMESTAMP_COLUMN,
            CLIENT_ID_COLUMN,
            "ip.dst_host",
            LABEL_COLUMN,
            ATTACK_TYPE_COLUMN,
        }
        feature_set = set(FEATURE_COLUMNS)
        assert metadata.isdisjoint(feature_set)

    def test_normal_sensors_count(self) -> None:
        assert len(NORMAL_SENSOR_DIRS) == 10

    def test_benign_label_is_zero_string(self) -> None:
        assert BENIGN_LABEL == "0"

    def test_split_ratios_sum_less_than_one(self) -> None:
        total = sum(SPLIT_RATIOS.values())
        assert total < 1.0, "Train+cal must leave room for test_benign"

    def test_spec_registered_in_catalog(self) -> None:
        spec = dataset_spec(DatasetID.EDGE_IIOTSET)
        assert spec.id == DatasetID.EDGE_IIOTSET
        assert spec.feature_count == 58
        assert spec.display_name == "Edge-IIoTset"

    def test_spec_expected_client_count(self) -> None:
        assert EDGE_IIOTSET_SPEC.expected_client_count == 10

    def test_feature_columns_are_strings(self) -> None:
        for col in FEATURE_COLUMNS:
            assert isinstance(col, str)

    def test_all_columns_unique(self) -> None:
        assert len(ALL_COLUMNS) == len(set(ALL_COLUMNS))


class TestRegimeD:
    """Regime.D is wired to Edge-IIoTset."""

    def test_regime_d_exists(self) -> None:
        assert Regime.D == "d"

    def test_regime_d_maps_to_edge_iiotset(self) -> None:
        assert dataset_for_regime(Regime.D) == DatasetID.EDGE_IIOTSET

    def test_regime_d_is_not_dirichlet(self) -> None:
        from datp.data.regimes.catalog import is_dirichlet_regime

        assert not is_dirichlet_regime(Regime.D)

    def test_regime_d_does_not_require_alpha(self) -> None:
        from datp.data.regimes.catalog import requires_alpha

        assert not requires_alpha(Regime.D)


class TestFeasibilityOutcome:
    """Feasibility outcome enum per PRE_CODING_PLAN §5.5."""

    def test_device_clients_value(self) -> None:
        assert (
            FeasibilityOutcome.EDGE_FEASIBLE_DEVICE_CLIENTS
            == "edge_feasible_device_clients"
        )

    def test_group_clients_value(self) -> None:
        assert (
            FeasibilityOutcome.EDGE_FEASIBLE_GROUP_CLIENTS_ONLY
            == "edge_feasible_group_clients_only"
        )

    def test_rejected_no_metadata_value(self) -> None:
        assert (
            FeasibilityOutcome.EDGE_REJECTED_NO_METADATA == "edge_rejected_no_metadata"
        )

    def test_rejected_insufficient_clients_value(self) -> None:
        assert (
            FeasibilityOutcome.EDGE_REJECTED_INSUFFICIENT_CLIENTS
            == "edge_rejected_insufficient_clients"
        )

    def test_blocked_data_unavailable_value(self) -> None:
        assert (
            FeasibilityOutcome.EDGE_BLOCKED_DATA_UNAVAILABLE
            == "edge_blocked_data_unavailable"
        )

    def test_all_values_are_strings(self) -> None:
        for outcome in FeasibilityOutcome:
            assert isinstance(outcome.value, str)
