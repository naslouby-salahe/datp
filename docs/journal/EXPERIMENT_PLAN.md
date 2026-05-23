# EXPERIMENT PLAN

Documentation-only planning artifact. No experiments are executed by this plan.

The journal experiment strategy is: verify existing artifacts first, reuse stored scores where valid, run new training only when the dataset, seed, aggregation, personalization, or temporal split changes, then freeze results before manuscript editing.

---

## 1. Experiment Principles

- B1 vs B2 on Regime A remains the confirmatory center.
- B4 remains secondary.
- B3 is preserved for Regime A.
- Regime B-a remains an applicability-boundary case.
- Regime B-b exists only if Gate 0 verifies it.
- Regime C remains supportive severity evidence.
- Regime D exists only if Gate 0 verifies Edge-IIoTset.
- `B-FedStatsBenign`, FedProx, Ditto, and `LocalHead-PersonalizedAE` are comparators/stress tests, not core baselines.
- Stored-score analyses happen before heavy reruns.
- Result interpretation is pre-specified before result inspection.
- Null, mixed, failed, and suppressed outcomes are reported honestly.

---

## 2. Gate Overview

| Gate | Work | Purpose | Stored Scores? | Retraining? | Output | Status |
|---|---|---|---|---|---|---|
| Gate 0 | Artifact inventory and score verification | Decide what can be reused. | Read-only | No | Verification reports and reuse verdicts. | Pending |
| Gate 0 | CICIoT2023 root, feature, and B-b feasibility | Decide whether B-b exists. | N/A | No | One B-b outcome flag. | Pending |
| Gate 0 | Edge-IIoTset feasibility | Decide whether Regime D exists. | N/A | No | One Regime D outcome flag. | Pending |
| Gate 0 | Regime C completeness | Verify α and IID cells. | Read-only | No | Completeness verdict. | Pending |
| Gate 0 | Protocol locks | Lock `B-FedStatsBenign`, FedProx, Ditto/LocalHead, temporal rules. | N/A | No | Written lock sections. | Pending |
| Gate 1 | Stored-score analyses | q, calibration size, `τ-shrink`, `B2-conf`, B4 ablation, mechanism analyses. | Yes | No | Tables/figures. | Blocked until Gate 0 |
| Gate 1 | 10-seed extension decision | Decide/perform seed extension if journal claim requires it. | Existing 5 yes; new 5 no | Yes for seeds 5–9 | 10-seed metrics/CIs. | Pending |
| Gate 2 | Regime D | Edge-IIoTset external validation if feasible. | No | Yes | New scores/results. | Conditional |
| Gate 2 | Regime B-b | CICIoT2023 repartition if feasible. | No | Yes | New scores/results. | Conditional |
| Gate 3 | Stress tests | FedProx and Ditto/LocalHead. | No | Yes | Stress-test grid and absorption table. | Conditional |
| Gate 4 | Temporal recalibration probe | Frozen vs one-shot threshold recalibration. | Partially | Yes for early-window training | Temporal table/figure. | Conditional |
| Gate 5 | Result freeze | Freeze all result artifacts and claim wording. | N/A | No | Frozen result package. | Pending |

---

## 3. Gate 0 Verification Experiments

These are not scientific experiments; they are readiness checks.

| Check | Pass Requirement | Failure Handling |
|---|---|---|
| Score reuse | Recomputed metrics match references within tolerance and lineage passes. | Affected stored-score analyses blocked or rerun required. |
| CICIoT root | One canonical root selected. | All new CICIoT work blocked. |
| CICIoT features | 47-vs-39 discrepancy explained. | B-b blocked. |
| CICIoT B-b | One allowed B-b outcome assigned. | Suppress B-b if rejected/blocked. |
| Edge-IIoTset | One allowed Regime D outcome assigned. | Suppress Regime D if rejected/blocked. |
| Regime C | All required α/IID cells verified or missing cells documented. | Partial Regime C claims only. |
| B3 | Regime A B3 reproduces. | B3 reporting blocked until resolved. |
| Citation status | Critical sources verified or marked pending with safe wording. | Pending source cannot support critical claim. |
| Seed status | One seed-status label assigned. | No 10-seed claim until seed extension exists. |

The reproduced 5-seed CI check must use an explicit reference width. Current reference: `[0.647, 0.769]`, width `0.122`. Gate 2 is blocked if the reproduced 5-seed BCa CI width exceeds `0.147` (`1.2 × 0.122`) or otherwise materially disagrees with the reference.

---

## 4. Gate 1 Stored-Score Analyses

| Analysis | Scientific Question | Main Output | Failure/Null Interpretation |
|---|---|---|---|
| q-sensitivity | Is the B1→B2 effect tied only to q=0.95? | q-grid table/heatmap. | Inversions are reported; core claim narrowed if needed. |
| Calibration-size sweep | How does low benign calibration count affect DATP? | n_cal curve. | Low-data instability becomes a limitation. |
| `τ-shrink` | Can interpolation reduce disparity without harming low-end clients? | λ curve with CV(FPR), Macro-F1, P10 Macro-F1. | Non-monotone behavior is reported. |
| `B2-conf` | Does a conformal variant address construction-tautology critique? | Coverage diagnostic. | Coverage failure is reported as limitation. |
| `B-FedStatsBenign` | How does benign-only federated summary thresholding compare? | Comparator table + between_ratio. | If strong, DATP claim is narrowed to local benign threshold personalization. |
| B4 ablation | Are B4 fingerprints meaningful or arbitrary? | Feature-ablation table + cluster contingency. | Instability becomes limitation. |
| JS divergence vs gain | Does measured heterogeneity track DATP benefit? | Scatter + correlation. | Weak relation reported as non-causal/limited. |
| Threshold shift vs ΔFPR/ΔTPR | How do client thresholds change outcomes? | Per-client scatter/table. | All clients shown; no filtering. |
| Alert burden | What does FPR change mean operationally? | Alerts/day or normalized alert table. | If timestamps unavailable, label hypothetical. |
| B3 preservation | Keep family-mean evidence visible. | B3 row. | Missing/mismatch blocks B3 claim. |
| Regime C severity | Does heterogeneity severity align with B1−B2 gap? | Per-α figure/table. | Partial/missing cells disclosed. |
| Per-client CDF / failure mode | Explain worst-client behavior. | CDF overlay + failure-mode table. | Use canonical device labels only. |

---

## 5. Gate 1 Seed Extension

The journal may use the current 5-seed results only as preliminary or conference-reference numbers unless the claim is explicitly scoped to 5 seeds. For a stronger journal claim, train seeds 5–9.

Rules:
- Existing seed 0–4 stored-score analyses may run after verification.
- Seeds 5–9 require new shared training and scoring.
- The 10-seed result supersedes the 5-seed result even if less favorable.
- BCa CI is computed over per-seed deltas.
- If the 10-seed CI excludes zero, the confirmatory extension survives.
- If the CI touches/includes zero, the result becomes directionally consistent but statistically inconclusive.
- If per-seed signs are mixed, the claim becomes characterization, not confirmation.

---

## 6. Gate 2 External Validity

### 6.1 Regime D — Edge-IIoTset

Run only under:
- `EDGE_FEASIBLE_DEVICE_CLIENTS`
- `EDGE_FEASIBLE_GROUP_CLIENTS_ONLY`

Main outputs:
- Regime D B1/B2/B4 table.
- B3 only if valid and non-circular.
- q/variant/comparator analyses only after core Regime D scores are verified.

Reporting:
- Device-client outcome: “device-partitioned Regime D.”
- Group-only outcome: “group-partitioned external validation,” not physical-device validation.
- Rejected/blocked outcome: Regime D suppressed with reason; no substitute dataset added.

### 6.2 Regime B-b — CICIoT2023

Run only under:
- `B_B_FEASIBLE_MAC`
- `B_B_FEASIBLE_GROUP_ONLY`

Main outputs:
- Regime B-b B1/B2/B4 table.
- B3 only if valid and non-circular.
- Clear labeling of MAC-based or group-based partition.

Rejected/blocked outcome:
- Report CICIoT2023 under B-a only.

---

## 7. Gate 3 Stress Tests

### 7.1 FedProx

Purpose:
- Test whether B1→B2 CV(FPR) gain survives a heterogeneity-aware aggregation stress test.

Rules:
- µ grid: `{0.0, 0.001, 0.01, 0.1, 1.0}`.
- µ=0.0 must match FedAvg within tolerance.
- E equals FedAvg E.
- If E=1, state the stress test is conservative and does not explore larger local-update heterogeneity.
- Convergence failure is reported, not tuned away.

Interpretation:
- Gain survives: threshold personalization remains complementary.
- Gain absorbed: DATP claim narrows to FedAvg-style/shared-encoder settings.
- Failure: FedProx stress test unavailable under locked grid.

### 7.2 Ditto / `LocalHead-PersonalizedAE`

Purpose:
- Test whether model-side personalization makes threshold personalization redundant.

Rules:
- Use true Ditto only if implemented faithfully.
- Otherwise use `LocalHead-PersonalizedAE`.
- Main µ = 0.01 unless unavailable.
- Other µ values supplementary.
- Absorption thresholds from PRE plan are fixed.

Interpretation:
- Strong retention: threshold personalization remains complementary.
- Partial absorption: model personalization is a boundary condition.
- Near-full absorption: DATP claim narrows to lightweight alternative under shared-encoder/FedAvg-style settings.

---

## 8. Gate 4 Temporal Recalibration Probe

Run only under `TEMPORAL_FEASIBLE`.

Design:
1. Chronological 70/30 split per client.
2. Train/calibrate on early data.
3. Evaluate frozen thresholds on late data.
4. Perform one-shot threshold recalibration at the boundary.
5. Report recovery ratio and FPR stability.

Allowed outcomes:
- Helps.
- Neutral/no meaningful drift.
- Hurts/insufficient one-shot recovery.
- Infeasible with explicit rejection reason.

No streaming drift detector is added.

---

## 9. Rerun Policy

Do not rerun previous regimes by default.

Rerun only if:
- Score verification fails.
- Scores are missing/corrupted.
- Config compatibility fails.
- Dataset split or client partition changes.
- Seed set extends to 10.
- Training algorithm changes to FedProx.
- Model personalization changes to Ditto or LocalHead.
- Dataset changes to Edge-IIoTset.
- CICIoT2023 B-b partition is created.
- Temporal chronological training is required.
- Existing artifacts are incomplete for an active analysis.

Stored-score threshold analyses do not require retraining after verification succeeds.

---

## 10. Compute Rules

Before any sweep larger than one cell:
- Measure existing per-cell runtime from logs.
- Estimate disk usage from current score/checkpoint sizes.
- Validate machine profile and resource bounds.
- Set concurrency from RAM/GPU constraints, not a hardcoded number.
- Use skip/resume markers.
- Write `ABORTED.txt` on unclean exit.
- Atomic-write `metrics.json` only on success.
- Do not create success-shaped placeholders.

Known cost categories:
| Category | New Training Required |
|---|---|
| Group B stored-score analyses | No |
| Seed extension seeds 5–9 | Yes |
| Regime D | Yes |
| Regime B-b | Yes |
| FedProx | Yes |
| Ditto/LocalHead | Yes |
| Temporal early-window training | Yes |

Unknown runtimes are marked `MEASURE FIRST`; no runtime is invented.

---

## 11. Artifact Lineage Requirement

Every reported metric/table/figure must trace:

`raw data → processed split → resolved config → checkpoint → score parquet → metrics → table → figure sidecar`

Required fields:
- Dataset ID and version.
- Raw and processed artifact hashes.
- Resolved config hash.
- Checkpoint hash.
- Score parquet hashes.
- Metrics hash.
- Table and figure sidecar hashes.
- Git commit.
- Seed, regime, baseline/comparator, α if applicable.
- Training convergence status.

A broken lineage invalidates the affected claim.

---

## 12. Result Freeze Criteria

Gate 5 requires:

- All active experiments completed or explicitly suppressed.
- All reused cells are `VERIFIED_REUSE_SAFE`.
- All metrics reproducible.
- Same seed determinism passes.
- Resolved configs exist for every run.
- Lineage exists for every reported result.
- All tables/figures generated from canonical reporting pipeline.
- All figure sidecars exist.
- Null, mixed, failed, and skipped experiments documented.
- Stress tests kept outside the core ladder.
- Claim-survival wording selected before manuscript writing.
- 40% extension measurement prepared as internal benchmark, not Computer Networks requirement.
- Versioning and citation metadata ready for update.
- No unsupported claim remains.

Before prose writing begins, perform an anti-HARKing attestation:
- Compare every planned result claim against the locked outcome wording.
- Any new interpretation must be justified before writing, not after prose drafting.
