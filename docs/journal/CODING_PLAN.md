# CODING PLAN

Documentation-only planning artifact. This file describes future implementation work for the DATP journal extension. It does not create code, configs, notebooks, datasets, results, or manuscript edits.

All tasks depend on `PRE_CODING_PLAN.md`. The plan is additive: preserve the existing DATP implementation and add only the minimum code needed for the journal extension.

---

## 1. Coding Scope

Hard rules:
- No whole-repo rewrite.
- No broad cleanup.
- No replacement of locked B0–B4 implementations.
- No new dataset beyond N-BaIoT, CICIoT2023, and conditional Edge-IIoTset.
- No FedBN or BatchNorm-bearing encoder variant.
- No poisoning, backdoor, evasion, DP, secure aggregation, hardware, or concept-drift implementation.
- No Group B stored-score analysis may invoke FL training.
- No stress test may be wired into the core B1–B4 causal ladder.
- All scientific parameters flow from config.
- All processed artifacts remain Parquet.
- All outputs preserve the existing stage boundary: prepare → score → threshold/result → report.

Canonical new labels:
- `τ-shrink`, not a B3 variant.
- `B-FedStatsBenign`, not a numbered baseline.
- `B2-conf`, not a Plassier-primary method.
- `LocalHead-PersonalizedAE`, not Ditto, unless the implementation is truly Ditto.
- Regime D, not any prime label.

---

## 2. Existing Code Reuse Map

| Area | Existing Path(s) | Reuse Rule |
|---|---|---|
| Score loading | `src/datp/baselines/common/scoring.py`, `src/datp/evaluation/score_loading.py` | Reuse read-only for Group B. |
| Thresholds | `src/datp/baselines/common/thresholds.py` | Preserve locked B1/B2 formulas; add variants separately. |
| Baselines | `src/datp/baselines/main/{b0,b1,b2,b3,b4}.py` | Do not rewrite; new comparators live separately. |
| Training | `src/datp/training/fl/` | Preserve FedAvg path; add FedProx/Ditto/LocalHead only behind stress-test paths. |
| Eligibility | `src/datp/baselines/common/eligibility.py` | Reuse unchanged: `n_cal ≥ 100` and Calibration-Pending fallback. |
| Metrics | `src/datp/evaluation/metrics.py`, `confusion.py`, `metric_keys.py` | Reuse canonical metric calculations. |
| Statistics | `src/datp/statistics/*` | Reuse canonical CV, bootstrap, divergence, effect size, Wilcoxon, Spearman. |
| Reporting | `src/datp/reporting/*` | Add journal tables/figures through existing builders/templates. |
| Config | `src/datp/conf/`, `src/datp/config/*` | Extend schema; no inline defaults. |
| Dataset specs | `src/datp/data/datasets/*` | Add Edge-IIoTset only if feasible; do not silently change N-BaIoT/CICIoT2023. |
| CLI/sweep | `src/datp/cli/*`, `src/datp/sweep/*` | Add commands only after implementation exists; do not invent non-working commands. |
| Artifact utilities | `src/datp/artifacts/*` | Reuse canonical paths, constants, markers, atomic writes. |

---

## 3. Group A — Gate 0 Verification Utilities

Group A produces verification artifacts only. It produces no scientific claims.

| Task | Purpose | Input | Output | Required Tests | Retraining |
|---|---|---|---|---|---|
| A1 Artifact inventory | Enumerate existing results, scores, checkpoints, configs, logs, metrics index, tables, figures. | `outputs/`, `results/`, `paper/figures`, `paper/tables` | Inventory CSV/JSON. | Directory/index agreement. | No |
| A2 Score manifest verifier | Validate score parquet schema, manifests, checkpoint hashes, client IDs, splits. | `outputs/scores/*` | Per-cell verification report. | Hash, schema, split, ID tests. | No |
| A3 Metric reproducer | Recompute B1/B2/B4 and Regime A B3 from stored scores. | Stored score parquets + canonical configs. | `recomputed_metrics.json`. | Numeric tolerance tests. | No |
| A4 Reuse verdict checker | Emit `VERIFIED_REUSE_SAFE` or `REUSE_BLOCKED_RERUN_REQUIRED`. | A2/A3 outputs + references. | Cell verdict table. | Verdict logic tests. | No |
| A5 CICIoT2023 root resolver | Choose canonical processed root. | Both processed roots + specs/manifests. | Canonical-root decision. | Non-canonical root cannot be loaded. | No |
| A6 CICIoT2023 feature audit | Explain 47-vs-39 feature discrepancy. | Raw/processed CICIoT2023 + `spec.py`. | Feature-drop report. | Config/schema match. | No |
| A7 CICIoT2023 B-b scanner | Detect MAC/group/client metadata, counts, leakage risks. | Raw/processed CICIoT2023. | One B-b feasibility outcome. | Outcome enum test; leakage test. | No |
| A8 Edge-IIoTset feasibility scanner | Verify dataset files, schema, client identifiers, K, timestamps. | Raw Edge-IIoTset, if present. | One Regime D feasibility outcome. | Schema, counts, checksum tests. | No |
| A9 Regime C completeness verifier | Verify all α/IID cells and metrics. | Regime C scores/results. | Completeness table. | Missing-cell detection. | No |
| A10 Timestamp feasibility scanner | Verify chronological split feasibility. | Edge-IIoTset and conditional B-b. | One temporal feasibility outcome. | Timestamp parse/order/coverage tests. | No |
| A11 Citation verification logger | Record critical source status. | Source list from PRE plan. | Verification note. | Critical pending source cannot support critical claim. | No |
| A12 Lineage checker | Verify raw→processed→config→checkpoint→scores→metrics→tables/figures chain. | Existing manifests and outputs. | Lineage verdict per cell. | Missing hash blocks cell. | No |

Group A must complete before Groups B–F consume the affected artifacts.

---

## 4. Group B — Stored-Score Analyses

Runs only on cells with `VERIFIED_REUSE_SAFE`. No FL training is allowed.

| Task | Purpose | Input | Output | Validation | Gate |
|---|---|---|---|---|---|
| B1 q-sensitivity | Evaluate B1/B2/B4 at `q ∈ {0.90, 0.95, 0.975, 0.99}`. | Verified Regime A scores; conditional Regime C/D scores. | Per-q table + heatmap. | q=0.95 reproduces reference. | Gate 1 |
| B2 calibration-size sweep | Subsample benign calibration scores at `n_cal ∈ {50, 100, 250, 500, 1000, 5000}`. | Verified scores. | Sensitivity table/curve. | Deterministic subsampling. | Gate 1 |
| B3 `τ-shrink` | `τ_k(λ)=λτ_k+(1−λ)τ_global`, `λ ∈ {0, 0.25, 0.5, 0.75, 1}`. | Verified scores. | λ table + curve. | λ=0 reproduces B1; λ=1 reproduces B2. | Gate 1 |
| B4 `B2-conf` | Per-client conformal threshold variant with `α = 1 − q`; default q=0.95 → α=0.05. | Verified scores. | Empirical coverage table + diagnostic figure. | Coverage failure reported, not hidden. | Gate 1 |
| `B-FedStatsBenign` | Benign-only federated summary-statistics comparator. | Verified benign calibration scores. | Comparator table + between_ratio diagnostic. | Protocol lock identity check; no attack labels. | Gate 1 |
| B6 B4 feature ablation | Evaluate B4 fingerprint subsets and full 4-feature fingerprint. | Verified score-derived fingerprints. | Ablation table + contingency figure. | Full 4-feature version reproduces B4. | Gate 1 |
| B7 JS divergence vs DATP benefit | Relate distribution divergence to per-client B1−B2 FPR gain. | Verified distributions and metrics. | Scatter + ρ/R² table. | Uses canonical divergence implementation. | Gate 1 |
| B8 threshold-shift vs ΔFPR/ΔTPR | Explain per-client effect of threshold movement. | Verified scores/metrics. | Scatter + per-client table. | All Regime A devices included. | Gate 1 |
| B9 alert-burden table | Translate FPR to alerts/device/day or normalized hypothetical alert burden. | Verified FPR + traffic/timestamp source. | Alert table. | Caption declares source and limitations. | Gate 1 |
| B10 B3 preservation | Reproduce Regime A B3 and include in journal artifacts. | Verified Regime A scores/results. | B3 row/table. | Reproduces B3 within tolerance. | Gate 1 |
| B11 Regime C severity analysis | Analyze CV(FPR) gap over α values. | Verified Regime C cells. | Severity table + figure. | Missing α/IID cells trigger suppression note. | Gate 1 |
| B12 per-client CDF/failure-mode analysis | Overlay benign/attack CDFs with B1/B2/B4 thresholds. | Verified Regime A scores. | CDF figure + failure-mode table. | Use canonical dataset device names; no nickname-only labels. | Gate 1 |

---

## 5. Group C — Edge-IIoTset / Regime D Support

Runs only under `EDGE_FEASIBLE_DEVICE_CLIENTS` or `EDGE_FEASIBLE_GROUP_CLIENTS_ONLY`.

| Task | Purpose | Input | Output | Tests | Retraining |
|---|---|---|---|---|---|
| C1 Dataset spec | Add Edge-IIoTset dataset spec with locked feature schema. | Verified raw files. | `edge_iiotset/spec.py` equivalent. | Feature-count and schema tests. | No |
| C2 Preprocessing | Produce deterministic Parquet train/cal/test splits. | Raw Edge-IIoTset. | `data/processed/edge_iiotset/...` | Determinism, manifest, checksum tests. | No |
| C3 Client partition | Create device or group clients per Gate 0 outcome. | Metadata audit. | Partition manifest. | K, eligibility, no file-only pseudo-client leakage. | No |
| C4 Shared AE training/scoring | Train one shared AE per `(Regime D, seed)` and score clients. | Processed Regime D split. | Checkpoints + scores + manifests. | Determinism, convergence, config validation. | Yes |
| C5 Threshold evaluation | Apply B1/B2/B4; B3 only if valid and non-circular group mapping exists. | Regime D scores. | Metrics and table rows. | Canonical baseline reuse. | No |
| C6 Stored-score variants on Regime D | Apply q-sensitivity, `τ-shrink`, `B2-conf`, `B-FedStatsBenign` if relevant. | Regime D verified scores. | Supporting tables/figures. | Same Group B validation. | No |

B3 on Regime D:
- Suppressed if Regime D is group-partitioned.
- Suppressed if family/group labels are identical to client labels.
- Allowed only if a scientifically distinct grouping is locked before implementation.

---

## 6. Group D — Conditional CICIoT2023 B-b Support

Runs only under `B_B_FEASIBLE_MAC` or `B_B_FEASIBLE_GROUP_ONLY`.

| Task | Purpose | Input | Output | Tests | Retraining |
|---|---|---|---|---|---|
| D1 Metadata extraction | Extract verified MAC/group/client fields. | Canonical CICIoT2023 root + raw metadata. | Metadata table. | Field presence, uniqueness, leakage tests. | No |
| D2 Client definition | Define B-b clients from verified outcome. | D1 output. | `clients.json` / manifest. | Determinism and eligibility tests. | No |
| D3 Partition generation | Build train/cal/test_benign/test_attack per client. | D1/D2 output. | Processed B-b split. | Split and leakage validation. | No |
| D4 Shared AE training/scoring | Train one shared AE per `(Regime B-b, seed)`. | B-b processed split. | Checkpoints + scores + manifests. | Determinism, convergence, config validation. | Yes |
| D5 Threshold evaluation | Apply B1/B2/B4; B3 only if a valid non-circular group mapping exists. | B-b scores. | Metrics and table rows. | Canonical baseline reuse. | No |
| D6 B-b variants | Apply selected stored-score analyses after scores are verified. | B-b scores. | Supporting outputs. | Same Group B validation. | No |

If B-b outcome is rejected or blocked, all Group D tasks are suppressed and the paper reports Regime B-a only.

---

## 7. Group E — Stress-Test Support

Stress tests are supportive only. They require retraining and are never part of the core B1–B4 ladder.

| Task | Purpose | Input | Output | Tests | Retraining |
|---|---|---|---|---|---|
| E1 FedProx | Evaluate whether B1→B2 gain survives FedProx-trained scores. | N-BaIoT and conditional Regime D partitions. | FedProx checkpoints, scores, metrics. | µ=0.0 equivalence, determinism, E-lock, convergence status. | Yes |
| E2 Ditto or `LocalHead-PersonalizedAE` | Evaluate whether model personalization absorbs threshold personalization. | N-BaIoT and conditional Regime D partitions. | Personalized checkpoints, scores, metrics, absorption ratios. | Naming, model-state separation, determinism, µ-grid completeness. | Yes |
| E3 Threshold grid on stress-test scores | Apply B1/B2/B4 to stress-test scores. | E1/E2 scores. | Stress-test × threshold table. | Canonical threshold reuse. | No |
| E4 `B-FedStatsBenign` on stress-test scores | Apply benign-summary comparator if needed for reporting. | E1/E2 scores. | Comparator stress-test rows. | No attack labels; same lock as Group B. | No |
| E5 Absorption reporting | Apply pre-specified retention/absorption rules. | E1–E4 metrics. | Absorption-category table. | Thresholds applied exactly; no post-hoc rewording. | No |

FedProx specifics:
- µ grid: `{0.0, 0.001, 0.01, 0.1, 1.0}`.
- E equal to FedAvg E.
- If E=1, report as conservative FedProx stress test.
- If all µ values fail convergence on a dataset, report failure and stop.

Ditto/LocalHead specifics:
- Main table uses µ=0.01 unless unavailable by convergence failure.
- Other µ values go to supplement.
- Local-head variant is never labeled Ditto.

---

## 8. Group F — Temporal Recalibration Probe

Runs only under `TEMPORAL_FEASIBLE`.

| Task | Purpose | Input | Output | Tests | Retraining |
|---|---|---|---|---|---|
| F1 Chronological split | Create per-client early/late split. | Timestamp-verified data. | Temporal split manifest. | Timestamp order and coverage tests. | No |
| F2 Initial training/scoring | Train AE on early window and score. | Early split. | Initial scores and thresholds. | Determinism/convergence. | Yes |
| F3 Frozen-threshold evaluation | Apply early thresholds to later window. | F2 thresholds + late data. | Frozen-threshold metrics. | Canonical metrics. | No |
| F4 One-shot recalibration | Recompute thresholds at boundary and re-evaluate. | F2/F3 scores. | Recalibrated metrics + recovery ratio. | Recovery-ratio tests. | No |
| F5 Temporal reporting | Summarize helps/neutral/hurts/infeasible outcome. | F2–F4 outputs. | Temporal table/figure. | Pre-specified wording. | No |

If temporal feasibility is rejected, Group F is suppressed with a one-line reason.

---

## 9. Validation Requirements

The implementation must add tests/checks for:

- Locked B1/B2/B3/B4 invariance.
- Group B no-training guard.
- Score-reuse verification and tolerance.
- CICIoT2023 canonical-root assertion.
- CICIoT2023 feature-count audit.
- CICIoT2023 leakage checks.
- Edge-IIoTset schema, checksum, feature count, K, eligibility, and timestamp checks.
- `B-FedStatsBenign` protocol identity and no-attack-label rule.
- `τ-shrink` endpoint equivalence to B1/B2.
- `B2-conf` α/q alignment.
- B4 canonical K=3 main rendering.
- FedProx µ=0.0 equivalence to FedAvg.
- FedProx E equality with FedAvg E.
- Ditto vs LocalHead naming and state separation.
- Temporal feasibility outcome enum.
- Artifact lineage for every reported result.
- Stress-test claim-scope guard.
- No-extra-dataset guard.
- No-FedBN guard.
- Result schema validation.
- Same-seed determinism.

---

## 10. Coding Stop Conditions

Stop and report instead of improvising if:

- Gate 0 verification is incomplete for the task.
- A reused score cell is `REUSE_BLOCKED_RERUN_REQUIRED`.
- CICIoT2023 B-b metadata is rejected or blocked.
- Edge-IIoTset is unavailable, metadata-insufficient, or too small.
- Regime C α/IID artifacts are incomplete and no suppression note exists.
- A task requires changing the core encoder, FedAvg protocol, B1–B4 formulas, seed scheme, or score layout.
- A proposed change adds a new dataset beyond the allowed set.
- A proposed change adds FedBN or BatchNorm.
- A proposed change turns a stress test into the core ladder.
- A proposed change tunes a locked protocol after results are inspected.
- A proposed command is documented before it actually exists.
- A manuscript edit is attempted before result freeze.
