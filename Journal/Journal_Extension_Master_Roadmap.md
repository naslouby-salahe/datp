# Journal Extension Master Roadmap for DATP

---

## 1. Executive Verdict

1. **Best target journal**: **Computer Networks (Elsevier)**, with **Internet of Things (Elsevier)** as principled backup. **Computers & Security is excluded** — its official Aims & Scope page (sciencedirect.com/journal/computers-and-security) carries a verbatim moratorium since early 2024: *"items directed to the security of AI/ML systems themselves (such as LLM and federated learning) are out of scope of the journal and should be submitted to a venue primarily about AI/ML."* This exclusion is final and appears consistently in every section of this roadmap.
2. **Best expansion level**: **Strong** — between Minimal (insufficient against a Q1 reviewer) and Ambitious (destroys DATP identity).
3. **Wait for conference acceptance before journal submission?** **Yes** — begin experiments now; submit the journal version only after the conference camera-ready is set, so the conference paper is a citable anchor and the extension narrative is unambiguous under Elsevier's redundancy/originality rules.
4. **One-sentence final strategy**: Keep DATP a *threshold-scope-only, fixed-encoder, FPR-equity* paper; extend it on exactly one new device-partitioned dataset (Edge-IIoTset), three stress-test comparator families that close the "B2-by-construction" and "model-personalization-makes-it-obsolete" attack axes, four threshold variants that deepen the calibration story, one chronological-split temporal recalibration experiment, and six mechanism analyses.
5. **One-sentence biggest-risk warning**: The dominant existential risk is *novelty collapse against Laridi et al. (Sci. Rep. 2024)* — DATP must explicitly cite, contrast, and quantitatively compare against a pre-specified Laridi-style summary-statistics federated threshold using a matched operating-point protocol; otherwise a knowledgeable reviewer will dismiss the contribution as already covered.

---

## 2. Input Corpus Inventory

| File | Role | Used? | Main Contribution | Reliability | Notes |
|---|---|---|---|---|---|
| DATP.pdf | Current paper | Yes | Threshold-scope-only controlled study; CV(FPR) 1.017→0.299 on N-BaIoT; B4 ≈52% recovery; CICIoT2023 null under file-level pseudo-clients | Primary anchor | Verified directly via project knowledge |
| State_of_the_Art.md | Literature context | Yes | 40-study corpus with 6 gap clusters; thesis-scoped gap ledger | Primary anchor | Used as context, not as unquestionable truth |
| Blueprint.md | Methodology lock | Yes | Locks RQ hierarchy, claim discipline, statistical tests, null-finding contingencies | Primary anchor | Confirms sole confirmatory scope is RQ2 / Regime A / B1-vs-B2; no BN in encoder |
| Audit A | Strategy note | Partial | Recommends Cyber Security and Applications + Edge-IIoTset; correctly rules out COSE | Mixed | CSA is a viable backup; correct on COSE exclusion |
| Audit B | Strategy note | Partial | Recommends Computers & Security + ToN-IoT; misses COSE moratorium | Partially wrong | COSE rec invalid; ToN-IoT rejected for this cycle |
| Audit C | Detailed analysis | Yes | Strongest baseline+threshold-variant analysis; correctly cites COSE moratorium verbatim; recommends Internet of Things | Highly reliable | Most rigorous; some 2026 arXiv preprints noted as speculative |
| Audit D | Detailed analysis | Yes | Best novelty-threat analysis (Laridi 2024, Sáez-de-Cámara 2023); recommends Computer Networks (Rey 2022 lineage); flags 30%-rule as ICPR-specific | Highly reliable | Most accurate on policies and lineage |
| Audit E | Strategy note | Partial | Recommends JNCA + FedBN/temporal; misses COSE moratorium | Mixed | JNCA backup defensible; FedBN rejected — DATP encoder has no BatchNorm |
| Audits F, G | Strategy notes | Rejected for venue | Recommend Computers & Security; miss moratorium | Wrong on venue | COSE rec invalid throughout |

**Input limitation — Laridi 2024 quantitative gap**: No audit independently verified the Laridi method's performance on N-BaIoT score distributions specifically. The DATP-compatible adaptation must be pre-specified before results are inspected (see §8.4).

**Input limitation — DATP encoder architecture**: Confirmed via Blueprint.md / Algorithm 1 that the current AE has no BatchNorm layers. FedBN requires BN; adding BN changes the encoder and breaks the frozen-encoder discipline. FedBN is rejected everywhere in this roadmap.

---

## 3. Consolidated Understanding of Current DATP Identity

1. **Paper identity**: *Device-Aware Threshold Personalization: A Controlled Threshold-Calibration Study for Non-IID Federated IoT Anomaly Detection* — a fixed-encoder, fixed-FedAvg, **threshold-scope-only** controlled comparison.
2. **Sole confirmatory experimental variable**: threshold calibration scope (B1 shared / B2 per-client / B3 family-mean / B4 cluster-mean), with the AE, optimizer, rounds, seeds, and per-client score artifacts held identical. FedProx and Ditto are *external stress-test comparators*, not part of this causal ladder.
3. **Datasets**: N-BaIoT (9 physical-device clients, Mirai/BASHLITE); CICIoT2023 (63 file-defined pseudo-clients, JS mean 0.004); N-BaIoT Dirichlet repartition (α∈{0.1, 0.3, 0.5, 1.0, 10.0, IID}, K=20 synthetic clients).
4. **Regimes**: Regime A (N-BaIoT confirmatory); Regime B-a (CICIoT2023 file-level, near-homogeneous boundary); Regime B-b (CICIoT2023 device-MAC — *conditional on Priority 0 metadata verification, see §16*); Regime C (Dirichlet severity sweep).
5. **Baselines**: B0 centralized AE; B1 client-averaged shared τ; B2 per-client p95; B3 family-mean (Regime A only); B4 k-means cluster-mean on a 4-scalar fingerprint [µₑ, σₑ, skewₑ, p95(e)].
6. **Metrics**: CV(FPR) primary; CV(TPR), IQR(FPR), max-min FPR, worst-client BA, Macro-F1, P10 Macro-F1, coverage ratio, mean pairwise JS as descriptive severity.
7. **Statistical logic**: Per-seed Δₛ = CV(FPR)[B1,s] − CV(FPR)[B2,s] across 5 seeds (extended to 10 in journal); 95% BCa bootstrap CI on Δ; Wilcoxon and Cliff's δ as secondary descriptive evidence.
8. **Sole confirmatory claim** (locked): Under Regime A natural device split, B2 reduces CV(FPR) by a magnitude whose 95% BCa bootstrap CI excludes zero.
9. **Supportive claims**: Regime C shows the B1–B2 gap is largest at low α and vanishes under IID; Regime B-a shows near-homogeneous file-level pseudo-clients are an applicability boundary; q-sensitivity preserves B2 < B4 < B1; pooled and sample-weighted shared variants confirm reduction is not driven solely by arithmetic-mean construction.
10. **Exploratory claims**: B4 with K=3 recovers ≈52% of B2's improvement without taxonomy (exploratory at K=9); JS divergence is a descriptive severity statistic; B3 underperforms because device-type labels do not align with reconstruction-error calibration structure.
11. **Out-of-scope (deferred)**: poisoning, backdoor, evasion, formal privacy, hardware/edge profiling, communication cost, concept drift, E>1 sensitivity, deployment-scale fleets, model-level personalization beyond the one Ditto stress-test.
12. **Claims that must not be disturbed**: (a) threshold-scope-only experimental discipline; (b) Regime A confirmatory result and its bootstrap CI; (c) Regime B-a negative result as applicability boundary only; (d) explicit non-privacy framing of B4; (e) scope of all claims to "the tested datasets, partitions, and protocol."

---

## 4. Cross-File Agreement and Disagreement Map

| Topic | Agreement Across Files | Disagreement | Final Decision | Reason |
|---|---|---|---|---|
| DATP identity must be preserved | 6/6 audits | None | Lock identity | All recommend Strong (not Ambitious) extension |
| Need ≥1 new physical-device dataset | 6/6 | Edge-IIoTset (4 audits) vs ToN-IoT (2 audits) | **Edge-IIoTset** | Native FL framing; device-type partition precedent in Pradhan et al. (Sci. Rep. 2025); cleaner client mapping |
| CICIoT2023 file-level partition is weak | 6/6 | None | Redesign by device-MAC *if Priority 0 metadata feasibility is confirmed* | Priority 0 check determines feasibility before any other work |
| Need stronger FL training stress test | 6/6 | FedProx (5) vs FedAvgM (3) vs FedYogi (1) | **FedProx** | Highest reviewer-defensibility; Belarbi et al. 2023 precedent; Flower-native; framed as external stress test, not core causal |
| Need model-personalization comparator | 5/6 | FedBN (3) vs Ditto (2) vs Per-FedAvg (1) | **Ditto (or named variant)** | FedBN rejected (no BN in encoder); Ditto is encoder-agnostic; framed as external stress test |
| Privacy framing | 6/6: do not overclaim | Whether to add MIA probe | **Qualitative only** — bounded-disclosure table; no empirical MIA | MIA on percentile summaries lacks established IoT literature |
| Temporal experiment | 6/6: need one | MVE (3) vs full drift (2) vs none (1) | **MVE chronological split + one-shot recalibration** with three pre-specified outcome interpretations | Three outcomes pre-specified to prevent post-hoc narrative adjustment |
| Target journal | Split | COSE (3) / Computer Networks (1) / IoT-Elsevier (1) / CSA (1) / JNCA (1) | **Computer Networks** primary; **IoT (Elsevier)** backup | COSE moratorium verbatim-confirmed; Computer Networks has explicit extension policy + Rey 2022 lineage |
| Conference-extension novelty threshold | 5/6 cite ≥30% or ≥40% | No Elsevier-wide policy exists | **≥40% substantive new material** | Conservative; aligns with FGCS explicit 40% rule; avoids unsupported percentages |
| Wait for conference acceptance | 6/6 | None | **Yes** | Protects against duplicate-publication concerns |
| Conformal thresholding | Split (3 add / 3 reject) | Resolved | **Split-conformal B2-conf** | Closes construction-tautology critique with finite-sample coverage guarantee |
| Adversarial robustness | 5/6 out of scope | Audit C suggests light experiment | **Out of scope; discussion only** | Adversarial branch is scope drift into a separate thesis paper |
| FedBN vs Ditto | Resolved by encoder constraint | — | **Ditto (or named variant)** | FedBN rejected; Ditto encoder-agnostic |
| FedProx/Ditto role in DATP story | Resolved in prior update | Audits did not distinguish causal from stress-test | **External stress-test comparators only** | Not part of the B1–B4 causal ladder |

---

## 5. Consolidated Weak-Point Register

| Weak Point | Severity | Why Reviewer Cares | Evidence | Fix Type | Effort | Scope Drift Risk |
|---|---|---|---|---|---|---|
| W01: "B2 equalizes FPR by construction" tautology | **Critical** | Reviewer can dismiss headline as definitional | DATP §IV–V concedes construction equality | Mandatory | Moderate | Low |
| W02: 9 physical clients only in confirmatory regime | **Critical** | External validity ceiling; N-BaIoT is aging | DATP scope statement | Mandatory | Moderate | Low |
| W03: CICIoT2023 at file-level only | **Major** | Pradhan et al. (Sci. Rep. 2025) already partitioned CICIoT2023 by device-group | DATP §V-B | Mandatory (conditional on Priority 0) | Moderate | Low |
| W04: No comparison to Laridi 2024 | **Critical** | Closest direct competitor; novelty contested if omitted | DATP related work omits Laridi | Mandatory | Moderate | Low |
| W05: No model-personalization comparator | **Major** | "Would Ditto make B2 redundant?" | DATP §II discusses but does not test | Mandatory | Heavy | Medium |
| W06: No stronger FL aggregation stress test | **Major** | Recent FL-IDS (Belarbi 2023, FedMSE 2025) compare FedProx/FedAvgM | DATP uses FedAvg only | Mandatory | Moderate | Low |
| W07: No temporal drift / recalibration | **Major** | Operational reality | DATP explicit deferral | Mandatory | Moderate | Medium |
| W08: B4 metadata leakage not quantified | Moderate | Reviewers may push for DP/SecAgg | DATP §VII concedes risk | Recommended | Low | Low |
| W09: Five seeds only | Moderate | Statistical power | DATP §VII | Recommended | Immediate (10 seeds) | None |
| W10: No calibration-size sensitivity beyond nₘᵢₙ=100 | Moderate | Operational realism for low-data clients | DATP §IV nₘᵢₙ note | Recommended | Immediate | None |
| W11: No operational alert-burden translation | Moderate | Practitioners want alerts/day, not abstract CVs | DATP reports CV only | Recommended | Immediate | None |
| W12: P10 Macro-F1 degradation under-discussed | Moderate | Ennio Doorbell failure-mode is the honest negative | DATP §VII names it | Recommended | Immediate | None |
| W13: B4 cluster-feature ablation absent | Moderate | Reviewer demands interpretability | DATP §IV B4 description | Recommended | Immediate | Low |
| W14: q=0.95 sensitivity check is brief | Minor | Easy reviewer ask | DATP Table VII | Recommended | Immediate | None |
| W15: Conference-extension overlap not disclosed | **Critical (ethical)** | Without explicit disclosure + ≥40% new material, desk-rejection risk | Current paper is conference draft | Mandatory | Immediate | None |
| W16: No conformal / calibration-coverage analysis | Major | Aligns with split-conformal literature; closes W01 theoretically | DATP uses empirical quantile only | Recommended | Moderate | Low |
| W17: No shrinkage threshold variant | Moderate | Smooths B1↔B2 interpolation; mitigates P10 F1 loss | DATP §IV | Recommended | Immediate | None |

---

## 6. Reviewer-Loophole Closure Table

| Reviewer Attack | How to Close It | Remaining Risk | Safe Wording |
|---|---|---|---|
| "B2 equalizes FPR by construction" | (a) Appendix A formal derivation: equality is exact only on calibration data under stable test-time distributions; (b) split-conformal B2-conf with marginal coverage check; (c) calibration-size sensitivity sweep | A persistent reviewer may still call it a tautology | "On the calibration set, per-client q-percentile thresholding produces FPR ≈ 1−q by construction. On held-out test data, the empirical FPR variance is non-trivial and is what we measure." |
| "DATP is too narrow for a journal" | Edge-IIoTset + FedProx/Ditto stress tests + temporal MVE + six mechanism analyses + conformal variant + expanded related work | Editor may still see it as a narrow calibration paper | Frame as "a fairness-oriented threshold-calibration study under non-IID FL" |
| "Dataset coverage is limited" | Edge-IIoTset (device-type partition) + CICIoT2023 device-MAC repartition (conditional on Priority 0) | MAC repartition may be infeasible | "Two physically-partitioned IoT benchmarks (N-BaIoT, Edge-IIoTset); CICIoT2023 is included as a device-grouped evaluation if Priority 0 confirms metadata, or retained as a near-homogeneous boundary otherwise." |
| "N-BaIoT has only 9 devices" | Edge-IIoTset gives K∈{6,15}; CICIoT2023 device-MAC gives K≈10 if feasible | Combined K still modest | "We do not validate at fleet scale (K > 100); per-device calibration scaling is future work." |
| "CICIoT2023 clients are pseudo-clients" | Repartition by device-MAC per Pradhan et al. (Sci. Rep. 2025) if Priority 0 confirms metadata; retain file-level as Regime B-a regardless | MAC repartition conditional on Priority 0 | "Regime B-a (file-level) is a near-homogeneous applicability boundary; Regime B-b (device-MAC) is the heterogeneous evaluation where metadata permits." |
| "Missing model-personalization baselines" | Ditto (or explicitly named local-head variant) as one stress-test comparator with pre-specified absorption interpretation rule | One method, not exhaustive | "We compare against one representative model-personalization stress-test (Ditto/local-head comparator); exhaustive comparison is out of scope." |
| "Missing aggregation baselines" | FedProx as heterogeneity-aware aggregation stress test | One aggregation method | "We add the most-cited heterogeneity-aware aggregation stress test (FedProx); further aggregation sensitivity is future work." |
| "Missing federated thresholding SOTA comparison" | Laridi-style threshold on stored score artifacts with matched operating-point protocol (see §8.4) | Adaptation to non-IoT method | "We implement a faithful DATP-compatible adaptation of the Laridi-style federated threshold, using a matched operating-point protocol and reporting all adaptation choices before result inspection." |
| "Missing temporal drift" | Chronological split on Edge-IIoTset + one-shot recalibration MVE with three pre-specified outcome interpretations | Single split, not streaming | Outcome-specific wording per §10.1 |
| "Missing privacy/leakage discussion" | Bounded-disclosure table + qualitative MIA-risk analysis + cite SecAgg/DP literature | No empirical leakage quantification | "B4 fingerprints constitute distributional metadata; we provide a bounded-disclosure analysis and discuss SecAgg/DP mitigations as future work." |
| "Missing deployment-cost discussion" | Bytes-per-round table comparing B1/B2/B4 communication and per-client storage, estimated from message sizes | No hardware measurement | "Per-round communication and per-client storage overhead are estimated from message sizes; hardware-level profiling is future work." |
| "Journal version insufficiently different from conference" | ≥40% substantive new material with explicit cover-letter enumeration | Editor judgment | Cover letter lists each new section by number; introduction cites the conference paper as prior work |
| "Scope drift from adding too much" | Hard limits enforced: 1 new dataset, 1 conditional partition redesign, 3 stress-test comparators, 4 threshold variants, 1 temporal family, 6 mechanism analyses | Some reviewers always want more | "We hold the encoder, AE architecture, and mainline FedAvg training fixed; all extensions are threshold-scope or evaluation-side." |

---

## 7. Dataset Expansion Decision

| Dataset | Add / Maybe / Reject | Why | DATP Fit | Partition Quality | Calibration Suitability | Temporal Potential | Effort | Risk |
|---|---|---|---|---|---|---|---|---|
| N-BaIoT | **Keep (existing)** | Real 9-device physical partition; Rey 2022 lineage | Excellent | Native device IDs | Excellent | Moderate (chronological traces with gaps) | None new | Aging (2018); narrow attack families |
| CICIoT2023 | **Redesign partition (conditional — Priority 0 required)** | Device-MAC repartition per Pradhan et al. 2025 precedent; file-level is its own weakness | Strong after repartition; file-level retained as Regime B-a regardless | Device-MAC mapping feasibility determined by Priority 0 | Good if repartitioned | Moderate (capture timestamps) | Moderate (MAC mapping) | If Priority 0 is negative, retain Regime B-a only |
| **Edge-IIoTset (Ferrag 2022)** | **ADD — primary new dataset** | Native FL framing; 10+ device types; Pradhan et al. 2025 used 6-client device/application-type partition | Excellent | Native device-type partition | Good | Multi-day capture window enables chronological split | Moderate-Heavy (feature alignment) | Schema differs from N-BaIoT; feature extraction required |
| ToN-IoT | **Reject** | Multi-modal complicates threshold-scope-only design; doubles preprocessing | Medium | Possible via host/IP | Moderate | Good | Heavy | Rejected for this cycle; cite only |
| Bot-IoT, IoT-23, MedBIoT, FedAIoT bundle | **Reject** | Scope drift; insufficient DATP fit | Weak | Weak | Varies | Varies | Heavy | Cite as landscape references only |
| UNSW-NB15 | **Reject** | Not IoT-specific | Very low | None | Weak | Weak | — | Out of scope |

**CICIoT2023 benign-volume threshold (explicit)**: Regime B-b is only used as a main-paper regime if ≥8 clients each have nₖ ≥ 100 benign calibration samples (DATP's existing nₘᵢₙ=100). If fewer than 8 clients satisfy nₖ ≥ 100, Regime B-b is not used as a main-paper regime; retain CICIoT2023 Regime B-a as the near-homogeneous boundary only.

**Final dataset additions (within hard limit of 2 new datasets)**:
1. Edge-IIoTset with native device/application-type partition (1 new dataset)
2. CICIoT2023 device-MAC repartition (same dataset, new regime, conditional on Priority 0 — counts as 0 new datasets)

---

## 8. Baseline Expansion Decision

### 8.1 Framing Rule: Stress-Test Comparators vs Core Causal Ladder

**This distinction is mandatory throughout the roadmap and the eventual journal paper:**

- **Core DATP causal ladder (B1–B4)**: threshold scope is the only changing variable; AE encoder, training protocol, aggregator, and score artifacts are identical across B1, B2, B3, and B4. Results from this ladder support the confirmatory claim.
- **External stress-test comparators (FedProx, Ditto, Laridi-style)**: change the training protocol or threshold-generation mechanism to examine whether the B1→B2 gain survives under different conditions. These results are *framed as robustness checks*, not as part of the core causal isolation. No stress-test result should be presented as if it were within the same experimental control as the B1–B4 ladder.

### 8.2 Baseline Table

| Baseline Family | Add / Optional / Reject | Scientific Question (framed as stress test) | Minimal Implementation | Reviewer Value | Scope Drift Risk | Placement |
|---|---|---|---|---|---|---|
| **FedProx** | **ADD (stress-test)** | Does the B1→B2 CV(FPR) gain survive when a heterogeneity-aware aggregation optimizer is used? | Replace FedAvg aggregator with FedProx (µ ∈ {0.001, 0.01, 0.1}); apply B1–B4 threshold grid | High | Low | Main stress-test table |
| FedBN | **Reject** | — | Would require adding BatchNorm to encoder — breaks frozen-encoder discipline | — | High | Rejected everywhere |
| FedAvgM / FedYogi | Optional (future work) | — | — | Low–Medium | Medium | Not in this cycle |
| **Ditto (or named variant — see §8.3)** | **ADD (stress-test)** | Does the B1→B2 CV(FPR) gain survive when model-side personalization is also applied? | See §8.3 for mandatory implementation choice and pre-specified interpretation rule | High | Low | Main stress-test table |
| FedPer / APFL / Per-FedAvg | **Reject** | — | — | Diminishing | Medium | Rejected |
| Clustered FL (Sáez-de-Cámara 2023) | Optional / qualitative only | Qualitative contrast in related work | Full reimplementation heavy; cite and contrast | Medium | Medium | Related work section; no quantitative reimplementation |
| **Laridi-style federated summary-statistics threshold** | **ADD (threshold comparator)** | Does device-aware per-client thresholding (B2) provide stronger FPR-equity than the federated summary-statistics threshold under heterogeneous regimes? | See §8.4 for pre-specified matched operating-point protocol | Critical | Low | Main comparator table |
| Local-only bounding case | Optional supplementary | — | — | Low–Medium | Low | Supplementary |
| Centralized reference (B0) | **Keep** | Already present | — | — | None | Main |

**Final stress-test comparators (within hard limit of 3 families)**:
1. FedProx (aggregation-side heterogeneity stress test)
2. Ditto or explicitly named local-head personalization comparator (model-side personalization stress test)
3. Laridi-style federated summary-statistics threshold (federated-thresholding SOTA comparator, matched operating-point)

### 8.3 Ditto Implementation Choice and Interpretation Rule

#### Implementation Choice (mandatory — decide before training begins)

**Preferred option — Standard Ditto-style personalization**:
- Each client maintains a personalized local model (full AE, identical architecture to the FedAvg AE).
- The personalized model is trained with a proximal regularization term toward the current global model: `loss_local = loss_recon + (µ/2) · ||w_local − w_global||²`.
- Thresholds B1–B4 are evaluated over the personalized model's benign reconstruction-error score artifacts.
- Report explicitly as "Ditto-style model-side personalization stress test" with µ ∈ {0.001, 0.01, 0.1}.

**Acceptable fallback — Local-head personalization comparator** (use this label if standard Ditto is too heavy):
- Freeze the FedAvg-trained shared encoder; train a lightweight local reconstruction head per client.
- Apply B1–B4 over local-head score artifacts.
- **Do not call this "Ditto."** Label it "local-head personalization comparator" and state explicitly: *"This is a simplified model-personalization stress test using a frozen shared encoder with a local reconstruction head; it is not a full Ditto reproduction."*

**Decision gate**: the chosen option must be documented in a written implementation decision (action G3.0) before any training runs. The choice cannot be made after inspecting results.

#### Ditto Stress-Test Interpretation Rule (pre-specified)

Let:
- `Δ_FedAvg = CV(FPR)[FedAvg+B1] − CV(FPR)[FedAvg+B2]`
- `Δ_Ditto = CV(FPR)[Ditto+B1] − CV(FPR)[Ditto+B2]`

**Pre-specified interpretation**:
- If `Δ_Ditto ≥ 0.75 · Δ_FedAvg`: threshold personalization remains strongly useful under model personalization. Report as corroborating evidence for DATP.
- If `0.25 · Δ_FedAvg ≤ Δ_Ditto < 0.75 · Δ_FedAvg`: model personalization partially absorbs the threshold-scope effect but does not eliminate it. Report as a partial-absorption boundary condition.
- If `Δ_Ditto < 0.25 · Δ_FedAvg`: model personalization largely absorbs the threshold-scope effect. **DATP's claim must be narrowed** to FedAvg-style/shared-encoder settings; this must be reported explicitly in the paper, not hidden.
- If `CV(FPR)[Ditto+B1]` is already close to `CV(FPR)[FedAvg+B2]` (within 0.05 absolute): report that model personalization may be an alternative path to FPR equity — this is an important positive finding about Ditto, not a failure of DATP.

**Safe wording**: "Ditto is a stress-test comparator. If Ditto absorbs the B1→B2 gap, the journal paper must report this as an important boundary condition of the DATP effect rather than treating it as a negative result to be suppressed."

This interpretation rule must be documented before training and applied without adjustment after results are inspected.

### 8.4 Laridi-Style Baseline Pre-Specification (mandatory — finalize before computation begins)

The following protocol must be locked before any Laridi-style results are computed. **Do not tune any element of this protocol after seeing results.**

| Protocol element | Specification |
|---|---|
| What each client sends | Local benign-only summary statistics for pooled moments: count (nₖ), mean (µₖ), and variance (σₖ²) of reconstruction errors. No raw scores are shared. No attack labels are used in calibration. |
| Mean aggregation | Sample-count-weighted: `µ_global = Σ nₖ·µₖ / Σ nₖ` |
| Variance aggregation | **Full pooled variance including within-client and between-client components**: `σ²_global = Σ nₖ · [σₖ² + (µₖ − µ_global)²] / Σ nₖ`. This captures both local spread (within-client term) and mean heterogeneity across devices (between-client term). |
| Variance diagnostic (mandatory in main paper) | Report the following decomposition in the Laridi comparison section (not supplementary): `within_term = Σ nₖ·σₖ² / Σ nₖ`; `between_term = Σ nₖ·(µₖ − µ_global)² / Σ nₖ`; `between_ratio = between_term / (within_term + between_term)`. If `between_ratio > 0.5`, the paper must explicitly state: "The between-client mean shift dominates the global variance, indicating that a single global summary-statistics threshold is structurally strained under this level of heterogeneity." |
| Matched-exceedance count exchange | After computing `µ_global` and `σ_global`, the server broadcasts a pre-specified candidate threshold grid `τ(k) = µ_global + k · σ_global`, with fixed `k ∈ {0.00, 0.01, 0.02, ..., 5.00}`. Each client returns only its benign exceedance count for each candidate threshold, `cₖ(k) = #{e ∈ Eₖ,benign_cal : e > τ(k)}`, and its benign calibration count `nₖ`. No raw scores are shared. No attack labels are used. The candidate grid is fixed before results are inspected. |
| Global threshold computation — **main comparison (matched operating point)** | The server computes `exceedance(k) = Σ cₖ(k) / Σ nₖ`, then selects `k* = argmin_k |exceedance(k) − 0.05|`. If multiple `k` values are equally close, choose the larger `k` to avoid selecting a more permissive threshold post hoc. The final matched Laridi-style threshold is `τ_Laridi = µ_global + k* · σ_global`. Report `k*`, the achieved exceedance, and its absolute deviation from 5%. This matched-exceedance `k*` threshold is the **primary Laridi comparator** in the main table. |
| Operating-point fair-comparison wording | *"To avoid comparing B2 and the Laridi-style threshold at different operating points, the main comparison matches the benign calibration exceedance target of q=0.95. Fixed-k variants (k∈{2.0, 2.5, 3.0}) are reported only as sensitivity checks in supplementary material."* |
| Fixed-k variants | Compute `τ_global = µ_global + k·σ_global` for k∈{2.0, 2.5, 3.0} and report all three as sensitivity checks in supplementary material. These are **not the main Laridi comparison**. |
| When applied | Once per seed, per dataset/regime, using the same benign calibration split as B1 and B2. Candidate-grid k values and the matched exceedance target are pre-specified per this document and fixed before result inspection. |
| What makes it a fair comparison | Same benign calibration data; same score artifacts; matched operating point; summary-statistics-compatible count exchange; no raw score sharing; no attack labels. |
| Overlap-region search | If the original Laridi method requires attack-labeled calibration data for the overlap-region threshold search, this adaptation must use only benign calibration data and document the divergence from the original method explicitly. |
| Disclosure wording | *"We implement a faithful DATP-compatible adaptation of the Laridi-style federated summary-statistics threshold (Laridi et al. 2024, Sci. Rep.), using full pooled variance (including between-client mean shift) and a matched-exceedance operating point. All adaptation choices are reported; we distinguish this adaptation from the original method, which was evaluated on non-IoT tabular datasets with different task structure."* |

---

## 9. Threshold Variant Decision

| Threshold Variant | Definition | Add / Optional / Reject | Why It Matters | Risk | Placement |
|---|---|---|---|---|---|
| **q-sensitivity sweep** | B1/B2/B4 evaluated at q∈{0.90, 0.95, 0.975, 0.99} systematically | **ADD (mandatory)** | Shows headline result is not a q=0.95 artefact | None | Main heatmap |
| Global pooled p95 | Single global p95 over pooled benign scores | Already in Table VII | Sensitivity check on construction | None | Main (existing) |
| Sample-weighted shared | Weighted mean of local p95 by calibration n | Already in Table VII | Sensitivity check on construction | None | Main (existing) |
| Per-client B2 | Local p95 | Existing | DATP core | None | Main |
| Family-mean B3 | Per-family arithmetic mean | Existing | DATP core | None | Main |
| Cluster-mean B4 | k-means cluster-mean | Existing | DATP core | None | Main |
| Robust cluster median | Cluster-wise median of τₖ | Optional | Reduces sensitivity to outlier clients in B4 | None | Supplementary paragraph |
| **Local-global shrinkage** | τₖ(λ) = λ·τₖ,p95 + (1−λ)·τ_global, λ∈{0, 0.25, 0.5, 0.75, 1} | **ADD (mandatory)** | Interpolates B1↔B2; mitigates P10 Macro-F1 loss | Low | Main figure |
| **Calibration-size-aware fallback** | Size-dependent λ(nₖ); smooth transition from per-client to shared as nₖ drops | **ADD (mandatory)** | Closes operational loophole; supersedes hard nₘᵢₙ=100 fallback | None | Main subsection + algorithm pseudocode |
| **Split-conformal B2 (B2-conf)** | Per-client split-conformal calibration with marginal coverage 1−α per Plassier et al. ICML 2023 | **ADD (mandatory)** | Closes W01 with finite-sample coverage guarantee | Low | Main + Appendix A |
| Empirical-Bayes / James-Stein | Bayesian shrinkage | **Reject** | Heavier theoretical apparatus; scope drift | Medium | Future work |
| Drift-aware periodic recalibration | Periodic per-client recalibration | Folded into temporal section | See §10 | Medium | §10 |
| Full conformal anomaly detection | Distribution-free with Byzantine-robust extensions | **Reject** | Scope drift | High | Future work |

**Final threshold variants (within hard limit of 4 new variants)**:
1. q-sensitivity sweep
2. Local-global shrinkage τₖ(λ)
3. Calibration-size-aware fallback (size-dependent shrinkage)
4. Split-conformal B2 (B2-conf)

---

## 10. Temporal and Recalibration Decision

1. **Can current datasets support true temporal analysis?** Partially. N-BaIoT has chronological traces with gaps but limited drift magnitude. Edge-IIoTset has a multi-day capture window and is the preferred temporal substrate. CICIoT2023 Regime B-a discards within-file time and is unusable for temporal analysis; Regime B-b preserves capture timestamps if Priority 0 confirms metadata.
2. **Minimum viable temporal experiment (MVE)**: chronological 70/30 split on **Edge-IIoTset**. Train AE + calibrate thresholds B1/B2/B4 on the first 70% of each client's benign data by capture timestamp. Evaluate on the last 30% with: (a) frozen thresholds and (b) one-shot recalibration at the temporal boundary. The temporal regime must not begin until Edge-IIoTset preprocessing is stable (Gate 2 exit criteria satisfied).
3. **Rejected (scope drift)**: streaming sliding-window recalibration; cross-dataset transfer; Page-Hinkley drift detection; FLARE/FLAME-style concept-drift mitigation; Byzantine-robust federated conformal prediction.
4. **Metrics**: per-time-window CV(FPR), mean FPR drift, per-client FPR slope vs. time, Macro-F1 stability, one-shot recalibration recovery ratio (Z% = recovered CV(FPR) gain / original gain).

### 10.1 Pre-Specified Temporal MVE Outcome Interpretations

All three outcomes are valid findings. Outcome interpretation must not be adjusted after results are inspected.

**Outcome A — Drift exists and one-shot recalibration helps** (recovery ratio ≥50% of original CV(FPR) gain):
Report recovery percentage. Claim: "Under the available temporal window, one-shot threshold recalibration recovers a meaningful portion of the CV(FPR) gain; periodic recalibration is a viable operational policy for device-aware thresholds."

**Outcome B — Drift exists and one-shot recalibration does not help** (drift detectable but recovery ratio <50%):
Report as a limitation. Claim: "Device-aware thresholds exhibit temporal fragility in this benchmark; one-shot recalibration is insufficient; a continuous drift-mitigation mechanism would be required, which is future work." Do not add a streaming drift detector retroactively to rescue the result.

**Outcome C — No meaningful drift is observed** (FPR drift within bootstrap CI of the static split):
Report as a stability finding, not a failed experiment. Claim: *"Under the available chronological window of Edge-IIoTset, device-aware thresholds appear stable; this experiment does not prove general temporal robustness, but it reduces concern that the observed DATP effect is purely a static-split artefact."*

**Final temporal experiment family (within hard limit of 1)**: Edge-IIoTset chronological split + one-shot threshold recalibration, with pre-specified three-outcome interpretation.

---

## 11. Deeper Analysis Decision

| Analysis | Add / Optional / Reject | What It Proves | What It Does Not Prove | Required Artifact | Output | Reviewer Value |
|---|---|---|---|---|---|---|
| **Per-client benign+attack score CDFs with B1/B2/B4 overlays + Ennio Doorbell failure-mode deep dive** | **ADD** | Mechanism of FPR concentration; why P10 Macro-F1 drops in low-separability devices | Generalization beyond N-BaIoT clients | Stored per-client scores (existing) | Figure | High |
| **JS divergence ↔ DATP-benefit correlation** | **ADD** | Heterogeneity severity predicts DATP value | Causality | Per-client benign distributions + CV(FPR) deltas | Scatter + table | High |
| **Threshold shift vs ΔFPR/ΔTPR scatter** | **ADD** | Quantifies fairness-vs-sensitivity trade-off surface | Solves the trade-off | Per-client thresholds + scores | Scatter | High |
| **Calibration-size sensitivity sweep** (nₖ ∈ {50, 100, 250, 500, 1k, 5k}) | **ADD** | When DATP remains usable under low calibration data | Online cold-start | Subsampled benign scores | Figure | High |
| **Operational false-alarm burden** | **ADD (with declared traffic-volume source — see §11.1)** | Translates CV(FPR) into alerts/device/day under a declared traffic assumption | Hardware deployment | Per-client FPR × declared traffic volume | Table | High |
| **B4 cluster-feature ablation + interpretability** | **ADD** | Defends B4 as meaningful taxonomy-free approximation | Privacy safety of B4 | Re-run B4 with feature subsets (mean / std / skew / p95 alone, then all four) | Compact table + **cluster-to-device-type contingency table or small heatmap** (Sankey is not appropriate at K=3/K=9 scale) | High |
| Bootstrap CIs + effect sizes for all key metrics | Optional | Statistical rigor | New phenomena | Stored seed-level metrics | Updated tables (supplementary) | Medium |
| Worst-client balanced accuracy deep dive | Optional | Worst-case behavior | Average behavior | Existing | Table | Medium |
| Seed-level stability metrics (Cliff's δ, Wilcoxon) | Optional | Stronger statistical evidence | Causality | Stored results | Supplementary table | Medium |
| Sáez-de-Cámara model-clustering vs B4 score-stat clustering | Optional / qualitative only | Differentiates clustering basis | DATP superiority | Full reimplementation is out of scope | Related work table | Medium |
| Conformal coverage check (marginal coverage = 1−α) | Integrated with B2-conf | Verifies conformal guarantee | — | B2-conf new runs | Figure | High (integrated) |
| MIA-style empirical leakage probe | **Reject** | — | — | Would require MIA infrastructure not established in IoT-threshold literature | — | Reject |

### 11.1 Alert-Burden Traffic-Volume Specification (mandatory)

The operational alert-burden table must declare its traffic-volume assumption using one of the following sources. The chosen source must be stated in the paper:
- **Preferred**: derive volume from each dataset's own benign test-set record count per client per unit time (using capture timestamps where available).
- **Acceptable**: cite a published IoT traffic-profile study for traffic rates typical of each device type.
- **Fallback**: present numbers as a normalized hypothetical (e.g., "assuming N benign packets/day per client, consistent with [describe assumption]"), clearly labeled as illustrative rather than as a real deployment estimate.

Do not present hypothetical alert/day numbers as real deployment measurements.

**Final deeper analyses (within hard limit of 6)**:
1. Per-client error CDF overlays + Ennio Doorbell failure-mode deep dive
2. JS divergence ↔ DATP-benefit correlation
3. Threshold shift vs ΔFPR/ΔTPR scatter
4. Calibration-size sensitivity sweep
5. Operational false-alarm burden (with declared traffic-volume source)
6. B4 cluster-feature ablation + interpretability (contingency table or small heatmap; no Sankey)

---

## 12. Elsevier Venue Target Matrix

| Rank | Journal | Scope Match | Official Policy Evidence | Conference Extension Risk | Required Strengthening | Desk-Rejection Risk | Recommendation |
|---|---|---|---|---|---|---|---|
| **1** | **Computer Networks** (ISSN 1389-1286, 2024 JIF 4.6, Q1) | **Strongest** — Rey et al. 2022 (CN 204:108693) is the foundational FL-IoT-malware paper on N-BaIoT; identical dataset lineage | **Verbatim** Guide for Authors: *"Enhanced, extended versions of quality papers presented at conferences or workshops can be submitted to our journal for review"* | Low if extension is substantial and conference is cited | Strong package as specified in §18 | Low–Medium | **PRIMARY TARGET** |
| 2 | **Internet of Things (Elsevier)** (ISSN 2542-6605, 2024 JIF ~7.6, Q1) | Strong — IoT scope covers security and ML applications in IoT | Standard Elsevier originality language; no journal-specific conference-extension wording verified | Medium — editor may want stronger IoT-systems narrative | Same package + heavier IoT-deployment framing in introduction | Medium | **STRONG BACKUP** |
| 3 | **Cyber Security and Applications** (Elsevier OA) | Good — explicit cybersecurity + AI+IoT scope; Olanrewaju-George 2025 (DATP ref [7]) published here | TO VERIFY at submission time | Medium | Same package | Medium | Viable backup if CN/IoT both fail; OA cost consideration |
| 4 | **JNCA** (2024 JIF ~8.0, Q1) | Strong — networked applications + security | Standard Elsevier originality language | Low–Medium | Same package; emphasize networked-application framing | Medium | Acceptable third-tier backup |
| 5 | **FGCS** (2024 JIF ~6.1, Q1) | Moderate — distributed systems; security allowed but not central | Verbatim: 40% new contributions, different title, cite original, list new sections | Medium-High | Significant systems-framing rework | Medium-High | Not recommended — scope drift risk |
| **Excluded** | **Computers & Security (COSE)** | Topically appealing in principle | **Verbatim moratorium**: *"As of early 2024, we have instituted a moratorium on consideration of submissions that feature AI or ML as significant components… items directed to the security of AI/ML systems themselves (such as LLM and federated learning) are out of scope."* FedMSE (2025) and earlier COSE FL-IDS papers predated the moratorium or slipped through; they are not a safe precedent today. | **Certain desk-reject** | — | **VERY HIGH** | **DO NOT SUBMIT. Final.** |

---

## 13. Conference-to-Journal Originality Plan

1. **Conference paper contributes**: controlled threshold-scope study (B1–B4) under fixed FedAvg AE on N-BaIoT (confirmatory), CICIoT2023 file-level (applicability boundary), N-BaIoT Dirichlet sweep; CV(FPR) 1.017→0.299; B4 ≈52% recovery; bootstrap CI on per-seed deltas.
2. **Journal paper must add** (target ≥40% substantive new material): Edge-IIoTset device-partition regime; CICIoT2023 device-MAC repartition (conditional on Priority 0); 3 stress-test comparator families × B1–B4 threshold grid; 4 new threshold variants; chronological-split + one-shot recalibration regime; 6 deeper analyses; Appendix A; expanded related work.
3. **What can be reused**: DATP nomenclature and B1–B4 taxonomy verbatim; Regime A N-BaIoT confirmatory result (extended to 10 seeds); Regime C Dirichlet sweep; B0 centralized reference; theoretical definitions and notation; reproducibility artifact structure.
4. **What must be new**: every figure either redrawn with additional series or replaced; every table extended; every section above 50% reused prose rewritten substantially.
5. **Novelty threshold**: at least 40% substantive new material. No Elsevier-wide policy prescribes an exact percentage; 40% is the safe conservative bar (FGCS explicit; ICPR/PRL 30% is venue-specific only). Do not claim an exact percentage in the cover letter; list the new material concretely instead.
6. **Cover letter disclosure template**:
   *"This manuscript is an extended version of our conference paper '[title]' (Reference [X]). The conference version established the DATP framework with the four-policy threshold-scope comparison on N-BaIoT and reported CV(FPR) reduction from 1.017 to 0.299 under per-client thresholding. The present journal manuscript contains at least 40% substantive new material, including: (i) a new device-partitioned Edge-IIoTset benchmark and, if Priority 0 confirms metadata, a device-MAC repartition of CICIoT2023; (ii) four new threshold variants — q-sensitivity sweep, local-global shrinkage, calibration-size-aware fallback, and split-conformal B2; (iii) three stress-test comparator families (FedProx, a Ditto-style/local-head model-personalization comparator, and a matched-operating-point Laridi-style federated summary-statistics threshold) evaluated under the identical threshold grid; (iv) a formal Appendix A delineating where B2's construction-implied FPR equality holds and breaks down; (v) a temporal chronological-split and one-shot recalibration regime with pre-specified outcome interpretations; and (vi) six mechanism analyses. No figures or text passages are reused verbatim. The manuscript is not under consideration elsewhere."*
7. **Self-plagiarism risks**: keep iThenticate verbatim overlap below ~15–20%; redraw or substantially extend every figure; rewrite introduction, related work, and methodology sections.
8. **Duplicate-publication risks**: avoid simultaneous submission; wait for conference camera-ready before journal submission; cite conference paper as [X] in the introduction.
9. **Seed extension honesty rule**: If the 10-seed extension results in a wider CI or a CI that approaches zero, the 10-seed result is the main result. The 5-seed conference result is explicitly labeled as preliminary. If the 10-seed CI includes zero, the claim must be revised accordingly — the 10-seed result is not suppressed.

---

## 14. Three-Level Expansion Roadmap

### 14.1 Minimal Extension

| Component | Required Action | Reviewer Value | Effort | Risk |
|---|---|---|---|---|
| Datasets | Keep N-BaIoT; redesign CICIoT2023 by device-MAC (if Priority 0 confirms metadata) | Medium | Moderate | High — single physical-device benchmark is fragile vs Q1 reviewer |
| Baselines | FedProx stress test only | Medium | Moderate | High — no model-personalization and no federated-thresholding comparison |
| Threshold variants | q-sensitivity + shrinkage | Medium | Immediate | Medium |
| Temporal | None | None | None | High — drift question unaddressed |
| Deeper analyses | Client-CDF overlays + failure-mode taxonomy + operational burden | Medium | Immediate | Medium |
| **Net risk** | — | — | — | **High desk-reject risk at Computer Networks** |

### 14.2 Strong Extension (RECOMMENDED)

| Component | Required Action | Reviewer Value | Effort | Risk |
|---|---|---|---|---|
| Datasets | N-BaIoT + Edge-IIoTset + CICIoT2023 device-MAC (conditional on Priority 0) | High | Moderate-Heavy | Low |
| Stress-test comparators | FedProx + Ditto/named-variant + matched-operating-point Laridi-style (3 families × B1–B4 threshold grid) | High | Heavy | Low |
| Threshold variants | q-sensitivity + local-global shrinkage + calibration-size-aware fallback + split-conformal B2 | High | Moderate | Low |
| Temporal | Chronological split + one-shot recalibration on Edge-IIoTset; 3 pre-specified outcomes | Medium-High | Moderate | Low |
| Deeper analyses | All 6 must-have analyses | High | Moderate | Low |
| Appendix A | Formal B2 construction-equality note and boundary conditions | High | Immediate | Low |
| Seeds | Extend to 10; report honestly per seed-extension rule | Medium | Immediate | None |
| Privacy | Bounded-disclosure table + qualitative MIA-risk discussion | Medium | Immediate | Low |
| **Net risk** | — | — | — | **Low–Medium at Computer Networks** |

### 14.3 Ambitious Extension (NOT RECOMMENDED — scope drift)

Adds multiple datasets, broad personalized-FL benchmarking, streaming drift detection, hardware profiling, adversarial robustness. DATP identity dissolves; paper becomes generic FL-IDS. Not pursued this cycle.

---

## 15. Execution Priority: Journal Core vs Supplementary

### 15.1 Must-Have Journal Core

| Item | Notes |
|---|---|
| Priority 0: CICIoT2023 metadata feasibility check | Before everything else; determines dataset narrative |
| Appendix A: "B2 equalizes by construction" formal note | Immediate; no new training |
| Laridi-style federated threshold baseline (matched-operating-point protocol pre-specified) | Gate 1; operates on stored scores |
| q-sensitivity sweep | Gate 1; stored scores |
| Calibration-size sensitivity sweep | Gate 1; subsampled stored scores |
| Local-global shrinkage threshold τₖ(λ) | Gate 1; stored scores |
| Split-conformal B2-conf with marginal coverage check | Gate 1; stored scores |
| B4 cluster-feature ablation | Gate 1; stored fingerprints |
| JS divergence ↔ DATP-benefit regression | Gate 1; stored distributions |
| P10/worst-client failure-mode analysis (Ennio Doorbell deep dive) | Gate 1; stored scores |
| Operational alert-burden table (declared traffic-volume source) | Gate 1; derived from dataset benign counts |
| Threshold shift vs ΔFPR/ΔTPR scatter | Gate 1; stored scores |
| 10-seed extension (report honestly per seed-extension rule) | Gate 1 if compute allows; else 5-seed with explicit power limitation |
| Ditto implementation choice documented (§8.3) | Gate 3 prerequisite; document before training |
| Ditto stress-test interpretation rule pre-specified | Gate 3 prerequisite; see §8.3 |
| Edge-IIoTset preprocessing + device-partition + FedAvg AE training | Gate 2 |
| CICIoT2023 device-MAC repartition (conditional on Priority 0) | Gate 2 |
| FedProx stress-test training | Gate 3 |
| Ditto/named-variant stress-test training | Gate 3 |
| Temporal MVE (chronological split + one-shot recalibration on Edge-IIoTset) | Gate 3 |
| Privacy bounded-disclosure table + qualitative MIA-risk discussion | Gate 1 (writing) |
| Expanded related work | Gate 1 (writing) |

### 15.2 Supplementary or Only-If-Time

- Full communication/storage cost table
- Bootstrap CIs for all metrics beyond the primary CV(FPR) BCa CI
- Complete per-seed per-client raw result tables
- All-metric Wilcoxon + Cliff's δ
- Sáez-de-Cámara quantitative reimplementation (deferred)
- Full personalized-FL benchmark across APFL, FedPer, Per-FedAvg
- Temporal experiment on CICIoT2023 device-MAC (only after Edge-IIoTset temporal MVE is stable)
- Robust cluster median variant (supplementary paragraph)
- Fixed-k Laridi variants (k∈{2.0, 2.5, 3.0}) as sensitivity checks

### 15.3 Reject / Do Not Do

See §21 (Do-Not-Do List). Summary: no FedBN; no empirical MIA; no formal DP; no hardware; no streaming drift; no adversarial; no second new dataset; no >1 model-personalization stress test; no Sankey; no undeclared alert-burden hypotheticals; no hiding unfavorable 10-seed results; no post-hoc tuning of Laridi protocol; no calling local-head variant "Ditto"; no presenting FedProx/Ditto as core causal baselines; no COSE submission.

---

## 16. Priority 0 — Immediate Metadata Feasibility Check

**This must be completed before Gate 1 begins and before any CICIoT2023-related section is drafted in the journal paper.**

### Priority 0 Actions

| Step | Action | Output |
|---|---|---|
| P0.1 | Inspect current CICIoT2023 processed feature files: check whether MAC address, source/destination MAC, device identifier, device-group label, or any recoverable device metadata is retained | `ciciot2023_metadata_feasibility.md` (field-by-field report) |
| P0.2 | If processed metadata is absent: inspect upstream raw/source data (PCAP, CSV, log files) to determine whether device-group or MAC-level labels are recoverable via reprocessing | Appended to `ciciot2023_metadata_feasibility.md` |
| P0.3 | Evaluate benign sample counts per potential device-group client | Estimated benign-per-client table in `ciciot2023_metadata_feasibility.md` |
| P0.4 | Declare one of three outcomes (see below) | Final outcome in `ciciot2023_metadata_feasibility.md` |

### Priority 0 Outcome Declarations

The result must be one of:

- **`CONFIRMED: Regime B-b feasible from current artifacts`** — device-group or MAC metadata is present in processed files; ≥8 clients satisfy nₖ ≥ 100 benign calibration samples from stored data.
- **`REPROCESS REQUIRED: Regime B-b feasible only from raw/source data`** — metadata absent in processed files but recoverable from raw upstream data; reprocessing is feasible within the project timeline.
- **`REJECTED: Regime B-b not feasible; retain Regime B-a only`** — metadata not available in processed or raw data, or fewer than 8 clients satisfy nₖ ≥ 100; Regime B-b is dropped from all sections.

### Priority 0 Downstream Dependencies

- **Gate 2 (all Regime B-b tasks) depends on Priority 0 outcome.**
- If Priority 0 → `REJECTED`: all G2.0–G2.1 tasks are removed; Regime B-b references in §7, §15, §17, §20 are automatically inactive; the paper proceeds with Regime B-a as the CICIoT2023 entry.
- **Do not draft Regime B-b paper sections** (results table, method subsection, analysis) until Priority 0 is `CONFIRMED` or `REPROCESS REQUIRED` and at least G2.1 is complete.

---

## 17. Three-Gate Execution Plan

### Gate 1 — Existing-Score Extension First

**Rationale**: operates entirely on stored per-client score artifacts and fingerprints; no retraining; lowest execution risk; closes the most critical reviewer attacks before dataset or training infrastructure is needed.

**Gate 1 Actions**:

| # | Action | Output | Go/No-Go Criterion | Fallback |
|---|---|---|---|---|
| G1.1 | Write Appendix A: formal explanation of calibration-set vs held-out-test FPR behavior; bound the construction equality by nₖ and distribution stability | Appendix A draft (LaTeX) + small illustrative figure | Reviewed by 1 statistician; claims are bounded | Simplify to a formal note without full derivation |
| G1.2 | Lock and document the complete Laridi-style protocol per §8.4 — including full pooled variance formula, within/between diagnostic terms, and matched-exceedance operating point — before any computation | Written pre-specification document (filed before G1.7) | Protocol finalized and documented before any result is inspected | — |
| G1.3 | Run q-sensitivity heatmap at q∈{0.90, 0.95, 0.975, 0.99} on stored N-BaIoT scores | Main heatmap figure | Ordering B2 < B4 < B1 at all q, or any inversion reported honestly | Report inversion; does not invalidate DATP |
| G1.4 | Run calibration-size sweep (nₖ ∈ {50, 100, 250, 500, 1k, 5k}) via subsampling on stored N-BaIoT scores | Calibration-size sensitivity figure | Curve reaches plateau; shrinkage maps cleanly | Reduce granularity if compute is limited |
| G1.5 | Implement local-global shrinkage τₖ(λ) at λ∈{0, 0.25, 0.5, 0.75, 1} on stored scores | Shrinkage curve figure | λ-curve reported; P10 Macro-F1 per λ reported | Report any non-monotone behavior honestly |
| G1.6 | Implement split-conformal B2-conf with marginal coverage check at α=0.05 on stored scores | Coverage diagnostic figure + main-table row | Empirical coverage within ±0.02 of 1−α | Report coverage failure as conformal-adaptation limitation |
| G1.7 | Implement pre-specified Laridi-style baseline (protocol locked in G1.2): compute full pooled variance with between-client diagnostic; broadcast fixed candidate threshold grid; collect benign exceedance counts only; select matched-exceedance k*; apply to stored N-BaIoT scores | Main comparator table column + between_ratio diagnostic reported in main text | Protocol pre-specified; candidate grid fixed before result inspection; no raw scores or attack labels shared; result computed without tuning; between_ratio reported in main Laridi comparison section | Benign-only fallback if overlap-region requires attack labels |
| G1.8 | Run B4 cluster-feature ablation (4 subsets + all-four) on stored fingerprints | Feature-ablation table + cluster-to-device-type contingency table or small heatmap | Each subset's CV(FPR) reported; cluster assignments mapped to device labels | If unstable across seeds, report instability |
| G1.9 | Compute JS divergence ↔ DATP-benefit regression on stored per-client benign distributions | Scatter figure + correlation table | R² and ρ reported with caveats | Weak R² is a real result; report it |
| G1.10 | Compute operational alert-burden table (FPR × declared traffic volume) | Alert-burden table with declared traffic-volume source | Traffic-volume source documented and justified | Normalized hypothetical labeled as such |
| G1.11 | Compute threshold shift vs ΔFPR/ΔTPR scatter | Scatter figure | All 9 N-BaIoT devices reported; no device filtering | — |
| G1.12 | Extend to 10 seeds if compute allows; recompute all BCa CIs | Updated result tables; per-seed CSVs | 10-seed result reported honestly; if CI widens or approaches zero, the claim is revised accordingly | 5-seed result reported with explicit power limitation |
| G1.13 | Write privacy bounded-disclosure table + qualitative MIA-risk discussion | Privacy subsection draft | No formal-privacy claim; all wording bounded | — |
| G1.14 | Write expanded related work section | Related work draft | Covers Laridi 2024, Sáez-de-Cámara 2023, FedMSE 2025, Belarbi 2023, Plassier ICML 2023, Pradhan et al. 2025 | — |

**Gate 1 Exit Criteria**:
- Priority 0 is already complete (Priority 0 precedes Gate 1).
- All G1.1–G1.14 analyses are reproducible from stored artifacts; no retraining was required.
- Appendix A drafted and reviewed.
- Laridi-style protocol is locked, full pooled variance formula applied, between-client diagnostic computed and reported in main text.
- Matched-exceedance operating point is used as the primary Laridi comparator; fixed-k variants are sensitivity only.
- "B2 is tautological" reviewer attack is explicitly addressed by Appendix A + B2-conf + calibration-size sweep.
- All claims remain centered on threshold scope.
- 10-seed extension result (or explicit 5-seed power limitation) is documented.

---

### Gate 2 — Dataset Expansion (after Priority 0 outcome is known and Gate 1 is stable)

| # | Action | Output | Go/No-Go Criterion | Fallback |
|---|---|---|---|---|
| G2.0 | **Use Priority 0 result** to determine Regime B-b feasibility | `ciciot2023_metadata_feasibility.md` (from Priority 0) | Priority 0 outcome is documented | If `REJECTED`: remove all G2.1–G2.2 tasks; retain Regime B-a only |
| G2.1 | If Priority 0 → `CONFIRMED` or `REPROCESS REQUIRED`: build CICIoT2023 device-MAC partition per Pradhan et al. (Sci. Rep. 2025) precedent | Client-count table; benign calibration count per client; attack count; eligibility audit | ≥8 clients, each with nₖ ≥ 100 benign calibration samples | <8 eligible clients: retain Regime B-a only; do not use Regime B-b in main paper |
| G2.2 | Download and preprocess Edge-IIoTset; validate feature schema; audit capture timestamps | Feature-alignment report; client-count table; benign calibration per client; timestamp audit | Coverage ≥90% of clients (nₖ ≥ 100 for ≥90% of clients); timestamps available | Reduce K or defer temporal MVE to supplementary |
| G2.3 | Train FedAvg AE on Edge-IIoTset (K ∈ {6, 15}); compute per-client score artifacts | Edge-IIoTset score artifacts | Convergence per seed; calibration coverage logged | Reduce K if insufficient client data |
| G2.4 | If G2.0–G2.1 confirmed (≥8 clients with nₖ ≥ 100): train FedAvg AE on CICIoT2023 device-MAC partition; compute score artifacts | CICIoT2023 Regime B-b score artifacts | ≥8 clients each with nₖ ≥ 100 benign calibration samples; convergence per seed | Fall back to Regime B-a only |
| G2.5 | Run B1–B4 + matched-exceedance Laridi-style baseline + q-sensitivity on Edge-IIoTset + CICIoT2023 Regime B-b (if confirmed), using the same fixed-grid benign exceedance-count protocol from §8.4 | Updated main results tables | All deltas reported with BCa CIs; Laridi candidate grid fixed before result inspection; no raw scores or attack labels shared; between_ratio diagnostic from Laridi reported | Negative result reported and discussed |

**Gate 2 Exit Criteria**:
- Priority 0 outcome is documented and applied.
- Edge-IIoTset artifacts are valid with documented client counts, benign calibration counts, attack counts, and eligibility coverage.
- CICIoT2023 Regime B-b feasibility is either confirmed (≥8 clients with nₖ ≥ 100) or explicitly rejected.
- Temporal timestamp availability in Edge-IIoTset is verified.
- All partitions documented before any training-side stress tests begin.

---

### Gate 3 — Training-Side Stress Tests (after Gate 2 is stable)

| # | Action | Output | Go/No-Go Criterion | Fallback |
|---|---|---|---|---|
| G3.0 | Document Ditto implementation choice (standard Ditto vs local-head comparator per §8.3) and Ditto interpretation rule (§8.3 absorption margins) | Written implementation decision | Choice finalized and interpretation rule recorded before training | No post-hoc switching based on which performs better |
| G3.1 | Implement and run FedProx (µ ∈ {0.001, 0.01, 0.1}) on N-BaIoT and Edge-IIoTset; apply B1–B4 threshold grid | Stress-test comparator table | All seeds converge; labeled as stress-test comparator, not core causal claim | If all pre-specified µ values fail to converge, report convergence failure. Any additional µ search must be explicitly labeled exploratory and cannot be used to support the main stress-test claim. |
| G3.2 | Implement and run Ditto/named-variant on N-BaIoT and Edge-IIoTset; apply B1–B4 threshold grid; apply pre-specified absorption interpretation rule from §8.3 | Stress-test comparator table; absorption ratio Δ_Ditto / Δ_FedAvg reported | Personalized model converges; absorption ratio computed and interpretation rule applied | Report any absorption level honestly; all three absorption outcomes are valid findings |
| G3.3 | Run temporal MVE: chronological 70/30 split on Edge-IIoTset; frozen vs one-shot recalibration; apply pre-specified outcome interpretation (§10.1) | Temporal drift figure + table; pre-specified outcome applied | Pre-specified outcome interpretation applied without adjustment | If Edge-IIoTset timestamps are unsuitable (see G2.2 fallback): defer to supplementary and document reason |
| G3.4 | Extend to 10 seeds across all Gate 3 runs if compute budget allows; recompute BCa CIs | Updated seed count and CIs | 10-seed result reported honestly regardless of direction | 5-seed with power limitation |

**Gate 3 Exit Criteria**:
- FedProx and Ditto/named-variant are labeled as stress-test comparators throughout; never presented as part of core B1–B4 causal isolation.
- Ditto absorption ratio is reported according to the pre-specified rule.
- Temporal MVE pre-specified outcome interpretation is applied.
- No result is hidden because it weakens the original story.

---

## 18. Final Recommended Package

**Selected package: Strong Extension (§14.2). Selected target journal: Computer Networks. Selected backup: Internet of Things (Elsevier). Computers & Security: excluded.**

1. **Dataset additions (≤2)**: Edge-IIoTset (device/application-type partition, K ∈ {6, 15}); CICIoT2023 device-MAC repartition (conditional on Priority 0 — same dataset, new regime).
2. **Stress-test comparators (≤3 families; all external stress tests, not core causal)**: FedProx (aggregation-side); Ditto or named local-head variant (model-side, with pre-specified absorption interpretation rule); matched-operating-point Laridi-style federated summary-statistics threshold (federated-thresholding SOTA).
3. **Threshold additions (≤4 new variants)**: q-sensitivity sweep; local-global shrinkage τₖ(λ); calibration-size-aware fallback; split-conformal B2-conf.
4. **Temporal/recalibration addition (≤1 family)**: Edge-IIoTset chronological 70/30 split; frozen vs one-shot recalibration; three pre-specified outcome interpretations.
5. **Deeper analyses (≤6)**: per-client error CDF overlays + Ennio Doorbell failure-mode deep dive; JS divergence ↔ DATP-benefit correlation; threshold shift vs ΔFPR/ΔTPR scatter; calibration-size sensitivity sweep; operational false-alarm burden; B4 cluster-feature ablation + contingency table or small heatmap.
6. **New figures**: per-client benign-error CDF overlay; calibration-size sensitivity curve; shrinkage λ-curve; JS↔gain scatter; threshold-variant q-heatmap; temporal CV(FPR) drift trajectory; split-conformal coverage diagnostic; B4 feature-ablation heatmap.
7. **New tables**: stress-test comparator grid (FedAvg / FedProx / Ditto-or-named × B1–B4 + matched-Laridi-threshold); Edge-IIoTset Regime A' results; CICIoT2023 Regime B-b results (conditional); failure-mode analysis; privacy-disclosure tabulation; communication/storage overhead; B4 cluster-feature ablation; alert-burden; Laridi between-ratio diagnostic.
8. **New sections**: Threshold-Variant Taxonomy; Calibration-Size Analysis; Failure-Mode and Limits of DATP; Privacy and Leakage Analysis; Temporal Recalibration MVE; Comparison with Federated Thresholding SOTA and Model-Personalization Stress Test; Post-2022 Related Work.
9. **Supplementary/Appendix**: Appendix A (B2 construction-equality formal note + boundary conditions); fixed-k Laridi sensitivity (k∈{2.0, 2.5, 3.0}); full hyperparameter tables; per-seed per-client raw results; Docker image + git commit hash; extended Zenodo artifact.
10. **Claims to strengthen**: (a) threshold scope alone changes false-alarm distribution — backed by 2 datasets + conformal variant + calibration-size robustness; (b) gain not absorbed by heterogeneity-aware aggregation or model-side personalization — pre-specified stress-test results; (c) effect monotone in heterogeneity — Dirichlet + JS-divergence regression.
11. **Claims to avoid**: DATP "solves" non-IID; improved global Macro-F1; privacy preservation; concept-drift handling beyond one-shot recalibration; universal dominance over Laridi-style federated threshold.

---

## 19. Artifact and Claim Consistency Check

| Proposed Claim | Support Status | Required Evidence | Artifact Needed | Safe Wording |
|---|---|---|---|---|
| B2 reduces CV(FPR) from 1.017 to 0.299 on N-BaIoT | (1) Already supported | 10-seed extension (report honestly) | Updated seed artifacts | "B2 reduces CV(FPR) from 1.017 to 0.299 (10-seed BCa CI: [a, b]) under the tested N-BaIoT protocol" |
| Effect is monotone in Dirichlet α | (1) Already supported | None | Existing Regime C | "Per-client threshold benefit is monotonically related to Dirichlet α and collapses under IID" |
| B4 recovers ≈52% of B2's improvement | (1) Already supported | None | Existing | "B4 recovers ≈52% of B2's improvement at K=3 (exploratory at N=9)" |
| Effect generalizes to Edge-IIoTset | (3) New experiments | Edge-IIoTset device-partition runs (Gate 2–3) | New | "On Edge-IIoTset (device-partitioned, K=X), B2 reduces CV(FPR) from Y to Z (95% BCa CI: [a, b])" |
| Threshold-scope gain not absorbed by FedProx/Ditto | (3) New stress-test | FedProx/Ditto × B1–B4 grid (Gate 3); absorption rule from §8.3 applied | New | Absorption-category wording per §8.3 interpretation rule; if Δ_Ditto < 0.25·Δ_FedAvg, narrow claim to FedAvg-style settings |
| DATP vs Laridi-style federated threshold | (3) New experiments | Matched-operating-point Laridi-style baseline on stored scores + new datasets; between-ratio diagnostic reported | New | "Under heterogeneous device partitions, the matched-exceedance Laridi-style federated threshold reduces FPR dispersion vs B1 but achieves lower dispersion reduction than B2; between_ratio = [X] indicates [global summary-statistics thresholding is structurally strained / well-suited] under this heterogeneity level" |
| B2 is not a construction tautology | (2) Recomputation + (3) new | Appendix A + calibration-size sweep + B2-conf | New + analytical | "B2's CV(FPR) equalization is exact on calibration data; on held-out test data it is bounded by nₖ and distribution stability (Appendix A); the gain survives split-conformal calibration with marginal coverage 1−α" |
| DATP can handle limited calibration data | (2) Recomputation | n_cal sweep on stored scores | Subsampled scores | "For n_cal ≥ N*, B2 with shrinkage remains effective; below N*, calibration-size-aware fallback recovers B1-equivalent FPR" |
| DATP threshold aging | (3) Temporal MVE | Chronological split on Edge-IIoTset (Gate 3) | New | Outcome-specific wording per §10.1 |
| DATP preserves privacy | (5) Should not be claimed | — | — | "B4 fingerprints constitute distributional metadata; B4 is not a privacy mechanism" |
| B4 is privacy-safe | (5) Should not be claimed | — | — | Do not claim |
| Threshold personalization helps in CICIoT2023 generally | (5) Should not be claimed | — | — | "Regime B-a (file-level, near-homogeneous) is an applicability boundary; Regime B-b (device-MAC) is the heterogeneous evaluation where Priority 0 confirms metadata" |
| DATP reduces operational alert burden | (2) Recomputation | FPR × declared traffic volume | Derived from dataset benign counts | "Translating per-client FPR into expected alerts/day under [declared traffic assumption], B2 reduces worst-client alert load from N₁ to N₂ alerts/day" |
| DATP improves global Macro-F1 | (5) Should not be claimed | — | — | "DATP improves per-client FPR equity; P10 Macro-F1 degrades in low-separability clients (e.g., Ennio Doorbell on N-BaIoT)" |

---

## 20. Implementation-Ready Action Plan

Priorities follow the Priority 0 → Three-Gate structure.

| Priority | Action | Output Artifact | Depends On | Feasibility | Go/No-Go Criterion | Fallback | Placement |
|---|---|---|---|---|---|---|---|
| **P0** | **Priority 0**: inspect CICIoT2023 processed files and upstream raw data for MAC/device metadata; document outcome in `ciciot2023_metadata_feasibility.md` | `ciciot2023_metadata_feasibility.md` with one of three declared outcomes | Nothing — do first | Immediate | Unambiguous documented outcome | — | Prerequisite for all Regime B-b work |
| G1.1 | Write Appendix A: construction-equality formal note, calibration-set vs held-out-test FPR divergence, nₖ boundary conditions | Appendix A draft (LaTeX) + illustrative figure | None | Immediate | Reviewed by 1 statistician; no overclaiming | Simplify to formal note without full derivation | Main Appendix |
| G1.2 | Lock and document complete Laridi-style protocol per §8.4 (full pooled variance with between-client term, matched-exceedance operating point, diagnostic terms, disclosure wording) before any computation | Written pre-specification document | G1.1 | Immediate | Protocol finalized before any result is inspected | — | Protocol annex |
| G1.3 | Run q-sensitivity heatmap (q∈{0.90, 0.95, 0.975, 0.99}) on stored N-BaIoT scores | Main heatmap figure | Stored scores | Immediate | Any inversion reported honestly | — | Main |
| G1.4 | Run calibration-size sweep (nₖ ∈ {50, 100, 250, 500, 1k, 5k}) via subsampling on stored N-BaIoT scores | Calibration-size sensitivity figure | Stored scores | Immediate | Curve plateaus; shrinkage maps cleanly | Reduce granularity | Main |
| G1.5 | Implement local-global shrinkage τₖ(λ) at λ∈{0, 0.25, 0.5, 0.75, 1} on stored scores | Shrinkage curve figure | Stored scores | Immediate | λ-curve reported; P10 Macro-F1 per λ reported | Report non-monotone behavior | Main |
| G1.6 | Implement split-conformal B2-conf with coverage check at α=0.05 | Coverage diagnostic figure + main-table row | Stored scores | Moderate | Empirical coverage within ±0.02 of 1−α | Report coverage failure as conformal-adaptation limitation | Main + Appendix A |
| G1.7 | Implement pre-specified Laridi-style baseline (protocol locked in G1.2): compute full pooled variance with between-client term; broadcast fixed candidate threshold grid; collect benign exceedance counts only; select matched-exceedance k*; apply to stored N-BaIoT scores; report between_ratio in main Laridi section | Main comparator table column + between_ratio diagnostic in main text | G1.2; stored scores | Moderate | Protocol pre-specified; candidate grid fixed before result inspection; no raw scores or attack labels shared; matched-exceedance k* reported; between_ratio reported | Benign-only fallback if overlap-region requires attack labels | Main |
| G1.8 | Run B4 cluster-feature ablation (4 subsets + all-four) on stored fingerprints | Feature-ablation table + cluster-to-device-type contingency table or small heatmap | Stored fingerprints | Immediate | Each subset's CV(FPR) reported; instability reported if present | — | Main |
| G1.9 | Compute JS divergence ↔ DATP-benefit regression | Scatter figure + correlation table | Stored distributions | Immediate | R² and ρ reported with caveats | Weak R² is a real result | Main |
| G1.10 | Compute alert-burden table (FPR × declared traffic volume) | Alert-burden table with declared traffic-volume source | Stored scores + declared source | Immediate | Traffic-volume source documented | Normalized hypothetical labeled as such | Main |
| G1.11 | Compute threshold shift vs ΔFPR/ΔTPR scatter | Scatter figure | Stored scores + thresholds | Immediate | All 9 N-BaIoT clients reported; no filtering | — | Main |
| G1.12 | Extend to 10 seeds if compute allows; recompute all BCa CIs | Updated result tables; per-seed CSVs | Existing pipeline | Immediate | 10-seed result reported honestly including if CI widens | 5-seed with explicit power limitation | Main |
| G1.13 | Write privacy bounded-disclosure table + qualitative MIA-risk discussion | Privacy subsection draft | G1.1–G1.7 results | Immediate | No formal-privacy claim; all wording bounded | — | Main |
| G1.14 | Write expanded related work | Related work draft | G1.1–G1.13 | Immediate | Covers all 7 required references | — | Main |
| G2.0 | Apply Priority 0 outcome to determine Regime B-b tasks | Priority 0 outcome applied; G2.1–G2.2 activated or removed | Priority 0 complete | Immediate | Outcome `CONFIRMED`, `REPROCESS REQUIRED`, or `REJECTED` applied consistently | If `REJECTED`: remove all Regime B-b tasks | Prerequisite for G2.1–G2.2 |
| G2.1 | If Priority 0 positive: build CICIoT2023 device-MAC partition | Client-count table; eligibility audit | G2.0 positive | Moderate | ≥8 clients, each with nₖ ≥ 100 benign calibration samples | <8 eligible clients with nₖ ≥ 100: retain Regime B-a only; drop Regime B-b from main paper | Main (conditional) |
| G2.2 | Preprocess Edge-IIoTset; validate feature schema; audit timestamps | Feature-alignment report; client table; timestamp audit | Gate 1 complete | Moderate-Heavy | Coverage ≥90%; timestamps available | Reduce K; defer temporal MVE to supplementary | Prerequisite for G2.3–G3.3 |
| G2.3 | Train FedAvg AE on Edge-IIoTset (K ∈ {6, 15}); compute score artifacts | Edge-IIoTset score artifacts | G2.2 | Moderate-Heavy | Convergence per seed; calibration coverage logged | Reduce K | Main |
| G2.4 | If G2.0–G2.1 confirmed: train FedAvg AE on CICIoT2023 device-MAC; compute scores | CICIoT2023 Regime B-b score artifacts | G2.0 positive; G2.1 | Moderate-Heavy | ≥8 clients each with nₖ ≥ 100 benign calibration samples; convergence per seed | Fall back to Regime B-a only | Main (conditional) |
| G2.5 | Run B1–B4 + matched-exceedance Laridi-style + q-sensitivity on Edge-IIoTset + CICIoT2023 Regime B-b (if confirmed), using the same fixed-grid benign exceedance-count protocol from §8.4 | Updated main results tables | G2.2–G2.4 | Heavy | All deltas reported with BCa CIs; Laridi candidate grid fixed before result inspection; no raw scores or attack labels shared; Laridi between_ratio reported | Negative result reported and discussed | Main |
| G3.0 | Document Ditto implementation choice and absorption interpretation rule (§8.3) | Written implementation decision | Gate 2 complete | Immediate | Choice finalized; 75%/25% rule documented before training | No post-hoc switching | Protocol annex |
| G3.1 | Implement and run FedProx (µ ∈ {0.001, 0.01, 0.1}) on N-BaIoT + Edge-IIoTset; apply B1–B4 | Stress-test comparator table | G2.2–G2.3 | Moderate (Flower-native) | Convergence per seed; labeled as stress-test comparator | If all pre-specified µ values fail to converge, report convergence failure. Any additional µ search must be explicitly labeled exploratory and cannot be used to support the main stress-test claim. | Main (stress-test section) |
| G3.2 | Implement and run Ditto/named-variant on N-BaIoT + Edge-IIoTset; apply B1–B4; compute absorption ratio Δ_Ditto / Δ_FedAvg; apply pre-specified interpretation rule from §8.3 | Stress-test comparator table + absorption ratio | G3.0; G2.2–G2.3 | Heavy | Personalized model converges; absorption ratio computed; interpretation rule applied | Report any absorption level honestly | Main (stress-test section) |
| G3.3 | Run temporal MVE: chronological 70/30 split on Edge-IIoTset; frozen vs one-shot recalibration; apply pre-specified outcome interpretation (§10.1) | Temporal figure + table; pre-specified outcome applied | G2.2 timestamp confirmation | Moderate | Pre-specified outcome applied without adjustment | If timestamps unsuitable: defer to supplementary; document reason | Main (temporal section) |
| G3.4 | Finalize all Gate 3 runs; recompute BCa CIs to 10 seeds if not already done | Final result tables | G3.1–G3.3 | — | 10-seed rule applied honestly | — | Main |
| Final | Rewrite Introduction + Related Work + Methodology to ≥40% new prose; draft cover letter | Journal manuscript draft | All above | Moderate | iThenticate overlap ≤20%; cover letter lists all new sections | — | Submission |
| Submit | Submit to Computer Networks after conference camera-ready is set | Submission package | Conference decision | — | Conference accepted (or withdrawn) | — | — |

---

## 21. Do-Not-Do List

1. Do **not** submit to **Computers & Security** — verbatim AI/ML/federated-learning moratorium confirmed. Final. No exceptions.
2. Do **not** add FedBN — DATP's AE has no BatchNorm layers; adding BN changes the encoder and breaks the frozen-encoder discipline.
3. Do **not** add more than **one** new IoT dataset. ToN-IoT, IoT-23, Bot-IoT, MedBIoT, UNSW-NB15, TII-SSRC-23, FedAIoT bundle are all out of scope for this cycle.
4. Do **not** add more than **three** stress-test comparator families. Do not add Per-FedAvg, FedPer, APFL, pFedMe, FedAvgM, FedYogi, FedAdam, or Sáez-de-Cámara clustered-FL reimplementation.
5. Do **not** claim DATP "solves" non-IID FL.
6. Do **not** claim improved global Macro-F1 — P10 Macro-F1 degrades and must be reported honestly.
7. Do **not** claim privacy preservation without formal DP/SecAgg implementation.
8. Do **not** claim concept-drift handling — the temporal MVE is one-shot recalibration only; streaming drift handling is future work.
9. Do **not** add adversarial robustness, poisoning, backdoor, or evasion experiments.
10. Do **not** add hardware/edge profiling.
11. Do **not** add a streaming drift-detection framework (FLARE/FLAME-style).
12. Do **not** add Byzantine-robust federated conformal prediction.
13. Do **not** change the mainline AE architecture, FedAvg aggregator, or round budget between conference and journal.
14. Do **not** reuse conference figures verbatim — redraw or substantially extend each.
15. Do **not** silently change the CV(FPR) definition between conference and journal.
16. Do **not** frame the CICIoT2023 file-level null result as a general CICIoT2023 statement — keep it as Regime B-a.
17. Do **not** invoke FedMSE (COSE 2025) as evidence that COSE accepts FL submissions today.
18. Do **not** target FGCS as a primary venue — scope drift risk.
19. Do **not** use a Sankey diagram for B4 cluster interpretability — K=3 clusters / K=9 devices is too small; use a contingency table or small heatmap.
20. Do **not** present hypothetical alert/day numbers as real deployment measurements — declare the traffic-volume source or label as a normalized hypothetical.
21. Do **not** suppress or hide the 10-seed result if it is less favorable than the 5-seed result — the 10-seed result is the main result.
22. Do **not** tune the Laridi-style protocol after seeing results — the protocol is finalized at G1.2 before any computation.
23. Do **not** claim Regime B-b if Priority 0 returns `REJECTED`.
24. Do **not** call the Ditto fallback "Ditto" if it is only a frozen-body local-head variant — rename it explicitly per §8.3.
25. Do **not** present FedProx or Ditto results as part of the core B1–B4 causal ladder — they are external stress-test comparators.
26. Do **not** use the simple pooled variance formula `σ²_global = Σ nₖ·σₖ² / Σ nₖ` for the Laridi-style threshold — it ignores between-client mean shifts that are structurally present under Regime A heterogeneity. Always use the full formula per §8.4.
27. Do **not** use k=2.0 (or any fixed k) as the primary Laridi comparator — the main comparison must use the matched-exceedance operating point; fixed-k values are sensitivity-only (supplementary).

---

## 22. Final Reviewer Attack After Repair

1. **Remaining attackable weaknesses** (all are acceptable and explicitly bounded):
   - K is still modest — fleet-scale validation at K > 100 is deferred
   - One aggregation stress test (FedProx) — not exhaustive
   - One model-personalization stress test (Ditto/named-variant) — not exhaustive
   - Privacy analysis remains qualitative
   - Temporal MVE is a single chronological split — not streaming
   - Laridi adaptation is DATP-compatible but not an exact reproduction of the original non-IoT method (between-client formula and matched operating point are documented adaptations)
   - 10-seed result reported honestly — CIs may be wider than 5-seed

2. **Why each is acceptable**: each is explicitly out-of-scope of "threshold-scope-only controlled study under fixed FedAvg + frozen encoder"; scope discipline is the paper's core contribution; broader extensions are natural follow-up thesis papers.

3. **How to word them honestly**:
   - "Our evaluation comprises K ∈ [9, 15] physical-device clients across benchmarks; fleet-scale validation at K > 100 is reserved for future work."
   - "FedProx and Ditto [or named variant] are external stress-test comparators; we add one representative of each class."
   - "Privacy analysis is qualitative; formal DP or SecAgg integration is future work."
   - "The temporal regime is a one-shot recalibration MVE under a chronological split; streaming drift handling is future work."
   - "We implement a faithful DATP-compatible adaptation of the Laridi-style federated threshold using full pooled variance (including between-client mean shift) and a matched-exceedance operating point; we do not claim it is an exact reproduction of the original method."

4. **Ditto absorption risk**: Whether DATP's gain survives Ditto+B1 (i.e., whether model personalization makes threshold personalization redundant) is the highest residual risk. The pre-specified Ditto absorption interpretation rule (§8.3) handles all outcomes honestly: strong retention, partial absorption, and near-full absorption are all valid findings with pre-specified interpretations. No outcome is suppressed.

5. **Laridi operating-point risk**: A reviewer who is familiar with the Laridi method may ask whether the matched-exceedance adaptation is fair. The matched-exceedance protocol is chosen specifically to give Laridi the benefit of operating at the same target exceedance as B2 at q=0.95, making the comparison maximally fair to Laridi. The between-ratio diagnostic gives reviewers additional context on why the comparison is informative under heterogeneity.

6. **What would satisfy the reviewer**: (a) Appendix A + B2-conf closes tautology critique; (b) Edge-IIoTset provides cross-dataset evidence; (c) matched-exceedance Laridi comparison closes the federated-thresholding novelty question; (d) Ditto stress test with absorption rule answers "why not just personalize the model"; (e) temporal MVE answers threshold-aging concern; (f) alert-burden table grounds CV(FPR) in practitioner terms.

---

## 23. Search and Verification Audit Log

| Query or Source | Source Type | Date Checked | Key Finding | Confirmed / Changed / Contradicted Input Files | Used in Final Recommendation |
|---|---|---|---|---|---|
| DATP.pdf | Project knowledge | 2026-05-23 | CV(FPR) 1.017→0.299, B4 ≈52%, 9 physical devices, 5 seeds, E=1, q=0.95; B4-is-not-privacy framing | Confirmed | Yes |
| State_of_the_Art.md | Project knowledge | 2026-05-23 | 6 gap clusters; non-IID/privacy/adversarial/deployment/dataset/reproducibility | Confirmed | Yes |
| Blueprint.md | Project knowledge | 2026-05-23 | Sole confirmatory claim: Regime A B1-vs-B2 CV(FPR); RQ hierarchy; null-finding contingencies; no BN in encoder | Confirmed | Yes |
| sciencedirect.com/journal/computers-and-security (Aims & Scope) | Official Elsevier page | 2026-05-23 | Verbatim moratorium: "items directed to the security of AI/ML systems themselves (such as LLM and federated learning) are out of scope" | Changed — rules out COSE | Yes — decisive and final |
| sciencedirect.com/journal/computer-networks/publish/guide-for-authors | Official Elsevier page | 2026-05-23 | Verbatim: "Enhanced, extended versions of quality papers presented at conferences or workshops can be submitted" | Confirmed | Yes — anchors primary venue |
| Rey et al. (2022). Computer Networks 204:108693 | Peer-reviewed paper | 2026-05-23 | FL MLP+AE on N-BaIoT; foundational predecessor | Confirmed | Yes |
| Laridi, Palmer & Tam (2024). Sci. Rep. 14:26704 | Peer-reviewed paper | 2026-05-23 | Federated thresholding via summary statistics; closest novelty threat; uses between-client variance in aggregation | Confirmed | Yes — anchors mandatory comparator and full pooled variance requirement |
| Sáez-de-Cámara et al. (2023). Computers & Security 131:103299 | Peer-reviewed paper | 2026-05-23 | Clustered FL; Local-Largest-MSE thresholds; clusters models, not thresholds | Confirms B4 differentiation | Yes |
| Belarbi et al. (2023). GLOBECOM 2023 | Peer-reviewed paper | 2026-05-23 | FedAvg vs FedProx vs FedYogi on TON-IoT | Confirms FedProx as mandatory stress test | Yes |
| Pradhan et al. (2025). Sci. Rep. 10.1038/s41598-025-32567-w | Peer-reviewed paper | 2026-05-23 | Edge-IIoTset: 6 device/application-type clients; CICIoT2023: 10 device-group clients | Confirms partition precedent | Yes |
| Plassier et al. (2023). ICML 2023, PMLR 202:27907 | Conference proceedings | 2026-05-23 | Federated conformal prediction | Confirms B2-conf | Yes |
| Ferrag (2022). Edge-IIoTset. IEEE Access | Peer-reviewed paper | 2026-05-23 | Native FL framing; 10+ device types | Confirms Edge-IIoTset | Yes |
| FGCS Guide for Authors | Official Elsevier page | 2026-05-23 | 40% new contributions requirement | Confirms ≥40% bar | Yes |
| ACM Computing Surveys 2024, DOI 10.1145/3704633 | Peer-reviewed survey | 2026-05-23 | MIA risk is real; defenses include SecAgg, DP, partial sharing | Supports bounded-disclosure framing | Yes |
| Neto et al. (2023). CICIoT2023. Sensors 23(13):5941 | Official dataset paper | 2026-05-23 | 105 devices, 33 attacks; structure permits device-MAC repartition | Confirms repartition feasibility in principle | Yes |

---

## 24. Final Decision Gate

1. **Best target journal**: **Computer Networks (Elsevier)**, ISSN 1389-1286, 2024 JIF 4.6, Q1. Backup: Internet of Things (Elsevier), then Cyber Security and Applications, then JNCA.
2. **Best expansion level**: **Strong (§14.2)**.
3. **Exact must-do list before submission**: (i) Priority 0 metadata check; (ii) Appendix A formal note; (iii) Laridi protocol locked (matched-exceedance, full pooled variance with between-client term); (iv) q-sensitivity + calibration-size sweep + shrinkage + B2-conf; (v) Laridi-style comparator with between-ratio diagnostic; (vi) B4 ablation + contingency table; (vii) JS↔gain regression + alert-burden table + threshold-shift scatter; (viii) 10-seed extension reported honestly; (ix) privacy bounded-disclosure + related work expansion; (x) Edge-IIoTset preprocessing + training; (xi) CICIoT2023 device-MAC repartition if Priority 0 confirmed; (xii) FedProx + Ditto/named-variant stress tests with pre-specified interpretation rules applied; (xiii) temporal MVE with pre-specified outcome interpretation; (xiv) cover letter with explicit extension disclosure.
4. **Exact do-not-do list**: see §21 (27 items). Critical additions: no simple pooled variance for Laridi; no fixed-k as primary Laridi comparison; no Regime B-b without Priority 0 confirmation; no suppression of unfavorable Ditto absorption result.
5. **Should the journal extension wait until conference acceptance?** **Yes.** Begin all experiments now (Priority 0 and Gate 1 can start immediately). Submit to Computer Networks only after conference camera-ready is set.
6. **Confidence ratings**: High — venue exclusion; High — Computer Networks selection; High — dataset choice; High — threshold variants; Medium-High — stress-test comparator grid; Medium — temporal MVE outcome (three pre-specified interpretations cover all outcomes honestly); High — scope control; High — Laridi operating-point fairness (matched-exceedance protocol).
7. **Final verdict**: The DATP conference paper has a real, defensible empirical finding and a scientifically clean experimental discipline. The journal version must do exactly five things: (a) close the construction-tautology critique via Appendix A + B2-conf + calibration-size sweep; (b) prove generalization on Edge-IIoTset and (conditionally) redesigned CICIoT2023; (c) demonstrate via pre-specified stress tests that the threshold-scope gain is not absorbed by heterogeneity-aware aggregation (FedProx) or model-side personalization (Ditto), and is not dominated by a matched-operating-point Laridi-style federated threshold; (d) show threshold aging behavior under a chronological split; and (e) ground CV(FPR) in an operational alert-burden metric. The Computers & Security moratorium is final and cannot be circumvented. The Laridi comparison — with matched exceedance, full pooled variance, and between-ratio diagnostic — is both the dominant novelty risk and its own resolution.

---

## 25. Final Internal Consistency Audit

| Audit Item | Expected Final State | Status | Notes |
|---|---|---|---|
| Primary journal is Computer Networks everywhere | Computer Networks is primary in §1, §12, §14, §15, §18, §24 | ✅ Pass | No conflicting statement found |
| Computers & Security is excluded everywhere | COSE excluded in §1, §12, §19, §21, §24 | ✅ Pass | Moratorium wording consistent |
| Strong extension is selected everywhere | Strong selected in §1, §14, §15, §18, §24 | ✅ Pass | |
| Edge-IIoTset is the only new dataset | Edge-IIoTset sole new dataset in §7, §15, §18, §24 | ✅ Pass | ToN-IoT and others rejected |
| CICIoT2023 device-MAC repartition is conditional on Priority 0 | Priority 0 check stated in §3, §7, §15, §16 (Priority 0 section), §20, §24 | ✅ Pass | Contingency branches documented |
| FedBN is rejected everywhere | FedBN rejected in §4, §8, §15, §21 | ✅ Pass | Reason: no BN in encoder |
| FedProx and Ditto are stress-test comparators, not core causal baselines | Distinction stated in §3, §8.1, §15, §17, §20, §21 | ✅ Pass | Not part of B1–B4 ladder |
| Laridi variance formula includes between-client term | Full pooled variance σ²_global = Σ nₖ · [σₖ² + (µₖ − µ_global)²] / Σ nₖ in §8.4, G1.2, G1.7, G2.5 | ✅ Pass | Simple pooled formula is gone; Do-Not-Do item 26 |
| Laridi operating point is matched to q=0.95 for the main comparison | Matched-exceedance operating point in §8.4, §6, §15, §17; fixed-k variants explicitly sensitivity-only | ✅ Pass | Do-Not-Do item 27 bans k=2.0 as primary |
| Laridi matched-exceedance is implementable without raw scores | Server broadcasts fixed candidate thresholds; clients return benign exceedance counts only; no raw scores or attack labels are shared | ✅ Pass | Candidate grid and tie-break rule are pre-specified |
| Fixed-k Laridi variants are sensitivity-only | Fixed-k variants in §8.4 and §15.2 labeled supplementary sensitivity checks only | ✅ Pass | |
| CICIoT2023 metadata check is Priority 0 (before Gate 1) | Priority 0 section added as §16, before Three-Gate Execution Plan; P0 action in §20 is first | ✅ Pass | Priority 0 precedes G1.1 in §20 |
| Regime B-b requires ≥8 clients with nₖ ≥ 100 benign calibration samples | Explicit threshold in §7, §16 G2.1, G2.4, §20 G2.1, G2.4 | ✅ Pass | DATP's existing nₘᵢₙ=100 used |
| FedProx fallback wording is non-retroactive | G3.1 in §17 and §20 says: "If all pre-specified µ values fail to converge, report convergence failure. Any additional µ search must be explicitly labeled exploratory and cannot be used to support the main stress-test claim." | ✅ Pass | Old phrasing removed |
| Ditto absorption margin is pre-specified | §8.3 contains pre-specified 75%/25% rule; referenced in §19, §22; G3.0 and G3.2 in §17 and §20 | ✅ Pass | Rule locks in before training |
| Laridi between-ratio diagnostic is in main paper (not supplementary) | §8.4 specifies between_ratio must appear in main Laridi comparison section; G1.7 output includes between_ratio in main text | ✅ Pass | |
| Temporal MVE has three pre-specified outcome interpretations | §10.1 defines Outcomes A, B, C; referenced in §17 G3.3, §20 G3.3 | ✅ Pass | |
| 10-seed reporting rule is honest | Seed-extension rule in §13 (point 9) and §20 (G1.12) | ✅ Pass | Explicitly states CI widening requires claim revision |
| Cover-letter percentage is consistently "at least 40% substantive new material" | §13 (points 5 and 6) both use this wording | ✅ Pass | "approximately 50%" removed |
| Sankey diagram is removed | §11 specifies contingency table or small heatmap; §21 item 19 bans Sankey | ✅ Pass | |
| No privacy, poisoning, hardware, or broad personalized-FL scope drift | Confirmed by §15.3, §21 | ✅ Pass | |
| No old Laridi formula remains anywhere | Checked §8.4, §16, §17, §20, §24; all use full pooled variance | ✅ Pass | Silent check 1 passed |
| No section treats k=2.0 as the main Laridi setting | All k references in §8.4 and §15.2 label fixed-k as sensitivity-only; matched-exceedance is main | ✅ Pass | Silent check 2 passed |
| No section delays CICIoT2023 metadata verification until after Gate 1 | Priority 0 section (§16) precedes Three-Gate Execution Plan; P0 is first item in §20 | ✅ Pass | Silent check 3 passed |

---

## Final Cleanup Summary

The following eight targeted fixes were applied to the previous roadmap version. No major strategic decisions were changed.

**Fix 1 — Typo corrected**: "submit th journal version" corrected to "submit the journal version" in §1 Executive Verdict.

**Fix 2 — Laridi variance formula upgraded**: §8.4 Laridi protocol now uses the full pooled variance formula including the between-client mean-shift term: `σ²_global = Σ nₖ · [σₖ² + (µₖ − µ_global)²] / Σ nₖ`. The within_term, between_term, and between_ratio diagnostics are added as mandatory main-paper outputs (not supplementary). A new Do-Not-Do item (item 26) bans the simple pooled formula. All occurrences in §8.4, §17 (G1.7, G2.5), §20, and the internal audit (§25) are updated.

**Fix 3 — Laridi matched operating-point protocol**: §8.4 now specifies that the **primary Laridi comparator** uses a matched-exceedance operating point (calibrating k to achieve ≈5% benign calibration exceedance, matching q=0.95). The implementable federated protocol is fixed-grid count exchange: the server broadcasts `τ(k) = µ_global + k·σ_global` for pre-specified `k ∈ {0.00, 0.01, ..., 5.00}`, clients return benign exceedance counts only, and the server selects k* with a conservative larger-k tie-break. No raw scores or attack labels are shared. Fixed-k variants (k∈{2.0, 2.5, 3.0}) are demoted to supplementary sensitivity checks. Safe comparison wording added. Do-Not-Do item 27 added. §6 Reviewer-Loophole Closure Table and §24 updated.

**Fix 4 — CICIoT2023 metadata verification moved to Priority 0**: A new **Priority 0** section (§16, before the Three-Gate Execution Plan) was added. It defines three explicit outcome declarations (`CONFIRMED`, `REPROCESS REQUIRED`, `REJECTED`), requires output file `ciciot2023_metadata_feasibility.md`, and explicitly gates all Regime B-b tasks on this outcome. §20 implementation plan updated so P0 is the first action. §15 Execution Priority Table updated to list Priority 0 first. All downstream Gate 2 tasks now depend on Priority 0.

**Fix 5 — CICIoT2023 benign-volume threshold made explicit**: All occurrences of "≥8 clients with sufficient benign volume" updated to "≥8 clients, each with nₖ ≥ 100 benign calibration samples" in §7, §16 Gates, §20, and §25. The explicit fallback rule is added: "If fewer than 8 clients satisfy nₖ ≥ 100, Regime B-b is not used as a main-paper regime."

**Fix 6 — FedProx fallback wording fixed**: All occurrences of "do not tune µ until convergence is achieved retroactively" replaced with: "If all pre-specified µ values fail to converge, report convergence failure. Any additional µ search must be explicitly labeled exploratory and cannot be used to support the main stress-test claim." Applied in §17 (G3.1) and §20 (G3.1).

**Fix 7 — Ditto absorption margin pre-specified**: §8.3 now includes a named subsection "Ditto Stress-Test Interpretation Rule" with pre-specified 75%/25% absorption margins (Δ_Ditto ≥ 0.75·Δ_FedAvg = strongly useful; 0.25–0.75 = partial absorption; <0.25 = largely absorbed — claim must be narrowed). Safe wording added. §19 Claim Consistency updated for Ditto row. §22 Final Reviewer Attack updated. §20 G3.0 and G3.2 updated to reference the rule. §25 audit row added.

**Fix 8 — Internal consistency audit strengthened**: §25 expanded with rows covering: Laridi variance includes between-client term; Laridi operating point matched to q=0.95 for main comparison; Laridi matched-exceedance is implementable without raw scores; fixed-k Laridi variants are sensitivity-only; CICIoT2023 metadata check is Priority 0; Regime B-b requires ≥8 clients with nₖ ≥ 100; FedProx fallback wording is non-retroactive; Ditto absorption margin is pre-specified; Laridi between-ratio diagnostic is in main paper. All added rows now show ✅ Pass. Three silent checks confirm: no old Laridi formula remains, no section uses k=2.0 as primary, and no section delays CICIoT2023 metadata verification until after Gate 1.

**Final Micro-Fix Summary**: The Laridi-style matched-exceedance protocol is now technically implementable without raw score sharing. §8.4 specifies a fixed server-broadcast candidate threshold grid, client-side benign exceedance counts, server-side selection of k* against the 5% exceedance target, and the larger-k tie-break. G1.7, G2.5, §20, and §25 now consistently state that no raw scores or attack labels are shared, the candidate grid is fixed before result inspection, fixed-k values remain sensitivity-only, and the main comparison is the matched-exceedance k* result.
