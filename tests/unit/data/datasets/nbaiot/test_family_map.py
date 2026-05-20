from __future__ import annotations

from datp.data.datasets.nbaiot.spec import DEVICE_FAMILY_MAP


def test_other_family_contains_ecobee_and_philips_only_from_expected_pair() -> None:
    other_members = {
        device for device, family in DEVICE_FAMILY_MAP.items() if family == "other"
    }
    assert {"Ecobee_Thermostat", "Philips_B120N10_Baby_Monitor"}.issubset(other_members)
