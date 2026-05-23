# PRE-CODING PLAN

Documentation-only planning artifact. No code, configs, datasets, results, or manuscript files are changed by this plan.

Sources of truth, in order:
1. Actual repository code and outputs under `/home/naslouby/Projects/datp`.
2. `Journal/Journal_Extension_Master_Roadmap.md`.
3. The conference paper under `paper/`.
4. The consolidated journal planning rules in these four files.

Anything not directly observed is recorded as a blocker, suppression, or pending verification item. No online source, dataset property, venue rule, or experimental result is assumed.

---

## 1. Planning Package Scope

The journal planning package is intentionally limited to four files:

| File | Purpose |
|---|---|
| `docs/journal/PRE_CODING_PLAN.md` | Gate 0 verification, source-of-truth audit, locks, blockers, claim boundaries. |
| `docs/journal/CODING_PLAN.md` | Future implementation tasks only, grouped by gate and dependency. |
| `docs/journal/EXPERIMENT_PLAN.md` | Experiment order, rerun policy, compute rules, result freeze. |
| `docs/journal/POST_EXPERIMENT_PLAN.md` | Claim survival, manuscript update order, figures/tables, submission readiness. |

No additional journal-planning files are canonical. Content previously split into verification registers, feasibility notes, claim matrices, compute notes, runbooks, overlap reports, supplement plans, lineage plans, and rebuttal banks is merged into these four files.

---

## 2. Repository Readiness Summary

The current repository already contains the core DATP implementation and conference outputs:

| Area | Observed State | Status |
|---|---|---|
| Core baselines | `src/datp/baselines/main/{b0,b1,b2,b3,b4}.py` exist. | Present |
| Dataset specs | `src/datp/data/datasets/{nbaiot,ciciot2023}/{spec.py,prepare.py}` exist. | Present |
| Regime modules | `src/datp/data/regimes/{regime_a.py,regime_b.py,regime_c.py}` exist. | Present |
| Training | `src/datp/training/fl/` exists for shared FL training. | Present |
| Statistics | Bootstrap, CV, divergence, effect size, Wilcoxon, Spearman modules exist. | Present |
| Reporting | Jinja2-based reporting modules and figure/table builders exist. | Present |
| Regime A scores | `outputs/scores/a/seed_{0..4}/...` exist. | Present, not yet verified for reuse |
| Regime B-a scores | `outputs/scores/b/seed_{0..4}/...` exist. | Present, not yet verified for reuse |
| Regime C scores | `outputs/scores/c/seed_{0..4}/alpha_*...` exist. | Present, not yet fully verified |
| Regime A results | B0, B1, B2, B3, B4 results exist for seeds 0–4. | Present |
| Regime B-a results | B0, B1, B2, B4 results exist for seeds 0–4. | Present |
| Regime C results | B1, B2, B4 results exist for seeds 0–4 across α values. | Present, completeness must be verified |
| Edge-IIoTset | No raw, processed, score, checkpoint, or result artifacts are present. | Not started |
| CICIoT2023 B-b | No verified MAC/group repartition exists. | Blocked |
| 10-seed extension | Only seeds 0–4 are present. | Extension required if used |
| FedProx / Ditto / LocalHead artifacts | No artifacts exist. | Not started |
| Temporal recalibration artifacts | No chronological split or temporal results exist. | Not started |

Current headline references from existing conference artifacts:
- Regime A table includes B1 CV(FPR) ≈ 1.0172, B2 ≈ 0.2992, B3 ≈ 0.9643, B4 ≈ 0.6454, B0 ≈ 0.7874.
- Regime B-a table includes B1 CV(FPR) ≈ 0.0989, B2 ≈ 0.1332, B4 ≈ 0.1006, B0 ≈ 0.1085.
- These values are references for Gate 0 reproduction only, not journal-final claims.

---

## 3. Canonical Terminology

### 3.1 Regimes

| Label | Meaning | Claim Status |
|---|---|---|
| Regime A | N-BaIoT natural physical-device split. | Confirmatory center. |
| Regime B-a | CICIoT2023 file-level / pseudo-client boundary regime. | External boundary / near-null support only. |
| Regime B-b | Conditional CICIoT2023 MAC-based or group-based repartition. | Exists only if Gate 0 verifies metadata and eligible clients. |
| Regime C | N-BaIoT Dirichlet severity sweep over α. | Supportive / robustness evidence. |
| Regime D | Edge-IIoTset external validation. | Exists only if Gate 0 verifies dataset availability, client identifiers, and eligibility. |

Use `Regime D` only for Edge-IIoTset. The old prime label is removed.

### 3.2 Baselines and Comparators

| Label | Meaning | Scope |
|---|---|---|
| B0 | Centralized reference comparator. | Reference only. |
| B1 | Shared/global threshold. | Core ladder. |
| B2 | Per-client p95 threshold. | Core ladder; main comparison against B1. |
| B3 | Family/group threshold. | Regime A only unless a valid family/group mapping is locked before implementation. |
| B4 | Fingerprint-cluster threshold. | Secondary, taxonomy-free grouped approximation. |
| `τ-shrink` | Local-global threshold shrinkage: interpolation between B1 and B2. | Threshold variant, not B3. |
| `B2-conf` | Federated/split-conformal per-client threshold variant. | Threshold variant; primary anchor Lu et al. ICML 2023, co-anchor Humbert et al. ICML 2023. |
| `B-FedStatsBenign` | DATP-compatible benign-only federated summary-statistics threshold comparator. | Comparator; does not reproduce attack-labeled Laridi assumptions. |
| `B-LaridiFaithful` | Relaxed comparator requiring anomaly-labeled calibration summaries. | Out of current DATP scope because the DATP calibration assumption is benign-only. Not implemented in this plan. |
| FedProx | Heterogeneity-aware aggregation stress test. | Stress test only, not core ladder. |
| Ditto | True Ditto-style personalized model, only if implemented faithfully. | Stress test only. |
| `LocalHead-PersonalizedAE` | Frozen/shared encoder with client-local lightweight head. | Stress test only; never called Ditto. |

---

## 4. Claim Boundaries

### 4.1 Allowed Claims

The journal extension may claim only what frozen results support:

- Threshold calibration scope affects per-client FPR disparity under the tested datasets, partitions, and fixed protocol.
- The main confirmatory comparison is B1 vs B2 on Regime A.
- B2 is a per-client calibration method, not a new aggregation or model-personalization protocol.
- B4 is a practical taxonomy-free approximation, reported second after B2.
- B3 is preserved as a Regime A comparator and not silently dropped.
- Regime B-a is a near-homogeneous CICIoT2023 boundary condition.
- Regime B-b is conditional on verified metadata and sufficient eligible clients.
- Regime C is supportive severity-sweep evidence.
- Regime D is external validation only if Edge-IIoTset passes Gate 0.
- FedProx, Ditto, `LocalHead-PersonalizedAE`, and `B-FedStatsBenign` are stress tests or comparators, never members of the core causal ladder.
- B4 shares coarse distributional fingerprints; it is not a formal privacy mechanism.
- Any temporal result is a temporal recalibration probe, not a general concept-drift solution.

### 4.2 Forbidden Claims

- DATP solves non-IID FL.
- DATP improves anomaly detection globally or universally.
- DATP is privacy-preserving.
- B4 is privacy-preserving.
- DATP handles poisoning, backdoors, evasion, formal DP, secure aggregation, or real hardware deployment.
- DATP works on all IoT datasets.
- FedProx, Ditto, or `LocalHead-PersonalizedAE` is part of the core B1–B4 causal ladder.
- `B-FedStatsBenign` resolves the novelty risk against anomaly-labeled Laridi-style calibration.
- Regime B-b exists before Gate 0 verifies it.
- Regime D exists before Gate 0 verifies it.
- 5-seed results are journal-final if the final plan requires a 10-seed claim.
- Any causal wording such as “proves,” “confirms mechanism,” or “establishes causality” for the mechanism analyses.

---

## 5. Gate 0 Verification Requirements

No coding or experiments begin until the applicable Gate 0 checks are completed and recorded.

### 5.1 Score-Reuse Verification

Stored scores under `outputs/scores/<regime>/seed_<N>[/alpha_<α>]/` may be reused only after verification succeeds.

For every reused cell:
1. Recompute B1 and B2 from stored `cal`, `test_benign`, and `test_attack` score parquet files.
2. Recompute B4 where required inputs are recoverable.
3. Recompute B3 for Regime A.
4. Compare recomputed metrics to the original `metrics.json`, aggregate tables, and figure sidecars.
5. Verify resolved config compatibility on all scientific-impact fields.
6. Verify lineage: raw data → processed split → resolved config → checkpoint → scores → metrics → table/figure sidecar.

Required comparison fields:
- `cv_fpr`, `cv_tpr`, `mean_fpr`, `std_fpr`, `iqr_fpr`, `max_min_fpr_gap`.
- `worst_ba`, `p10_macro_f1`.
- `eligible_count`, `pending_count`, `coverage_ratio`.
- `eligible_ids`, `pending_ids`.
- Per-client confusion totals.
- Dataset, regime, baseline, α, seed, metric schema version.
- Checkpoint hash and score manifest identity.

Default tolerance:
| Field | Required Match |
|---|---|
| Scalar metrics | Absolute tolerance ≤ 0.01 |
| `coverage_ratio` | Absolute tolerance ≤ 0.001 |
| Counts and ID sets | Exact |
| Confusion totals | Exact |
| Dataset/regime/baseline/seed/α/schema identity | Exact |
| Checkpoint and score hashes | Exact, unless a written compatibility note proves scientific equivalence |

Allowed outcomes:
- `VERIFIED_REUSE_SAFE`
- `REUSE_BLOCKED_RERUN_REQUIRED`

Any `REUSE_BLOCKED_RERUN_REQUIRED` cell cannot support a journal claim.

### 5.2 CICIoT2023 Canonical Root

The repository lists two processed CICIoT2023 roots:
- `data/processed/ciciot/Merged*`
- `data/processed/ciciot2023/Merged*`

Gate 0 must:
1. Inspect both roots.
2. Compare file lists, schemas, sizes, manifests, and row counts.
3. Determine which root current code imports.
4. Declare one canonical root.
5. Move or quarantine the non-canonical root outside the import path.

No Regime B-a refresh or Regime B-b work may proceed while this conflict remains.

### 5.3 CICIoT2023 Feature-Count Discrepancy

The public CICIoT2023 description may expose 47 flow features, while the current DATP pipeline uses 39. Gate 0 must document:
- Which eight features, if any, were removed.
- Whether removal is deterministic and scientifically justified.
- Whether the same preprocessing is used for B-a and any conditional B-b partition.
- Whether the config feature count matches the processed schema.

If unresolved, all new CICIoT2023 B-b training is blocked.

### 5.4 CICIoT2023 B-b Feasibility

Gate 0 must inspect raw and processed CICIoT2023 files for reliable client identifiers:
- MAC address.
- Source/destination device identifier.
- Device group.
- Capture-source identifier.
- File-only pseudo-client indicator.

It must also define:
- Client role.
- Packet direction rule.
- Deduplication rule.
- Leakage check: a benign flow attributed to client A in train must not be re-attributed to client B in test.
- Minimum benign calibration samples: `n_cal ≥ 100`.
- Minimum client count: at least 8 eligible clients.
- Attack coverage summary per candidate client.

Exactly one outcome is allowed:

| Outcome | Meaning | Downstream Rule |
|---|---|---|
| `B_B_FEASIBLE_MAC` | Reliable MAC/victim-device clients; ≥ 8 eligible clients. | Regime B-b may run and must be labeled MAC-based. |
| `B_B_FEASIBLE_GROUP_ONLY` | Only group labels are reliable; ≥ 8 eligible groups. | Regime B-b may run and must be labeled group-based, not device-MAC. |
| `B_B_REJECTED_FILES_ONLY` | Only file pseudo-clients exist. | Suppress B-b; report B-a only. |
| `B_B_REJECTED_METADATA_INSUFFICIENT` | No reliable client identifier. | Suppress B-b. |
| `B_B_REJECTED_TOO_FEW_ELIGIBLE_CLIENTS` | Identifier exists but too few eligible clients. | Suppress B-b. |
| `B_B_BLOCKED_UNVERIFIED` | Audit not completed. | No B-b coding or claim. |

### 5.5 Edge-IIoTset Regime D Feasibility

Edge-IIoTset is not present in the repository. Gate 0 must verify before any Regime D work:
- Download source and dataset version.
- Raw file list and checksums.
- Feature schema and final feature count.
- Timestamp availability and parseability.
- Candidate client identifiers.
- Candidate client counts under device, group, application, and file partitions.
- Per-client benign calibration counts.
- Per-client attack test counts.
- Eligibility coverage.
- Whether natural physical-device clients are possible.

Eligibility rules:
- `n_cal ≥ 100` per eligible client.
- Device-client Regime D requires `K ≥ 6` eligible physical-device clients.
- Group-client Regime D may be used only as group-partitioned external validation.
- Eligibility coverage target: ≥ 90% of candidate clients under the chosen partition.

Allowed outcomes:
| Outcome | Meaning | Downstream Rule |
|---|---|---|
| `EDGE_FEASIBLE_DEVICE_CLIENTS` | Device/client identifiers support K ≥ 6 and coverage target. | Regime D physical-device validation may run. |
| `EDGE_FEASIBLE_GROUP_CLIENTS_ONLY` | Only group clients are feasible. | Regime D group-partitioned validation may run, explicitly labeled as such. |
| `EDGE_REJECTED_METADATA_INSUFFICIENT` | No usable client identifier. | Suppress Regime D. |
| `EDGE_REJECTED_TOO_FEW_ELIGIBLE_CLIENTS` | Too few eligible clients. | Suppress Regime D. |
| `EDGE_BLOCKED_DATA_UNAVAILABLE` | Dataset unavailable or integrity failure. | Suppress Regime D until resolved. |

B3 suppression rule:
- If Regime D is group-partitioned, B3 is automatically suppressed because the client and group levels are not meaningfully separate.

Dataset-specific AE rule:
- A separate AE is trained per dataset.
- The Edge-IIoTset AE uses the same hyperparameter specification as N-BaIoT but with input dimension matched to Edge-IIoTset's feature count.
- The fixed-encoder rule applies within each dataset/regime ladder, not across datasets.

### 5.6 Regime C Completeness

Gate 0 must verify that Regime C has complete and reproducible B1, B2, and B4 artifacts for:
- `α ∈ {0.1, 0.3, 0.5, 1.0, 10.0, IID}`
- Seeds 0–4 initially.
- Seeds 5–9 only if the seed extension runs.

If `α = 10.0` or IID is missing or non-reproducible, Regime C severity claims are suppressed or reported as partial with explicit missing-cell notes.

### 5.7 Seed-Extension Status

Allowed statuses:
| Status | Meaning |
|---|---|
| `SEEDS_ALREADY_10` | Ten seeds already exist and pass verification. |
| `SEEDS_5_ONLY_EXTENSION_REQUIRED` | Only seeds 0–4 exist; journal 10-seed claim requires new training. |
| `SEEDS_BLOCKED_MISSING_RESULTS` | Even the 5-seed set is incomplete. |
| `SEEDS_CONFLICT_UNRESOLVED` | Seed artifacts conflict across sources. |

Current repository state: `SEEDS_5_ONLY_EXTENSION_REQUIRED`.

If 10-seed results are produced, they supersede the 5-seed results regardless of favorability.

### 5.8 Citation and Policy Verification

Gate 0 must maintain the following source statuses inside this file or a result-freeze note. Pending sources cannot support critical claims.

| Source / Fact | Current Status | Rule |
|---|---|---|
| Laridi et al. 2024 Scientific Reports | Verified with correction: original method uses normal and anomalous validation summaries. | `B-FedStatsBenign` must be described as benign-only adaptation, not faithful reproduction. |
| Edge-IIoTset Ferrag et al. 2022 | Verified as dataset source; checksums/version pending until download. | Regime D blocked until local dataset audit passes. |
| CICIoT2023 Neto et al. 2023 | Verified dataset description; usable client metadata not guaranteed. | B-b blocked until metadata audit passes. |
| Computer Networks extension policy | Partially verified; no fixed percentage rule found. | 40% is internal conservative benchmark, not venue requirement. |
| FGCS 40% guidance | Pending direct fresh verification. | Mention only as conservative Elsevier-family alignment, not as a Computer Networks rule. |
| Computers & Security AI/ML moratorium | Verified with correction: broad AI/ML security/privacy moratorium, including FL. | Exclude as target venue. |
| Lu et al. ICML 2023 | Verified; primary B2-conf anchor. | Use as primary conformal anchor. |
| Humbert et al. ICML 2023 | Co-anchor for one-shot/federated conformal framing. | Verify bibliographic details before submission. |
| FedProx Li et al. 2020 | Verified. | FedProx stress-test citation. |
| Ditto Li et al. 2021 | Verified. | Ditto only if true Ditto is implemented. |
| Rey et al. 2022 Computer Networks | Pending fresh verification. | Use only soft venue-fit framing until verified. |
| Belarbi et al. 2023 | Pending. | Related work only, not critical claim. |
| Sáez-de-Cámara et al. 2023 | Pending. | Related work only, not critical claim. |

An unverified partition precedent previously cited in drafts is removed and must not appear in any canonical planning file or manuscript update.

---

## 6. Protocol Locks Before Implementation

These locks are written before coding and before result inspection.

### 6.1 `B-FedStatsBenign` Protocol Lock

`B-FedStatsBenign` is the only planned Laridi-style comparator in this plan.

Required lock:
- Benign-only calibration summaries.
- No attack labels.
- No raw score sharing.
- Client summaries: count, mean, variance.
- Sample-count-weighted global mean.
- Full pooled variance with between-client mean-shift term.
- Threshold grid: `τ(k) = μ_global + k · σ_global`, `k ∈ {0.00, 0.01, ..., 5.00}`.
- Primary operating point: matched benign exceedance, `k* = argmin_k |exceedance(k) − 0.05|`.
- Tie-break: choose larger k.
- Fixed-k variants, if used, go to supplement only.
- Outputs: achieved exceedance, absolute deviation from 5%, between/within variance terms, between_ratio, CV(FPR), Macro-F1, coverage.
- No post-hoc tuning.

Mandatory wording:
> `B-FedStatsBenign` is a DATP-compatible benign-only federated summary-statistics comparator. It does not reproduce attack-labeled calibration access and therefore does not resolve the novelty question under anomaly-labeled Laridi-style assumptions.

### 6.2 `B-LaridiFaithful` Scope Decision

`B-LaridiFaithful` is out of current scope because it requires anomaly-labeled calibration summaries, which violates the benign-only threshold-calibration assumption of DATP.

Consequences:
- No `B-LaridiFaithful` task is implemented.
- No claim says DATP dominates the original attack-labeled method.
- Related work must state that the calibration assumptions differ.
- If a reviewer requests this comparison, the response is that it is a relaxed-supervision comparator outside the paper's controlled benign-only calibration contract.

### 6.3 FedProx Lock

- µ grid: `{0.0, 0.001, 0.01, 0.1, 1.0}`.
- µ=0.0 is a FedAvg equivalence sanity check.
- Local epoch count E is locked equal to FedAvg E.
- If current FedAvg uses E=1, the paper must state that FedProx is evaluated conservatively and its proximal term may have limited effect at one local epoch.
- µ=0.0 FedProx must match FedAvg within scalar metric tolerance ≤ 0.01 and exact eligibility/count identity. Any larger divergence blocks FedProx reporting until investigated.
- No additional µ is added after results are inspected.
- Convergence failure is reported; no grid search rescue is allowed.

### 6.4 Ditto / `LocalHead-PersonalizedAE` Lock

Before training, choose one:
- True Ditto, if the algorithm is implemented faithfully.
- `LocalHead-PersonalizedAE`, if the implementation is only a frozen/shared encoder with local heads.

Absorption ratio:
- `Δ_FedAvg = CV(FPR)[FedAvg+B1] − CV(FPR)[FedAvg+B2]`
- `Δ_personalized = CV(FPR)[Personalized+B1] − CV(FPR)[Personalized+B2]`
- Strong retention: `Δ_personalized / Δ_FedAvg ≥ 0.75`
- Partial absorption: `[0.25, 0.75)`
- Near-full absorption: `< 0.25`

The selected interpretation rule is applied without adjustment after results are seen.

### 6.5 Temporal Recalibration Lock

Allowed outcomes:
- `TEMPORAL_FEASIBLE`
- `TEMPORAL_REJECTED_NO_TIMESTAMP`
- `TEMPORAL_REJECTED_LOW_COVERAGE`
- `TEMPORAL_REJECTED_INSUFFICIENT_ATTACKS`
- `TEMPORAL_REJECTED_NONCHRONOLOGICAL`

Required feasibility checks:
- Timestamp exists.
- Timestamp parses.
- Timestamp is not constant.
- Enough early benign calibration samples.
- Enough late benign test samples.
- Enough late attack test samples.
- Per-client coverage is adequate.
- Chronological order is meaningful.

Allowed interpretations:
- Helps: one-shot recalibration recovers a pre-specified meaningful share of CV(FPR) loss.
- Neutral: no meaningful drift appears in the available chronological window.
- Hurts/insufficient: recalibration does not recover performance or data do not support temporal analysis.

No streaming detector or new temporal method is added retroactively.

### 6.6 B4 Canonical K Lock

- Main-paper B4 uses canonical `K = 3`.
- Other K values are sensitivity/supplement only.
- B4 is described as a distributional fingerprint approximation, not a privacy method.

---

## 7. Gate 0 Exit Checklist

Gate 0 is complete only when every row is resolved:

| Item | Required Status Before Coding |
|---|---|
| Score reuse verification | PASS for consumed cells or affected tasks suppressed. |
| CICIoT2023 canonical root | PASS. |
| CICIoT2023 47-vs-39 feature explanation | PASS before B-b. |
| CICIoT2023 B-b feasibility | One allowed outcome assigned. |
| Edge-IIoTset availability and feasibility | One allowed outcome assigned before Regime D. |
| Regime C completeness | PASS or partial with suppression note. |
| B3 Regime A reproduction | PASS. |
| Seed-extension status | One allowed status assigned. |
| `B-FedStatsBenign` protocol | Locked. |
| `B-LaridiFaithful` scope exclusion | Locked. |
| FedProx grid and E rule | Locked. |
| Ditto vs LocalHead decision | Locked before stress-test training. |
| Temporal feasibility rule | Locked. |
| Citation verification | Critical sources verified or marked pending with safe wording. |
| Lineage rule | Adopted for every reported result. |

No coding, experiment, dataset addition, result modification, or manuscript edit begins before the relevant Gate 0 rows are closed.
