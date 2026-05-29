"""Canonical reporting constants: device labels, figure specs, alpha display order."""

from __future__ import annotations

# Short display labels for N-BaIoT device client IDs used in figures 1 and 2.
NBAIOT_DEVICE_SHORT_LABELS: dict[str, str] = {
    "Danmini_Doorbell": "Danmini DB",
    "Ecobee_Thermostat": "Ecobee Tstat",
    "Ennio_Doorbell": "Ennio DB",
    "Philips_B120N10_Baby_Monitor": "Philips B120N10",
    "Provision_PT_737E_Security_Camera": "Prov. PT-737E",
    "Provision_PT_838_Security_Camera": "Prov. PT-838",
    "Samsung_SNH_1011_N_Webcam": "Samsung SNH",
    "SimpleHome_XCS7_1002_WHT_Security_Camera": "SH XCS7-1002",
    "SimpleHome_XCS7_1003_WHT_Security_Camera": "SH XCS7-1003",
}

# Canonical Dirichlet-α / IID display order for Regime C figures.
# Order matches the x-axis progression: increasing heterogeneity then IID reference.
REGIME_C_ALPHA_DISPLAY_ORDER: tuple[str, ...] = (
    "0.1",
    "0.3",
    "0.5",
    "1.0",
    "10.0",
    "iid",
)

# X-axis tick labels for Regime C alpha sweep figure (IID in uppercase for display).
REGIME_C_ALPHA_TICK_LABELS: tuple[str, ...] = (
    "0.1",
    "0.3",
    "0.5",
    "1.0",
    "10.0",
    "IID",
)

# Canonical figure filename stems — seed suffix appended by figure1 only.
FIGURE1_STEM = "figure1_seed"  # completed by generate_figure1 with seed number
FIGURE2_STEM = "figure2_ecdf"
FIGURE3_STEM = "figure3_boxplots"
FIGURE4_STEM = "figure4_alpha_sweep"
