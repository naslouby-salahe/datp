from __future__ import annotations

from dataclasses import dataclass
from typing import NamedTuple

from datp.core.enums import (
    Baseline,
    Regime,
    ScoringStage,
    controlled_baselines_for_regime,
)
from datp.validation.enums import AuditStatus, InvariantField
from datp.validation.schemas import BaselineInvariantResult


class InvariantKey(NamedTuple):
    """Hashable key identifying a single (regime, seed, alpha) training cell."""

    regime: Regime
    seed: int
    alpha: str | None


@dataclass(frozen=True, slots=True)
class InvariantHashes:
    """Provenance hashes that must be identical across B1–B4 for a fixed cell."""

    split_hash: str
    model_hash: str
    encoder_hash: str
    scoring_code_hash: str
    metrics_code_hash: str


# Per-client score-array hashes keyed by (stage, client_id).
_ScoreHashMap = dict[Baseline, dict[tuple[ScoringStage, str], str]]


@dataclass(frozen=True, slots=True)
class _SharedFlags:
    split_shared: bool
    model_shared: bool
    scoring_shared: bool
    metrics_shared: bool
    recon_shared: bool
    score_hashes_missing: bool


@dataclass(frozen=True, slots=True)
class _ReconVerdict:
    shared: bool
    missing: bool


def _shared_input_hashes(
    by_baseline: dict[Baseline, InvariantHashes],
    checked: list[Baseline],
) -> _SharedFlags:
    split_shared = len({by_baseline[b].split_hash for b in checked}) <= 1
    model_shared = (
        len(
            {by_baseline[b].model_hash for b in checked}
            | {by_baseline[b].encoder_hash for b in checked}
        )
        <= 1
    )
    scoring_shared = len({by_baseline[b].scoring_code_hash for b in checked}) <= 1
    metrics_shared = len({by_baseline[b].metrics_code_hash for b in checked}) <= 1
    return _SharedFlags(
        split_shared=split_shared,
        model_shared=model_shared,
        scoring_shared=scoring_shared,
        metrics_shared=metrics_shared,
        recon_shared=False,
        score_hashes_missing=True,
    )


def _reconstruction_hash_verdict(
    checked: list[Baseline],
    per_baseline_hashes: _ScoreHashMap,
) -> _ReconVerdict:
    checked_score_maps = [
        per_baseline_hashes[b] for b in checked if b in per_baseline_hashes
    ]
    if len(checked_score_maps) >= 2:
        reference = checked_score_maps[0]
        shared = all(hmap == reference for hmap in checked_score_maps[1:])
        return _ReconVerdict(shared=shared, missing=False)
    if len(checked_score_maps) == 1:
        return _ReconVerdict(shared=True, missing=False)
    return _ReconVerdict(shared=False, missing=True)


def _disallowed_differences(flags: _SharedFlags) -> list[InvariantField]:
    disallowed: list[InvariantField] = []
    if not flags.split_shared:
        disallowed.append(InvariantField.SPLIT_HASH)
    if not flags.model_shared:
        disallowed.append(InvariantField.MODEL_OR_ENCODER_HASH)
    if not flags.scoring_shared:
        disallowed.append(InvariantField.SCORING_CODE_HASH)
    if not flags.metrics_shared:
        disallowed.append(InvariantField.METRICS_CODE_HASH)
    if not flags.recon_shared and not flags.score_hashes_missing:
        disallowed.append(InvariantField.RECONSTRUCTION_ERROR_ARRAYS)
    return disallowed


def _invariant_status(
    *,
    missing: list[Baseline],
    score_hashes_missing: bool,
    disallowed: list[InvariantField],
) -> AuditStatus:
    if disallowed:
        return AuditStatus.FAIL
    if missing or score_hashes_missing:
        return AuditStatus.BLOCKED_PENDING_RUN
    return AuditStatus.PASS


def build_invariant_results(
    invariant_inputs: dict[InvariantKey, dict[Baseline, InvariantHashes]],
    score_hashes_by_cell: dict[InvariantKey, _ScoreHashMap],
) -> list[BaselineInvariantResult]:
    invariant_results: list[BaselineInvariantResult] = []
    for key, by_baseline in sorted(invariant_inputs.items()):
        regime, seed, alpha_text = key
        required = list(controlled_baselines_for_regime(regime))
        missing = [b for b in required if b not in by_baseline]
        checked = [b for b in required if b in by_baseline]
        shared_flags = _shared_input_hashes(by_baseline, checked)
        verdict = _reconstruction_hash_verdict(
            checked, score_hashes_by_cell.get(key, {})
        )
        flags = _SharedFlags(
            split_shared=shared_flags.split_shared,
            model_shared=shared_flags.model_shared,
            scoring_shared=shared_flags.scoring_shared,
            metrics_shared=shared_flags.metrics_shared,
            recon_shared=verdict.shared,
            score_hashes_missing=verdict.missing,
        )
        disallowed = _disallowed_differences(flags)
        status = _invariant_status(
            missing=missing,
            score_hashes_missing=verdict.missing,
            disallowed=disallowed,
        )
        invariant_results.append(
            BaselineInvariantResult(
                regime=regime,
                seed=seed,
                alpha=alpha_text,
                status=status,
                checked_baselines=checked,
                missing_baselines=missing,
                split_hash_shared=flags.split_shared,
                model_or_encoder_hash_shared=flags.model_shared,
                reconstruction_error_hashes_shared=flags.recon_shared,
                scoring_code_hash_shared=flags.scoring_shared,
                metrics_code_hash_shared=flags.metrics_shared,
                disallowed_differences=[v.value for v in disallowed],
            )
        )
    return invariant_results
