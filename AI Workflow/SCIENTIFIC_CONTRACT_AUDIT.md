# Scientific Contract Audit

This file protects the DATP scientific identity during refactoring.

## Locked identity

DATP is a controlled threshold-calibration study for federated IoT anomaly/malware detection. The mainline comparison holds the encoder, FedAvg training, data, splits, and seeds fixed while varying threshold scope.

## Non-negotiable invariants

| Invariant | Required behavior | Audit status |
|---|---|---|
| Fixed encoder | Do not silently alter the AE/encoder architecture in the mainline comparison. | `PENDING` |
| Fixed FedAvg mainline | Do not replace the mainline aggregation protocol when refactoring. | `PENDING` |
| Threshold-scope-only design | B1/B2/B3/B4 differ by threshold calibration scope, not by retraining. | `PENDING` |
| Shared training per cell | For a fixed dataset/regime/seed/alpha, train once and derive thresholds from shared score artifacts. | `PENDING` |
| No retraining per baseline | Thresholding/result code must not trigger baseline-specific training. | `PENDING` |
| Stage boundaries | Prepare → score → threshold/result → report. Downstream stages read upstream artifacts. | `PENDING` |
| Config-driven scientific parameters | Scientific/runtime parameters must come from config, not hidden constants. | `PENDING` |
| Calibration-pending handling | Clients below benign calibration `n_min` use the global fallback and are excluded from eligible-only operations. | `PENDING` |
| Baseline semantics | B1/B2/B3/B4 meanings must not drift. | `PENDING` |
| Claim discipline | Do not introduce unsupported claims in comments, docs, or reports. | `PENDING` |

## Baseline semantic lock

| Baseline | Meaning |
|---|---|
| B0 | Centralized reference comparator only. |
| B1 | Shared/global threshold, arithmetic mean of eligible per-client thresholds unless active docs say otherwise. |
| B2 | Per-client threshold, typically the configured benign calibration quantile. |
| B3 | Family/group threshold where scientifically applicable. |
| B4 | Fingerprint-cluster threshold with calibration-pending fallback to global threshold. |

## Stage-boundary audit

| Stage | May read | May write | Must not do |
|---|---|---|---|
| Prepare | Raw/source data and config | Processed artifacts | Thresholding/results/reporting. |
| Score | Checkpoints, processed splits, config | Score artifacts | Threshold selection or result claims. |
| Threshold/result | Score artifacts, threshold config | Metrics/results | Training or score recomputation. |
| Analysis/reporting | Metrics/results/scores as allowed | Tables/figures/reports | Training or hidden recomputation. |

## Scientific audit findings

| ID | Finding | Evidence | Risk | Required fix | Packet | Status |
|---|---|---|---|---|---|---|
| SCI-000 | Scientific audit not yet run on current code. | Workflow just created. | Unknown | Run PKT-001/PKT-006 audits. | PKT-001 | `OPEN` |

## Required scientific review gates

- Before moving thresholding, scoring, training, or metrics code.
- After consolidating constants/enums/config values.
- After eligibility/calibration logic changes.
- Before final integration.
- During final hostile review.
