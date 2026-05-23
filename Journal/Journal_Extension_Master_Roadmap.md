# Journal Extension Master Roadmap for DATP

---

## 1. Executive Verdict

1. **Best target journal**: **Computer Networks (Elsevier)**, with **Internet of Things (Elsevier)** as principled backup. **Computers & Security is excluded** — its official Aims & Scope page (sciencedirect.com/journal/computers-and-security) carries a verbatim moratorium since early 2024: *"items directed to the security of AI/ML systems themselves (such as LLM and federated learning) are out of scope of the journal and should be submitted to a venue primarily about AI/ML."* This exclusion is final and appears consistently in every section of this roadmap.
2. **Best expansion level**: **Strong** — between Minimal (insufficient against a Q1 reviewer) and Ambitious (destroys DATP identity).
3. **Wait for conference acceptance before journal submission?** **Yes** — begin experiments now; submit th
 journal version only after the conference camera-ready is set, so the conference paper is a citable anchor and the extension narrative is unambiguous under Elsevier's redundancy/originality rules.
4. **One-sentence final strategy**: Keep DATP a *threshold-scope-only, fixed-encoder, FPR-equity* paper; extend it on exactly one new device-partitioned dataset (Edge-IIoTset), three stress-test comparator families that close the "B2-by-construction" and "model-personalization-makes-it-obsolete" attack axes, four threshold variants that deepen the calibration story, one chronological-split temporal recalibration experiment, and six mechanism analyses.
5. **One-sentence biggest-risk warning**: The dominant existential risk is *novelty collapse against Laridi et al. (Sci. Rep. 2024)* — DATP must explicitly cite, contrast, and quantitatively compare against a pre-specified Laridi-style summary-statistics federated threshold; otherwise a knowledgeable reviewer will dismiss the contribution as already covered.

---

## 2. Input Corpus Inventory

| File | Role | Used? | Main Contribution | Reliability | Notes |
|---|---|---|---|---|---|
| DATP.pdf | Current paper | Yes | Threshold-scope-only controlled study; CV(FPR) 1.017→0.299 on N-BaIoT; B4 ≈52% recovery; CICIoT2023 null under file-level pseudo-clients | Primary anchor | Verified directly via project knowledge |
| State_of_the_Art.md | Literature context | Yes | 40-study corpus with 6 gap clusters; thesis-scoped gap ledger | Primary anchor | Used as context, not as unquestionable truth |
| Blueprint.md | Methodology lock | Yes | Locks RQ hierarchy, claim discipline, statistical tests, null-finding contingencies | Primary anchor | Confirms sole confirmatory scope is RQ2 / Regime A / B1-vs-B2 |
| Audit A | Strategy note | Partial | Recommends Cyber Security and Applications + Edge-IIoTset; correctly rules out COSE | Mixed | CSA is a viable backup; correct on COSE exclusion |
| Audit B | Strategy note | Partial | Recommends Computers & Security + ToN-IoT; misses COSE moratorium | Partially wrong | COSE rec invalid; ToN-IoT is rejected for this cycle |
| Audit C | Detailed analysis | Yes | Strongest baseline+threshold-variant analysis; correctly cites COSE moratorium verbatim; recommends Internet of Things | Highly reliable | Most rigorous; some 2026 arXiv preprints noted as speculative |
| Audit D | Detailed analysis | Yes | Best novelty-threat analysis (Laridi 2024, Sáez-de-Cámara 2023); recommends Computer Networks (Rey 2022 lineage); flags 30%-rule as ICPR-specific | Highly reliable | Most accurate on policies and lineage |
| Audit E | Strategy note | Partial | Recommends JNCA + FedBN/temporal; misses COSE moratorium | Mixed | JNCA backup defensible; FedBN rejected — DATP encoder has no BatchNorm |
| Audits F, G | Strategy notes | Rejected for venue | Recommend Computers & Security; miss moratorium | Wrong on venue | COSE rec invalid throughout |

**Input limitation — Laridi 2024 quantitative gap**: No audit independently verified the Laridi method's performance on N-BaIoT score distributions specifically. The DATP-compatible adaptation must be pre-specified before results are inspected (see §8).

**Input limitation — DATP encoder architecture**: Confirmed via Blueprint.md / Algorithm 1 that the current AE has no BatchNorm layers. FedBN requires BN; adding BN changes the encoder and breaks the frozen-encoder discipline. FedBN is rejected everywhere in this roadmap.

---

## 3. Consolidated Understanding of Current DATP Identity

1. **Paper identity**: *Device-Aware Threshold Personalization: A Controlled Threshold-Calibration Study for Non-IID Federated IoT Anomaly Detection* — a fixed-encoder, fixed-FedAvg, **threshold-scope-only** controlled comparison.
2. **Sole confirmatory experimental variable**: threshold calibration scope (B1 shared / B2 per-client / B3 family-mean / B4 cluster-mean), with the AE, optimizer, rounds, seeds, and per-client score artifacts held identical. FedProx and Ditto are *external stress-test comparators*, not part of this causal ladder.
3. **Datasets**: N-BaIoT (9 physical-device clients, Mirai/BASHLITE); CICIoT2023 (63 file-defined pseudo-clients, JS mean 0.004); N-BaIoT Dirichlet repartition (α∈{0.1, 0.3, 0.5, 1.0, 10.0, IID}, K=20 synthetic clients).
4. **Regimes**: Regime A (N-BaIoT confirmatory); Regime B-a (CICIoT2023 file-level, near-homogeneous boundary); Regime B-b (CICIoT2023 device-MAC — *conditional on metadata verification, see §16*); Regime C (Dirichlet severity sweep).
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
| CICIoT2023 file-level partition is weak | 6/6 | None | Redesign by device-MAC *if metadata feasibility verified* | TO VERIFY — see §16 contingency |
| Need stronger FL training stress test | 6/6 | FedProx (5) vs FedAvgM (3) vs FedYogi (1) | **FedProx** | Highest reviewer-defensibility; Belarbi et al. 2023 precedent; Flower-native; framed as external stress test, not core causal |
| Need model-personalization comparator | 5/6 | FedBN (3) vs Ditto (2) vs Per-FedAvg (1) | **Ditto (or named variant)** | FedBN rejected (no BN in encoder); Ditto is encoder-agnostic; framed as external stress test |
| Privacy framing | 6/6: do not overclaim | Whether to add MIA probe | **Qualitative only** — bounded-disclosure table; no empirical MIA | MIA on percentile summaries lacks established IoT literature |
| Temporal experiment | 6/6: need one | MVE (3) vs full drift (2) vs none (1) | **MVE chronological split + one-shot recalibration** with three pre-specified outcome interpretations | Strongest realistic addition; three outcomes pre-specified to prevent post-hoc narrative adjustment |
| Target journal | Split | COSE (3) / Computer Networks (1) / IoT-Elsevier (1) / CSA (1) / JNCA (1) | **Computer Networks** primary; **IoT (Elsevier)** backup | COSE moratorium verbatim-confirmed; Computer Networks has explicit extension policy + Rey 2022 lineage |
| Conference-extension novelty threshold | 5/6 cite ≥30% or ≥40% | No Elsevier-wide policy exists | **≥40% substantive new material** | Conservative; aligns with FGCS explicit 40% rule; avoids unsupported percentages |
| Wait for conference acceptance | 6/6 | None | **Yes** | Protects against duplicate-publication concerns |
| Conformal thresholding | Split (3 add / 3 reject) | Resolved | **Split-conformal B2-conf** | Closes construction-tautology critique with finite-sample coverage guarantee |
| Adversarial robustness | 5/6 out of scope | Audit C suggests light experiment | **Out of scope; discussion only** | Adversarial branch is scope drift into a separate thesis paper |
| FedBN vs Ditto | Resolved by encoder constraint | — | **Ditto (or named variant)** | FedBN rejected; Ditto encoder-agnostic |
| FedProx/Ditto role in DATP story | Resolved in this update | Audits did not distinguish causal from stress-test | **External stress-test comparators only** | Not part of the B1–B4 causal ladder |

---

## 5. Consolidated Weak-Point Register

| Weak Point | Severity | Why Reviewer Cares | Evidence | Fix Type | Effort | Scope Drift Risk |
|---|---|---|---|---|---|---|
| W01: "B2 equalizes FPR by construction" tautology | **Critical** | Reviewer can dismiss headline as definitional | DATP §IV–V concedes construction equality | Mandatory | Moderate | Low |
| W02: 9 physical clients only in confirmatory regime | **Critical** | External validity ceiling; N-BaIoT is aging | DATP scope statement | Mandatory | Moderate | Low |
| W03: CICIoT2023 at file-level only; physical heterogeneity discarded | **Major** | Pradhan et al. (Sci. Rep. 2025) already partitioned CICIoT2023 by device-group | DATP §V-B | Mandatory (conditional on metadata) | Moderate | Low |
| W04: No comparison to Laridi 2024 federated thresholding SOTA | **Critical** | Closest direct competitor; novelty contested if omitted | DATP related work omits Laridi | Mandatory | Moderate | Low |
| W05: No model-personalization comparator | **Major** | "Would Ditto make B2 redundant?" | DATP §II discusses but does not test | Mandatory | Heavy | Medium |
| W06: No stronger FL aggregation stress test | **Major** | Recent FL-IDS (Belarbi 2023, FedMSE 2025) compare FedProx/FedAvgM | DATP uses FedAvg only | Mandatory | Moderate | Low |
| W07: No temporal drift / recalibration | **Major** | Operational reality | DATP explicit deferral | Mandatory | Moderate | Medium |
| W08: B4 metadata leakage not quantified | Moderate | Reviewers may push for DP/SecAgg | DATP §VII concedes risk | Recommended | Low | Low |
| W09: Five seeds only | Moderate | Statistical power | DATP §VII | Recommended | Immediate (10 seeds) | None |
| W10: No calibration-size sensitivity beyond fixed nₘᵢₙ=100 | Moderate | Operational realism for low-data clients | DATP §IV nₘᵢₙ note | Recommended | Immediate | None |
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
| "DATP is too narrow for a journal" | Edge-IIoTset + FedProx/Ditto stress tests + temporal MVE + six mechanism analyses + conformal variant + expanded related work | Editor may still see it as a narrow calibration paper | Frame as "a fairness-oriented threshold-calibration study under non-IID FL" — neither claim breadth nor apologize for scope |
| "Dataset coverage is limited" | Edge-IIoTset (device-type partition) + CICIoT2023 device-MAC repartition (conditional on metadata) | New dataset is one testbed; MAC repartition may be infeasible | "Two physically-partitioned IoT benchmarks (N-BaIoT, Edge-IIoTset); CICIoT2023 is included as a device-grouped evaluation if metadata permits, or retained as a near-homogeneous boundary otherwise." |
| "N-BaIoT has only 9 devices" | Edge-IIoTset gives K∈{6,15}; CICIoT2023 device-MAC gives K≈10 if feasible | Combined K still modest | "We do not validate at fleet scale (K > 100); per-device calibration scaling is future work." |
| "CICIoT2023 clients are pseudo-clients" | Repartition by device-MAC per Pradhan et al. (Sci. Rep. 2025) if metadata is verifiably available; retain file-level as Regime B-a regardless | MAC repartition conditional on metadata | "Regime B-a (file-level) is a near-homogeneous applicability boundary; Regime B-b (device-MAC) is the heterogeneous evaluation where metadata permits." |
| "Missing model-personalization baselines" | Ditto (or explicitly named local-head variant) as one comparator, framed as a stress test | One method, not exhaustive | "We compare against one representative model-personalization stress-test (Ditto/local-head comparator); exhaustive comparison is out of scope." |
| "Missing aggregation baselines" | FedProx as a heterogeneity-aware aggregation stress test | One aggregation method | "We add the most-cited heterogeneity-aware aggregation stress test (FedProx); further aggregation sensitivity is future work." |
| "Missing federated thresholding SOTA comparison" | Laridi-style summary-statistics federated threshold on stored score artifacts, with pre-specified protocol (see §8) | Adaptation to non-IoT method | "We implement a faithful DATP-compatible adaptation of the Laridi-style federated threshold, with all adaptation choices reported before result inspection." |
| "Missing temporal drift" | Chronological split on Edge-IIoTset + one-shot recalibration MVE with three pre-specified outcome interpretations | Single split, not streaming | "Under a chronological train/test split, per-client thresholds are evaluated with and without one-shot recalibration; three pre-specified outcomes guide interpretation." |
| "Missing privacy/leakage discussion" | Bounded-disclosure table + qualitative MIA-risk analysis + cite SecAgg/DP literature | No empirical leakage quantification | "B4 fingerprints constitute distributional metadata; we provide a bounded-disclosure analysis and discuss SecAgg/DP mitigations as future work." |
| "Missing deployment-cost discussion" | Bytes-per-round table comparing B1/B2/B4 communication and per-client storage, estimated from message sizes | No hardware measurement | "Per-round communication and per-client storage overhead are estimated from message sizes; hardware-level profiling is future work." |
| "Journal version insufficiently different from conference" | ≥40% substantive new material with explicit cover-letter enumeration | Editor judgment | Cover letter lists each new section by number; introduction cites the conference paper as prior work |
| "Scope drift from adding too much" | Hard limits enforced: 1 new dataset, 1 conditional partition redesign, 3 stress-test comparators, 4 threshold variants, 1 temporal family, 6 mechanism analyses | Some reviewers always want more | "We hold the encoder, AE architecture, and mainline FedAvg training fixed; all extensions are threshold-scope or evaluation-side." |

---

## 7. Dataset Expansion Decision

| Dataset | Add / Maybe / Reject | Why | DATP Fit | Partition Quality | Calibration Suitability | Temporal Potential | Effort | Risk |
|---|---|---|---|---|---|---|---|---|
| N-BaIoT | **Keep (existing)** | Real 9-device physical partition; Rey 2022 lineage | Excellent | Native device IDs | Excellent | Moderate (chronological traces with gaps) | None new | Aging (2018); narrow attack families |
| CICIoT2023 | **Redesign partition (conditional — TO VERIFY)** | Device-MAC repartition per Pradhan et al. 2025 precedent; file-level is its own weakness | Strong after repartition; file-level retained as Regime B-a regardless | Device-MAC mapping: **feasibility depends on whether MAC/device-group metadata is retained in the current preprocessing pipeline** | Good if repartitioned | Moderate (capture timestamps) | Moderate (MAC mapping) | If metadata is not verifiably available, retain Regime B-a only |
| **Edge-IIoTset (Ferrag 2022)** | **ADD — primary new dataset** | Native FL framing; 10+ device types; Pradhan et al. 2025 used 6-client device/application-type partition | Excellent | Native device-type partition | Good | Multi-day capture window enables chronological split | Moderate-Heavy (feature alignment) | Schema differs from N-BaIoT; feature extraction required |
| ToN-IoT | **Reject** | Multi-modal complicates threshold-scope-only design; doubles preprocessing; IP-based partition less clean | Medium | Possible via host/IP | Moderate | Good | Heavy | Rejected for this cycle; cite only |
| Bot-IoT, IoT-23, MedBIoT, FedAIoT bundle | **Reject** | Scope drift; insufficient DATP fit or preprocessing burden | Weak | Weak | Varies | Varies | Heavy | Cite as landscape references only |
| UNSW-NB15 | **Reject** | Not IoT-specific | Very low | None | Weak | Weak | — | Out of scope |

**TO VERIFY — CICIoT2023 device-MAC metadata**: Before any repartition work begins (Gate 2, see §16), verify whether the current CICIoT2023 preprocessing pipeline retains MAC address or device-group labels. **Contingency**: if metadata is not available in the stored pipeline, (a) reprocess from raw CICIoT2023 source if upstream availability is confirmed, or (b) retain Regime B-a (file-level) as the only CICIoT2023 regime and explicitly document this choice. Do not claim device-MAC validation if the metadata cannot be verified.

**Final dataset additions (within hard limit of 2 new datasets)**:
1. **Edge-IIoTset** with native device/application-type partition (1 new dataset)
2. **CICIoT2023 device-MAC repartition** (same dataset, new regime, conditional on metadata verification — counts as 0 new datasets)

---

## 8. Baseline Expansion Decision

### 8.1 Framing Rule: Stress-Test Comparators vs Core Causal Ladder

**This distinction is mandatory throughout the roadmap and the eventual journal paper:**

- **Core DATP causal ladder (B1–B4)**: threshold scope is the only changing variable; AE encoder, training protocol, aggregator, and score artifacts are identical across B1, B2, B3, and B4. Results from this ladder support the confirmatory claim.
- **External stress-test comparators (FedProx, Ditto, Laridi-style)**: change the training protocol or threshold-generation mechanism to examine whether the B1→B2 gain survives under different conditions. These results are *framed as robustness checks*, not as part of the core causal isolation. No stress-test result should be presented as if it were within the same experimental control as the B1–B4 ladder.

### 8.2 Baseline Table

| Baseline Family | Add / Optional / Reject | Scientific Question (framed as stress test) | Minimal Implementation | Reviewer Value | Scope Drift Risk | Placement |
|---|---|---|---|---|---|---|
| **FedProx** | **ADD (stress-test)** | Does the B1→B2 CV(FPR) gain survive when a heterogeneity-aware aggregation optimizer is used instead of FedAvg? | Replace FedAvg aggregator with FedProx (µ ∈ {0.001, 0.01, 0.1}); apply B1–B4 threshold grid to resulting score artifacts | High | Low | Main stress-test table |
| FedBN | **Reject** | — | Would require adding BatchNorm to encoder — breaks frozen-encoder discipline | — | High | Rejected everywhere |
| FedAvgM / FedYogi | Optional (future work) | — | — | Low–Medium | Medium | Not in this cycle |
| **Ditto (or named variant — see §8.3)** | **ADD (stress-test)** | Does the B1→B2 CV(FPR) gain survive when model-side personalization is also applied? | See §8.3 for mandatory implementation choice | High | Low (body remains shared) | Main stress-test table |
| FedPer / APFL / Per-FedAvg | **Reject** | — | — | Diminishing | Medium | Rejected |
| Clustered FL (Sáez-de-Cámara 2023) | Optional | Qualitative contrast only | Full reimplementation heavy; cite and contrast in related work | Medium | Medium | Related work section; no quantitative reimplementation |
| **Laridi-style federated summary-statistics threshold** | **ADD (threshold comparator)** | Does device-aware per-client thresholding (B2) provide stronger FPR-equity than the federated summary-statistics threshold under heterogeneous regimes? | See §8.4 for mandatory pre-specified protocol | Critical (closes biggest novelty threat) | Low (operates on existing score artifacts) | Main comparator table |
| Local-only bounding case | Optional supplementary | — | — | Low–Medium | Low | Supplementary |
| Centralized reference (B0) | **Keep** | — | Already present | — | None | Main |

**Final stress-test comparators (within hard limit of 3 families)**:
1. **FedProx** (aggregation-side heterogeneity stress test)
2. **Ditto or named variant** (model-side personalization stress test)
3. **Laridi-style federated summary-statistics threshold** (federated-thresholding SOTA comparator)

### 8.3 Ditto Implementation Choice (mandatory — choose one before implementation begins)

**Preferred option — Standard Ditto-style personalization**:
- Each client maintains a personalized local model (full AE, identical architecture to the FedAvg AE).
- The personalized model is trained with a proximal regularization term toward the current global model: `loss_local = loss_recon + (µ/2) · ||w_local − w_global||²`.
- Thresholds B1–B4 are evaluated over the personalized model's benign reconstruction-error score artifacts.
- Report explicitly as "Ditto-style model-side personalization stress test" with the proximal weight µ ∈ {0.001, 0.01, 0.1}.

**Acceptable fallback — Local-head personalization comparator** (use this label if standard Ditto is too heavy):
- Freeze the FedAvg-trained shared encoder; train a lightweight local reconstruction head per client.
- Apply B1–B4 over local-head score artifacts.
- **Do not call this "Ditto."** Label it "local-head personalization comparator" and state explicitly: *"This is a simplified model-personalization stress test using a frozen shared encoder with a local reconstruction head; it is not a full Ditto reproduction."*

**Decision gate**: the chosen option must be documented in the implementation plan (§19) before any training runs. The choice cannot be made after inspecting results.

### 8.4 Laridi-Style Baseline Pre-Specification (mandatory — finalize before implementation)

The following protocol must be locked before any Laridi-style results are computed. **Do not tune any element of this protocol after seeing whether it helps or hurts DATP.**

| Protocol element | Specification |
|---|---|
| What each client sends | Local benign-only statistics: count (nₖ), mean (µₖ), variance (σₖ²) of reconstruction errors. No attack labels used in calibration. |
| Aggregation at server | Sample-count-weighted pooling: µ_global = Σ nₖ·µₖ / Σ nₖ; σ²_global = Σ nₖ·σₖ² / Σ nₖ (pooled variance, ignoring between-group term for simplicity; document this choice). |
| Global threshold computation | τ_global = µ_global + k·σ_global where k ∈ {2.0, 2.5, 3.0}; the value of k is pre-specified per dataset and fixed before result inspection. Default: k=2.0 for all regimes; if a different k is chosen, it must be documented before training. |
| Threshold type | Single global scalar applied uniformly to all clients (functionally analogous to B1 in scope, but derived from summary statistics rather than arithmetic mean of local percentiles). |
| When applied | Once per seed, per dataset/regime, using the same benign calibration split as B1 and B2. |
| What makes it a fair comparison | Same benign calibration data; same score artifacts; no information not available to B1 is used. |
| Overlap-region search | If the original Laridi method requires attack-labeled calibration data for the overlap-region threshold search, this adaptation must use only benign calibration data and document the divergence from the original method explicitly. |
| Disclosure wording | *"We implement a faithful DATP-compatible adaptation of the Laridi-style federated summary-statistics threshold (Laridi et al. 2024, Sci. Rep.), with the following adaptation choices: [list above]. We distinguish this adaptation from the original method, which was evaluated on non-IoT tabular datasets with different task structure."* |

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
| Full conformal anomaly detection | Distribution-free with Byzantine-robust extensions | **Reject** | Scope drift to a different paper | High | Future work |

**Final threshold variants (within hard limit of 4 new variants)**:
1. q-sensitivity sweep
2. Local-global shrinkage τₖ(λ)
3. Calibration-size-aware fallback (size-dependent shrinkage)
4. Split-conformal B2 (B2-conf)

---

## 10. Temporal and Recalibration Decision

1. **Can current datasets support true temporal analysis?** Partially. N-BaIoT has chronological traces with gaps but limited drift magnitude. Edge-IIoTset has a multi-day capture window and is the preferred temporal substrate. CICIoT2023 Regime B-a (file-level) discards within-file time and is unusable for temporal analysis; Regime B-b (device-MAC) preserves capture timestamps and could support a secondary temporal check if metadata is confirmed.
2. **Minimum viable temporal experiment (MVE)**: chronological 70/30 split on **Edge-IIoTset** (preferred; cleaner device structure than CICIoT2023). Train AE + calibrate thresholds B1/B2/B4 on the first 70% of each client's benign data by capture timestamp. Evaluate on the last 30% with: (a) frozen thresholds and (b) one-shot recalibration at the temporal boundary. The temporal regime must not begin until Edge-IIoTset preprocessing is stable (Gate 2 exit criteria satisfied).
3. **Rejected (scope drift)**: streaming sliding-window recalibration; cross-dataset transfer; Page-Hinkley drift detection framework; FLARE/FLAME-style autonomous concept-drift mitigation; Byzantine-robust federated conformal prediction.
4. **Metrics**: per-time-window CV(FPR), mean FPR drift, per-client FPR slope vs. time, Macro-F1 stability, one-shot recalibration recovery ratio (Z% = recovered CV(FPR) gain / original gain).

### 10.1 Pre-Specified Temporal MVE Outcome Interpretations

All three outcomes must be interpreted as defined below, regardless of which is observed. Outcome interpretation must not be adjusted after results are inspected.

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
| **JS divergence ↔ DATP-benefit correlation** | **ADD** | Heterogeneity severity predicts DATP value; provides "when to apply" rule | Causality | Per-client benign distributions + CV(FPR) deltas | Scatter + table | High |
| **Threshold shift vs ΔFPR/ΔTPR scatter** | **ADD** | Quantifies fairness-vs-sensitivity trade-off surface | Solves the trade-off | Per-client thresholds + scores | Scatter | High |
| **Calibration-size sensitivity sweep** (nₖ ∈ {50, 100, 250, 500, 1k, 5k}) | **ADD** | When DATP remains usable under low calibration data | Online cold-start | Subsampled benign scores | Figure | High |
| **Operational false-alarm burden** | **ADD (with declared traffic-volume source — see §11.1)** | Translates CV(FPR) into alerts/device/day under a declared traffic assumption | Hardware deployment or absolute fleet-level measurement | Per-client FPR × declared traffic volume | Table | High |
| **B4 cluster-feature ablation + interpretability** | **ADD** | Defends B4 as meaningful taxonomy-free approximation; shows which statistics drive cluster assignments | Privacy safety of B4 | Re-run B4 with feature subsets (mean / std / skew / p95 alone, then all four) | Compact table + **cluster-to-device-type contingency table or small heatmap** (K=3 clusters × device groups; Sankey diagram is not appropriate at K=3/K=9 scale) | High |
| Bootstrap CIs + effect sizes for all key metrics | Optional | Statistical rigor | New phenomena | Stored seed-level metrics | Updated tables (supplementary) | Medium |
| Worst-client balanced accuracy extended deep dive | Optional | Worst-case behavior beyond Ennio Doorbell | Average behavior | Existing | Table | Medium |
| Seed-level stability metrics (Cliff's δ, Wilcoxon) | Optional | Stronger statistical evidence | Causality | Stored results | Supplementary table | Medium |
| Sáez-de-Cámara model-parameter clustering vs B4 score-stat clustering | Optional / qualitative only | Differentiates clustering basis | DATP superiority | Full reimplementation is out of scope; qualitative contrast in related work | Related work table | Medium |
| Conformal coverage check (marginal coverage = 1−α) | Integrated with B2-conf | Verifies conformal guarantee | — | B2-conf new runs | Figure | High (integrated) |
| MIA-style empirical leakage probe | **Reject** | — | Formal privacy | Would require MIA infrastructure not established in IoT-threshold literature | — | Reject |

### 11.1 Alert-Burden Traffic-Volume Specification (mandatory)

The operational alert-burden table must declare its traffic-volume assumption using one of the following acceptable sources. The chosen source must be stated in the paper:
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
| **1** | **Computer Networks** (ISSN 1389-1286, 2024 JIF 4.6, Q1) | **Strongest** — Rey et al. 2022 (CN 204:108693) is the foundational FL-IoT-malware paper on N-BaIoT; identical dataset lineage | **Verbatim** Guide for Authors: *"Enhanced, extended versions of quality papers presented at conferences or workshops can be submitted to our journal for review"* | Low if extension is substantial and conference is cited | Strong package as specified in §15 | Low–Medium | **PRIMARY TARGET** |
| 2 | **Internet of Things (Elsevier)** (ISSN 2542-6605, 2024 JIF ~7.6, Q1) | Strong — IoT scope covers security and ML applications in IoT | Standard Elsevier originality language; no journal-specific conference-extension wording verified | Medium — editor may want stronger IoT-systems narrative | Same package + heavier IoT-deployment framing in introduction | Medium | **STRONG BACKUP** |
| 3 | **Cyber Security and Applications** (Elsevier OA) | Good — explicit cybersecurity + AI+IoT scope; Olanrewaju-George 2025 (DATP ref [7]) published here | TO VERIFY at submission time; one audit cites explicit conference-extension wording | Medium | Same package | Medium | Viable backup if CN/IoT both fail; OA cost consideration |
| 4 | **JNCA** (2024 JIF ~8.0, Q1) | Strong — networked applications + security | Standard Elsevier originality language | Low–Medium | Same package; emphasize networked-application framing | Medium | Acceptable third-tier backup |
| 5 | **FGCS** (2024 JIF ~6.1, Q1) | Moderate — distributed systems; security allowed but not central | Verbatim: 40% new contributions, different title, cite original, list new sections | Medium-High — wants distributed-systems breadth | Significant systems-framing rework | Medium-High | Not recommended — scope drift risk |
| **Excluded** | **Computers & Security (COSE)** | Topically appealing in principle | **Verbatim moratorium** (sciencedirect.com/journal/computers-and-security): *"As of early 2024, we have instituted a moratorium on consideration of submissions that feature AI or ML as significant components… items directed to the security of AI/ML systems themselves (such as LLM and federated learning) are out of scope."* FedMSE (2025) and earlier COSE FL-IDS papers predated the moratorium or slipped through; they are not a safe precedent for new submissions today. | **Certain desk-reject** | — | **VERY HIGH** | **DO NOT SUBMIT. Final. Appears in every section consistently.** |

All other journals (Ad Hoc Networks, Computer Standards & Interfaces, EAAI, IEEE TIFS, IEEE TDSC) are not considered in this cycle — either scope mismatch or insufficient improvement over the four ranked options above.

---

## 13. Conference-to-Journal Originality Plan

1. **Conference paper contributes**: controlled threshold-scope study (B1–B4) under fixed FedAvg AE on N-BaIoT (confirmatory), CICIoT2023 file-level (applicability boundary), N-BaIoT Dirichlet sweep; CV(FPR) 1.017→0.299; B4 ≈52% recovery; bootstrap CI on per-seed deltas.
2. **Journal paper must add** (target ≥40% substantive new material): Edge-IIoTset device-partition regime; CICIoT2023 device-MAC repartition (conditional); 3 stress-test comparator families × B1–B4 threshold grid; 4 new threshold variants; chronological-split + one-shot recalibration regime; 6 deeper analyses; Appendix A; expanded related work covering Laridi 2024, Sáez-de-Cámara 2023, FedMSE 2025, Olanrewaju-George 2025, Belarbi 2023, Plassier ICML 2023, Pradhan et al. 2025.
3. **What can be reused**: DATP nomenclature and B1–B4 taxonomy verbatim; Regime A N-BaIoT confirmatory result (extended to 10 seeds); Regime C Dirichlet sweep; B0 centralized reference; theoretical definitions and notation; reproducibility artifact structure.
4. **What must be new**: every figure either redrawn with additional series or replaced; every table extended; every section that is above 50% reused prose must be rewritten substantially; all new sections are entirely new.
5. **Novelty threshold**: aim for **at least 40% substantive new material**. No single Elsevier-wide policy prescribes an exact percentage (the 30% figure is ICPR/PRL-specific; FGCS explicitly states 40%). 40% is the safe conservative bar. Do not claim an exact percentage in the cover letter; instead, list the new material concretely.
6. **Cover letter disclosure template** (6–8 sentences):
   *"This manuscript is an extended version of our conference paper '[title]' (Reference [X]). The conference version established the DATP framework with the four-policy threshold-scope comparison on N-BaIoT and reported CV(FPR) reduction from 1.017 to 0.299 under per-client thresholding. The present journal manuscript contains at least 40% substantive new material, including: (i) a new device-partitioned Edge-IIoTset benchmark and, if metadata permits, a device-MAC repartition of CICIoT2023; (ii) four new threshold variants — q-sensitivity sweep, local-global shrinkage, calibration-size-aware fallback, and split-conformal B2; (iii) three stress-test comparator families (FedProx, a Ditto-style model-personalization comparator, and a pre-specified Laridi-style federated summary-statistics threshold) evaluated under the identical threshold grid; (iv) a formal Appendix A delineating where B2's construction-implied FPR equality holds and breaks down; (v) a temporal chronological-split and one-shot recalibration regime with pre-specified outcome interpretations; and (vi) six mechanism analyses. No figures or text passages are reused verbatim. The manuscript is not under consideration elsewhere."*
7. **Self-plagiarism risks**: keep iThenticate verbatim overlap below ~15–20%; redraw or substantially extend every figure; rewrite introduction, related work, and methodology sections.
8. **Duplicate-publication risks**: avoid simultaneous submission; wait for conference camera-ready before journal submission; cite conference paper as [X] in the introduction.
9. **Seed extension honesty rule**: If the 10-seed extension results in a wider CI or a CI that approaches zero, the 10-seed result is the main result and the 5-seed conference result is explicitly labeled as preliminary. The 5-seed result is not retained as the main result if the 10-seed result is less favorable. If the 10-seed CI includes zero, the claim must be revised accordingly — do not suppress the 10-seed result.

---

## 14. Three-Level Expansion Roadmap

### 14.1 Minimal Extension

| Component | Required Action | Reviewer Value | Effort | Risk |
|---|---|---|---|---|
| Datasets | Keep N-BaIoT; redesign CICIoT2023 by device-MAC (if metadata available) | Medium | Moderate | High — single physical-device benchmark is fragile vs Q1 reviewer |
| Baselines | FedProx stress test only | Medium | Moderate | High — no model-personalization and no federated-thresholding comparison |
| Threshold variants | q-sensitivity + shrinkage | Medium | Immediate | Medium |
| Temporal | None | None | None | High — drift question unaddressed |
| Deeper analyses | Client-CDF overlays + failure-mode taxonomy + operational burden | Medium | Immediate | Medium |
| **Net risk** | — | — | — | **High desk-reject risk at Computer Networks** |

### 14.2 Strong Extension (RECOMMENDED)

| Component | Required Action | Reviewer Value | Effort | Risk |
|---|---|---|---|---|
| Datasets | N-BaIoT + Edge-IIoTset + CICIoT2023 device-MAC (conditional) | High | Moderate-Heavy | Low |
| Stress-test comparators | FedProx + Ditto/named-variant + Laridi-style (3 families × 4 threshold policies) | High | Heavy | Low |
| Threshold variants | q-sensitivity + local-global shrinkage + calibration-size-aware fallback + split-conformal B2 | High | Moderate | Low |
| Temporal | Chronological split + one-shot recalibration on Edge-IIoTset; 3 pre-specified outcomes | Medium-High | Moderate | Low |
| Deeper analyses | All 6 must-have analyses | High | Moderate | Low |
| Appendix A | Formal derivation of B2 construction-equality and boundary conditions | High | Immediate | Low |
| Seeds | Extend to 10; report honestly even if CI widens | Medium | Immediate | None |
| Privacy | Bounded-disclosure table + qualitative MIA-risk discussion | Medium | Immediate | Low |
| **Net risk** | — | — | — | **Low–Medium at Computer Networks** |

### 14.3 Ambitious Extension (NOT RECOMMENDED — scope drift)

Adds multiple datasets, broad personalized-FL benchmarking, streaming drift detection, hardware profiling, adversarial robustness. DATP identity dissolves; paper becomes generic FL-IDS. Not pursued this cycle.

---

## 15. Execution Priority: Journal Core vs Supplementary

### 15.1 Must-Have Journal Core

These items are required for Computer Networks submission. None is optional. All must appear in the main paper body or a numbered appendix.

| Item | Notes |
|---|---|
| Appendix A: "B2 equalizes by construction" formal note | Immediate; no new training |
| Laridi-style federated threshold baseline (pre-specified protocol) | Gate 1; operates on stored scores |
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
| Edge-IIoTset preprocessing + device-partition + FedAvg AE training | Gate 2 |
| CICIoT2023 device-MAC repartition (conditional on metadata verification) | Gate 2 |
| FedProx stress-test training on N-BaIoT + Edge-IIoTset | Gate 3 |
| Ditto/named-variant stress-test training on N-BaIoT + Edge-IIoTset | Gate 3 |
| Temporal MVE (chronological split + one-shot recalibration on Edge-IIoTset) | Gate 3 (after Edge-IIoTset preprocessing is stable) |
| Privacy bounded-disclosure table + qualitative MIA-risk discussion | Gate 1 (writing) |
| Expanded related work (Laridi 2024, Sáez-de-Cámara 2023, FedMSE 2025, Belarbi 2023, Plassier ICML 2023, Pradhan et al. 2025) | Gate 1 (writing) |

### 15.2 Supplementary or Only-If-Time

These items are useful but not blocking for Computer Networks submission. They go in supplementary material, future-work discussion, or are deferred to a separate paper.

- Full communication/storage cost table (unless a reviewer explicitly requests it)
- Bootstrap CIs for all metrics beyond the primary CV(FPR) BCa CI (supplementary)
- Complete per-seed per-client raw result tables (supplementary/artifact)
- All-metric Wilcoxon + Cliff's δ report (supplementary)
- Sáez-de-Cámara quantitative reimplementation (deferred)
- Full personalized-FL benchmark across APFL, FedPer, Per-FedAvg (rejected for this cycle; future paper)
- Temporal experiment on CICIoT2023 device-MAC (only after Regime B-b is confirmed and the Edge-IIoTset temporal MVE is already stable)
- Robust cluster median variant (brief supplementary paragraph)

### 15.3 Reject / Do Not Do

See §20 (Do-Not-Do List) for the full enumeration. Summary of additions-specific items:
- No FedBN (encoder incompatibility)
- No empirical MIA experiments
- No formal differential-privacy implementation
- No hardware/edge profiling
- No streaming drift detection framework
- No adversarial robustness branch
- No second new dataset (ToN-IoT, IoT-23, Bot-IoT, etc.)
- No broad personalized-FL benchmark (>1 comparator)
- No Sankey diagram for B4 cluster interpretability (K=3/K=9 is too small; use contingency table or small heatmap)
- No Computers & Security submission

---

## 16. Three-Gate Execution Plan

### Gate 1 — Existing-Score Extension First

**Rationale**: operates entirely on stored per-client score artifacts and fingerprints; no retraining; lowest execution risk; closes the most critical reviewer attacks before any dataset or training infrastructure is needed.

**Actions**:
| # | Action | Output | Go/No-Go Criterion | Fallback |
|---|---|---|---|---|
| G1.1 | Write Appendix A: formal explanation of calibration-set vs held-out-test FPR behavior; bound the construction equality by nₖ and distribution stability | Appendix A draft (LaTeX) | Reviewed by 1 statistician; claims are bounded | Simplify to a theorem-free "formal note" if full derivation is too involved |
| G1.2 | Implement and run q-sensitivity heatmap at q∈{0.90, 0.95, 0.975, 0.99} on stored N-BaIoT scores | Heatmap figure | Ordering B2 < B4 < B1 preserved at all q | Report any inversion honestly; it does not invalidate DATP but must be discussed |
| G1.3 | Implement calibration-size sweep (nₖ ∈ {50, 100, 250, 500, 1k, 5k}) via subsampling on stored N-BaIoT scores | Calibration-size sensitivity figure | Curve reaches plateau; shrinkage maps cleanly | Reduce nₖ granularity if compute is limited |
| G1.4 | Implement local-global shrinkage τₖ(λ) at λ∈{0, 0.25, 0.5, 0.75, 1} on stored N-BaIoT scores | Shrinkage curve figure | λ-curve reported; P10 Macro-F1 behavior at each λ reported | Report any unintuitive result honestly |
| G1.5 | Implement split-conformal B2-conf with marginal coverage check at α=0.05 on stored N-BaIoT scores | Coverage diagnostic figure + main-table row | Empirical coverage within ±0.02 of 1−α | If coverage fails, report as limitation of the conformal adaptation |
| G1.6 | Implement pre-specified Laridi-style baseline (protocol locked in §8.4) on stored N-BaIoT scores | Main comparator table column | Protocol finalized and documented before computation | If overlap-region search requires attack labels unavailable in calibration split, apply the benign-only fallback and document the divergence |
| G1.7 | Run B4 cluster-feature ablation (four feature subsets + all-four) on stored N-BaIoT fingerprints | Compact feature-ablation table + cluster-to-device-type contingency table or heatmap | Each feature subset's CV(FPR) reported; cluster assignments mapped to device labels | If cluster assignments are unstable across seeds, report instability |
| G1.8 | Compute JS divergence ↔ DATP-benefit regression on stored per-client benign distributions | Scatter figure + linear fit | R² and correlation reported with appropriate caveats | Weak R² is a real finding; report it, not an error |
| G1.9 | Compute operational alert-burden table (FPR × declared benign traffic volume from dataset) | Alert-burden table with declared traffic-volume source | Traffic-volume source is documented and justified | If actual volumes are unavailable, use normalized hypothetical clearly labeled as such |
| G1.10 | Compute threshold shift vs ΔFPR/ΔTPR scatter | Scatter figure | Data points for all 9 N-BaIoT devices reported per seed | No filtering of unfavorable devices |
| G1.11 | Extend seeds from 5 to 10 if compute allows; recompute all BCa CIs | Updated result tables; per-seed CSVs in artifact | 10-seed CI reported honestly; if CI widens or approaches zero, the claim is revised accordingly | If 10-seed runs are not feasible before Gate 2 begins, report 5-seed result with explicit statistical-power limitation |
| G1.12 | Write privacy bounded-disclosure table + qualitative MIA-risk discussion | Privacy subsection | No formal-privacy claim; all wording bounded | — |
| G1.13 | Write expanded related work section | Related work draft | Covers Laridi 2024, Sáez-de-Cámara 2023, FedMSE 2025, Belarbi 2023, Plassier ICML 2023, Pradhan et al. 2025 | — |

**Gate 1 Exit Criteria** (all must be satisfied before Gate 2 begins):
- All analyses in G1.1–G1.13 are reproducible from stored artifacts; no retraining was required.
- Appendix A drafted and reviewed.
- Laridi-style protocol is locked and documented; results computed.
- The "B2 is tautological" reviewer attack is explicitly addressed by Appendix A + B2-conf + calibration-size sweep.
- All claims remain centered on threshold scope.
- 10-seed extension result (or explicit 5-seed power limitation) is documented.

---

### Gate 2 — Dataset Expansion (after Gate 1 is stable)

**Actions**:
| # | Action | Output | Go/No-Go Criterion | Fallback |
|---|---|---|---|---|
| G2.1 | **Verify CICIoT2023 MAC/device-group metadata**: inspect the existing preprocessing pipeline to determine whether MAC addresses or device-group labels are retained in stored feature files | Documented verification result: "metadata present" or "metadata absent" | — | If absent: proceed with Regime B-a (file-level) as the only CICIoT2023 regime; do not claim Regime B-b; document explicitly |
| G2.2 | If G2.1 confirms metadata present: build CICIoT2023 device-MAC partition following Pradhan et al. (Sci. Rep. 2025) precedent | Client-count table, benign calibration count per client, attack count, eligibility audit | ≥8 clients with sufficient benign volume for calibration | If <8 eligible clients emerge, retain Regime B-a only and document |
| G2.3 | Download and preprocess Edge-IIoTset; validate feature schema against DATP's existing feature extraction pipeline | Feature-alignment report; list of device/application-type clients; benign calibration per client; attack count per client; capture timestamp availability | Calibration coverage ≥90% of clients (i.e., nₖ ≥ nₘᵢₙ for ≥90% of clients); timestamp available for temporal split | If coverage <90%, adjust nₘᵢₙ or reduce target K |
| G2.4 | Verify chronological timestamp structure in Edge-IIoTset suitable for 70/30 temporal split | Timestamp audit report | A meaningful chronological ordering exists with minimal repeated captures | If timestamps are absent or non-monotonic, defer temporal MVE to supplementary |
| G2.5 | Train FedAvg AE on Edge-IIoTset (K ∈ {6, 15}); compute per-client score artifacts | Edge-IIoTset score artifact files | Convergence per seed; calibration coverage logged | Reduce K if insufficient client data |
| G2.6 | If G2.1–G2.2 are confirmed: train FedAvg AE on CICIoT2023 device-MAC partition; compute score artifacts | CICIoT2023 Regime B-b score artifact files | At least 8 clients; convergence per seed | Fall back to Regime B-a only |
| G2.7 | Run B1–B4 + Laridi-style baseline + q-sensitivity on Edge-IIoTset and (if confirmed) CICIoT2023 device-MAC | Updated main results tables | All deltas reported with BCa CIs | Negative result reported honestly |

**Gate 2 Exit Criteria**:
- Edge-IIoTset artifacts are valid with documented client counts, benign calibration counts, attack counts, and eligibility coverage.
- CICIoT2023 device-MAC feasibility is either confirmed (Regime B-b exists) or explicitly rejected (Regime B-a only).
- Temporal timestamp availability in Edge-IIoTset is verified.
- All partitions are documented before any training-side stress tests begin.

---

### Gate 3 — Training-Side Stress Tests (after Gate 2 is stable)

**Rationale**: FedProx and Ditto require new training runs; these are the highest compute cost and should not begin until the dataset infrastructure is validated.

**Actions**:
| # | Action | Output | Go/No-Go Criterion | Fallback |
|---|---|---|---|---|
| G3.1 | Decide between standard Ditto and local-head comparator (§8.3) and document the choice | Written implementation decision | Choice documented before training | No post-hoc switching based on which performs better |
| G3.2 | Implement and run FedProx (µ ∈ {0.001, 0.01, 0.1}) on N-BaIoT and Edge-IIoTset; apply B1–B4 + Laridi-style threshold grid | Stress-test results table: FedAvg vs FedProx × B1–B4 | All seeds converge; report clearly as stress-test comparator, not core causal claim | If FedProx fails to converge, report failure; do not tune µ until convergence is achieved retroactively |
| G3.3 | Implement and run Ditto/named-variant on N-BaIoT and Edge-IIoTset; apply B1–B4 threshold grid | Stress-test results table: FedAvg vs Ditto × B1–B4 | Personalized model loss converges; B2 gain preserved or attenuated — both outcomes are acceptable | Report attenuation honestly; it weakens one attack axis but does not invalidate DATP |
| G3.4 | Run temporal MVE: chronological 70/30 split on Edge-IIoTset; frozen vs one-shot recalibration | Temporal drift figure + table | Pre-specified outcome interpretation applied (Outcome A, B, or C); no retroactive interpretation changes | If Edge-IIoTset temporal structure is unsuitable (see G2.4 fallback), drop temporal MVE to supplementary |
| G3.5 | Extend to 10 seeds across all Gate 3 runs if compute budget allows | Updated seed count and CIs | Report honestly regardless of direction of change | Report 5-seed results with power limitation if 10 seeds not feasible |

**Gate 3 Exit Criteria**:
- FedProx and Ditto/named-variant are clearly labeled as stress-test comparators throughout the paper; they are never presented as part of the core B1–B4 causal isolation.
- Temporal MVE has been run (or explicitly deferred to supplementary with a documented reason); pre-specified outcome interpretation is applied.
- No result is hidden because it weakens the original story. Negative or null stress-test results are reported and discussed as deployment caveats or scope limitations.

---

## 17. Final Recommended Package

**Selected package: Strong Extension (§14.2). Selected target journal: Computer Networks. Selected backup: Internet of Things (Elsevier). Computers & Security: excluded.**

1. **Dataset additions (≤2)**:
   - Edge-IIoTset (device/application-type partition, K ∈ {6, 15})
   - CICIoT2023 device-MAC repartition (same dataset, new regime, conditional on Gate 2 metadata verification)
2. **Stress-test comparators (≤3 families; all framed as external stress tests, not core causal)**:
   - FedProx (aggregation-side heterogeneity stress test)
   - Ditto or explicitly named local-head personalization comparator (model-side personalization stress test)
   - Laridi-style federated summary-statistics threshold (pre-specified per §8.4; federated-thresholding SOTA comparator)
3. **Threshold additions (≤4 new variants)**:
   - q-sensitivity sweep at q ∈ {0.90, 0.95, 0.975, 0.99}
   - Local-global shrinkage τₖ(λ)
   - Calibration-size-aware fallback (size-dependent shrinkage)
   - Split-conformal B2 (B2-conf) with marginal coverage 1−α
4. **Temporal/recalibration addition (≤1 family)**:
   - Edge-IIoTset chronological 70/30 split; frozen vs one-shot recalibration; three pre-specified outcome interpretations
5. **Deeper analyses (≤6)**:
   - Per-client error CDF overlays + Ennio Doorbell failure-mode deep dive
   - JS divergence ↔ DATP-benefit correlation
   - Threshold shift vs ΔFPR/ΔTPR scatter
   - Calibration-size sensitivity sweep
   - Operational false-alarm burden (declared traffic-volume source)
   - B4 cluster-feature ablation + cluster-to-device-type contingency table or small heatmap
6. **New figures**: (i) per-client benign-error CDF overlay, (ii) calibration-size sensitivity curve, (iii) shrinkage λ-curve, (iv) JS↔gain scatter, (v) threshold-variant q-heatmap, (vi) temporal CV(FPR) drift trajectory, (vii) split-conformal coverage diagnostic, (viii) B4 feature-ablation heatmap
7. **New tables**: (i) stress-test comparator grid (FedAvg / FedProx / Ditto-or-named × B1–B4 + Laridi-threshold), (ii) Edge-IIoTset Regime A' results, (iii) CICIoT2023 device-MAC Regime B-b results (conditional), (iv) failure-mode analysis, (v) privacy-disclosure tabulation per policy, (vi) communication/storage overhead per policy (estimated from message sizes), (vii) B4 cluster-feature ablation, (viii) alert-burden
8. **New sections**: (i) Threshold-Variant Taxonomy, (ii) Calibration-Size Analysis, (iii) Failure-Mode and Limits of DATP, (iv) Privacy and Leakage Analysis, (v) Temporal Recalibration MVE, (vi) Comparison with Federated Thresholding SOTA (Laridi-style) and with Model-Personalization Stress Test (Ditto), (vii) Post-2022 Related Work
9. **Supplementary / Appendix**: Appendix A (B2 construction-equality formal note + boundary conditions); full hyperparameter tables; per-seed per-client raw results; Docker image + git commit hash; extended Zenodo artifact
10. **Claims to strengthen**: (a) "Under non-IID device heterogeneity, threshold scope alone changes the distribution of false alarms across clients" — backed by 2 datasets + conformal variant + calibration-size robustness; (b) "The threshold-scope gain is not absorbed by either heterogeneity-aware aggregation (FedProx) or model-side personalization (Ditto)" — phrased as a stress-test result, not a causal isolation; (c) "Effect is monotone in heterogeneity severity" — Dirichlet + JS-divergence regression
11. **Claims to avoid**: DATP "solves" non-IID; improved global Macro-F1; privacy preservation; concept-drift handling beyond one-shot recalibration evidence; DATP beats Laridi's method universally (phrase as conditional on heterogeneity level)

---

## 18. Artifact and Claim Consistency Check

| Proposed Claim | Support Status | Required Evidence | Artifact Needed | Safe Wording |
|---|---|---|---|---|
| B2 reduces CV(FPR) from 1.017 to 0.299 on N-BaIoT | (1) Already supported | 10-seed extension (report honestly) | Updated seed artifacts | "B2 reduces CV(FPR) from 1.017 to 0.299 (10-seed BCa CI: [a, b]) under the tested N-BaIoT protocol" |
| Effect is monotone in Dirichlet α | (1) Already supported | None | Existing Regime C | "Per-client threshold benefit is monotonically related to Dirichlet α and collapses under IID" |
| B4 recovers ≈52% of B2's improvement | (1) Already supported | None | Existing | "B4 recovers ≈52% of B2's improvement at K=3 (exploratory at N=9)" |
| Effect generalizes to Edge-IIoTset | (3) New experiments | Edge-IIoTset device-partition runs (Gate 2–3) | New | "On Edge-IIoTset (device-partitioned, K=X), B2 reduces CV(FPR) from Y to Z (95% BCa CI: [a, b])" |
| Threshold-scope gain not absorbed by FedProx/Ditto | (3) New stress-test | FedProx/Ditto × B1–B4 grid (Gate 3) | New | "Across FedAvg, FedProx, and Ditto [or named variant] encoders, the B1→B2 CV(FPR) reduction is preserved within ±X% (stress-test comparators; not part of core causal isolation)" |
| DATP vs Laridi-style federated threshold | (3) New experiments | Laridi-style baseline on stored scores + new datasets | New | "Under heterogeneous device partitions, the pre-specified Laridi-style federated threshold reduces FPR dispersion vs B1 but achieves lower dispersion reduction than B2; under near-homogeneous regimes the methods converge" |
| B2 is not a construction tautology | (2) Recomputation + (3) new | Appendix A + calibration-size sweep + B2-conf | New + analytical | "B2's CV(FPR) equalization is exact on calibration data; on held-out test data it is bounded by nₖ and distribution stability (Appendix A); the gain survives split-conformal calibration with marginal coverage 1−α" |
| DATP can handle limited calibration data | (2) Recomputation | n_cal sweep | Subsampled scores | "For n_cal ≥ N*, B2 with shrinkage remains effective; below N*, calibration-size-aware fallback recovers B1-equivalent FPR" |
| DATP threshold aging | (3) Temporal MVE | Chronological split on Edge-IIoTset (Gate 3) | New | Outcome-specific wording per §10.1 |
| DATP preserves privacy | (5) Should not be claimed | — | — | "B4 fingerprints constitute distributional metadata; B4 is not a privacy mechanism" (existing DATP §VII wording) |
| B4 is privacy-safe | (5) Should not be claimed | — | — | Do not claim |
| Threshold personalization helps in CICIoT2023 generally | (5) Should not be claimed | — | — | "Regime B-a (file-level, near-homogeneous) is an applicability boundary; Regime B-b (device-MAC) is the heterogeneous evaluation where metadata permits" |
| DATP reduces operational alert burden | (2) Recomputation | FPR × declared traffic volume | Derived from dataset benign counts | "Translating per-client FPR into expected alerts/day under [declared traffic assumption], B2 reduces worst-client alert load from N₁ to N₂ alerts/day" |
| DATP improves global Macro-F1 | (5) Should not be claimed | — | — | "DATP improves per-client FPR equity; P10 Macro-F1 degrades in low-separability clients (e.g., Ennio Doorbell on N-BaIoT)" |

---

## 19. Implementation-Ready Action Plan

Priorities follow the Three-Gate structure. Items within a gate are ordered by dependency, not by editorial importance.

| Priority | Action | Output Artifact | Depends On | Feasibility | Go/No-Go Criterion | Fallback | Placement |
|---|---|---|---|---|---|---|---|
| G1.1 | Write Appendix A: construction-equality formal note, calibration-set vs held-out-test FPR divergence, nₖ boundary conditions | Appendix A draft (LaTeX) + small illustrative figure | None | Immediate | Reviewed by 1 statistician; no overclaiming | Simplify to a formal note without full derivation | Main Appendix |
| G1.2 | Lock and document Laridi-style protocol per §8.4 (before any computation) | Written pre-specification document | G1.1 | Immediate | Protocol finalized before any result is inspected | — | Protocol annex |
| G1.3 | Run q-sensitivity heatmap (q∈{0.90, 0.95, 0.975, 0.99}) on stored N-BaIoT scores | Main heatmap figure | Stored scores | Immediate | Ordering B2 < B4 < B1 at all q (or any inversion reported honestly) | Report inversion; it does not invalidate DATP | Main |
| G1.4 | Run calibration-size sweep (nₖ ∈ {50, 100, 250, 500, 1k, 5k}) via subsampling | Calibration-size sensitivity figure | Stored scores | Immediate | Curve plateaus; shrinkage maps cleanly | Reduce granularity | Main |
| G1.5 | Implement local-global shrinkage τₖ(λ) at λ∈{0, 0.25, 0.5, 0.75, 1} on stored scores | Shrinkage curve figure | Stored scores | Immediate | λ-curve reported; P10 Macro-F1 per λ reported | Report any non-monotone behavior | Main |
| G1.6 | Implement split-conformal B2-conf with coverage check at α=0.05 | Coverage diagnostic figure + main-table row | Stored scores | Moderate | Empirical coverage within ±0.02 of 1−α | Report coverage failure as conformal-adaptation limitation | Main + Appendix A |
| G1.7 | Implement pre-specified Laridi-style baseline on stored N-BaIoT scores | Main comparator table column | G1.2; stored scores | Moderate | Protocol pre-specified; result computed without tuning | Benign-only fallback if overlap-region requires attack labels | Main |
| G1.8 | Run B4 cluster-feature ablation (4 subsets + all-four) on stored fingerprints | Feature-ablation table + cluster-to-device-type contingency table or small heatmap | Stored fingerprints | Immediate | Each subset's CV(FPR) reported; cluster assignments mapped | If unstable across seeds, report instability | Main |
| G1.9 | Compute JS divergence ↔ DATP-benefit regression | Scatter figure + correlation table | Stored distributions | Immediate | R² and ρ reported with caveats | Weak R² is a real result; report it | Main |
| G1.10 | Compute alert-burden table (FPR × declared traffic volume) | Alert-burden table | Stored scores + declared traffic-volume source | Immediate | Traffic-volume source documented and justified | Normalized hypothetical labeled as such | Main |
| G1.11 | Compute threshold shift vs ΔFPR/ΔTPR scatter | Scatter figure | Stored scores + thresholds | Immediate | All 9 N-BaIoT clients reported; no device filtering | — | Main |
| G1.12 | Extend to 10 seeds if compute allows; recompute all BCa CIs | Updated result tables; per-seed CSVs | Existing pipeline | Immediate | 10-seed result reported honestly including if CI widens | 5-seed result reported with power limitation | Main |
| G1.13 | Write privacy bounded-disclosure table + qualitative MIA-risk discussion | Privacy subsection draft | G1.1–G1.7 results | Immediate | No formal-privacy claim; all wording bounded | — | Main |
| G1.14 | Write expanded related work | Related work draft | G1.1–G1.13 | Immediate | Covers all 7 required references | — | Main |
| G2.0 | **Verify CICIoT2023 MAC/device metadata availability** | Written verification result | Gate 1 complete | Moderate | Unambiguous outcome: metadata present or absent | If absent: Regime B-a retained; Regime B-b dropped | Prerequisite for G2.1 |
| G2.1 | If G2.0 confirms: build CICIoT2023 device-MAC partition | Client-count table; eligibility audit | G2.0 (positive) | Moderate | ≥8 clients with sufficient benign volume | <8 clients: retain Regime B-a only | Main (conditional) |
| G2.2 | Download and preprocess Edge-IIoTset; validate feature schema; audit timestamps | Feature-alignment report; client-count table; benign calibration per client; timestamp audit | Gate 1 complete | Moderate-Heavy | Coverage ≥90%; timestamp available | Reduce K or defer temporal MVE to supplementary | Prerequisite for G2.3–G3.3 |
| G2.3 | Train FedAvg AE on Edge-IIoTset (K ∈ {6, 15}); compute score artifacts | Edge-IIoTset score artifacts | G2.2 | Moderate-Heavy | Convergence per seed; calibration coverage logged | Reduce K | Main |
| G2.4 | If G2.0–G2.1 confirmed: train FedAvg AE on CICIoT2023 device-MAC; compute scores | CICIoT2023 Regime B-b score artifacts | G2.0 positive; G2.1 | Moderate-Heavy | ≥8 clients; convergence per seed | Fall back to Regime B-a only | Main (conditional) |
| G2.5 | Run B1–B4 + Laridi-style + q-sensitivity on Edge-IIoTset + CICIoT2023 Regime B-b (if confirmed) | Updated main results tables | G2.2–G2.4 | Heavy | All deltas reported with BCa CIs | Negative result reported and discussed | Main |
| G3.0 | Document Ditto implementation choice (standard Ditto vs local-head comparator per §8.3) | Written implementation decision | Gate 2 complete | Immediate | Choice finalized before training | No post-hoc switching | Protocol annex |
| G3.1 | Implement and run FedProx (µ ∈ {0.001, 0.01, 0.1}) on N-BaIoT + Edge-IIoTset; apply B1–B4 | Stress-test comparator table | G2.2–G2.3 | Moderate (Flower-native) | Convergence per seed; labeled as stress-test comparator | Report convergence failure; do not tune µ retroactively | Main (stress-test section) |
| G3.2 | Implement and run Ditto/named-variant on N-BaIoT + Edge-IIoTset; apply B1–B4 | Stress-test comparator table | G3.0; G2.2–G2.3 | Heavy | Personalized model converges; result reported regardless of direction | Report attenuation honestly | Main (stress-test section) |
| G3.3 | Run temporal MVE: chronological 70/30 split on Edge-IIoTset; frozen vs one-shot recalibration | Temporal figure + table; pre-specified outcome applied | G2.2 timestamp confirmation | Moderate | Pre-specified outcome interpretation applied | If timestamps unsuitable: defer to supplementary; report reason | Main (temporal section) |
| G3.4 | Finalize all Gate 3 runs; recompute BCa CIs to 10 seeds if not already done | Final result tables | G3.1–G3.3 | — | 10-seed rule applied honestly | — | Main |
| Final | Draft cover letter; rewrite Introduction + Related Work + Methodology to ≥40% new prose | Journal manuscript draft | All above | Moderate | iThenticate overlap ≤20%; cover letter enumerates new sections | — | Submission |
| Submit | Submit to Computer Networks after conference camera-ready is set | Submission package | Conference decision | — | Conference accepted (or withdrawn) | — | — |

---

## 20. Do-Not-Do List

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
13. Do **not** change the mainline AE architecture, FedAvg aggregator, or round budget between conference and journal — would break the extension framing.
14. Do **not** reuse conference figures verbatim — redraw or substantially extend each.
15. Do **not** silently change the CV(FPR) definition between conference and journal.
16. Do **not** frame the CICIoT2023 file-level null result as a general CICIoT2023 statement — keep it as Regime B-a (near-homogeneous applicability boundary).
17. Do **not** invoke FedMSE (COSE 2025) as evidence that COSE accepts FL submissions today — the moratorium is explicit and current.
18. Do **not** target FGCS as a primary venue — scope drift risk too high.
19. Do **not** use a Sankey diagram for B4 cluster interpretability — K=3 clusters / K=9 devices is too small; use a contingency table or small heatmap.
20. Do **not** present hypothetical alert/day numbers as real deployment measurements — declare the traffic-volume source or label as a normalized hypothetical.
21. Do **not** suppress or hide the 10-seed result if it is less favorable than the 5-seed result — the 10-seed result is the main result under the seed-extension honesty rule.
22. Do **not** tune the Laridi-style protocol after seeing results — the protocol is finalized (G1.2) before any computation.
23. Do **not** claim Regime B-b (CICIoT2023 device-MAC) if the metadata verification (G2.0) is negative.
24. Do **not** call the Ditto fallback "Ditto" if it is only a frozen-body local-head variant — rename it explicitly (see §8.3).
25. Do **not** present FedProx or Ditto results as part of the core B1–B4 causal ladder — they are external stress-test comparators.

---

## 21. Final Reviewer Attack After Repair

1. **Remaining attackable weaknesses** (all are acceptable and explicitly bounded):
   - K is still modest (Edge-IIoTset K ∈ {6, 15}, N-BaIoT K=9, CICIoT2023-MAC K≈10 if confirmed) — fleet-scale validation at K > 100 is deferred
   - One aggregation stress test (FedProx) — not exhaustive
   - One model-personalization stress test (Ditto/named-variant) — not exhaustive
   - Privacy analysis remains qualitative — no MIA experiment, no DP epsilon-accuracy curve
   - Temporal MVE is a single chronological split — not streaming
   - Laridi adaptation is DATP-compatible but not an exact reproduction of the original non-IoT method
   - 10-seed result reported honestly — CIs may be wider than 5-seed

2. **Why each is acceptable**: each is explicitly out-of-scope of the "threshold-scope-only controlled study under fixed FedAvg + frozen encoder" design; scope discipline is the paper's core contribution; broader extensions are natural follow-up papers in the thesis program.

3. **How to word them honestly**:
   - "Our evaluation comprises K ∈ [9, 15] physical-device clients across benchmarks; fleet-scale validation at K > 100 is reserved for future work."
   - "FedProx and Ditto [or named variant] are external stress-test comparators, not part of the core causal isolation; we add one representative of each class."
   - "Privacy analysis is qualitative; formal DP or SecAgg integration is future work."
   - "The temporal regime is a one-shot recalibration MVE under a chronological split; streaming drift handling is future work."
   - "We implement a faithful DATP-compatible adaptation of the Laridi-style federated threshold; we do not claim it is an exact reproduction of the original method."

4. **Highest residual risk**: Whether DATP's gain survives Ditto+B1 (i.e., whether model personalization makes threshold personalization redundant) — this must be reported honestly regardless of direction.

5. **What would satisfy the reviewer**: (a) Appendix A + B2-conf closes the tautology critique; (b) Edge-IIoTset provides cross-dataset generalization evidence; (c) Laridi comparison closes the federated-thresholding novelty question; (d) Ditto stress test answers "why not just personalize the model"; (e) temporal MVE answers threshold-aging concern; (f) alert-burden table grounds CV(FPR) in practitioner terms.

---

## 22. Search and Verification Audit Log

| Query or Source | Source Type | Date Checked | Key Finding | Confirmed / Changed / Contradicted Input Files | Used in Final Recommendation |
|---|---|---|---|---|---|
| DATP.pdf | Project knowledge | 2026-05-23 | CV(FPR) 1.017→0.299, B4 ≈52%, 9 physical devices, 5 seeds, E=1, q=0.95; B4-is-not-privacy framing | Confirmed | Yes |
| State_of_the_Art.md | Project knowledge | 2026-05-23 | 6 gap clusters; non-IID/privacy/adversarial/deployment/dataset/reproducibility | Confirmed | Yes |
| Blueprint.md | Project knowledge | 2026-05-23 | Sole confirmatory claim: Regime A B1-vs-B2 CV(FPR); RQ hierarchy; null-finding contingencies; no BN in encoder | Confirmed | Yes — anchors encoder constraint (FedBN rejection) |
| sciencedirect.com/journal/computers-and-security (Aims & Scope) | Official Elsevier page | 2026-05-23 | Verbatim moratorium: "items directed to the security of AI/ML systems themselves (such as LLM and federated learning) are out of scope" | **Changed** — rules out COSE (contradicts Audits B, F, G) | Yes — decisive and final |
| sciencedirect.com/journal/computer-networks/publish/guide-for-authors | Official Elsevier page | 2026-05-23 | Verbatim: "Enhanced, extended versions of quality papers presented at conferences or workshops can be submitted" | Confirmed (Audit D) | Yes — anchors primary venue |
| Rey et al. (2022). Computer Networks 204:108693 | Peer-reviewed paper | 2026-05-23 | FL MLP+AE on N-BaIoT; foundational predecessor on identical dataset and venue | Confirmed | Yes — anchors venue choice |
| Laridi, Palmer & Tam (2024). Sci. Rep. 14:26704 | Peer-reviewed paper | 2026-05-23 (via Audits) | Federated thresholding via summary statistics; closest novelty threat | Confirmed (Audits A–D) | Yes — anchors mandatory comparator and pre-specification requirement |
| Sáez-de-Cámara et al. (2023). Computers & Security 131:103299 | Peer-reviewed paper | 2026-05-23 (via Audits) | Clustered FL on Gotham testbed; Local-Largest-MSE per-client thresholds; clusters *models*, not *thresholds* | Confirms differentiation: B4 clusters thresholds, not models | Yes |
| Belarbi et al. (2023). GLOBECOM 2023 | Peer-reviewed paper | 2026-05-23 (via Audits) | FedAvg vs FedProx vs FedYogi on TON-IoT; raises aggregation-baseline expectations | Confirms FedProx is the mandatory stress test | Yes |
| Pradhan et al. (2025). Sci. Rep. 10.1038/s41598-025-32567-w | Peer-reviewed paper | 2026-05-23 (via Audits) | Edge-IIoTset: 6 device/application-type clients; CICIoT2023: 10 device-group clients | Confirms partition precedent for both datasets | Yes |
| Plassier et al. (2023). ICML 2023, PMLR 202:27907 | Conference proceedings | 2026-05-23 (via Audits) | Federated conformal prediction with DP guarantees | Confirms B2-conf as defensible threshold variant | Yes |
| Ferrag (2022). Edge-IIoTset. IEEE Access 10.1109/ACCESS.2022.3165809 | Peer-reviewed paper | 2026-05-23 (via Audits) | Native FL framing; 10+ device types; 14 attacks | Confirms Edge-IIoTset as primary new dataset | Yes |
| FGCS Guide for Authors | Official Elsevier page | 2026-05-23 (via Audit D) | 40% new contributions requirement for conference extensions | Confirms ≥40% as safe bar | Yes |
| Nguyen & Beuran (2025). FedMSE. Computers & Security 151:104337 | Peer-reviewed paper | 2026-05-23 | Submitted July 2024 before/during moratorium transition; not a safe precedent for new submissions | Clarifies COSE risk | Yes |
| 30%/40% extension rule | Multiple Elsevier sources | 2026-05-23 | No Elsevier-wide policy; 30% is ICPR/PRL-specific; FGCS explicitly states 40% | Audits C and D are correct | Yes — sets ≥40% as the standard |
| ACM Computing Surveys 2024, DOI 10.1145/3704633 (MIA in FL) | Peer-reviewed survey | 2026-05-23 (via Audit C) | MIA risk is real; threshold-based MIA exists; defenses include SecAgg, DP, partial sharing | Supports bounded-disclosure framing | Yes |
| Neto et al. (2023). CICIoT2023. Sensors 23(13):5941 | Official dataset paper (DATP ref [3]) | 2026-05-23 | 105 devices, 33 attacks; structure permits device-MAC repartition | Confirms repartition feasibility in principle | Yes |

---

## 23. Final Decision Gate

1. **Best target journal**: **Computer Networks (Elsevier)**, ISSN 1389-1286, 2024 JIF 4.6, Q1. Reasons: (a) Rey et al. 2022 direct lineage on identical dataset and venue; (b) Guide for Authors verbatim accepts enhanced extended conference versions; (c) scope explicitly covers network security, intrusion detection, and malicious code; (d) Computers & Security is excluded by a verbatim and current AI/ML moratorium. Backup: Internet of Things (Elsevier), then Cyber Security and Applications, then JNCA.
2. **Best expansion level**: **Strong (§14.2)**. Minimal risks desk-rejection; Ambitious destroys identity.
3. **Exact must-do list before submission**: (i) Appendix A formal note (G1.1); (ii) Laridi protocol locked (G1.2); (iii) q-sensitivity + calibration-size sweep + shrinkage + B2-conf (G1.3–G1.6); (iv) Laridi-style comparator on stored scores (G1.7); (v) B4 feature ablation + contingency table (G1.8); (vi) JS↔gain regression (G1.9); (vii) alert-burden table with declared traffic-volume source (G1.10); (viii) threshold-shift scatter (G1.11); (ix) 10-seed extension reported honestly (G1.12); (x) privacy bounded-disclosure + related work expansion (G1.13–G1.14); (xi) Edge-IIoTset preprocessing + device-partition + training (G2.2–G2.3); (xii) CICIoT2023 device-MAC repartition if metadata confirmed (G2.0–G2.4); (xiii) FedProx + Ditto/named-variant stress tests on both datasets (G3.1–G3.2); (xiv) temporal MVE on Edge-IIoTset with pre-specified outcome interpretation (G3.3); (xv) cover letter with explicit extension disclosure.
4. **Exact do-not-do list**: see §20 (25 items). Summary: no COSE; no FedBN; no second new dataset; no more than one model-personalization stress test; no empirical MIA; no streaming drift; no adversarial branch; no hardware; no overclaiming; no post-hoc tuning of Laridi protocol; no Sankey; no hiding unfavorable 10-seed results; no calling the local-head variant "Ditto"; no presenting FedProx/Ditto as core causal baselines.
5. **Should the journal extension wait until conference acceptance?** **Yes.** Begin experiments now (Gate 1 can start immediately). Submit to Computer Networks only after conference camera-ready is set. If the conference paper is rejected, fold reviewer feedback into the journal manuscript and submit as an original full paper (still cite any posted preprint as prior work).
6. **Confidence ratings**: High — venue exclusion (verbatim-confirmed); High — Computer Networks selection (lineage + explicit policy); High — dataset choice (Pradhan et al. 2025 precedent); High — threshold variants (all four operate on stored artifacts or minimal new runs); Medium-High — stress-test comparator grid; Medium — temporal MVE outcome (three pre-specified interpretations cover all outcomes honestly); High — scope control (all hard limits respected).
7. **Final verdict**: The DATP conference paper has a real, defensible empirical finding and a scientifically clean experimental discipline. The journal version must do exactly five things and no more: (a) close the construction-tautology critique via Appendix A + B2-conf + calibration-size sweep; (b) prove generalization on Edge-IIoTset and (conditionally) redesigned CICIoT2023; (c) demonstrate via stress tests that the threshold-scope gain is not absorbed by heterogeneity-aware aggregation (FedProx) or model-side personalization (Ditto), and is not dominated by the Laridi-style federated threshold; (d) show threshold aging behavior under a chronological split with pre-specified outcome interpretation; and (e) ground CV(FPR) in an operational alert-burden metric. The Computers & Security moratorium is the most consequential single fact and is final. The Laridi 2024 comparison is the dominant novelty risk and must be pre-specified. The Strong package — one new dataset, one conditional partition redesign, three stress-test comparator families, four threshold variants, one temporal family, six mechanism analyses, one formal appendix — respects every hard limit, preserves DATP's threshold-scope-only identity, and is feasible in 4–6 months of focused work.

---

## 24. Final Internal Consistency Audit

| Audit Item | Expected Final State | Status | Notes |
|---|---|---|---|
| Primary journal is Computer Networks everywhere | Computer Networks is primary in every section (§1, §12, §14, §15, §17, §23) | ✅ Pass | No conflicting statement found |
| Computers & Security is excluded everywhere | COSE excluded in §1, §12, §18, §20, §23 | ✅ Pass | Moratorium wording consistent |
| Strong extension is selected everywhere | Strong selected in §1, §14, §15, §17, §23 | ✅ Pass | Minimal and Ambitious are clearly labeled as not recommended |
| Edge-IIoTset is the only new dataset | Edge-IIoTset is the sole new dataset in §7, §15, §17, §23 | ✅ Pass | ToN-IoT, IoT-23, Bot-IoT, etc. are all rejected |
| CICIoT2023 device-MAC repartition is conditional on metadata verification | "Conditional on metadata verification / TO VERIFY" appears in §3, §7, §16, §19, §23 | ✅ Pass | Contingency branches documented in G2.0 |
| FedBN is rejected everywhere | FedBN rejected in §4, §8, §15, §20 | ✅ Pass | Reason: no BN layers in DATP encoder; stated consistently |
| FedProx and Ditto are stress-test comparators, not core causal baselines | Framing distinction stated in §3, §8.1, §15, §17, §19, §20 | ✅ Pass | Explicitly not part of B1–B4 causal ladder |
| Laridi-style baseline protocol is pre-specified | Full pre-specified protocol in §8.4; G1.2 requires locking before computation | ✅ Pass | Protocol includes disclosure wording and pre-registration rule |
| Temporal MVE has three pre-specified outcome interpretations | Three outcomes (A, B, C) defined in §10.1; referenced in §19 (G3.3) and §17 | ✅ Pass | All three outcomes are valid research findings |
| 10-seed reporting rule is honest | Seed-extension honesty rule stated in §13 (point 9) and §19 (G1.12) | ✅ Pass | Explicitly states CI widening or zero-crossing requires claim revision |
| Cover-letter percentage is consistently "at least 40% substantive new material" | §13 (points 5 and 6) both use "at least 40% substantive new material" | ✅ Pass | "approximately 50%" removed; consistent throughout |
| Sankey diagram is removed | B4 interpretability in §11 specifies "contingency table or small heatmap"; §20 item 19 explicitly bans Sankey | ✅ Pass | Rationale: K=3 clusters / K=9 devices too small |
| No privacy scope drift | Privacy analysis is qualitative only (bounded-disclosure table + MIA-risk discussion); no empirical MIA; no DP implementation; §20 items 7, 21 | ✅ Pass | Bounded-disclosure table is included but no formal-privacy claim |
| No adversarial / poisoning scope drift | Adversarial branch rejected in §4, §14.3, §20 (item 9) | ✅ Pass | Clearly deferred to thesis robustness paper |
| No hardware / deployment scope drift | Hardware excluded in §11, §20 (item 10) | ✅ Pass | Alert-burden table uses dataset-derived or hypothetical volumes only |
| No broad personalized-FL benchmark scope drift | Only one model-personalization stress test (Ditto); all others rejected in §8.2, §20 (items 4, 24) | ✅ Pass | |
| Alert-burden traffic volume declared | §11.1 specifies three acceptable sources; §20 (item 20) bans undeclared hypotheticals | ✅ Pass | |
| Ditto naming is unambiguous | §8.3 requires choosing standard Ditto or renaming to "local-head personalization comparator" before training | ✅ Pass | Post-hoc switching banned |
| Three-gate dependency ordering is consistent | Gate 1 (stored scores) → Gate 2 (datasets) → Gate 3 (training); all dependencies in §19 follow this order | ✅ Pass | No Gate 3 item starts before Gate 2 exit |
| Venue matrix excludes irrelevant journals | Ad Hoc Networks, Computer Standards & Interfaces, EAAI removed from ranked venues; compressed to a single exclusion note | ✅ Pass | |
| Cover letter does not claim an exact percentage | §13 (point 6) says "at least 40% substantive new material" and does not assert an exact number | ✅ Pass | |

---

## Change Summary

The following changes were made to the original roadmap (document index 25) to produce this updated version:

**Structural additions**:
- §15 "Execution Priority: Journal Core vs Supplementary" — new section classifying all proposed work into Must-Have Journal Core, Supplementary/Only-If-Time, and Reject
- §16 "Three-Gate Execution Plan" — new section with three gated phases (Gate 1: stored-score extension; Gate 2: dataset expansion; Gate 3: training-side stress tests), each with explicit actions, go/no-go criteria, and fallbacks
- §24 "Final Internal Consistency Audit" — new closing table auditing 22 items against expected final state

**Corrections to existing sections**:
- §8 (Baseline Expansion): added mandatory framing rule distinguishing core causal ladder (B1–B4) from external stress-test comparators (FedProx, Ditto, Laridi); added Ditto implementation choice (§8.3) with preferred standard-Ditto option and acceptable local-head fallback with required renaming; added full Laridi-style baseline pre-specification table (§8.4) with protocol elements, aggregation rule, disclosure wording, and pre-registration rule
- §10 (Temporal): added three mandatory pre-specified outcome interpretations (Outcome A: drift + recalibration helps; Outcome B: drift + recalibration fails; Outcome C: no meaningful drift observed); each outcome has specified wording to prevent post-hoc narrative adjustment
- §11 (Deeper Analysis): removed "cluster→device-type Sankey" from B4 ablation row; replaced with "contingency table or small heatmap"; added §11.1 specifying three acceptable traffic-volume sources for the alert-burden table
- §12 (Venue Matrix): removed Computer Standards & Interfaces, Ad Hoc Networks, and EAAI as ranked rows; all consolidated into a brief exclusion note; COSE exclusion strengthened with consistent language
- §13 (Cover Letter): fixed "approximately 50% new material" to "at least 40% substantive new material" throughout; fixed §13 point 6 cover-letter template to match; added seed-extension honesty rule as point 9
- §17 (Action Plan): substantially expanded with dependency column, go/no-go criterion column, fallback column, and placement column for every item; reorganized by gate
- §18 (Claim Consistency): "DATP is robust to threshold aging" row updated to reference pre-specified outcome interpretations
- §19 renumbered from 17; §20 renumbered from 18; §21 from 19; §22 from 20; §23 from 21
- §3 (DATP Identity): added note that FedProx and Ditto are external stress-test comparators, not part of the core causal ladder; updated Regime B notation to Regime B-a / Regime B-b
- §7 (Dataset Expansion): added TO VERIFY note for CICIoT2023 MAC metadata with contingency branch; updated notation to Regime B-a / Regime B-b
- §4 (Cross-File Agreement): added row on FedProx/Ditto framing; updated Ditto row to reflect §8.3 clarification
- §20 (Do-Not-Do): expanded from 18 to 25 items; added: no Sankey, no undeclared alert-burden hypotheticals, no suppression of 10-seed results, no post-hoc tuning of Laridi protocol, no calling local-head variant "Ditto", no presenting FedProx/Ditto as core causal baselines, no Regime B-b claim without metadata confirmation

**Items preserved without change**: Executive Verdict (§1), Input Corpus Inventory (§2), Reviewer-Loophole Closure Table (§6) except minor wording alignment, Dataset Expansion Decision main table (§7), Threshold Variant Decision (§9), Final Reviewer Attack (§21), Search Audit (§22), Final Decision Gate (§23 core verdict), Artifact and Claim Consistency Check (§18) except one row update.