from __future__ import annotations

from datp.audit.enums import AuditStatus
from datp.audit.schemas import BaselineInvariantResult
from datp.core.enums import (
    Baseline,
    Regime,
)


def build_invariant_results(
    invariant_inputs: dict[
        tuple[Regime, int, str | None], dict[Baseline, dict[str, str]]
    ],
    score_hashes_by_cell: dict[
        tuple[Regime, int, str | None], dict[Baseline, dict[tuple[str, str], str]]
    ],
    controlled_baselines: tuple[Baseline, ...],
) -> list[BaselineInvariantResult]:
    invariant_results: list[BaselineInvariantResult] = []
    for key, by_baseline in sorted(invariant_inputs.items()):
        regime, seed, alpha_text = key
        required = [
            b
            for b in controlled_baselines
            if not (b == Baseline.B3 and regime != Regime.A)
        ]
        missing = [b for b in required if b not in by_baseline]
        checked = [b for b in required if b in by_baseline]
        disallowed: list[str] = []
        split_shared = len({by_baseline[b]["split_hash"] for b in checked}) <= 1
        model_shared = (
            len(
                {by_baseline[b]["model_hash"] for b in checked}
                | {by_baseline[b]["encoder_hash"] for b in checked}
            )
            <= 1
        )
        scoring_shared = (
            len({by_baseline[b]["scoring_code_hash"] for b in checked}) <= 1
        )
        metrics_shared = (
            len({by_baseline[b]["metrics_code_hash"] for b in checked}) <= 1
        )

        per_baseline_hashes = (
            score_hashes_by_cell[key] if key in score_hashes_by_cell else {}
        )
        checked_score_maps = [
            per_baseline_hashes[b] for b in checked if b in per_baseline_hashes
        ]
        score_hashes_missing = len(checked_score_maps) == 0
        if len(checked_score_maps) >= 2:
            reference = checked_score_maps[0]
            recon_shared = all(hmap == reference for hmap in checked_score_maps[1:])
        elif len(checked_score_maps) == 1:
            recon_shared = True
        else:
            recon_shared = False

        if not split_shared:
            disallowed.append("split_hash")
        if not model_shared:
            disallowed.append("model_hash_or_encoder_hash")
        if not scoring_shared:
            disallowed.append("scoring_code_hash")
        if not metrics_shared:
            disallowed.append("metrics_code_hash")
        if not recon_shared and not score_hashes_missing:
            disallowed.append("reconstruction_error_arrays")
        status = AuditStatus.PASS
        if missing or score_hashes_missing:
            status = AuditStatus.BLOCKED_PENDING_RUN
        if disallowed:
            status = AuditStatus.FAIL
        invariant_results.append(
            BaselineInvariantResult(
                regime=regime,
                seed=seed,
                alpha=alpha_text,
                status=status,
                checked_baselines=checked,
                missing_baselines=missing,
                split_hash_shared=split_shared,
                model_or_encoder_hash_shared=model_shared,
                reconstruction_error_hashes_shared=recon_shared,
                scoring_code_hash_shared=scoring_shared,
                metrics_code_hash_shared=metrics_shared,
                disallowed_differences=disallowed,
            )
        )
    return invariant_results
