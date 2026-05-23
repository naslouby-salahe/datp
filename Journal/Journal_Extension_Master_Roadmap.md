# Journal Extension Master Roadmap for DATP

## 1. Executive Verdict

1. **Best target journal**: **Computer Networks (Elsevier)**, with **Internet of Things (Elsevier)** as principled backup. **Computers & Security is excluded** — its official Aims & Scope page (sciencedirect.com/journal/computers-and-security) carries a verbatim moratorium since early 2024: *"items directed to the security of AI/ML systems themselves (such as LLM and federated learning) are out of scope of the journal and should be submitted to a venue primarily about AI/ML."* Two of the six input audits recommended COSE and were wrong on this point.
2. **Best expansion level**: **Strong** — between Minimal (insufficient against a Q1 reviewer) and Ambitious (destroys DATP identity).
3. **Wait for conference acceptance before journal submission?** **Yes** — prepare experiments now, submit journal version only after the conference decision so the conference paper is a citable anchor and the extension narrative is unambiguous under Elsevier's redundancy/originality rules.
4. **One-sentence final strategy**: Keep DATP a *threshold-scope-only, fixed-encoder, FPR-equity* paper; extend it on exactly one new device-partitioned dataset (Edge-IIoTset), three baseline families that close the "B2-by-construction" and "model-personalization-makes-it-obsolete" attack axes, four threshold variants that deepen the calibration story without changing identity, one chronological-split temporal recalibration experiment, and six mechanism analyses.
5. **One-sentence biggest-risk warning**: The dominant existential risk is *novelty collapse against Laridi et al. (Sci. Rep. 2024)* on federated AE thresholding — DATP must explicitly cite, contrast, and quantitatively compare against a Laridi-style summary-statistics federated threshold, otherwise a knowledgeable reviewer will dismiss the contribution as already covered.

---

## 2. Input Corpus Inventory

| File | Role | Used? | Main Contribution | Reliability | Notes |
|---|---|---|---|---|---|
| DATP.pdf | Current paper | Yes | Threshold-scope-only controlled study; CV(FPR) 1.017→0.299 on N-BaIoT; B4 ≈52% recovery; CICIoT2023 null under file-level pseudo-clients | Primary anchor | Verified directly via project knowledge |
| State_of_the_Art.md | Literature context | Yes | 40-study corpus with 6 gap clusters; thesis-scoped gap ledger | Primary anchor | Used as context, not as unquestionable truth |
| Blueprint.md | Methodology lock | Yes | Locks RQ hierarchy, claim discipline, statistical tests, null-finding contingencies | Primary anchor | Confirms paper's confirmatory scope is RQ2 / Regime A / B1-vs-B2 only |
| Audit A (#2 — "DATP Journal Extension Audit") | Strategy note | Partial | Recommends Cyber Security and Applications + Edge-IIoTset; correctly rules out COSE | Mixed | Venue rec defensible but not strongest; correct on COSE exclusion |
| Audit B (#3 — "Journal Extension Audit for DATP") | Strategy note | Partial | Recommends Computers & Security + ToN-IoT; misses COSE moratorium | Partially wrong | COSE rec invalid; ToN-IoT case is defensible alternative |
| Audit C (#4 — "DATP Journal-Extension Audit Report") | Detailed analysis | Yes | Strongest baseline+threshold-variant analysis; correctly cites COSE moratorium verbatim; recommends Internet of Things | Highly reliable | Most rigorous source; some 2026-dated arXiv preprints noted as speculative |
| Audit D (#5 — "Extreme Deep-Research Audit") | Detailed analysis | Yes | Best novelty-threat analysis (Laridi 2024, Sáez-de-Cámara 2023); recommends Computer Networks (Rey 2022 lineage); flags 30%-rule as ICPR-specific | Highly reliable | Most accurate on policies and lineage |
| Audit E (#6 — "Extreme Deep-Research Audit and Journal Extension Roadmap") | Strategy note | Partial | Recommends JNCA + FedBN/temporal; misses COSE moratorium | Mixed | JNCA backup is defensible; FedBN technical caveat (no BN in DATP encoder) noted |
| Audit F (#7 — generic numbered) | Strategy note | Partial | Recommends Computers & Security; misses moratorium | Partially wrong | COSE rec invalid |
| Audit G (#8 — generic numbered) | Strategy note | Partial | Recommends Computers & Security; misses moratorium | Partially wrong | COSE rec invalid |

**Input limitations**: No audit independently verified the *quantitative* Laridi 2024 thresholding results on N-BaIoT (the closest novelty threat). No audit verified whether the DATP autoencoder architecture contains BatchNorm layers — it does not (Algorithm 1 + reproducibility configs in project knowledge), so FedBN as a baseline would require an encoder change and is therefore demoted to a non-recommended option.

---

## 3. Consolidated Understanding of Current DATP Identity

1. **Paper identity**: *Device-Aware Threshold Personalization: A Controlled Threshold-Calibration Study for Non-IID Federated IoT Anomaly Detection* — a fixed-encoder, fixed-FedAvg, **threshold-scope-only** controlled comparison.
2. **Sole confirmatory experimental variable**: threshold calibration scope (B1 shared / B2 per-client / B3 family-mean / B4 cluster-mean), with the AE, optimizer, rounds, seeds, and per-client score artifacts held identical.
3. **Datasets**: N-BaIoT (9 physical-device clients, Mirai/BASHLITE); CICIoT2023 (63 file-defined pseudo-clients, JS mean 0.004); N-BaIoT Dirichlet repartition (α∈{0.1, 0.3, 0.5, 1.0, 10.0, IID}, K=20 synthetic clients).
4. **Regimes**: Regime A (N-BaIoT confirmatory); Regime B (CICIoT2023 applicability boundary, near-homogeneous); Regime C (Dirichlet severity sweep).
5. **Baselines**: B0 centralized AE; B1 client-averaged shared τ; B2 per-client p95; B3 family-mean (Regime A only); B4 k-means cluster-mean on a 4-scalar fingerprint [µₑ, σₑ, skewₑ, p95(e)].
6. **Metrics**: CV(FPR) primary; CV(TPR), IQR(FPR), max-min FPR, worst-client BA, Macro-F1, P10 Macro-F1, coverage ratio, mean pairwise JS as descriptive severity.
7. **Statistical logic**: Per-seed Δₛ = CV(FPR)[B1,s] − CV(FPR)[B2,s] across 5 seeds; 95% bootstrap CI on Δ; pre-specified practical-significance thresholds; Wilcoxon and Cliff's δ as secondary descriptive evidence.
8. **Confirmatory claim** (single, locked): Under Regime A natural device split, B2 reduces CV(FPR) by a magnitude whose 95% bootstrap CI excludes zero.
9. **Supportive claims**: Regime C shows the B1–B2 gap is largest at low α and vanishes under IID; Regime B shows near-homogeneous file-level pseudo-clients are an applicability boundary; threshold-quantile sensitivity at q∈{0.90,0.95,0.99} preserves B2 < B4 < B1; pooled and sample-weighted shared variants confirm the B1→B2 reduction is not driven solely by arithmetic-mean construction.
10. **Exploratory claims**: B4 with K=3 recovers ≈52% of B2's improvement without taxonomy; JS divergence is a descriptive severity statistic; family taxonomy (B3) under-performs because device-type labels do not align with reconstruction-error calibration structure.
11. **Out-of-scope (deferred)**: poisoning, backdoor, evasion, formal privacy, hardware/edge profiling, communication cost, concept drift, E>1 sensitivity, deployment-scale fleets, model-level personalization.
12. **Claims that must not be disturbed by the journal extension**: (a) the threshold-scope-only experimental discipline; (b) the Regime A confirmatory result and its bootstrap CI; (c) the negative result on Regime B (it is an applicability boundary, not a universal CICIoT2023 statement); (d) the explicit non-privacy framing of B4; (e) the scope of all claims to "the tested datasets, partitions, and protocol."

---

## 4. Cross-File Agreement and Disagreement Map

| Topic | Agreement Across Files | Disagreement | Final Decision | Reason |
|---|---|---|---|---|
| DATP identity must be preserved | 6/6 audits | None | Lock identity | All recommend Strong (not Ambitious) extension |
| Need ≥1 new physical-device dataset | 6/6 | Edge-IIoTset (4 audits) vs ToN-IoT (2 audits) | **Edge-IIoTset** | Native FL framing (Ferrag 2022); device-type partition precedent in Pradhan et al. (Sci. Rep. 2025); cleaner client mapping than ToN-IoT |
| CICIoT2023 file-level partition is weak | 6/6 | None | Redesign with device-MAC partition | Pradhan et al. (Sci. Rep. 2025) precedent: 10-client device-group partition on CICIoT2023 |
| Need stronger FL training baseline | 6/6 | FedProx (5 audits) vs FedAvgM (3 audits) vs FedYogi (1 audit) | **FedProx** | Highest reviewer-defensibility under non-IID; Belarbi et al. 2023 precedent on FL-IDS |
| Need model-personalization comparator | 5/6 | FedBN (3) vs Ditto (2) vs Per-FedAvg (1) | **Ditto** | FedBN requires BN layers DATP's encoder lacks; Ditto is encoder-agnostic and the cleanest local-head comparator |
| Privacy framing | 6/6: do not overclaim | Whether to add MIA probe | Add **qualitative** privacy section + bounded-disclosure table; no MIA experiment | Audit C is right that empirical MIA on percentile summaries lacks established literature; experiment would be exploratory and risk over-claiming |
| Temporal experiment | 6/6: need one | MVE (3) vs full drift framework (2) vs none (1) | **MVE** chronological split + one-shot recalibration | Audits C/D/E/G concur this is the strongest realistic addition |
| Target journal | Split | COSE (3) / Computer Networks (1) / IoT-Elsevier (1) / CSA (1) / JNCA (1) | **Computer Networks** primary; **IoT (Elsevier)** backup | COSE moratorium is verbatim-confirmed; Computer Networks has explicit extension policy + Rey 2022 lineage on the exact dataset |
| Conference-extension % threshold | 5/6 cite ≥30% or ≥40% | Audit C and D correctly note no Elsevier-wide policy | Aim for **≥40% genuinely new material** | Conservative; aligns with FGCS's explicit 40% rule and outpaces ICPR/PRL's 30% |
| Wait for conference acceptance | 6/6 | None | Wait | Protects against duplicate-publication concerns |
| Conformal thresholding | Split (3 add / 3 reject) | None resolved | **Add split-conformal B2-conf** | Best single mechanism to close the "by-construction" tautology with finite-sample coverage guarantee; aligns with Plassier et al. ICML 2023 lineage |
| Adversarial robustness | 5/6: out of scope or supplementary | Audit C suggests light experiment | **Out of scope; only discussion** | Adversarial branch is scope drift; SoA correctly defers to thesis paper on robustness |
| FedBN vs Ditto for personalization | Split | Encoder constraint resolves | **Ditto** | DATP encoder has no BN; FedBN would require encoder change, violating the threshold-scope-only discipline |

---

## 5. Consolidated Weak-Point Register

| Weak Point | Severity | Why Reviewer Cares | Evidence | Fix Type | Effort | Scope Drift Risk |
|---|---|---|---|---|---|---|
| W01: "B2 equalizes FPR by construction" tautology | **Critical** | A knowledgeable reviewer can dismiss the headline result as definitional | DATP §IV–V already concedes the construction equality | Mandatory | Moderate | Low |
| W02: 9 physical clients only in confirmatory regime | **Critical** | External validity ceiling; N-BaIoT is aging | DATP scope statement | Mandatory | Moderate | Low |
| W03: CICIoT2023 used at file-level only; physical heterogeneity discarded | **Major** | Pradhan et al. (Sci. Rep. 2025) already partitioned CICIoT2023 by device-group | DATP §V-B | Mandatory | Moderate | Low |
| W04: No comparison to recent federated thresholding SOTA (Laridi 2024) | **Critical** | Closest direct competitor; if uncited and uncompared, novelty is contested | DATP related work omits Laridi | Mandatory | Moderate | Low |
| W05: No model-personalization comparator | **Major** | "Would Ditto/FedPer make B2 redundant?" | DATP §II discusses but does not test | Mandatory | Heavy | Medium |
| W06: No stronger FL aggregation baseline | **Major** | Recent FL-IDS (Belarbi 2023, FedMSE 2025) routinely compare FedProx/FedAvgM | DATP uses FedAvg only | Mandatory | Moderate | Low |
| W07: No temporal drift / recalibration | **Major** | Operational reality; conformal AD literature increasingly raises this | DATP explicit scope deferral | Mandatory | Moderate | Medium |
| W08: B4 metadata leakage not quantified | Moderate | Reviewers may push for DP/SecAgg or formal bounds | DATP §VII concedes risk | Recommended | Low | Low |
| W09: Five seeds only | Moderate | Statistical power | DATP §VII | Recommended | Immediate | None |
| W10: No calibration-size sensitivity beyond fixed nₘᵢₙ=100 | Moderate | Operational realism for low-data clients | DATP §IV nₘᵢₙ note | Recommended | Immediate | None |
| W11: No operational alert-burden translation of CV(FPR) | Moderate | Practitioners want alerts/day, not abstract CVs | DATP reports CV only | Recommended | Immediate | None |
| W12: P10 Macro-F1 degradation under-discussed | Moderate | Ennio Doorbell failure-mode is the honest negative | DATP §VII names it | Recommended | Immediate | None |
| W13: B4 cluster-feature ablation absent | Moderate | Reviewer demands interpretability | DATP §IV B4 description | Recommended | Immediate | Low |
| W14: q=0.95 sensitivity check is brief | Minor | Easy reviewer ask | DATP Table VII | Recommended | Immediate | None |
| W15: Conference-extension overlap not disclosed | **Critical (ethical)** | Without explicit disclosure + ≥40% new material, the manuscript risks desk rejection | Current paper is conference draft | Mandatory | Immediate | None |
| W16: No conformal / calibration-coverage analysis | Major | Aligns with split-conformal literature (Plassier 2023) and closes W01 with theoretical backing | DATP uses empirical quantile only | Recommended | Moderate | Low |
| W17: No shrinkage threshold variant | Moderate | Smooths B1↔B2 interpolation; mitigates P10 F1 loss | DATP §IV | Recommended | Immediate | None |

---

## 6. Reviewer-Loophole Closure Table

| Reviewer Attack | How to Close It | Remaining Risk | Safe Wording |
|---|---|---|---|
| "B2 equalizes FPR by construction" | (a) Add Appendix A formal derivation showing equality is *exact only on calibration data and only under stable test-time distributions*; (b) add split-conformal B2-conf variant; (c) calibration-size sensitivity sweep | Persistent reviewer may still call it a tautology | "On the calibration set, per-client q-percentile thresholding produces FPR ≈ 1−q by construction. On held-out test data, the empirical FPR variance is non-trivial and is what we measure." |
| "DATP is too narrow for a journal" | Add second device-partitioned dataset, FedProx+Ditto baselines, temporal recalibration, six mechanism analyses, conformal variant, expanded related work | Editor may still see it as a calibration paper rather than a system paper | Frame consistently as "a fairness-oriented threshold-calibration study under non-IID FL" — neither claim breadth nor apologize for scope |
| "Dataset coverage is limited" | Add Edge-IIoTset (device-type partition) + repartition CICIoT2023 by device-MAC | New dataset is still one testbed | "Two physically-partitioned IoT benchmarks (N-BaIoT, Edge-IIoTset) and a large-scale testbed (CICIoT2023 device-grouped)" |
| "N-BaIoT has only 9 devices" | Edge-IIoTset gives K∈{6,15}; CICIoT2023 device-MAC gives K≈10 | Combined K still modest vs. theoretical FL scale | State explicitly: "We do not validate at fleet scale (K > 100); per-device calibration scaling is future work." |
| "CICIoT2023 clients are pseudo-clients" | Repartition by device-MAC per Pradhan et al. (Sci. Rep. 2025) precedent; retain old file-level partition as Regime B-a (boundary) and new as Regime B-b (heterogeneous) | Repartition still imperfect | "Regime B-a (file-level) is a near-homogeneous boundary; Regime B-b (device-MAC) is the heterogeneous evaluation." |
| "Missing model-personalization baselines" | Add **Ditto** as one comparator with same threshold grid; explicitly note FedBN is incompatible with current encoder (no BN layers) | Ditto is one of many | "We compare against one representative model-personalization method (Ditto); exhaustive comparison across personalized-FL methods is out of scope." |
| "Missing aggregation baselines" | Add **FedProx** under same threshold rules; report B1–B4 × {FedAvg, FedProx} grid | One aggregation method, not full sensitivity | "We add the most-cited heterogeneity-aware aggregation baseline (FedProx); further aggregation sensitivity is future work." |
| "Missing federated thresholding SOTA comparison" | Implement **Laridi-style** summary-statistics federated threshold (Sci. Rep. 2024) as a third baseline family on stored score artifacts | Adaptation to non-IoT method; describe carefully | "We implement the federated summary-statistics threshold of Laridi et al. (2024) as a federated-threshold comparator on identical score artifacts." |
| "Missing temporal drift" | Add chronological split on Edge-IIoTset + one-shot recalibration MVE | Single split, not streaming | "Under a chronological train/test split, per-client thresholds drift at rate ΔFPR/window; one-shot recalibration recovers Z% of the CV(FPR) gain. Streaming drift detection is future work." |
| "Missing privacy/leakage discussion" | Add bounded-disclosure table + qualitative MIA-risk analysis + cite secure-aggregation literature | No empirical leakage quantification | "B4 fingerprints constitute distributional metadata; we provide a bounded-disclosure analysis and discuss secure-aggregation/DP mitigations as future work." |
| "Missing deployment-cost discussion" | Add bytes-per-round table comparing B1/B2/B4 communication and per-client storage | No hardware measurement | "Per-round communication and per-client storage overhead of B1/B2/B4 are estimated from message sizes; hardware-level profiling is future work." |
| "Journal version insufficiently different from conference" | Explicit ≥40% new material plan: new dataset, repartitioned dataset, three baseline families, four threshold variants, temporal regime, six analyses, conformal Appendix A | Editor judgment | Cover letter enumerates new sections explicitly; introduction cites conference paper as prior work |
| "Scope drift from adding too much" | Hard limits enforced: 1 new dataset (+1 redesigned partition), 3 baseline families, 4 threshold variants, 1 temporal family, 6 analyses | Some reviewers always want more | Frame as "we hold the encoder, AE architecture, and FedAvg training fixed; all extensions are threshold-scope or evaluation-side" |

---

## 7. Dataset Expansion Decision

| Dataset | Add / Maybe / Reject | Why | DATP Fit | Partition Quality | Calibration Suitability | Temporal Potential | Effort | Risk |
|---|---|---|---|---|---|---|---|---|
| N-BaIoT | **Keep (existing)** | Real 9-device physical partition; Rey 2022 lineage; current confirmatory regime | Excellent | Native device IDs | Excellent (rich benign traffic per device) | Moderate (chronological traces exist) | None new | Aging (2018); narrow attack families |
| CICIoT2023 | **Redesign partition (not new dataset)** | Pradhan et al. (Sci. Rep. 2025) precedent: 10-client device-group partition; current file-level is its own weakness | Strong after repartition | Device-MAC mapping feasible | Good | Moderate (capture timestamps) | Moderate (MAC mapping) | Reframing required |
| **Edge-IIoTset (Ferrag 2022)** | **ADD — primary new dataset** | Native FL framing in the dataset paper itself; 10+ device types; Pradhan et al. used 6-client device/application-type partition | Excellent | Native device-type partition | Good | Multi-day capture window enables chronological split | Moderate-Heavy (feature alignment) | Schema differs from N-BaIoT |
| ToN-IoT | Reject (for primary; cite) | Belarbi 2023 IP-based partition precedent; multi-modal complicates the threshold-scope-only design; doubles preprocessing | Medium | Possible via host/IP | Moderate; varies by modality | Good | Heavy | Multi-modality fragments narrative |
| Bot-IoT | Reject | Virtualized testbed; no natural device partition; older feature set | Weak | Weak | Moderate | Weak | Heavy | Synthetic + outdated |
| IoT-23 | Reject (cite only) | Strong temporal structure but device-level federation is artificial; benign coverage per device insufficient | Weak | Per-capture only | Moderate | Strong | Heavy | Preprocessing burden, weak DATP fit |
| Edge-IIoTset alternatives (MedBIoT, FedAIoT bundle) | Reject (cite as landscape) | Add literature context but not central evidence | — | — | — | — | — | Scope drift |
| UNSW-NB15 | Reject | Not IoT-specific; adjacent at best | Very low | None | Weak | Weak | — | Out of IoT-malware scope |

**Final dataset additions (within the hard limit of 2 new datasets)**:
1. **Edge-IIoTset** with native device/application-type partition (new dataset)
2. **CICIoT2023 device-MAC repartition** (same dataset, new regime, counts as 0 new datasets)

Net: 1 new dataset + 1 redesigned partition. Well within the 2-dataset limit.

---

## 8. Baseline Expansion Decision

| Baseline Family | Add / Optional / Reject | Scientific Question | Minimal Implementation | Reviewer Value | Scope Drift Risk | Placement |
|---|---|---|---|---|---|---|
| **FedProx** | **ADD (mandatory)** | Does DATP's threshold-scope gain survive heterogeneity-aware FL training? | Replace FedAvg aggregator with FedProx (µ ∈ {0.001, 0.01, 0.1}); apply B1–B4 to each | High | Low | Main |
| FedBN | **Reject** | Encoder personalization via local BN | Would require adding BN to encoder — **breaks frozen-encoder discipline** | Medium | High (changes encoder) | Reject |
| FedAvgM / FedYogi | Optional (future work) | Aggregator family sensitivity | One additional aggregator | Low–Medium | Medium | Supplementary or future work |
| **Ditto** | **ADD (mandatory)** | Does threshold personalization still help when model personalization is added? | Local head + shared body; apply B1–B4 to local-head AE | High | Low (body remains shared) | Main table 3 |
| FedPer / APFL / Per-FedAvg | Reject | Same as Ditto territory | — | Diminishing returns | Medium | Reject |
| Clustered FL (Sáez-de-Cámara 2023) | Optional | Model-clustering vs threshold-clustering | Full reimplementation is heavy | Medium | Medium | Qualitative comparison + table in related work; quantitative reimplementation deferred |
| **Laridi-style federated summary-statistics threshold** | **ADD (mandatory)** | Does device-aware thresholding beat the closest federated thresholding SOTA? | Aggregate per-client benign-error mean+std (and overlap-region search if labels permit); apply globally | Critical (closes biggest novelty threat) | Low (operates on existing score artifacts) | Main table 2 |
| Local-only (per-client encoders + per-client thresholds) | Optional supplementary | Bounding case | One run per dataset; reuse stored scores partially | Low–Medium | Low | Supplementary |
| Centralized reference | **Keep (B0)** | Already present | — | — | None | Main |
| Threshold-only alternatives (Local-MinMax, Local-IQR, Local-KQE) | Optional supplementary | Is p95 cherry-picked? | Compute from stored scores | Medium | None | Supplementary |

**Final baseline additions (within hard limit of 3 families)**:
1. **FedProx** (aggregation-side heterogeneity baseline)
2. **Ditto** (model-side personalization comparator; encoder-compatible)
3. **Laridi-style Federated Summary-Statistics Threshold** (closest federated-thresholding SOTA)

---

## 9. Threshold Variant Decision

| Threshold Variant | Definition | Add / Optional / Reject | Why It Matters | Risk | Placement |
|---|---|---|---|---|---|
| **q-sensitivity sweep** | B1/B2/B4 evaluated at q∈{0.90, 0.95, 0.975, 0.99} systematically (not just brief sensitivity check) | **ADD (mandatory)** | Trivial reviewer ask; shows headline is not q=0.95 artefact | None | Main heatmap |
| Global pooled p95 | Single global p95 over pooled benign scores | Already in Table VII | Sensitivity check on construction | None | Main (existing) |
| Sample-weighted shared | Weighted mean of local p95 by calibration n | Already in Table VII | Sensitivity check on construction | None | Main (existing) |
| Per-client (B2) | Local p95 | Existing | DATP core | None | Main |
| Family-mean (B3) | Per-family arithmetic mean | Existing | DATP core | None | Main |
| Cluster-mean (B4) | k-means cluster-mean | Existing | DATP core | None | Main |
| Robust cluster median | Cluster-wise median of τₖ instead of mean | Optional | Reduces sensitivity to outlier clients in B4 | None | Supplementary (paragraph) |
| **Local-global shrinkage** | τₖ(λ) = λ·τₖ,p95 + (1−λ)·τ_global, λ∈{0, 0.25, 0.5, 0.75, 1} | **ADD (mandatory)** | Interpolates B1↔B2; can mitigate P10 Macro-F1 loss | Low | Main figure |
| Empirical-Bayes / James-Stein | Bayesian shrinkage | Reject | Heavier theoretical apparatus; scope drift | Medium | Future work |
| **Calibration-size-aware fallback** | Size-dependent λ(nₖ) shrinkage; smooth transition from per-client to shared as nₖ drops | **ADD (mandatory)** | Closes the real deployment loophole; supersedes hard nₘᵢₙ=100 fallback | None | Main subsection |
| **Split-conformal B2 (B2-conf)** | Per-client split-conformal calibration with marginal coverage 1−α; aggregated under federated quantile per Plassier et al. ICML 2023 | **ADD (mandatory)** | Closes W01 with theoretical finite-sample coverage guarantee | Low (clear distinction from Laridi method) | Main + Appendix A |
| Drift-aware recalibration | Periodic per-client recalibration | Folded into temporal section | See Section 10 | Medium | Section 10 |
| Full conformal anomaly detection | Distribution-free with Byzantine-robust extensions | Reject | Scope drift to a different paper | High | Future work |

**Final threshold variants (within hard limit of 4 new variants)**:
1. **q-sensitivity sweep** (formal main heatmap, not brief check)
2. **Local-global shrinkage** τₖ(λ)
3. **Calibration-size-aware fallback** (size-dependent shrinkage)
4. **Split-conformal B2 (B2-conf)**

---

## 10. Temporal and Recalibration Decision

1. **Can current datasets support true temporal analysis?** Partially. N-BaIoT has chronological traces with gaps but limited drift magnitude. CICIoT2023 retains capture timestamps (169 traces). Edge-IIoTset has a multi-day capture window. **The current CICIoT2023 file-level partition discards within-file time and is unusable**, but the redesigned device-MAC partition preserves usable temporal ordering.
2. **Minimum useful temporal/recalibration experiment**: chronological split on **Edge-IIoTset** (preferred over CICIoT2023 because Edge-IIoTset has cleaner device structure). Train AE + calibrate thresholds on first 70% of benign data by capture timestamp; evaluate on last 30% with (a) frozen thresholds and (b) one-shot recalibration at the boundary. Report CV(FPR), per-client FPR drift slope, alert-burden change, AUROC stability.
3. **Strongest feasible version (skip this cycle)**: streaming sliding-window recalibration with drift detection (e.g., Page-Hinkley); cross-dataset transfer (N-BaIoT → Edge-IIoTset). **Skip** — too heavy and stretches DATP identity toward drift-detection framework territory.
4. **Reject as too broad**: FLARE/FLAME-style autonomous concept-drift mitigation frameworks; cross-year longitudinal deployment studies; Byzantine-robust federated conformal prediction.
5. **Metrics**: per-time-window CV(FPR), mean FPR drift, per-client FPR slope vs. time, Macro-F1 stability, alert-burden change, one-shot recalibration recovery ratio (Z% = recovered CV(FPR) gain / original gain).
6. **Effect on DATP claim**: A positive result strengthens DATP from a static-calibration study to a deployment-aware policy; a negative result must be reported honestly as a **deployment caveat** — DATP is then explicitly framed as "calibration policy under stationary benign distributions; drift mitigation requires recalibration whose feasibility we partially demonstrate." **Pre-specified interpretation rule**: a non-trivial drift effect is *claimable only if* (a) the chronological split shows FPR drift outside the bootstrap CI of the static split AND (b) recalibration recovers ≥50% of the lost CV(FPR) gain. Otherwise report as null and frame as a deployment caveat. **Do not claim concept-drift handling.**

**Final temporal experiment family (within hard limit of 1)**: Edge-IIoTset chronological split + one-shot threshold recalibration.

---

## 11. Deeper Analysis Decision

| Analysis | Add / Optional / Reject | What It Proves | What It Does Not Prove | Required Artifact | Figure/Table | Reviewer Value |
|---|---|---|---|---|---|---|
| **Per-client benign+attack score CDFs with B1/B2/B4 overlays + Ennio Doorbell failure-mode deep dive** | **ADD** | Mechanism of FPR concentration; why P10 Macro-F1 drops in low-separability devices | Generalization beyond N-BaIoT clients | Stored per-client scores (existing) | Figure | High (must-do) |
| **JS divergence ↔ DATP-benefit correlation** | **ADD** | Heterogeneity severity predicts DATP value; provides "when to apply" rule | Causality | Per-client benign distributions + CV(FPR) deltas | Scatter + table | High (must-do) |
| **Threshold shift vs ΔFPR/ΔTPR scatter** | **ADD** | Quantifies the fairness-vs-sensitivity trade-off surface | Solves the trade-off | Per-client thresholds + scores | Scatter | High (must-do) |
| **Calibration-size sensitivity sweep** (nₖ ∈ {50, 100, 250, 500, 1k, 5k}) | **ADD** | When DATP remains usable under low calibration data; supports shrinkage variant | Online cold-start | Subsampled benign scores | Figure | High (must-do) |
| **Operational false-alarm burden** | **ADD** | Translates CV(FPR) into alerts/device/day under realistic benign volumes | Hardware deployment | Per-client FPR × estimated traffic volume | Table | High (must-do) |
| **B4 cluster-feature ablation + interpretability** | **ADD** | Defends B4 as meaningful taxonomy-free approximation | Privacy safety of B4 | Re-run B4 with feature subsets (mean only / std only / skew only / p95 only / all) | Table + cluster→device-type Sankey | High (must-do) |
| Bootstrap CIs + effect sizes for all key metrics | Optional | Statistical rigor | New phenomena | Stored seed-level metrics | Updated tables | Medium |
| Worst-client balanced accuracy deep dive | Optional | Worst-case behavior | Average behavior | Existing | Table | Medium |
| Coverage ratio + Calibration-Pending counts | Already in paper | Eligibility transparency | — | Existing | Existing | Medium |
| Seed-level stability metrics (Cliff's δ, Wilcoxon) | Optional | Stronger statistical evidence | Causality | Stored seed-level results | Supplementary table | Medium |
| Sáez-de-Cámara model-parameter clustering vs B4 score-stat clustering | Optional | Differentiates clustering basis | DATP general superiority | Full reimplementation (heavy) | Supplementary | Medium |
| Conformal coverage check (marginal coverage = 1−α) | Already integrated with B2-conf | Verifies conformal guarantee | — | New runs (in B2-conf) | Figure | High (integrated) |
| MIA-style leakage probe | Reject (qualitative only) | Empirical leakage from shared p95 | Formal privacy | Would require MIA infrastructure | — | Medium but high scope drift |
| Failure-mode taxonomy across all clients | Subsumed in Ennio Doorbell analysis | — | — | — | — | — |

**Final deeper analyses (within hard limit of 6)**:
1. Per-client error CDF overlays + Ennio Doorbell failure-mode deep dive
2. JS divergence ↔ DATP-benefit correlation
3. Threshold shift vs ΔFPR/ΔTPR scatter
4. Calibration-size sensitivity sweep
5. Operational false-alarm burden table
6. B4 cluster-feature ablation + interpretability

---

## 12. Elsevier Venue Target Matrix

| Rank | Journal | Scope Match | Official Policy Evidence | Conference Extension Risk | Required Strengthening | Desk-Rejection Risk | Recommendation |
|---|---|---|---|---|---|---|---|
| **1** | **Computer Networks** (ISSN 1389-1286, 2024 JIF 4.6, Q1) | **Strongest** — Rey et al. 2022 (CN 204:108693) is *the* foundational FL-IoT-malware paper on N-BaIoT and is the direct predecessor of DATP | **Verbatim** from Guide for Authors: *"Enhanced, extended versions of quality papers presented at conferences or workshops can be submitted to our journal for review"* (sciencedirect.com/journal/computer-networks/publish/guide-for-authors) | Low if extension is substantial and conference is cited | Strong package as recommended | Low–Medium | **PRIMARY TARGET** |
| 2 | **Internet of Things (Elsevier)** (ISSN 2542-6605, 2024 JIF ~7.6, Q1) | Strong — IoT scope explicitly covers security and ML applications in IoT | Standard Elsevier originality language; no journal-specific conference-extension wording verified | Medium — editor may want stronger IoT-systems narrative | Same package + heavier IoT-deployment framing in introduction | Medium | **STRONG BACKUP** |
| 3 | **Cyber Security and Applications** (Elsevier OA) | Good — explicit cybersecurity + AI+IoT scope; Olanrewaju-George 2025 (DATP ref [7]) published here | One audit cites explicit conference-extension wording; needs re-verification at submission time | Medium | Same package | Medium | Viable backup if CN/IoT both fail; OA cost consideration |
| 4 | **Journal of Network and Computer Applications (JNCA)** (2024 JIF ~8.0, Q1) | Strong — networked applications + security | Standard Elsevier originality language | Low–Medium | Same package; emphasize networked-application framing | Medium | Acceptable third-tier backup |
| 5 | **Future Generation Computer Systems (FGCS)** (2024 JIF ~6.1, Q1) | Moderate — distributed systems; security is allowed but not central | **Verbatim** Guide for Authors: 40% new contributions, different title, cite original, list new sections | Medium-High — wants distributed-systems breadth | Significant systems-framing rework | Medium-High | **Not recommended** — scope drift risk |
| **Excluded** | **Computers & Security (COSE)** | Topically a perfect match in principle | **Verbatim moratorium** (sciencedirect.com/journal/computers-and-security): *"As of early 2024, we have instituted a moratorium on consideration of submissions that feature AI or ML as significant components… items directed to the security of AI/ML systems themselves (such as LLM and federated learning) are out of scope of the journal"* | **Desk-reject for AI/ML scope** | — | **HIGH (≈certain desk reject)** | **DO NOT SUBMIT.** That FedMSE (Nguyen & Beuran 2025) and earlier 2023 FL-IDS papers appeared in COSE does *not* override the current scope: they were submitted before the moratorium took effect or slipped through editorial transitions; relying on this precedent for a new submission today is high-risk. |
| Excluded | Computer Standards & Interfaces | Moderate; standards-focused | — | — | Would need standardization framing | High | Scope mismatch |
| Excluded | Ad Hoc Networks | Weak — wireless/MAC focus | — | — | Would need topology focus | High | Not in scope |
| Excluded | Engineering Applications of AI (EAAI) | Moderate; AI-method generic | — | — | Would need broader AI framing | Medium | Lower fit; risks losing IoT-security positioning |

---

## 13. Conference-to-Journal Originality Plan

1. **Conference paper contributes**: controlled threshold-scope study (B1–B4) under fixed FedAvg AE on N-BaIoT (confirmatory), CICIoT2023 file-level (boundary), N-BaIoT Dirichlet sweep; CV(FPR) 1.017→0.299 headline; B4 ≈52% recovery; bootstrap CI on per-seed deltas.
2. **Journal paper must add** (target ≥40% genuinely new material): Edge-IIoTset device-partition regime; CICIoT2023 device-MAC repartition (counts as new regime); 3 baseline families × 4 threshold policies grid; 4 new threshold variants (q-sweep, shrinkage, calibration-size-aware fallback, split-conformal); chronological-split + one-shot recalibration regime on Edge-IIoTset; 6 deeper analyses; Appendix A formal derivation of B2's construction equality and its boundaries; expanded related work covering Laridi 2024, Sáez-de-Cámara 2023, FedMSE 2025, Olanrewaju-George 2025, Belarbi 2023, Plassier ICML 2023, and the dataset-centric Pradhan et al. 2025.
3. **What can be reused**: DATP nomenclature and B1–B4 taxonomy verbatim; Regime A N-BaIoT confirmatory result and bootstrap CI methodology; Regime C Dirichlet sweep; B0 centralized reference; theoretical definitions and notation; reproducibility artifact structure.
4. **What must be new**: every figure either redrawn with additional series (e.g., new dataset overlaid, baseline grid added) or replaced; every table extended; every section above 50% reused must be rewritten substantially.
5. **How much novelty is needed**: aim for ≥40% new content. No Elsevier-wide policy prescribes a single percentage (the 30% rule originated in ICPR→Pattern Recognition Letters and is not Elsevier-wide); FGCS explicitly states 40%. 40% is the safe conservative bar.
6. **Cover letter disclosure** (template, 6–8 sentences): *"This manuscript is an extended version of our conference paper '[title]' (Reference [X]). The conference version established the DATP framework with the four-policy threshold-scope comparison on N-BaIoT and reported CV(FPR) reduction from 1.017 to 0.299 under per-client thresholding. The present journal manuscript contains approximately 50% new material, including: (i) a new device-partitioned Edge-IIoTset benchmark and a device-MAC repartition of CICIoT2023; (ii) four new threshold variants — q-sensitivity sweep, local-global shrinkage, calibration-size-aware fallback, and split-conformal B2; (iii) three FL baseline families (FedProx, Ditto, and a federated summary-statistics threshold à la Laridi et al. 2024) under the identical threshold grid; (iv) a formal Appendix A delineating where B2's construction-implied FPR equality holds and breaks down; (v) a temporal chronological-split and one-shot recalibration regime; and (vi) six mechanism analyses including operational alert-burden translation. The original conference results are reproduced and contextualized but no figures or text passages are reused verbatim. The manuscript is not under consideration elsewhere."*
7. **Self-plagiarism risks**: keep iThenticate verbatim overlap below ~15–20%; redraw or substantially extend every figure; rewrite introduction, related work, and methodology sections.
8. **Duplicate-publication risks**: avoid simultaneous submission; wait for conference camera-ready before journal submission; cite conference paper as [X] in the introduction.
9. **Wait for conference acceptance**: **Yes** — run all new experiments now, but submit the journal version only after the conference camera-ready is set. If the conference paper is rejected, the journal version can proceed as an original full paper (still cite the preprint if posted).
10. **Honest journal-extension wording**: never claim DATP "solves" non-IID FL; never claim formal privacy guarantees; never claim improved global Macro-F1; never claim concept-drift handling beyond the one-shot recalibration evidence.

---

## 14. Three-Level Expansion Roadmap

### 14.1 Minimal Extension

| Component | Required Action | Reviewer Value | Effort | Risk |
|---|---|---|---|---|
| Datasets | Keep N-BaIoT; redesign CICIoT2023 by device-MAC only | Medium | Moderate | High — single physical-device benchmark is fragile vs Q1 reviewer |
| Baselines | Add FedProx only | Medium | Moderate | High — no model-personalization and no federated-thresholding comparison invites dismissal |
| Threshold variants | q-sensitivity + shrinkage | Medium | Immediate | Medium |
| Temporal | None | None | None | High — drift question unaddressed |
| Deeper analyses | Client-CDF overlays + failure-mode taxonomy + operational burden | Medium | Immediate | Medium |
| Privacy | One paragraph + bounded-disclosure table | Low | Immediate | Low |
| **Net risk** | — | — | — | **High desk-reject risk at Computer Networks; possibly viable at lower-tier OA venues** |

### 14.2 Strong Extension (RECOMMENDED)

| Component | Required Action | Reviewer Value | Effort | Risk |
|---|---|---|---|---|
| Datasets | N-BaIoT + **Edge-IIoTset** + CICIoT2023 device-MAC repartition | High | Moderate-Heavy | Low |
| Baselines | **FedProx + Ditto + Laridi-style federated summary-statistics threshold** (3 families × 4 threshold policies) | High | Heavy | Low |
| Threshold variants | q-sensitivity + **local-global shrinkage** + **calibration-size-aware fallback** + **split-conformal B2** | High | Moderate | Low |
| Temporal | Chronological split + one-shot recalibration on Edge-IIoTset | Medium-High | Moderate | Low |
| Deeper analyses | All 6 must-do analyses | High | Moderate | Low |
| Appendix A | Formal derivation of B2 construction-equality + boundary conditions (small nₖ, distribution shift, conformal correction) | High | Immediate | Low |
| Seeds | Extend to 10 seeds; recompute BCa CIs | Medium | Immediate | None |
| Privacy | Bounded-disclosure table + qualitative MIA-risk discussion + secure-aggregation/DP mitigation discussion | Medium | Immediate | Low |
| Statistical rigor | Bootstrap CIs on all main metrics; Cliff's δ + Wilcoxon as descriptive | Medium | Immediate | None |
| **Net risk** | — | — | — | **Low–Medium at Computer Networks** |

### 14.3 Ambitious Extension (NOT RECOMMENDED — scope drift)

| Component | Required Action | Reviewer Value | Effort | Risk |
|---|---|---|---|---|
| Datasets | Edge-IIoTset + ToN-IoT + CICIoT2023 + IoT-23 chronological | Diminishing | Very Heavy | High |
| Baselines | All Strong + clustered-FL reimplementation (Sáez-de-Cámara 2023) + Per-FedAvg | Diminishing | Very Heavy | High |
| Threshold variants | Add full conformal anomaly detection + drift-aware streaming recalibration | Diminishing | Very Heavy | Very High |
| Temporal | Streaming sliding-window + cross-dataset transfer + Page-Hinkley drift detection | Medium | Very Heavy | High |
| Hardware | Raspberry-Pi edge profiling | Low (out of scope) | Very Heavy | Very High |
| Adversarial | Label-flip / poisoning | Medium | Heavy | Very High |
| **Net risk** | — | — | — | **DATP identity dissolves; paper becomes generic FL-IDS** |

---

## 15. Final Recommended Package

**Selected package: Strong Extension (§14.2). Selected target journal: Computer Networks. Selected backup: Internet of Things (Elsevier).**

1. **Dataset additions (≤2)**:
   - Edge-IIoTset (device/application-type partition, K ∈ {6, 15})
   - CICIoT2023 device-MAC repartition (counts as new regime, not new dataset)
2. **Baseline additions (≤3 families)**:
   - FedProx (heterogeneity-aware aggregation)
   - Ditto (model-personalization with frozen body)
   - Laridi-style federated summary-statistics threshold (closest federated-thresholding SOTA)
3. **Threshold additions (≤4 new variants)**:
   - q-sensitivity sweep at q ∈ {0.90, 0.95, 0.975, 0.99} (formal main heatmap)
   - Local-global shrinkage τₖ(λ)
   - Calibration-size-aware fallback (smooth, size-dependent shrinkage replacing hard nₘᵢₙ=100)
   - Split-conformal B2 (B2-conf) with marginal coverage 1−α
4. **Temporal/recalibration addition (≤1 family)**:
   - Chronological train/test split on Edge-IIoTset (70/30 by capture timestamp) with (a) frozen threshold and (b) one-shot recalibration at boundary; CV(FPR) drift trajectory reported
5. **Deeper analyses (≤6)**:
   - Per-client benign+attack error CDFs with B1/B2/B4 overlays + Ennio Doorbell failure-mode deep dive
   - JS divergence ↔ DATP-benefit correlation
   - Threshold shift vs ΔFPR/ΔTPR scatter
   - Calibration-size sensitivity sweep
   - Operational false-alarm burden quantification (alerts/device/day)
   - B4 cluster-feature ablation + interpretability
6. **New figures**: (i) per-client benign-error CDF overlay, (ii) calibration-size sensitivity curve, (iii) shrinkage λ-curve, (iv) JS↔gain scatter, (v) threshold-variant heatmap (q × policy), (vi) temporal CV(FPR) drift trajectory, (vii) split-conformal coverage diagnostic
7. **New tables**: (i) personalized-FL baseline grid (FedAvg / FedProx / Ditto × B1–B4 + Laridi-threshold), (ii) Edge-IIoTset Regime A' results, (iii) CICIoT2023 device-MAC Regime B' results, (iv) failure-mode taxonomy, (v) privacy-disclosure tabulation per policy, (vi) communication/storage overhead per policy
8. **New sections**: (i) Threshold-Variant Taxonomy, (ii) Calibration-Size Analysis, (iii) Failure-Mode and Limits-of-DATP, (iv) Privacy and Leakage Analysis, (v) Temporal Recalibration MVE, (vi) Comparison with Federated Thresholding (Laridi-style) and with Model Personalization (Ditto), (vii) Post-2022 Related Work
9. **Supplementary material**: Appendix A (formal B2 construction-equality derivation + boundary conditions); full hyperparameter tables; per-seed per-client raw results; Docker image + git commit hash; Zenodo artifact extended with new code
10. **Claims to strengthen**: (a) "Under non-IID device heterogeneity, threshold scope alone changes the distribution of false alarms across clients" — now backed by 2 datasets + conformal variant + calibration-size robustness; (b) "Threshold-scope effect is orthogonal to model-side personalization" — backed by FedAvg+Ditto grid; (c) "Effect is monotone in heterogeneity severity" — Dirichlet + Edge-IIoTset JS-divergence regression
11. **Claims to avoid**: do not claim DATP "solves" non-IID; do not claim improved global Macro-F1 (P10 F1 trade-off is real); do not claim privacy preservation; do not claim concept-drift handling beyond the one-shot recalibration evidence; do not claim DATP dominates Laridi's federated threshold unless empirically demonstrated

---

## 16. Artifact and Claim Consistency Check

| Proposed Claim | Support Status | Required Evidence | Artifact Needed | Safe Wording |
|---|---|---|---|---|
| B2 reduces CV(FPR) from 1.017 to 0.299 on N-BaIoT under non-IID | (1) Already supported | None | Existing artifacts | Keep verbatim with bootstrap CI [0.647, 0.769]; flag as "under the tested N-BaIoT protocol" |
| Effect is monotone in Dirichlet α and collapses under IID | (1) Already supported | None | Existing Regime C | "Per-client threshold benefit is monotonically related to Dirichlet α and collapses under IID" |
| B4 recovers ≈52% of B2's improvement without taxonomy | (1) Already supported | None | Existing | Keep with explicit "exploratory at K=9" caveat |
| Effect generalizes to Edge-IIoTset | (3) Requires new experiments | Edge-IIoTset device-partition runs | New | "On Edge-IIoTset (device-partitioned, K=X), B2 reduces CV(FPR) from Y to Z (95% BCa CI […])" |
| Effect is orthogonal to model-side personalization | (3) Requires new experiments | FedAvg/FedProx/Ditto × B1–B4 grid | New | "Across FedAvg, FedProx, and Ditto encoders, the B1→B2 CV(FPR) reduction is preserved within ±X%" — never claim *exhaustiveness* |
| DATP beats Laridi-style federated summary-statistics threshold under non-IID | (3) Requires new experiments | Laridi-threshold baseline on identical scores | New | "Under heterogeneity (low Dirichlet α / device-partitioned regimes), the federated summary-statistics threshold reduces FPR dispersion compared to B1 but remains less effective than B2; under near-homogeneous regimes the methods converge" |
| B2 is not a construction tautology | (2) Recomputation + (3) new | Appendix A derivation + calibration-size sweep + B2-conf | New + analytical | "B2's CV(FPR) equalization is exact on the calibration set; on held-out test data it is bounded by calibration-set size and benign-tail shape (Appendix A); the empirically observed gain survives split-conformal calibration with marginal coverage 1−α" |
| DATP can handle limited benign calibration | (2) Recomputation | n_cal sweep on existing scores | Recomputation | "Sensitivity analysis suggests B2 with shrinkage remains effective for n_cal ≥ N*; below N*, calibration-size-aware fallback recovers B1-equivalent FPR" |
| DATP is robust to threshold aging | (3) Requires new experiments | Temporal MVE on Edge-IIoTset | New | "Under a chronological train/test split, per-client thresholds drift at rate Δ; one-shot recalibration recovers Z% of the CV(FPR) gain. Streaming drift handling is future work." |
| DATP preserves privacy | (5) Should not be claimed | — | — | Replace with "B4 fingerprints constitute distributional metadata leakage; B4 is not a privacy mechanism" (existing DATP §VII wording is already correct) |
| B4 is privacy-safe | (5) Should not be claimed | — | — | Do not claim |
| Threshold personalization helps in CICIoT2023 generally | (5) Should not be claimed | — | — | Keep partition-scoped framing: file-level boundary vs device-MAC heterogeneity |
| DATP reduces operational alert burden | (2) Recomputation | FPR × estimated traffic volume per device | Recomputation | "Translating per-client FPR into expected alerts/day, B2 reduces worst-client alert load from N₁ to N₂ alerts/day under representative testbed volumes" |
| B4 clusters are interpretable | (3) New analysis | B4 cluster-feature ablation + cluster→device-type mapping | New | "Cluster assignments align with X% of [device-family / protocol class] labels under feature subset [µₑ, p95(e)]" |
| DATP improves global Macro-F1 | (5) Should not be claimed | DATP redistributes FPR; mean F1 is roughly preserved with P10 degradation | — | "DATP improves per-client FPR equity on top of FedAvg-trained encoders, at the cost of P10 Macro-F1 degradation concentrated in low-separability clients (e.g., Ennio Doorbell on N-BaIoT)" |

---

## 17. Implementation-Ready Action Plan

| Priority | Action | Exact Output Artifact | Depends On | Feasibility | Stop Condition |
|---|---|---|---|---|---|
| 1 | Write Appendix A: formal derivation of B2 construction-equality and where it breaks (small nₖ, distribution shift) | Appendix A LaTeX section + figure showing calibration-vs-test FPR divergence under small nₖ | None | Immediate | Derivation reviewed by 1 statistician |
| 2 | Extend seeds from 5 to 10; recompute all BCa CIs from stored score arrays | Updated Tables III–VI in main paper; per-seed CSVs in artifact | Existing artifacts | Immediate | All deltas remain positive; CIs exclude zero |
| 3 | Compute calibration-size sensitivity sweep (n_cal ∈ {50, 100, 250, 500, 1k, 5k}) from existing N-BaIoT scores via subsampling | New Figure: CV(FPR) and P10 F1 vs n_cal | Existing scores | Immediate | Curve plateaus and shrinkage variant maps cleanly |
| 4 | Compute JS divergence ↔ DATP-benefit regression on existing per-client distributions | New Figure: scatter + linear fit | Existing scores | Immediate | R² reported with caveats |
| 5 | Compute operational alert-burden table (FPR × benign volume) | New Table | Existing scores + per-client benign counts | Immediate | Burden ratio reported per device |
| 6 | Run B4 cluster-feature ablation (mean / std / skew / p95 subsets) on existing fingerprints | New Table + cluster interpretability mapping | Existing fingerprints | Immediate | Each feature subset's CV(FPR) reported |
| 7 | Implement and run **q-sensitivity heatmap** at q ∈ {0.90, 0.95, 0.975, 0.99} on stored scores | Main heatmap figure | Existing scores | Immediate | Ordering B2 < B4 < B1 preserved at all q |
| 8 | Implement and run **local-global shrinkage threshold** at λ ∈ {0, 0.25, 0.5, 0.75, 1} on stored scores | Main shrinkage curve figure | Existing scores | Immediate | λ-curve reported per dataset |
| 9 | Implement **calibration-size-aware fallback** (size-dependent λ(nₖ)) | New Algorithm pseudocode + supplementary results | Stored scores | Immediate | Replaces hard nₘᵢₙ=100 fallback |
| 10 | Implement **split-conformal B2 (B2-conf)** with marginal coverage check at α=0.05 | New main-table row + coverage diagnostic figure | Existing scores | Moderate | Empirical coverage within ±0.02 of 1−α |
| 11 | Implement and run **FedProx** training (µ ∈ {0.001, 0.01, 0.1}) on N-BaIoT; apply B1–B4 | Updated main results table | FedProx implementation | Moderate (Flower-native) | All 5 seeds converge |
| 12 | Implement and run **Ditto** (local head + shared body) on N-BaIoT; apply B1–B4 | New main results table row | Ditto implementation | Heavy | Local-head loss converges; B2 gain preserved or attenuated |
| 13 | Implement **Laridi-style federated summary-statistics threshold** baseline on stored score artifacts (all regimes) | New main table column | Stored scores + summary-stats aggregation | Moderate | Coverage check vs N-BaIoT, Edge-IIoTset, CICIoT2023 device-MAC |
| 14 | Preprocess **Edge-IIoTset** with device/application-type partition (K ∈ {6, 15}); train FedAvg AE; compute scores | New regime artifacts | Edge-IIoTset download + feature extraction | Moderate-Heavy | Calibration coverage ≥ 90% of clients |
| 15 | Repartition **CICIoT2023 by device-MAC** following Pradhan et al. (Sci. Rep. 2025) precedent; train FedAvg AE; compute scores | New regime artifacts | CICIoT2023 metadata + MAC mapping | Moderate-Heavy | At least 8 clients with sufficient benign volume |
| 16 | Run full B1–B2–B3–B4 + new threshold variants + 3 baseline families across Edge-IIoTset and CICIoT2023-device-MAC | Updated main tables | Steps 11–15 | Heavy | All deltas reported with BCa CIs |
| 17 | Run **temporal MVE**: chronological 70/30 split on Edge-IIoTset; frozen threshold vs one-shot recalibration | New temporal figure + table | Step 14 | Moderate | Drift outside static CI **and** recalibration recovers ≥50% of CV(FPR) gain — else report as null and frame as deployment caveat |
| 18 | Write all six deeper-analysis sections | Updated main paper §VI–VII | Steps 3–6, 16 | Moderate | Each section ≤ 1 page including figures |
| 19 | Write privacy & leakage section + bounded-disclosure table + communication overhead table | New supplementary subsection + table | Step 16 | Immediate | No formal-privacy claim; all wording bounded |
| 20 | Rewrite Introduction, Related Work (with Laridi 2024, Sáez-de-Cámara 2023, FedMSE 2025, Olanrewaju-George 2025, Belarbi 2023, Plassier ICML 2023, Pradhan et al. 2025), Methodology to ≥50% new prose | New journal manuscript draft | All above | Moderate | iThenticate verbatim overlap ≤ 20% |
| 21 | Draft cover letter with explicit extension disclosure | Cover letter | Step 20 | Immediate | Lists each new section with section numbers |
| 22 | Submit to Computer Networks after conference camera-ready | Submission package | Conference decision | — | Conference accepted (or withdrawn) |

---

## 18. Do-Not-Do List

1. Do **not** submit to **Computers & Security** under the current AI/ML moratorium — verbatim-confirmed desk-reject risk.
2. Do **not** add FedBN as a baseline — DATP's autoencoder has no BatchNorm layers; adding BN to enable FedBN would break the frozen-encoder discipline and the threshold-scope-only experimental contract.
3. Do **not** add more than **one** new IoT dataset (Edge-IIoTset). ToN-IoT, IoT-23, Bot-IoT, MedBIoT, UNSW-NB15, TII-SSRC-23 are scope drift for this cycle.
4. Do **not** add more than **three** baseline families. Specifically, do not add Per-FedAvg, FedPer, APFL, pFedMe, FedAvgM, FedYogi, FedAdam, or clustered FL (Sáez-de-Cámara 2023 reimplementation).
5. Do **not** claim DATP "solves" non-IID FL.
6. Do **not** claim improved global Macro-F1 — P10 Macro-F1 degrades.
7. Do **not** claim privacy preservation without formal DP/SecAgg mechanisms.
8. Do **not** claim concept-drift handling — the temporal MVE is one-shot recalibration only.
9. Do **not** add adversarial robustness, poisoning, backdoor, or evasion experiments — clearly out of scope.
10. Do **not** add hardware/edge profiling — separate paper.
11. Do **not** add a streaming drift-detection framework (FLARE/FLAME-style) — separate paper.
12. Do **not** add Byzantine-robust federated conformal prediction — separate paper.
13. Do **not** change the autoencoder, aggregator (in mainline), or round budget between conference and journal — would break the "extension" framing under originality rules.
14. Do **not** reuse conference figures verbatim — redraw or substantially extend each.
15. Do **not** silently change the CV(FPR) definition between conference and journal.
16. Do **not** continue to frame the CICIoT2023 file-level null result as a general CICIoT2023 statement — keep it as Regime B-a (boundary), with Regime B-b (device-MAC) as the heterogeneous evaluation.
17. Do **not** invoke the FedMSE precedent (COSE 2025) as evidence that COSE accepts FL submissions today — the moratorium is current and explicit.
18. Do **not** target FGCS — its scope tilt toward distributed systems would require systems-framing rework and significant scope drift.

---

## 19. Final Reviewer Attack After Repair

1. **Remaining attackable weaknesses**:
   - K is still modest (Edge-IIoTset K ∈ {6, 15}, N-BaIoT K=9, CICIoT2023-MAC K≈10) — reviewers asking for K > 50 cannot be satisfied
   - Single FedAvg-family aggregator with FedProx as the only deviation — aggregator sensitivity is partial
   - Only one model-personalization comparator (Ditto) — the personalized-FL space is not exhausted
   - Privacy analysis remains qualitative — no MIA experiment, no DP epsilon-accuracy curve
   - Temporal MVE is a single chronological split, not streaming
   - Five (extended to ten) seeds — some venues now expect 20+
   - The Laridi adaptation is an *adapted* implementation, not a direct reproduction of their published method
2. **Why they are acceptable**: each is explicitly out-of-scope of "threshold-scope-only controlled study under FedAvg + frozen encoder"; scope is *the* core methodological discipline of DATP; broader sensitivity studies are the natural follow-up papers in the thesis program (Paper 2 in the user's thesis roadmap).
3. **How to word them honestly**:
   - "Our evaluation comprises K ∈ [9, 15] physical-device clients across three benchmarks; fleet-scale validation at K > 100 requires hardware-grounded deployment evidence and is reserved for future work."
   - "We add one representative heterogeneity-aware aggregation method (FedProx); exhaustive comparison across the aggregation family is out of scope."
   - "Ditto is included as one representative model-personalization method with a frozen body, preserving encoder discipline; exhaustive personalization comparison is out of scope."
   - "Privacy analysis is qualitative: B4 transmits distributional metadata; formal differential-privacy or secure-aggregation integration is future work."
   - "The temporal regime is a one-shot recalibration MVE under a chronological split; streaming drift handling requires a drift-detection module and is future work."
4. **What would still worry an Elsevier reviewer**:
   - Whether DATP's gain truly survives Ditto+B1 (i.e., whether model personalization makes thresholding redundant) — this is the highest residual risk
   - Whether the Laridi-style federated threshold *adaptation* fairly represents the original method — must be carefully described
   - Whether B4's metadata leakage, even if bounded, raises operational concerns
5. **What would likely satisfy the reviewer**: the combination of (a) explicit citation, contrast, and quantitative comparison with Laridi 2024 + Sáez-de-Cámara 2023 + FedMSE 2025; (b) the Appendix A formal derivation + B2-conf variant that closes the construction-tautology critique; (c) Edge-IIoTset as a second device-partitioned benchmark; (d) the Ditto baseline showing the threshold-scope gain is *at least not entirely absorbed* by model personalization; (e) the temporal MVE showing whether DATP ages gracefully; (f) the operational alert-burden translation that grounds CV(FPR) in practitioner terms.

---

## 20. Search and Verification Audit Log

| Query or Source | Source Type | Date Checked | Key Finding | Confirmed / Changed / Contradicted Input Files | Used in Final Recommendation |
|---|---|---|---|---|---|
| DATP.pdf | Project knowledge — current paper | 2026-05-23 | CV(FPR) 1.017→0.299, B4 ≈52% recovery, 9 physical N-BaIoT devices, 5 seeds, E=1, q=0.95; explicit B4-is-not-privacy framing | Confirmed | Yes |
| State_of_the_Art.md | Project knowledge — SoA chapter | 2026-05-23 | 6 gap clusters; non-IID/privacy/adversarial/deployment/dataset/reproducibility | Confirmed | Yes |
| Blueprint.md | Project knowledge — methodology lock | 2026-05-23 | Sole confirmatory claim: Regime A B1-vs-B2 CV(FPR); RQ hierarchy; null-finding contingencies | Confirmed | Yes |
| sciencedirect.com/journal/computers-and-security (Aims & Scope) | Official Elsevier page | 2026-05-23 | **Verbatim**: "items directed to the security of AI/ML systems themselves (such as LLM and federated learning) are out of scope of the journal" | **Changed**: rules out COSE as venue (contradicts Audits B, F, G) | Yes — decisive |
| sciencedirect.com/journal/computer-networks/publish/guide-for-authors | Official Elsevier page | 2026-05-23 | **Verbatim**: "Enhanced, extended versions of quality papers presented at conferences or workshops can be submitted to our journal for review" | Confirmed (Audit D) | Yes — decisive |
| Rey, Sánchez Sánchez, Huertas Celdrán, Bovet, Jaggi (2022). *Computer Networks* 204:108693 | Peer-reviewed paper (DATP reference [5]) | 2026-05-23 | FL MLP+AE on N-BaIoT, foundational precedent on identical dataset; published in target venue | Confirmed | Yes — anchors venue choice |
| Olanrewaju-George & Pranggono (2025). *Cyber Security and Applications* 3:100068 | Peer-reviewed paper (DATP reference [7]) | 2026-05-23 | FL AE on N-BaIoT; supports related-work positioning | Confirmed | Yes |
| Nguyen & Beuran (2025). FedMSE. *Computers & Security* 151:104337 | Peer-reviewed paper (DATP reference [8]) | 2026-05-23 | Submitted July 2024, accepted Oct 2024 — under moratorium; not a safe precedent for new submissions today | Clarifies COSE risk — does not invalidate moratorium | Yes |
| Pradhan et al. (2025). "Dataset-centric evaluation of federated intrusion detection models in IoT networks." *Scientific Reports* 10.1038/s41598-025-32567-w | Peer-reviewed paper | 2026-05-23 (via Audits) | Edge-IIoTset partitioned into 6 device/application-type clients; CICIoT2023 partitioned into 10 device-group clients | Confirms feasibility of Edge-IIoTset partition + CICIoT2023 repartition | Yes |
| Laridi, Palmer & Tam (2024). "Enhanced federated anomaly detection through autoencoders using summary statistics-based thresholding." *Scientific Reports* 14:26704 | Peer-reviewed paper | 2026-05-23 (via Audits) | Federated thresholding on summary statistics; closest novelty threat to DATP | Confirmed (Audits A, B, C, D, F all cite) | Yes — anchors mandatory comparison baseline |
| Sáez-de-Cámara et al. (2023). *Computers & Security* 131:103299 | Peer-reviewed paper | 2026-05-23 (via Audits) | Clustered FL on Gotham testbed; uses Local-Largest-MSE per-client thresholds; clusters *models*, not *thresholds* | Confirms differentiation: B4 clusters thresholds, not models | Yes |
| Belarbi et al. (2023). GLOBECOM 2023 | Peer-reviewed paper | 2026-05-23 (via Audits) | FedAvg vs FedProx vs FedYogi on TON-IoT with IP-based partitions; raises baseline expectations | Confirms FedProx is mandatory baseline | Yes |
| Plassier et al. (2023). "Conformal Prediction for Federated Uncertainty Quantification Under Label Shift." ICML 2023, PMLR 202:27907–27947 | Peer-reviewed paper | 2026-05-23 (via Audits) | Federated conformal prediction with DP guarantees | Confirms split-conformal B2-conf as valid threshold variant with formal coverage guarantee | Yes |
| Ferrag (2022). Edge-IIoTset. *IEEE Access* DOI 10.1109/ACCESS.2022.3165809 | Peer-reviewed paper | 2026-05-23 (via Audits) | Native FL framing; 10+ device types; 14 attacks | Confirms Edge-IIoTset as primary new dataset | Yes |
| FGCS Guide for Authors | Official Elsevier page | 2026-05-23 (via Audit D) | "40% new contributions" requirement for conference extensions | Confirms ≥40% as safe extension bar | Yes (calibrates extension target) |
| Neto et al. (2023). CICIoT2023. *Sensors* 23(13):5941 | Official dataset paper (DATP reference [3]) | 2026-05-23 | 105 devices, 33 attacks; structure permits device-MAC repartition | Confirms repartition is feasible without new dataset | Yes |
| MIA in FL — ACM Computing Surveys 2024, DOI 10.1145/3704633 | Peer-reviewed survey | 2026-05-23 (via Audit C) | Threshold-based MIA exists; defenses include partial sharing, SecAgg, DP, AD | Supports bounded-disclosure framing for B4 | Yes (privacy section) |
| 30%/40% conference-extension rule | Multiple Elsevier guides | 2026-05-23 | No single Elsevier-wide policy; 30% is ICPR/PRL-specific; 40% is FGCS-explicit | Audits D and C are correct that the 30% rule is not universal | Yes (extension threshold set at ≥40%) |
| Plassier ICML 2023 (PMLR) | Conference proceedings | 2026-05-23 | Federated conformal prediction; principled basis for B2-conf | Confirms B2-conf as defensible threshold variant | Yes |

---

## 21. Final Decision Gate

1. **Best target journal**: **Computer Networks (Elsevier)**, ISSN 1389-1286, 2024 JIF 4.6, Q1. Primary because (a) Rey et al. 2022 (the foundational FL-N-BaIoT paper) is published there, giving DATP a direct lineage and editorial familiarity; (b) the Guide for Authors verbatim accepts enhanced extended conference versions; (c) the journal's scope explicitly covers network security, intrusion detection, and malicious code; (d) **Computers & Security is excluded by an explicit and current AI/ML moratorium that covers federated learning**. **Backup**: Internet of Things (Elsevier), then Cyber Security and Applications, then JNCA.
2. **Best expansion level**: **Strong (§14.2)**. Minimal will desk-reject at this tier; Ambitious destroys DATP identity.
3. **Exact must-do list before submission** (consolidated from §17): (i) Appendix A formal derivation; (ii) 10 seeds + BCa CIs; (iii) calibration-size sweep + JS↔gain regression + alert-burden table + B4 ablation + failure-mode taxonomy + threshold-shift scatter; (iv) q-sensitivity heatmap + local-global shrinkage + calibration-size-aware fallback + split-conformal B2; (v) FedProx + Ditto + Laridi-style federated threshold baselines; (vi) Edge-IIoTset device-partition + CICIoT2023 device-MAC repartition; (vii) temporal chronological-split + one-shot recalibration on Edge-IIoTset; (viii) bounded-disclosure privacy section + communication overhead table; (ix) Related Work rewrite covering Laridi 2024, Sáez-de-Cámara 2023, FedMSE 2025, Belarbi 2023, Plassier ICML 2023, Pradhan et al. 2025; (x) cover letter with explicit extension disclosure.
4. **Exact do-not-do list** (consolidated from §18): no COSE; no FedBN; no second new dataset; no model-personalization beyond Ditto; no streaming drift framework; no adversarial branch; no hardware profiling; no encoder/aggregator changes in mainline; no MIA empirical experiments; no privacy or drift-handling claims; do not reframe Regime B-a null as a universal CICIoT2023 statement.
5. **Should the journal extension wait until conference acceptance?** **Yes.** Begin all new experiments now (they are the dominant cost). Submit the journal version only after conference camera-ready so the conference paper is a stable citable anchor. If the conference paper is rejected, fold the strongest reviewer feedback into the journal manuscript and submit as an original full paper.
6. **Final confidence rating**: **High** on venue exclusion (COSE moratorium verbatim-confirmed); **High** on Computer Networks selection (Rey 2022 lineage + verbatim extension policy); **High** on dataset choice (Edge-IIoTset has documented FL-ready precedent in Pradhan et al. 2025); **Medium-High** on baseline grid (FedProx + Ditto + Laridi-style); **Medium** on temporal MVE outcome (positive result is not guaranteed; the paper must handle a null result gracefully); **High** on threshold variants (all four are defensible and operate on existing or minimal-new artifacts); **High** on package scope-control (all hard limits respected).
7. **One-paragraph final verdict**: The DATP conference paper has a real, defensible empirical finding (CV(FPR) reduction, monotone in heterogeneity, applicability boundary at near-IID) and a scientifically clean experimental discipline (threshold-scope-only under frozen encoder). To meet the Q1 bar at Computer Networks, the journal version must do exactly five things and no more: (a) close the "B2-by-construction" tautology via Appendix A + split-conformal B2-conf + calibration-size sweep; (b) prove generalization with one new device-partitioned dataset (Edge-IIoTset) and a redesigned CICIoT2023 partition; (c) demonstrate that threshold personalization is not absorbed by either heterogeneity-aware aggregation (FedProx) or model-side personalization (Ditto), and is not dominated by the closest federated-thresholding SOTA (Laridi 2024); (d) show that the calibration ages gracefully under a chronological split with one-shot recalibration; and (e) ground the abstract CV(FPR) metric in operational alert-burden numbers. The Computers & Security moratorium is the most consequential single fact of this audit and decisively reroutes the venue strategy. The dominant existential risk is novelty collapse against Laridi et al. 2024 if the comparison is omitted. The recommended Strong package — exactly 1 new dataset, 1 redesigned partition, 3 baseline families, 4 threshold variants, 1 temporal experiment, 6 mechanism analyses, and one formal appendix — respects every hard limit, preserves DATP's threshold-scope-only identity, and is feasible in 4–6 months of focused work parallel to conference review.