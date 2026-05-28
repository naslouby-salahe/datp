# DATP Scientific Drift Lock

This file defines the non-negotiable scientific boundaries for the DATP AI workflow.

It exists to prevent accidental drift while refactoring, implementing tickets, running experiments, updating results, or editing the manuscript.

A change is unsafe if it makes the project cleaner technically but less valid scientifically.

---

## 1. Core Identity

DATP means:

> Device-Aware Threshold Personalization: a controlled threshold-calibration study for non-IID federated IoT anomaly detection.

The core scientific question is not:

```text
Which FL algorithm is best?
Which anomaly detector is best?
Which dataset gives the highest score?
Which model-personalization method wins?
Which privacy mechanism is strongest?
```

The core scientific question is:

```text
When the encoder, training protocol, data, splits, and seeds are fixed, how much does threshold calibration scope affect cross-client false-positive-rate dispersion?
```

---

## 2. Mainline Controlled Comparison

The mainline controlled comparison is:

```text
B1 vs B2, with B3 and B4 as structured threshold-scope variants.
```

Mainline threshold policies:

| Label | Meaning | Core status |
|---|---|---|
| B0 | Centralized AE reference comparator | Reference only |
| B1 | Client-averaged shared threshold | Core |
| B2 | Per-client threshold | Core, primary comparison against B1 |
| B3 | Device-family mean threshold | Core threshold-scope variant, Regime A only unless explicitly extended |
| B4 | Cluster-mean threshold from reconstruction-error fingerprint | Core threshold-scope variant |
| B5 | Local-only bounding case | Supplementary only, never central claim |
| B-FedStatsBenign | Benign-only federated-statistics threshold comparator | Journal comparator, not numbered baseline |
| B-LaridiFaithful | Relaxed Laridi-style reproduction using anomaly-labeled calibration summaries | Only if permitted; outside DATP benign-only assumption |

Do not rename these casually.

Do not change their semantics to fit code.

Do not reuse a label for a different method.

---

## 3. Locked Baseline Semantics

### B1 — Client-averaged shared threshold

B1 is a single shared threshold derived from eligible clients' local benign calibration thresholds.

Required properties:

1. One scalar threshold is broadcast.
2. Eligible clients contribute equally unless an explicitly named sensitivity variant says otherwise.
3. Calibration-pending clients do not distort the eligible-client calculation.
4. B1 does not retrain the encoder.
5. B1 does not use attack labels.

### B2 — Per-client threshold

B2 assigns each eligible client its own benign calibration threshold.

Required properties:

1. Each eligible client uses its own benign calibration errors.
2. The canonical threshold is p95 unless the active config explicitly changes q.
3. Calibration-pending clients use the B1/global fallback.
4. B2 does not retrain the encoder.
5. B2 does not use attack labels.
6. B2 is expected to reduce benign-tail FPR dispersion under stable calibration/test distributions, but detection-quality tradeoffs must be reported.

### B3 — Family-mean threshold

B3 groups eligible clients by configured device family.

Required properties:

1. Family labels must come from the canonical family taxonomy.
2. Each family threshold is computed from eligible clients in that family.
3. Calibration-pending clients are excluded from eligible-only family calculation.
4. Missing or singleton family behavior must be explicit.
5. B3 does not retrain the encoder.

### B4 — Cluster-mean threshold

B4 clusters eligible clients using the canonical reconstruction-error fingerprint:

```text
[mean(error), std(error), skew(error), p95(error)]
```

Required properties:

1. Uses benign calibration reconstruction-error summaries.
2. Does not use device taxonomy as input.
3. Does not use attack labels.
4. Calibration-pending clients are excluded from clustering.
5. Calibration-pending clients use the global fallback.
6. The journal main-paper canonical K is the one locked by the active journal package.
7. Other K values are exploratory or supplementary only.

---

## 4. Regime Semantics

| Regime | Dataset / partition | Status | Claim boundary |
|---|---|---|---|
| Regime A | N-BaIoT natural physical-device split | Confirmatory | Primary B1 vs B2 evidence |
| Regime B-a | CICIoT2023 file-level pseudo-clients | Boundary condition | Near-homogeneous applicability check |
| Regime B-b | CICIoT2023 device-MAC or device-group repartition | Conditional | Used only after feasibility gate |
| Regime C | N-BaIoT Dirichlet severity sweep | Supportive / exploratory severity evidence | Not primary confirmatory evidence |
| Regime D | Edge-IIoTset external validation | Conditional external validation | Used only after feasibility gate |

Do not make Regime B-a sound like physical-device evidence.

Do not make Regime C the primary claim.

Do not use Regime D without feasibility evidence.

Do not invent client identity for datasets that do not support it.

---

## 5. Metrics Lock

Primary metric:

```text
CV(FPR)
```

Required companion:

```text
coverage ratio
```

Whenever CV(FPR) is reported, coverage ratio must be reported nearby.

Required detection-quality context:

1. Mean FPR.
2. Mean TPR.
3. CV(TPR), when used in result tables.
4. Macro-F1.
5. P10 Macro-F1 or lower-tail Macro-F1 when available.
6. Worst-client balanced accuracy.
7. IQR(FPR) or max-min FPR when guarding against small-denominator artifacts.

Required statistical context:

1. Seed-level deltas.
2. Sign consistency.
3. Bootstrap CI where required by the active plan.
4. Wilcoxon and Cliff's delta only as secondary descriptive evidence when included.
5. Explicit seed count.

Do not report only aggregate accuracy.

Do not hide lower-tail degradation.

Do not report CV(FPR) without coverage.

Do not present five-seed evidence as a high-powered population test.

---

## 6. Shared-Training Lock

For any fixed experiment cell:

```text
dataset + regime + seed + alpha + training protocol
```

the controlled B1–B4 comparison must train once and derive thresholds from shared score artifacts.

Allowed:

1. One shared checkpoint for B1–B4 in the same cell.
2. Shared score parquet artifacts.
3. Multiple threshold policies computed downstream from the same score artifacts.
4. Reuse verification before stored-score analyses.

Forbidden:

1. Training separately for B1.
2. Training separately for B2.
3. Training separately for B3.
4. Training separately for B4.
5. Calling training from threshold-analysis modules.
6. Recomputing score artifacts silently inside result/report code.
7. Allowing output paths to imply one checkpoint per threshold baseline in the controlled ladder.

If a stress-test comparator changes training, it must be outside the core ladder.

---

## 7. Stage Boundary Lock

Pipeline stages are:

```text
prepare → score → threshold/result → report
```

Rules:

1. `prepare` creates processed data artifacts.
2. `score` creates checkpoints and score artifacts.
3. `threshold/result` reads scores and writes metrics.
4. `report` reads metrics, tables, figures, and sidecars.
5. No downstream stage triggers an upstream stage implicitly.
6. No reporting module trains.
7. No table or figure script recomputes scientific results from raw data.
8. No threshold variant reaches into raw data when stored scores should be used.
9. No result file is written unless the producing stage succeeds.
10. Temporary files do not count as results.

---

## 8. Config and Parameter Lock

Scientific parameters must flow from config.

Examples include:

1. q / percentile level.
2. n_min.
3. seed list.
4. alpha list.
5. number of clients.
6. B4 K.
7. convergence thresholds.
8. round budgets.
9. calibration-size sweep values.
10. shrinkage lambda values.
11. conformal alpha.
12. dataset feature counts.
13. paths to raw and processed data.
14. output roots.
15. stress-test comparator settings.

Forbidden:

1. Hidden module constants for scientific parameters.
2. Defaults added to make tests pass.
3. CLI values that override locked plans silently.
4. Runtime-generated config values not saved to `resolved_config.yaml`.
5. Result artifacts without config lineage.

---

## 9. Dataset and Feature Lock

Dataset claims must be checked against actual code, configs, and artifacts.

Known critical guards:

1. N-BaIoT Regime A uses physical-device clients.
2. CICIoT2023 Regime B-a uses file-level pseudo-clients, not physical devices.
3. CICIoT2023 feature count must match actual prepared schema.
4. N-BaIoT feature count must match actual prepared schema.
5. Edge-IIoTset is conditional and must pass feasibility gates before claims or full experiments.
6. CICIoT2023 B-b requires feasible device-MAC or device-group evidence before use.
7. Processed artifacts are Parquet.
8. Attack data must not enter benign-only calibration unless explicitly required by an out-of-DATP comparator.
9. Splits must be recorded and reproducible.
10. Dataset caps must be documented and consistent.

Do not assume metadata exists.

Do not infer physical devices from filenames.

Do not rename regimes to hide weak partitioning.

---

## 10. Journal Extension Lock

The journal extension may add:

1. Seed extension.
2. Edge-IIoTset if feasible.
3. CICIoT2023 B-b if feasible.
4. FedProx as aggregation-side stress test.
5. Ditto only if faithfully implemented.
6. `FedRep-AE/FedPer-AE fallback` if Ditto is not faithful.
7. `B-FedStatsBenign`.
8. `B-LaridiFaithful` only when anomaly-labeled calibration is allowed.
9. q-sensitivity.
10. calibration-size sweep.
11. local-global threshold shrinkage.
12. split-conformal B2-conf.
13. B4 feature ablation.
14. JS-divergence benefit analysis.
15. per-client CDF mechanism analysis.
16. threshold-shift analysis.
17. operational alert-burden analysis with declared traffic-volume source.
18. temporal MVE / one-shot recalibration only with the active plan's wording.

The journal extension must not become:

1. A broad FL-IDS benchmark.
2. A broad personalized-FL benchmark.
3. A hardware deployment paper.
4. A privacy paper.
5. A poisoning or evasion robustness paper.
6. A concept-drift paper.
7. A multi-dataset leaderboard.
8. A FedBN paper.
9. A paper that hides the conference overlap.
10. A paper that overstates DATP against anomaly-labeled methods.

---

## 11. Claim Discipline Lock

Allowed core claim pattern:

> Under the tested Regime A physical-device N-BaIoT protocol, per-client threshold calibration reduces cross-client FPR dispersion relative to a shared threshold under a fixed FedAvg autoencoder.

Allowed journal claim pattern:

> DATP's threshold-scope effect remains observable under the stronger journal protocol, subject to the active feasibility gates, result-freeze evidence, and claim-survival wording.

Forbidden claim patterns:

1. DATP improves anomaly detection globally.
2. DATP is better than all thresholding methods.
3. DATP is privacy-preserving beyond raw-data locality.
4. B4 provides privacy.
5. DATP is poisoning robust.
6. DATP is evasion robust.
7. DATP handles concept drift.
8. DATP is hardware validated.
9. DATP is deployment-ready.
10. DATP proves per-client thresholds always improve results.
11. CICIoT2023 file-level results prove device-level behavior.
12. Regime C proves the main claim.
13. FedProx or Ditto results belong to the same causal ladder as B1–B4.
14. B-FedStatsBenign is the original Laridi method.
15. A fallback personalized model is Ditto when it is not actually Ditto.

---

## 12. Artifact Lineage Lock

Every reported metric, table, and figure must trace:

```text
raw data
→ processed split
→ resolved config
→ checkpoint
→ score parquet
→ metrics
→ table
→ figure sidecar
→ manuscript claim
```

Required lineage fields:

1. Dataset ID.
2. Dataset version or source fingerprint.
3. Raw artifact hash where available.
4. Processed artifact hash.
5. Split manifest hash.
6. Resolved config hash.
7. Checkpoint hash.
8. Score parquet hashes.
9. Metrics hash.
10. Table hash.
11. Figure sidecar hash.
12. Git commit.
13. Seed.
14. Regime.
15. Baseline or comparator.
16. Alpha if applicable.
17. Training protocol.
18. Convergence status.
19. Eligibility count.
20. Coverage ratio.

A broken lineage invalidates the affected claim.

---

## 13. Manuscript Lock

Manuscript work begins only after the active result-freeze criteria pass.

Before manuscript edits:

1. Freeze active results.
2. Verify all lineage chains.
3. Select claim-survival wording.
4. Confirm null, mixed, skipped, and failed outcomes.
5. Confirm overlap disclosure against the conference paper.
6. Confirm no unsupported claim remains.
7. Confirm figure/table sidecars exist.
8. Confirm abstract and conclusion are updated last.

Do not write the abstract first.

Do not update claims while experiments are still mutable.

Do not silently remove failed experiments.

Do not let page-budget cuts remove limitations.

---

## 14. Ticket Completion Lock

A ticket cannot be `DONE` if:

1. Scientific invariants are not audited.
2. The implementation was not checked against actual code.
3. Tests were not updated.
4. Quality gates were not run or documented.
5. Result artifacts are missing or invalid.
6. Claims are unsupported.
7. Source hierarchy conflicts remain.
8. Human intervention is required.
9. Feasibility gates are unresolved.
10. The final audit did not produce a PASS-like verdict.

Allowed non-DONE statuses:

```text
NOT_STARTED
IN_PROGRESS
BLOCKED_HUMAN
BLOCKED_TECHNICAL
BLOCKED_SCIENTIFIC
SKIPPED_WITH_REASON
REAUDIT_REQUIRED
```

Use `REAUDIT_REQUIRED` after structural moves, major refactors, or scientific-scope touches.

---

## 15. Final Stop Conditions

Stop immediately if any of these occur:

1. A change would alter the core controlled comparison.
2. A result would be produced from unverified artifacts.
3. A ticket asks for an out-of-scope experiment.
4. A tool output contradicts the plan.
5. A dataset feasibility assumption is unsupported.
6. A manuscript claim lacks direct evidence.
7. A stress-test comparator is being moved into the core ladder.
8. A fallback method is being mislabeled.
9. A code refactor would preserve old wrappers or redirects.
10. An agent is about to mark incomplete work as done.

Stopping with a precise blocker is correct.

Continuing through scientific uncertainty is wrong.