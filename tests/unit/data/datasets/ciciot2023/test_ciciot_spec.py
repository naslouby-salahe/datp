"""Tests for CICIoT2023 dataset spec integrity."""

from __future__ import annotations

from datp.data.catalog import CapStrategy, DatasetID, dataset_spec
from datp.data.datasets.ciciot2023.spec import (
    ATTACK_FAMILIES,
    BENIGN_LABEL,
    CAL_FRACTION,
    CAP_ATTACK_RESERVE,
    CAP_TOTAL,
    CICIOT2023_SPEC,
    EXPECTED_COLUMNS,
    FEATURE_COLUMNS,
    FEATURE_COUNT,
    LABEL_COLUMN,
    NUM_CLIENTS,
    TEST_ATTACK_LABELS_ARTIFACT,
    attack_family,
)


class TestCiciotSpecIntegrity:
    """Structural integrity of the CICIoT2023 dataset spec."""

    def test_feature_count_matches_columns(self) -> None:
        assert len(FEATURE_COLUMNS) == FEATURE_COUNT
        assert FEATURE_COUNT == 39

    def test_expected_columns_includes_features_and_label(self) -> None:
        assert len(EXPECTED_COLUMNS) == 40
        assert EXPECTED_COLUMNS[-1] == LABEL_COLUMN
        for col in FEATURE_COLUMNS:
            assert col in EXPECTED_COLUMNS

    def test_label_column_not_in_features(self) -> None:
        assert LABEL_COLUMN not in FEATURE_COLUMNS

    def test_feature_columns_are_unique(self) -> None:
        assert len(FEATURE_COLUMNS) == len(set(FEATURE_COLUMNS))

    def test_feature_columns_are_strings(self) -> None:
        for col in FEATURE_COLUMNS:
            assert isinstance(col, str)

    def test_benign_label_set(self) -> None:
        assert BENIGN_LABEL == "BENIGN"

    def test_num_clients(self) -> None:
        assert NUM_CLIENTS == 63

    def test_cap_constants_positive(self) -> None:
        assert CAP_TOTAL == 50000
        assert CAP_ATTACK_RESERVE == 10000
        assert CAP_TOTAL > CAP_ATTACK_RESERVE

    def test_cal_fraction_in_range(self) -> None:
        assert 0 < CAL_FRACTION < 1

    def test_test_attack_labels_artifact_is_parquet(self) -> None:
        assert TEST_ATTACK_LABELS_ARTIFACT.endswith(".parquet")

    def test_spec_registered_in_catalog(self) -> None:
        spec = dataset_spec(DatasetID.CICIOT2023)
        assert spec.id == DatasetID.CICIOT2023
        assert spec.feature_count == 39
        assert spec.display_name == "CICIoT2023"

    def test_spec_expected_client_count(self) -> None:
        assert CICIOT2023_SPEC.expected_client_count == NUM_CLIENTS

    def test_spec_client_identity(self) -> None:
        from datp.data.catalog import ClientIdentity

        assert CICIOT2023_SPEC.client_identity == ClientIdentity.MERGED_FILE

    def test_spec_has_cap_policy(self) -> None:
        assert CICIOT2023_SPEC.cap_policy is not None
        assert CICIOT2023_SPEC.cap_policy.total == CAP_TOTAL
        assert CICIOT2023_SPEC.cap_policy.attack_reserve == CAP_ATTACK_RESERVE
        assert CICIOT2023_SPEC.cap_policy.strategy == CapStrategy.ATTACK_PRESERVING

    def test_spec_has_split_policy(self) -> None:
        sp = CICIOT2023_SPEC.split_policy
        assert sp.name == "stratified_random"
        assert sp.calibration_benign_only is True
        assert sp.chronological is False
        assert sp.contiguous_gaps is False
        assert "train" in sp.ratios
        assert "cal" in sp.ratios
        assert "test_benign" in sp.ratios

    def test_spec_feature_columns_match_module_level(self) -> None:
        assert CICIOT2023_SPEC.feature_columns == FEATURE_COLUMNS

    def test_spec_label_column_matches_module_level(self) -> None:
        assert CICIOT2023_SPEC.label_column == LABEL_COLUMN

    def test_spec_benign_label_matches_module_level(self) -> None:
        assert CICIOT2023_SPEC.benign_label == BENIGN_LABEL

    def test_spec_no_family_map(self) -> None:
        assert CICIOT2023_SPEC.family_map is None

    def test_spec_no_device_ids(self) -> None:
        assert CICIOT2023_SPEC.device_ids == ()

    def test_spec_no_attack_family_dirs(self) -> None:
        assert CICIOT2023_SPEC.attack_family_dirs == ()

    def test_spec_processed_slug(self) -> None:
        assert CICIOT2023_SPEC.processed_slug == "ciciot2023"

    def test_spec_raw_root_slug(self) -> None:
        assert CICIOT2023_SPEC.raw_root_slug == "CIC_IOT_Dataset2023"


class TestAttackFamilies:
    """Attack family constants and mapping function."""

    def test_attack_families_has_seven_entries(self) -> None:
        assert len(ATTACK_FAMILIES) == 7
        assert "DDoS" in ATTACK_FAMILIES
        assert "DoS" in ATTACK_FAMILIES
        assert "Mirai" in ATTACK_FAMILIES
        assert "Recon" in ATTACK_FAMILIES
        assert "Spoofing" in ATTACK_FAMILIES
        assert "Web-based" in ATTACK_FAMILIES
        assert "Brute-Force" in ATTACK_FAMILIES


class TestAttackFamilyMapping:
    """attack_family() label-to-family mapping."""

    def test_ddos_prefix(self) -> None:
        assert attack_family("DDoS_TCP") == "DDoS"
        assert attack_family("DDoS_UDP") == "DDoS"
        assert attack_family("DDOS_HTTP") == "DDoS"

    def test_dos_prefix(self) -> None:
        assert attack_family("DoS_SYN") == "DoS"
        assert attack_family("DOS_SYN") == "DoS"

    def test_mirai_prefix(self) -> None:
        assert attack_family("Mirai_Botnet_HTTP") == "Mirai"
        assert attack_family("MIRAI_UDP") == "Mirai"

    def test_recon_prefix(self) -> None:
        assert attack_family("Recon_Port_Scan") == "Recon"
        assert attack_family("RECON_OS") == "Recon"

    def test_spoofing_prefix(self) -> None:
        assert attack_family("Spoofing_ARP") == "Spoofing"
        assert attack_family("SPOOFING_DNS") == "Spoofing"

    def test_bruteforce_prefix(self) -> None:
        assert attack_family("BruteForce_SSH") == "Brute-Force"
        assert attack_family("BRUTEFORCE_FTP") == "Brute-Force"
        assert attack_family("BRUTE_FORCE_HTTP") == "Brute-Force"

    def test_webattack_labels(self) -> None:
        assert attack_family("XSS") == "Web-based"
        assert attack_family("SQL_Injection") == "Web-based"
        assert attack_family("SQLINJECTION") == "Web-based"
        assert attack_family("CommandInjection") == "Web-based"
        assert attack_family("COMMANDINJECTION") == "Web-based"

    def test_webattack_extra_labels(self) -> None:
        assert attack_family("BACKDOOR_MALWARE") == "Web-based"
        assert attack_family("MITM") == "Web-based"
        assert attack_family("BROWSERHIJACKING") == "Web-based"
        assert attack_family("UPLOADING_ATTACK") == "Web-based"

    def test_recon_labels(self) -> None:
        assert attack_family("VULNERABILITYSCAN") == "Recon"
        assert attack_family("VulnerabilityScan") == "Recon"

    def test_spoofing_labels(self) -> None:
        assert attack_family("DNS_SPOOFING") == "Spoofing"
        assert attack_family("MITM_ARPSPOOFING") == "Spoofing"

    def test_bruteforce_labels(self) -> None:
        assert attack_family("DICTIONARYBRUTEFORCE") == "Brute-Force"

    def test_normalization_handles_dashes_and_spaces(self) -> None:
        assert attack_family("DDoS-TCP_Flood") == "DDoS"
        assert attack_family("  DDoS_UDP  ") == "DDoS"

    def test_benign_returns_none(self) -> None:
        assert attack_family("BENIGN") is None

    def test_unknown_returns_none(self) -> None:
        assert attack_family("COMPLETELY_UNKNOWN") is None
        assert attack_family("") is None

    def test_all_families_have_at_least_one_path(self) -> None:
        """Every family in ATTACK_FAMILIES is reachable via attack_family()."""
        reachable: set[str] = set()
        # Test a representative label for each family.
        test_labels = [
            "DDoS_TCP",
            "DoS_SYN",
            "Mirai_Botnet_HTTP",
            "Recon_Port_Scan",
            "Spoofing_ARP",
            "XSS",
            "BruteForce_SSH",
        ]
        for label in test_labels:
            result = attack_family(label)
            assert result is not None, f"attack_family({label!r}) returned None"
            reachable.add(result)
        assert reachable == set(ATTACK_FAMILIES)
