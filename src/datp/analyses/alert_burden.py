"""GB-09 Alert-Burden Table.

Translates FPR to alerts/device/day using real timestamped flow/packet rates.

N-BaIoT raw data contains only 115 statistical features (MI_dir, H, HH, HH_jit,
HpHp weights/means/variances across 5 window sizes). There are NO timestamps,
NO flow rates, NO packet counts, and NO per-second or per-day rate data.

Per T13 acceptance criteria: when no valid rate source exists, produce an
explicit suppression artifact. No rates are invented.

Output: <base_dir>/analysis/alert_burden_suppression.json
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict

from datp.analyses._common import ensure_analysis_dir


class AlertBurdenSuppression(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
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


ALERT_BURDEN_SUPPRESSION_JSON = "alert_burden_suppression.json"


def run_alert_burden(
    base_dir: Path,
    *,
    write_outputs: bool = False,
) -> AlertBurdenSuppression:
    result = AlertBurdenSuppression()

    if write_outputs:
        out_dir = ensure_analysis_dir(base_dir)
        path = out_dir / ALERT_BURDEN_SUPPRESSION_JSON
        path.write_text(result.model_dump_json(indent=2), encoding="utf-8")

    return result
