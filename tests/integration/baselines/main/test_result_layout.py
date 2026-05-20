from __future__ import annotations

from pathlib import Path

import pytest

from datp.artifacts.directories import OUTPUTS_DIR
from datp.artifacts.paths import ExperimentLocator
from datp.core.enums import (
    Baseline,
    Regime,
)


@pytest.mark.integration
def test_canonical_path() -> None:
    loc_a = ExperimentLocator.for_main(Path(OUTPUTS_DIR), Regime.A)
    loc_c = ExperimentLocator.for_main(Path(OUTPUTS_DIR), Regime.C)

    rp = loc_a.result(Baseline.B1, seed=0)
    parts = rp.parts
    assert "b1" in parts, f".result() should contain baseline 'b1': {rp}"
    assert parts[-2] == "b1"  # baseline segment
    assert parts[-3] == "a"  # regime segment
    assert parts[-1].startswith("seed_")

    rp_alpha = loc_c.result(Baseline.B2, seed=1, alpha=0.5)
    parts_a = rp_alpha.parts
    assert "b2" in parts_a
    assert "alpha_0.5" in parts_a

    sp = loc_a.score(seed=0)
    assert "b1" not in sp.parts and "b2" not in sp.parts

    cp = loc_a.checkpoint(seed=0)
    assert "b1" not in cp.parts and "b2" not in cp.parts

    rp_check = loc_a.result(Baseline.B1, seed=42)
    expected_suffix = "results/a/b1/seed_42"
    assert str(rp_check).endswith(expected_suffix), (
        f"Expected path ending with '{expected_suffix}', got '{rp_check}'"
    )

    sp_check = loc_a.score(seed=42)
    expected_score_suffix = "scores/a/seed_42"
    assert str(sp_check).endswith(expected_score_suffix), (
        f"Expected path ending with '{expected_score_suffix}', got '{sp_check}'"
    )

    cp_check = loc_a.checkpoint(seed=42)
    expected_ckpt_suffix = "checkpoints/a/seed_42"
    assert str(cp_check).endswith(expected_ckpt_suffix), (
        f"Expected path ending with '{expected_ckpt_suffix}', got '{cp_check}'"
    )
