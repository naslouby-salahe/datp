from __future__ import annotations

from datp.validation.invariants import build_invariant_results
from datp.validation.enums import AuditStatus
from datp.core.enums import Baseline, Regime

_CONTROLLED = (Baseline.B1, Baseline.B2, Baseline.B3, Baseline.B4)

_CELL_A = (Regime.A, 0, None)
_CELL_B = (Regime.B, 0, None)
_CELL_C = (Regime.C, 0, "0.5")

_HASH_MAP_REF: dict[tuple[str, str], str] = {
    ("cal", "client_1"): "aaa",
    ("test_benign", "client_1"): "bbb",
    ("test_attack", "client_1"): "ccc",
}
_HASH_MAP_ALT: dict[tuple[str, str], str] = {
    ("cal", "client_1"): "aaa",
    ("test_benign", "client_1"): "bbb",
    ("test_attack", "client_1"): "XXX",
}


def _inputs(
    cell: tuple[Regime, int, str | None],
    baselines: list[Baseline],
    split: str = "split1",
    model: str = "model1",
    scoring: str = "score1",
    metrics: str = "metrics1",
) -> dict[tuple[Regime, int, str | None], dict[Baseline, dict[str, str]]]:
    return {
        cell: {
            b: {
                "split_hash": split,
                "model_hash": model,
                "encoder_hash": model,
                "scoring_code_hash": scoring,
                "metrics_code_hash": metrics,
            }
            for b in baselines
        }
    }


def _score_hashes(
    cell: tuple[Regime, int, str | None],
    baselines: list[Baseline],
    hash_map: dict[tuple[str, str], str] | None = None,
) -> dict[tuple[Regime, int, str | None], dict[Baseline, dict[tuple[str, str], str]]]:
    if hash_map is None:
        hash_map = _HASH_MAP_REF
    return {cell: {b: dict(hash_map) for b in baselines}}


class TestInvariantPass:
    def test_all_b1_b2_b3_b4_match_regime_a(self) -> None:
        baselines = [Baseline.B1, Baseline.B2, Baseline.B3, Baseline.B4]
        results = build_invariant_results(
            _inputs(_CELL_A, baselines),
            _score_hashes(_CELL_A, baselines),
            _CONTROLLED,
        )
        assert len(results) == 1
        assert results[0].status == AuditStatus.PASS
        assert results[0].split_hash_shared is True
        assert results[0].model_or_encoder_hash_shared is True
        assert results[0].reconstruction_error_hashes_shared is True
        assert results[0].scoring_code_hash_shared is True
        assert results[0].metrics_code_hash_shared is True
        assert results[0].disallowed_differences == []

    def test_regime_b_no_b3_required_pass(self) -> None:
        baselines = [Baseline.B1, Baseline.B2, Baseline.B4]
        results = build_invariant_results(
            _inputs(_CELL_B, baselines),
            _score_hashes(_CELL_B, baselines),
            _CONTROLLED,
        )
        assert results[0].status == AuditStatus.PASS
        assert Baseline.B3 not in results[0].checked_baselines
        assert Baseline.B3 not in results[0].missing_baselines

    def test_regime_c_no_b3_required_pass(self) -> None:
        baselines = [Baseline.B1, Baseline.B2, Baseline.B4]
        results = build_invariant_results(
            _inputs(_CELL_C, baselines),
            _score_hashes(_CELL_C, baselines),
            _CONTROLLED,
        )
        assert results[0].status == AuditStatus.PASS
        assert Baseline.B3 not in results[0].checked_baselines


class TestInvariantFail:
    def test_model_hash_differs_marks_fail(self) -> None:
        baselines = [Baseline.B1, Baseline.B2, Baseline.B3, Baseline.B4]
        inv_inputs: dict[
            tuple[Regime, int, str | None], dict[Baseline, dict[str, str]]
        ] = {
            _CELL_A: {
                Baseline.B1: {
                    "split_hash": "s1",
                    "model_hash": "model_A",
                    "encoder_hash": "model_A",
                    "scoring_code_hash": "sc",
                    "metrics_code_hash": "mc",
                },
                Baseline.B2: {
                    "split_hash": "s1",
                    "model_hash": "model_B",
                    "encoder_hash": "model_B",
                    "scoring_code_hash": "sc",
                    "metrics_code_hash": "mc",
                },
                Baseline.B3: {
                    "split_hash": "s1",
                    "model_hash": "model_A",
                    "encoder_hash": "model_A",
                    "scoring_code_hash": "sc",
                    "metrics_code_hash": "mc",
                },
                Baseline.B4: {
                    "split_hash": "s1",
                    "model_hash": "model_A",
                    "encoder_hash": "model_A",
                    "scoring_code_hash": "sc",
                    "metrics_code_hash": "mc",
                },
            }
        }
        results = build_invariant_results(
            inv_inputs,
            _score_hashes(_CELL_A, baselines),
            _CONTROLLED,
        )
        assert results[0].status == AuditStatus.FAIL
        assert "model_hash_or_encoder_hash" in results[0].disallowed_differences
        assert results[0].model_or_encoder_hash_shared is False

    def test_score_array_hash_differs_marks_fail(self) -> None:
        baselines = [Baseline.B1, Baseline.B2, Baseline.B4]
        score_hashes: dict[
            tuple[Regime, int, str | None], dict[Baseline, dict[tuple[str, str], str]]
        ] = {
            _CELL_B: {
                Baseline.B1: dict(_HASH_MAP_REF),
                Baseline.B2: dict(_HASH_MAP_ALT),
                Baseline.B4: dict(_HASH_MAP_REF),
            }
        }
        results = build_invariant_results(
            _inputs(_CELL_B, baselines),
            score_hashes,
            _CONTROLLED,
        )
        assert results[0].status == AuditStatus.FAIL
        assert results[0].reconstruction_error_hashes_shared is False
        assert "reconstruction_error_arrays" in results[0].disallowed_differences

    def test_split_hash_differs_marks_fail(self) -> None:
        inv_inputs: dict[
            tuple[Regime, int, str | None], dict[Baseline, dict[str, str]]
        ] = {
            _CELL_A: {
                Baseline.B1: {
                    "split_hash": "s1",
                    "model_hash": "m1",
                    "encoder_hash": "m1",
                    "scoring_code_hash": "sc",
                    "metrics_code_hash": "mc",
                },
                Baseline.B2: {
                    "split_hash": "s2",
                    "model_hash": "m1",
                    "encoder_hash": "m1",
                    "scoring_code_hash": "sc",
                    "metrics_code_hash": "mc",
                },
                Baseline.B3: {
                    "split_hash": "s1",
                    "model_hash": "m1",
                    "encoder_hash": "m1",
                    "scoring_code_hash": "sc",
                    "metrics_code_hash": "mc",
                },
                Baseline.B4: {
                    "split_hash": "s1",
                    "model_hash": "m1",
                    "encoder_hash": "m1",
                    "scoring_code_hash": "sc",
                    "metrics_code_hash": "mc",
                },
            }
        }
        results = build_invariant_results(
            inv_inputs,
            _score_hashes(
                _CELL_A, [Baseline.B1, Baseline.B2, Baseline.B3, Baseline.B4]
            ),
            _CONTROLLED,
        )
        assert results[0].status == AuditStatus.FAIL
        assert "split_hash" in results[0].disallowed_differences


class TestInvariantBlocked:
    def test_missing_baselines_marks_blocked(self) -> None:
        baselines = [Baseline.B1, Baseline.B2]
        results = build_invariant_results(
            _inputs(_CELL_A, baselines),
            _score_hashes(_CELL_A, baselines),
            _CONTROLLED,
        )
        assert results[0].status == AuditStatus.BLOCKED_PENDING_RUN
        assert Baseline.B3 in results[0].missing_baselines
        assert Baseline.B4 in results[0].missing_baselines

    def test_no_score_hashes_marks_blocked_not_fail(self) -> None:
        baselines = [Baseline.B1, Baseline.B2, Baseline.B3, Baseline.B4]
        results = build_invariant_results(
            _inputs(_CELL_A, baselines),
            {},
            _CONTROLLED,
        )
        assert results[0].status == AuditStatus.BLOCKED_PENDING_RUN
        assert results[0].reconstruction_error_hashes_shared is False
