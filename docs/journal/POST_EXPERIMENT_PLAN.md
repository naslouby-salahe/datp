# POST-EXPERIMENT PLAN

Documentation-only planning artifact. No manuscript files are edited by this plan. Manuscript updates begin only after `EXPERIMENT_PLAN.md` Gate 5 result freeze.

This file controls claim survival, manuscript update order, figure/table placement, overlap disclosure, reviewer-risk responses, and submission readiness.

Narrow claim wording (must appear wherever DATP's scope is introduced):
> DATP does not claim global superiority over anomaly-labeled thresholding methods. Its claim is narrower: under a benign-only calibration assumption and a fixed FL encoder, device-aware threshold scope reduces FPR dispersion relative to a shared threshold.

Dataset scope note:
> New/expanded external dataset work is limited to Edge-IIoTset and the conditional CICIoT2023 B-b repartition. N-BaIoT remains the confirmatory anchor and is not counted as new dataset expansion.

---

## 1. Result Consolidation

| Result Area | Source | Consolidated Output | Required Check | Claim Impact |
|---|---|---|---|---|
| Regime A B1 vs B2 | Frozen Regime A results. | Primary table/figure with seed count and BCa CI. | Reproducible and lineage-valid. | Main confirmatory endpoint. |
| Regime A B3 | Regime A B3 results. | Preserved B3 row. | Reproduces stored-score reference. | Comparator preservation. |
| Regime A B4 | Regime A B4 + ablation. | B4 row + ablation/contingency. | Canonical K=3 main result. | Secondary grouped approximation. |
| Regime B-a | CICIoT2023 file-level results. | Boundary table. | Reproducible. | Near-homogeneous boundary. |
| Regime B-b | Conditional B-b results. | MAC/group table if feasible. | Gate 0 feasibility flag matches output. | Conditional external evidence. |
| Regime C | Per-α results. | Severity table/figure. | α/IID completeness checked. | Supportive severity evidence. |
| Regime D | Edge-IIoTset results. | External-validation table. | Dataset feasibility and lineage valid. | External validation or boundary. |
| `B-FedStatsBenign` | Comparator outputs. | Comparator table + between_ratio. | Benign-only protocol passes. | Threshold-comparator support, not faithful attack-labeled claim. |
| FedProx | Stress-test outputs. | FedProx grid/summary. | µ=0.0 sanity and convergence status. | Aggregation stress test. |
| Ditto/FedRep-AE fallback | Stress-test outputs. | Absorption table. | Correct naming (fallback labeled clearly, never Ditto); absorption rule applied. | Model-personalization stress test. |
| Temporal probe | Temporal outputs. | Frozen vs recalibrated table/figure. | Feasibility and outcome rule. | Temporal recalibration only. |
| Alert burden | Mechanism analysis. | Alerts/device/day table (or suppression note). | Derived from real timestamped rates or cited operational rate only. | Do not invent rates. If neither is available, metric is omitted. |
| Other mechanism analyses | Gate 1 analyses. | CDF, JS/gain, threshold-shift, calibration-size, q, shrinkage, conformal diagnostics. | All all-client or all-seed inclusion rules satisfied. | Mechanistic explanation, non-causal. |
| Skipped/failed items | Gate status flags. | Failure/suppression table. | Every skipped gate has one reason. | Honesty and limitations. |
| Privacy boundary | B4 fingerprint description. | Bounded-disclosure table. | No formal privacy claim. | Scope control. |

---

## 2. Claim Survival Matrix

The wording below is binding. Instantiate only with frozen numbers.

### 2.1 Main Regime A Outcome

Primary statistic: BCa bootstrap CI on per-seed `Δ_s = CV(FPR)[B1,s] − CV(FPR)[B2,s]`. Secondary robustness indicator: `x/10` seeds with positive Δ_s. Wilcoxon and Cliff’s delta are secondary/descriptive only.

| Outcome | Required Wording | Claim Status |
|---|---|---|
| B2 beats B1, 10-seed BCa CI excludes zero, and most seeds positive | “Under Regime A natural device split on N-BaIoT, B2 reduces CV(FPR) from [B1] to [B2] over 10 seeds (95% BCa CI: [a, b]; [x]/10 seeds positive) under the tested fixed-encoder FedAvg protocol.” | Confirmatory extension survives. |
| B2 beats B1 but CI touches/includes zero | “B2 reduces CV(FPR) directionally, but the 95% BCa CI over 10 seeds includes zero; the Regime A result is directionally consistent but statistically inconclusive at the journal seed budget.” | Downgrade to directional evidence. |
| Mixed signs across seeds | “Per-seed deltas change sign; the result is reported as characterization of threshold-scope behavior, not a confirmatory comparison.” | Main claim narrowed. |
| 5-seed reproduction materially disagrees or CI width > 0.147 | “Gate 2 expansion is paused because the reproduced 5-seed CI does not match the reference tolerance. The cause is investigated before extension claims are made.” | Expansion blocked. |

### 2.2 B4 and B3

| Outcome | Required Wording |
|---|---|
| B4 partially recovers B2 | “B4 with K=3 recovers approximately [x]% of B2's CV(FPR) improvement without using device-type taxonomy; this is a practical grouped approximation, not the main claim.” |
| B4 unstable/mixed | “B4 is sensitive to the fingerprint/cluster structure under the tested setting and is reported as exploratory grouped thresholding.” |
| B3 underperforms B2 | “B3 is preserved as a family/group comparator but does not match the per-client calibration behavior of B2 under Regime A.” |

### 2.3 Regime B-a / B-b

| Outcome | Required Wording |
|---|---|
| B-a remains near-null | “Regime B-a is a near-homogeneous file-level boundary where threshold-scope effects are not expected to manifest strongly.” |
| B-b MAC feasible and positive | “On the MAC-based CICIoT2023 repartition (Regime B-b, K=[x]), B2 reduces CV(FPR) from [y] to [z] (95% BCa CI: [a, b]).” |
| B-b group-only feasible and positive | “On the group-based CICIoT2023 repartition (Regime B-b, group-partitioned, K=[x]), B2 reduces CV(FPR) from [y] to [z] (95% BCa CI: [a, b]); this is not physical-device validation.” |
| B-b rejected/blocked | “CICIoT2023 B-b was not feasible from the available metadata and eligibility constraints; CICIoT2023 is reported under Regime B-a only.” |

### 2.4 Regime C

| Outcome | Required Wording |
|---|---|
| Severity trend supports DATP | “The B1−B2 CV(FPR) gap varies with Dirichlet α, consistent with the heterogeneity-severity framing.” |
| Severity trend mixed/null | “Regime C does not show a monotone severity pattern under the verified cells; it is retained as a robustness characterization.” |
| Missing α/IID cells | “Regime C is reported only over verified α values; missing cells are disclosed and not used for severity claims.” |

### 2.5 Regime D

| Outcome | Required Wording |
|---|---|
| Device-client Regime D positive | “On Edge-IIoTset (Regime D, device-partitioned, K=[x]), B2 reduces CV(FPR) from [y] to [z] (95% BCa CI: [a, b]), corroborating Regime A on a second device-partitioned IoT benchmark.” |
| Group-only Regime D positive | “On Edge-IIoTset (Regime D, group-partitioned, K=[x]), B2 reduces CV(FPR) from [y] to [z]; this is group-partitioned external validation, not physical-device validation.” |
| Mixed/null | “Regime D shows [direction] threshold-scope behavior under the tested protocol; this is reported as an external boundary condition.” |
| Rejected/blocked | “Edge-IIoTset was excluded after Gate 0 feasibility checks; no substitute dataset is added.” |

### 2.6 `B-FedStatsBenign`

| Outcome | Required Wording |
|---|---|
| B2 beats `B-FedStatsBenign` | “Under benign-only calibration, B2 achieves lower CV(FPR) than `B-FedStatsBenign`; this comparison applies only under benign-only calibration assumptions.” |
| `B-FedStatsBenign` beats or matches B2 | “The benign-only federated summary-statistics comparator matches or improves on B2 under [setting]; DATP is therefore framed as local benign threshold personalization rather than a dominant thresholding policy.” |
| between_ratio > 0.5 | “The descriptive between_ratio suggests between-client mean shift dominates the pooled summary variance.” |
| between_ratio ≤ 0.5 | “The descriptive between_ratio suggests within-client variance dominates; this weakens but does not eliminate the structural disadvantage of a single global summary threshold.” |

Do not claim this resolves attack-labeled Laridi-style novelty risk.

### 2.7 FedProx / Ditto / LocalHead

| Outcome | Required Wording |
|---|---|
| FedProx retains B2 gain | “The threshold-scope gain survives the FedProx stress test under the locked grid; threshold personalization remains complementary to this aggregation variant.” |
| FedProx absorbs gain | “FedProx closes much of the B1→B2 gap; DATP's claim is narrowed to fixed FedAvg-style shared-encoder settings.” |
| FedProx null/no change (E=1 or locked grid) | “No change is observed in the FedProx stress test under the locked grid. This is interpreted conservatively as no observed effect under this locked stress-test setting, not as evidence that FedProx is generally ineffective.” |
| FedProx fails convergence | “FedProx did not converge under the locked µ grid and is reported as unavailable rather than tuned post hoc.” |
| Ditto/FedRep-AE fallback retains gain | “Threshold personalization remains complementary under the selected model-personalization stress test.” |
| Ditto/FedRep-AE fallback absorbs gain | “Model personalization reduces the need for threshold personalization; DATP is framed as a lightweight post-hoc alternative rather than a substitute for personalization.” |

### 2.8 Temporal Recalibration

| Outcome | Required Wording |
|---|---|
| Helps | “Under the available chronological window, one-shot threshold recalibration recovers approximately [x]% of the CV(FPR) degradation.” |
| Neutral | “No meaningful temporal degradation is observed in the available chronological window; this does not establish general temporal robustness.” |
| Hurts/insufficient | “One-shot recalibration is insufficient under the available chronological window; continuous drift mitigation remains outside this paper.” |
| Infeasible | “No reliable chronological split satisfying the pre-specified coverage rules was available; the temporal probe is suppressed with reason.” |

---

## 3. Forbidden Post-Result Moves

After results are inspected, do not:
- Tune q, λ, µ, k, K, seeds, split definitions, or outcome thresholds to rescue a result.
- Rename a stress test as a core baseline.
- Use a bespoke unnamed local-head baseline as the personalization comparator; it must be a recognized FedRep or FedPer style variant if Ditto is infeasible.
- Hide a null, mixed, failed, or rejected gate.
- Use a pending citation for a critical claim.
- Claim formal privacy.
- Claim concept-drift handling beyond the one-shot temporal probe.
- Claim device-level validation from group-only partitions.
- Claim broad superiority over attack-labeled summary-statistics methods.
- Remove B3 from Regime A reporting.
- Use any result without lineage and config evidence.
- Report alert burden derived from an invented or assumed flow rate; either compute from timestamps, cite a defensible device-specific rate, or omit.

---

## 4. Manuscript Update Order

Manuscript editing starts only after result freeze.

1. Results.
2. Methods.
3. Discussion.
4. Limitations/threats.
5. Related work.
6. Abstract.
7. Conclusion.
8. Supplement/appendix.
9. Cover letter and submission metadata.

Rules:
- Results first because claims must follow frozen numbers.
- Methods include only protocols actually executed.
- Discussion uses the claim-survival matrix.
- Limitations include modest K, feasible/rejected regimes, stress-test scope, temporal scope, benign-only comparator scope, B4 privacy boundary, and any convergence failures.
- Related work includes only verified or safely pending sources.
- Abstract and conclusion are written last with real numbers only.
- The conference paper is disclosed explicitly.

---

## 5. Main Paper and Supplement Split

### 5.1 Main Paper Core Items

Main body should prioritize:
1. Regime A B1/B2/B4 primary table or figure.
2. B3 Regime A row.
3. Regime C severity summary.
4. Regime D or B-b external-validation result if feasible.
5. `B-FedStatsBenign` comparator summary with between_ratio.
6. One compact stress-test summary for FedProx and Ditto/LocalHead.
7. Temporal outcome if feasible, otherwise suppression note.
8. Failure/suppression table.
9. Privacy bounded-disclosure table or concise paragraph.

### 5.2 Supplement Candidates

Move to supplement unless needed for a reviewer-critical claim:
- Full q grid.
- Full calibration-size curves.
- Full `τ-shrink` λ grid.
- Full `B2-conf` coverage diagnostics.
- Full B4 ablation heatmap.
- Per-client CDF overlays.
- Full JS/gain scatter.
- Full threshold-shift scatter.
- Full µ grid details.
- Fixed-k `B-FedStatsBenign` variants.
- Detailed lineage manifests.
- Full skipped/failure diagnostics.

### 5.3 If Page Budget Is Exceeded

Cut order:
1. Move detailed mechanism figures to supplement.
2. Collapse FedProx and Ditto/LocalHead into one stress-test table.
3. Move alert-burden table to supplement.
4. Move threshold-variant grid to supplement.
5. Collapse Regime C into one figure.

Never cut:
- Main Regime A B1/B2 result.
- B4 secondary result.
- B3 Regime A row.
- Honest failure/suppression note.
- Critical limitations.

---

## 6. Reviewer-Risk Register

| Reviewer Attack | Required Evidence | Response |
|---|---|---|
| B2 equalizes FPR by construction. | Calibration-size sweep, held-out test FPR, `B2-conf`. | Acknowledge calibration-set construction; report held-out behavior and conformal diagnostic. |
| Paper is too narrow for journal. | External validation, comparator, stress tests, mechanism analyses. | Frame as controlled threshold-calibration study, not broad FL method. |
| N-BaIoT has only 9 devices. | Regime D or B-b if feasible; modest-K limitation. | Add external validation only if verified; otherwise state limitation honestly. |
| CICIoT2023 uses pseudo-clients. | B-b feasibility audit. | If B-b rejected, report B-a as boundary only. |
| Missing Laridi comparison. | `B-FedStatsBenign` benign-only comparator and related-work scope. | State calibration assumptions differ; do not claim attack-labeled superiority. |
| Missing aggregation baseline. | FedProx stress test. | Report survival, absorption, or convergence failure. |
| Missing model personalization. | Ditto or LocalHead stress test. | Apply absorption rule. |
| Missing temporal aspect. | Temporal recalibration probe if feasible. | Report helps/neutral/hurts/infeasible. |
| B4 leaks information. | Bounded-disclosure analysis. | Acknowledge coarse fingerprint sharing; no privacy claim. |
| Conference-to-journal overlap. | New experiments/analyses, rewritten sections, overlap note. | Disclose conference origin and internal 40% benchmark. |
| Unsupported generalization. | Scope boundaries and forbidden-claim audit. | Restrict to tested datasets/partitions/protocol. |

---

## 7. Related Work and Citation Rules

Mandatory verified/checked anchors before submission:
- Laridi et al. 2024 for summary-statistics federated thresholding.
- Lu et al. ICML 2023 as primary federated conformal anchor.
- Humbert et al. ICML 2023 as co-anchor.
- Ferrag et al. 2022 for Edge-IIoTset.
- Neto et al. 2023 for CICIoT2023.
- Li et al. 2020 for FedProx.
- Li et al. 2021 for Ditto.
- Rey et al. 2022 only after fresh bibliographic verification.
- Belarbi et al. 2023 and Sáez-de-Cámara et al. 2023 only if verified or clearly marked as non-critical related work.

Rules:
- Do not cite unverified partition precedents.
- Do not use a pending source for a critical methodological claim.
- Do not use Computers & Security as a target venue given the current AI/ML moratorium.
- State Computer Networks has no fixed 40% rule found; the 40% benchmark is internal.

---

## 8. Conference-to-Journal Overlap Disclosure

The journal manuscript must disclose the conference paper.

Internal benchmark:
- Target ≥ 40% substantive new material.
- This is a conservative internal benchmark, not a Computer Networks requirement.
- Measure after result freeze using section/table/figure/experiment count plus similarity report if available.

Cover-letter content:
- Cite the conference paper.
- Explain the journal extension adds verified new experiments/analyses.
- List new datasets/regimes only if actually executed.
- List new comparators/stress tests only if actually executed.
- State no figures are reused verbatim unless redrawn/extended.
- State the manuscript is not under consideration elsewhere.

Similarity protocol:
- Run similarity check if institutional access exists.
- Exclude references, equations, and properly cited prior conference paper where appropriate.
- Rewrite excessive verbatim overlap.
- Save final report with submission artifacts if available.

---

## 9. Versioning and Citation Metadata

Before submission:
- Create a journal-extension tag, e.g. `v2.0.0-journal`.
- Update `VERSIONING.md` with conference vs journal artifact distinction.
- Update `CITATION.cff` with the journal-extension version metadata.
- Record git commit, dataset versions, config hashes, and result-freeze date.
- Preserve conference camera-ready artifacts separately from journal artifacts.

---

## 10. Submission Readiness Checklist

| Item | Required Status |
|---|---|
| Result freeze complete | PASS |
| All metrics reproducible | PASS |
| All configs saved and compatible | PASS |
| All reused scores verified | PASS |
| All lineage chains valid | PASS |
| All active claims supported | PASS |
| All skipped/failed experiments disclosed | PASS |
| No forbidden claim remains | PASS |
| No placeholder/TODO/TBD remains | PASS |
| Citation verification complete for critical sources | PASS |
| Tables/figures have backing artifacts | PASS |
| Stress tests scoped correctly | PASS |
| B3 preserved | PASS |
| Regime C status documented | PASS |
| B-b status documented | PASS |
| Regime D status documented | PASS |
| Temporal status documented | PASS |
| `B-FedStatsBenign` scope documented | PASS |
| Page budget checked | PASS |
| Abstract and conclusion updated last | PASS |
| Conference-extension disclosure ready | PASS |
| VERSIONING and CITATION updated | PASS |

---

## 11. Post-Experiment Stop Conditions

Stop manuscript work if:

- A frozen table/figure disagrees with source metrics.
- A referenced cell lacks resolved config or lineage.
- A citation remains unverified for a critical claim.
- A page-budget cut would remove the core Regime A result or hide a limitation.
- A new experiment is proposed after result freeze without reopening the freeze process.
- Any locked protocol is being changed after results are seen.
- Any stress test is being reframed as a core baseline.
- Any rejected B-b, Regime D, or temporal outcome is silently removed.
- Any claim contradicts the claim-survival matrix.
