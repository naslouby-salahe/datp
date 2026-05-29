"""GB-09 Alert-Burden Table.

N-BaIoT processed data contains no timestamps, flow rates, or per-device-day
rate data. Per T13 stop condition: never invent rates.

Output: <base_dir>/analysis/alert_burden_suppression.json
"""

from __future__ import annotations

from pathlib import Path

from datp.analyses.constants import ALERT_BURDEN_SUPPRESSION_JSON
from datp.analyses.io import write_analysis_json
from datp.analyses.types import FrozenModel


class AlertBurdenSuppression(FrozenModel):
    suppressed: bool = True
    reason: str = (
        "N-BaIoT processed data contains only 115 statistical features "
        "(MI_dir, H, HH, HH_jit, HpHp weights/means/variances). "
        "No timestamps, flow rates, packet counts, or per-device-day rate "
        "data exist in either the raw CSV or processed Parquet artifacts. "
        "Per T13 stop condition: never invent rates."
    )
    recommendation: str = (
        "Alert-burden translation requires a citable dataset-specific "
        "operational rate (e.g., flows/device/day from N-BaIoT paper "
        "or supplement). Without such a rate, alerts/device/day cannot "
        "be computed from FPR alone."
    )


def run_alert_burden(
    base_dir: Path,
    *,
    write_outputs: bool = False,
) -> AlertBurdenSuppression:
    result = AlertBurdenSuppression()
    if write_outputs:
        write_analysis_json(base_dir, ALERT_BURDEN_SUPPRESSION_JSON, result)
    return result
