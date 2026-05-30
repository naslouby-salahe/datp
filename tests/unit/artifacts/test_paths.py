from __future__ import annotations

import re
import time
from pathlib import Path

from datp.artifacts.directories import OUTPUTS_DIR
from datp.artifacts.paths import (
    ExperimentLocator,
)
from datp.core.enums import (
    Baseline,
    Regime,
    ScoringStage,
)
from datp.core.identity import make_run_id


class TestMakeRunId:
    """Tests marked with ``collision_proof`` for gate-file -k matching."""

    def test_collision_proof_different_timestamps(self) -> None:
        id1 = make_run_id(Regime.A, seed=0)
        time.sleep(0.002)
        id2 = make_run_id(Regime.A, seed=0)
        assert id1 != id2

    def test_collision_proof_format_without_alpha(self) -> None:
        rid = make_run_id(Regime.A, seed=42)
        assert rid.startswith("a_seed42_")
        ts_part = rid.split("_")[-1]
        assert ts_part.isdigit()
        assert len(ts_part) >= 13  # ms since epoch

    def test_collision_proof_format_with_alpha(self) -> None:
        rid = make_run_id(Regime.C, seed=7, alpha=0.5)
        assert "c_seed7_alpha0.5_" in rid
        ts_part = rid.rsplit("_", 1)[-1]
        assert ts_part.isdigit()

    def test_collision_proof_no_flat_file_pattern(self) -> None:
        rid = make_run_id(Regime.A, seed=0)
        assert not re.match(r"^regime_[a-c]_b\d_seed\d+\.json$", rid)


class TestCanonicalResultPath:
    """Tests marked with ``canonical_result_path`` for gate-file -k matching."""

    def test_canonical_result_path_without_alpha(self) -> None:
        p = ExperimentLocator.for_main(Path(OUTPUTS_DIR), Regime.A).result(
            Baseline.B1, seed=0
        )
        assert p == Path("outputs/results/a/b1/seed_0")

    def test_canonical_result_path_with_alpha(self) -> None:
        p = ExperimentLocator.for_main(Path(OUTPUTS_DIR), Regime.C).result(
            Baseline.B2, seed=3, alpha=0.1
        )
        assert p == Path("outputs/results/c/b2/seed_3/alpha_0.1")

    def test_canonical_result_path_custom_base(self) -> None:
        p = ExperimentLocator.for_main(Path("/tmp/out"), Regime.B).result(
            Baseline.B4, seed=1
        )
        assert p == Path("/tmp/out/results/b/b4/seed_1")

    def test_canonical_result_path_includes_baseline(self) -> None:
        p = ExperimentLocator.for_main(Path(OUTPUTS_DIR), Regime.A).result(
            Baseline.B3, seed=5
        )
        assert "b3" in p.parts

    def test_log_path_without_alpha(self) -> None:
        p = ExperimentLocator.for_main(Path(OUTPUTS_DIR), Regime.A).log(
            Baseline.B1, seed=0
        )
        assert p == Path("outputs/logs/a/b1/seed_0")

    def test_log_path_with_alpha(self) -> None:
        p = ExperimentLocator.for_main(Path(OUTPUTS_DIR), Regime.C).log(
            Baseline.B2, seed=3, alpha=0.5
        )
        assert p == Path("outputs/logs/c/b2/seed_3/alpha_0.5")

    def test_log_path_includes_baseline(self) -> None:
        p = ExperimentLocator.for_main(Path(OUTPUTS_DIR), Regime.B).log(
            Baseline.B4, seed=1
        )
        assert "b4" in p.parts


class TestCheckpointPath:
    def test_checkpoint_path_without_alpha(self) -> None:
        p = ExperimentLocator.for_main(Path(OUTPUTS_DIR), Regime.A).checkpoint(seed=0)
        assert p == Path("outputs/checkpoints/a/seed_0")

    def test_checkpoint_path_with_alpha(self) -> None:
        p = ExperimentLocator.for_main(Path(OUTPUTS_DIR), Regime.C).checkpoint(
            seed=2, alpha=0.3
        )
        assert p == Path("outputs/checkpoints/c/seed_2/alpha_0.3")

    def test_checkpoint_path_has_no_baseline_segment(self) -> None:
        p = ExperimentLocator.for_main(Path(OUTPUTS_DIR), Regime.A).checkpoint(seed=0)
        for part in p.parts:
            assert not re.match(r"^b\d$", part), (
                f"checkpoint path must not contain baseline segment, got {part}"
            )


class TestScorePath:
    def test_score_path_base(self) -> None:
        p = ExperimentLocator.for_main(Path(OUTPUTS_DIR), Regime.A).score(seed=0)
        assert p == Path("outputs/scores/a/seed_0")

    def test_score_path_with_stage(self) -> None:
        p = ExperimentLocator.for_main(Path(OUTPUTS_DIR), Regime.A).score(
            seed=0, stage=ScoringStage.CAL
        )
        assert p == Path("outputs/scores/a/seed_0/cal")

    def test_score_path_with_stage_and_client(self) -> None:
        p = ExperimentLocator.for_main(Path(OUTPUTS_DIR), Regime.A).score(
            seed=0, stage=ScoringStage.CAL, client_id="device_01"
        )
        assert p == Path("outputs/scores/a/seed_0/cal/device_01.parquet")

    def test_score_path_with_alpha(self) -> None:
        p = ExperimentLocator.for_main(Path(OUTPUTS_DIR), Regime.C).score(
            seed=1, alpha=0.5, stage=ScoringStage.TEST_BENIGN
        )
        assert p == Path("outputs/scores/c/seed_1/alpha_0.5/test_benign")

    def test_score_path_has_no_baseline_segment(self) -> None:
        p = ExperimentLocator.for_main(Path(OUTPUTS_DIR), Regime.A).score(
            seed=0, stage=ScoringStage.CAL, client_id="c1"
        )
        for part in p.parts:
            assert not re.match(r"^b\d$", part), (
                f"score path must not contain baseline segment, got {part}"
            )
