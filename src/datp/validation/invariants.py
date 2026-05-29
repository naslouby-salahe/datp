from __future__ import annotations

from dataclasses import dataclass, replace

from datp.validation.enums import AuditStatus
from datp.validation.schemas import BaselineInvariantResult
from datp.core.enums import (
    Baseline,
    Regime,
    controlled_baselines_for_regime,
)

_InvariantKey = tuple[Regime, int, str | None]
_InvariantInputs = dict[Baseline, dict[str, str]]
_ScoreHashMap = dict[Baseline, dict[tuple[str, str], str]]


@dataclass(frozen=True, slots=True)
class SharedFlags:
    split_shared: bool
    model_shared: bool
    scoring_shared: bool
    metrics_shared: bool
    recon_shared: bool
    score_hashes_missing: bool


def _shared_input_hashes(
    by_baseline: _InvariantInputs,
    checked: list[Baseline],
) -> SharedFlags:
    split_shared = len({by_baseline[b]["split_hash"] for b in checked}) <= 1
    model_shared = (
        len(
            {by_baseline[b]["model_hash"] for b in checked}
            | {by_baseline[b]["encoder_hash"] for b in checked}
        )
        <= 1
    )
    scoring_shared = len({by_baseline[b]["scoring_code_hash"] for b in checked}) <= 1
    metrics_shared = len({by_baseline[b]["metrics_code_hash"] for b in checked}) <= 1
    return SharedFlags(
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
) -> tuple[bool, bool]:
    checked_score_maps = [
        per_baseline_hashes[b] for b in checked if b in per_baseline_hashes
    ]
    if len(checked_score_maps) >= 2:
        reference = checked_score_maps[0]
        return all(hmap == reference for hmap in checked_score_maps[1:]), False
    if len(checked_score_maps) == 1:
        return True, False
    return False, True


def _disallowed_differences(flags: SharedFlags) -> list[str]:
    disallowed: list[str] = []
    if not flags.split_shared:
        disallowed.append("split_hash")
    if not flags.model_shared:
        disallowed.append("model_hash_or_encoder_hash")
    if not flags.scoring_shared:
        disallowed.append("scoring_code_hash")
    if not flags.metrics_shared:
        disallowed.append("metrics_code_hash")
    if not flags.recon_shared and not flags.score_hashes_missing:
        disallowed.append("reconstruction_error_arrays")
    return disallowed


def _invariant_status(
    *,
    missing: list[Baseline],
    score_hashes_missing: bool,
    disallowed: list[str],
) -> AuditStatus:
    if disallowed:
        return AuditStatus.FAIL
    if missing or score_hashes_missing:
        return AuditStatus.BLOCKED_PENDING_RUN
    return AuditStatus.PASS


def build_invariant_results(
    invariant_inputs: dict[_InvariantKey, _InvariantInputs],
    score_hashes_by_cell: dict[_InvariantKey, _ScoreHashMap],
) -> list[BaselineInvariantResult]:
    invariant_results: list[BaselineInvariantResult] = []
    for key, by_baseline in sorted(invariant_inputs.items()):
        regime, seed, alpha_text = key
        required = list(controlled_baselines_for_regime(regime))
        missing = [b for b in required if b not in by_baseline]
        checked = [b for b in required if b in by_baseline]
        shared_flags = _shared_input_hashes(by_baseline, checked)
        recon_shared, score_hashes_missing = _reconstruction_hash_verdict(
            checked, score_hashes_by_cell.get(key, {})
        )
        flags = replace(
            shared_flags,
            recon_shared=recon_shared,
            score_hashes_missing=score_hashes_missing,
        )
        disallowed = _disallowed_differences(flags)
        status = _invariant_status(
            missing=missing,
            score_hashes_missing=score_hashes_missing,
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
                reconstruction_error_hashes_shared=recon_shared,
                scoring_code_hash_shared=flags.scoring_shared,
                metrics_code_hash_shared=flags.metrics_shared,
                disallowed_differences=disallowed,
            )
        )
    return invariant_results
