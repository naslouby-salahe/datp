# Ticket Progress

## Purpose

This file tracks what is done, what is missing, what is blocked, and what must happen next.

Before starting any ticket, the executing agent must check this file and verify previous-ticket completion.

## Current Rule

Before starting ticket `TXX`, check every previous ticket.

If any previous ticket is incomplete and not correctly blocked or skipped with reason, return to that ticket first.

## Current Status Summary

| Field | Value |
|---|---|
| Total tickets | 28 |
| Current ticket | T17 |
| Last completed ticket | T16 |
| NOT_STARTED tickets | T17–T23, T25, T26–T28 (11 tickets) |
| BLOCKED_HUMAN tickets | None (H01 and H02 both CLOSED) |
| SKIPPED_WITH_REASON tickets | T24 (CICIoT2023 B-b is infeasible on the currently available CSV artifact; T23 will write the rejection manifest) |
| Technical-blocked tickets | None |
| Scientific-blocked tickets | None |
| Next recommended action | **MANUAL APPROVAL REQUIRED** before T17 — see `docs/tickets/audits/T17_T20_readiness_boundary_report.md` |

## Progress Log

| Entry | Ticket | Old Status | New Status | Reason | Next Action |
|---|---|---|---|---|---|
| 025 | T16-STABILIZE | — | COMPLETED | **Refactor/Stabilization (2026-05-24):** Enum ownership corrected: `AuditStatus`, `WarningCode`, `ReuseVerdict`, `DemotionDecision` moved from `core/enums.py` → `audit/enums.py`. 29 import sites updated. Manual glob in `reporting/build.py` replaced with canonical `ExperimentLocator` path. Dead `ArtifactKind` duplicate removed. `BaselineRole` re-added to core. ruff: 0 errors. pyright: 0 errors. Unit tests: 784 passed, 9 skipped, 1 pre-existing doc test failure. No T17+ work started. No scientific drift. Audit: `docs/tickets/audits/T16_refactor_clean_code_audit.md`. | Proceed with T17 when approved. |

| Entry | Ticket | Old Status | New Status | Reason | Next Action |
|---|---|---|---|---|---|
| 024 | T16 | NOT_STARTED | DONE | **Implementation (2026-05-24):** Per-client CDF/failure-mode analysis. `per_client_cdf.py` with empirical CDF + B1/B2/B4 threshold overlay. Failure-mode classification (HIGH_FPR_B1, LOW_TPR_B1, HIGH_FPR_B2, LOW_TPR_B2, NORMAL). All 9 Regime A devices. Canonical device names. CDF grid figure + failure-mode table. 12 tests pass. ruff: 0 errors. pyright: 0 errors. No retraining. Audit: `docs/tickets/audits/T16_actual_code_audit.md`. Boundary report: `docs/tickets/audits/T17_T20_readiness_boundary_report.md`. | **STOP — MANUAL APPROVAL REQUIRED before T17.** |

| Entry | Ticket | Old Status | New Status | Reason | Next Action |
|---|---|---|---|---|---|
| 022 | T01-T10 | — | AUDITED | **Actual Code Audit (2026-05-24):** orchestrator-agent verified ALL 10 tickets against actual source code, not docs. 100/100 tests pass. ruff: 0 errors. pyright: 0 errors. 12/12 scientific invariants preserved. 12/12 no-drift checks clean. 9 code quality issues found (7 fixed: dead code, inline imports, dangling comments, comment clutter). All acceptance criteria satisfied per ticket. Audit file: `docs/tickets/audits/T01_T10_actual_code_audit.md`. | Proceed with T11. |

| Entry | Ticket | Old Status | New Status | Reason | Next Action |
|---|---|---|---|---|---|
| 001 | N/A | N/A | N/A | Ticket system initialized. | Run ticket generation. |
| 002 | ALL | N/A | NOT_STARTED / BLOCKED_HUMAN | Ticket generation complete (28 tickets). 5 blocked on human interventions. | Start T01. |
| 003 | H01 | OPEN | CLOSED | Edge-IIoTset downloaded from Kaggle (`mohamedamineferrag/edgeiiotset-cyber-security-dataset-of-iot-iiot`, 11 GB, 26 CSVs + matching PCAPs + 2 selected ML/DL aggregates) to `data/raw/Edge-IIoTset/`. Schema audit (63 columns): `frame.time` timestamps populated; `ip.src_host`/`ip.dst_host` client identifiers populated; `Attack_label`/`Attack_type` labels populated; protocol fields TCP/UDP/HTTP/DNS/MQTT/Modbus/ARP/ICMP present. T21/T22/T25(Edge-IIoTset) FEASIBLE. | Proceed with T01 → T21. |
| 004 | H02 | OPEN | CLOSED | Existing CICIoT2023 raw CSVs verified in-place (inspection only, no files modified). Found 372 per-attack CSVs across 35 class folders in `data/raw/CIC_IOT_Dataset2023/CSV/CSV/` + 63 merged CSVs in `data/raw/CIC_IOT_Dataset2023/CSV/MERGED_CSV/` (17 GB total). Schema audit: 39 numeric features + `Label` (merged only). **No** MAC, device, IP, capture-source, or timestamp columns. B-b INFEASIBLE; temporal probe on CICIoT2023 INFEASIBLE. | T23 to formally assign `B_B_REJECTED_NO_METADATA`; T24 to be `SKIPPED_WITH_REASON` after T23 executes. |
| 005 | T21 | BLOCKED_HUMAN | NOT_STARTED | H01 CLOSED. Edge-IIoTset raw files available with verified schema for preprocessing. | Schedule after T01 completes. |
| 006 | T22 | BLOCKED_HUMAN | NOT_STARTED | H01 CLOSED. Dependency reduced to T21 (ticket dependency, not human). | Schedule after T21 completes. |
| 007 | T23 | BLOCKED_HUMAN | NOT_STARTED | H02 CLOSED. Ticket implements `B_B_REJECTED_NO_METADATA` formally: defines the outcome enum, records schema evidence, writes the rejection manifest, and adds the downstream B-b training guard. No partition is built. | Execute after T01 to formalize the rejection enum, manifest, and guard. |
| 008 | T24 | BLOCKED_HUMAN | SKIPPED_WITH_REASON | CICIoT2023 B-b training/evaluation skipped because the verified raw CSV schema contains no MAC, device ID, client ID, capture-source identifier, source/destination IP, or other usable client partition metadata. H02 is closed; the branch is rejected by feasibility audit, not blocked by missing user action. CICIoT2023 B-b is infeasible on the currently available CSV artifact. No CICIoT2023 PCAP branch added now. | None — ticket is terminal. CICIoT2023 reported under Regime B-a only. |
| 009 | T25 | BLOCKED_HUMAN | NOT_STARTED | H01 + H02 CLOSED. Edge-IIoTset path FEASIBLE (`frame.time` timestamps populated); CICIoT2023 path rejected with `TEMPORAL_REJECTED_NO_TIMESTAMPS`. Ticket proceeds on Edge-IIoTset only. | Schedule after T21 completes. |
| 010 | T01 | NOT_STARTED | DONE | Diagnostic CLI `--data-root` default changed from `Path("data")` to `Path(".")` via `DEFAULT_BASE_DIR` constant in `data/paths.py`. Sweep CLI aligned to same constant. Added `assert_no_root_conflict(base_dir, dataset)` helper that compares manifests at `data/processed/<slug>/` vs `data/data/processed/<slug>/` and raises only when both exist with diverging dataset/file_hashes/metadata. Wired into `ensure_prepared_data` (sweep startup) and into all three diagnostic CLI entry points before banner. Added `tests/unit/data/test_paths_conflict.py` (6 cases: default constant, single canonical, single legacy, agreeing dual manifests, diverging dual manifests, neither exists). `make test-unit` targeted at `tests/unit/data/ tests/unit/cli/` → 131 passed, 9 skipped. `make gate0` → 50 passed + G0-1 PASS. | Start T02 (Score Manifest Verifier). |
| 011 | T02 | NOT_STARTED | DONE | Implemented `src/datp/audit/score_manifest.py` with `verify_score_cell` and `verify_all_score_cells`. Added `ScoreCheckCode` enum (18 atomic checks), `ScoreCheckResult` / `ScoreCellVerification` pydantic schemas (extra='forbid', frozen=True). Extended `src/datp/audit/discovery.py` with `ScoreCellLocation` and `iter_score_cells(base_dir)`. Added `SCORE_CELL_VERIFICATION_JSON` / `SCORE_CELL_VERIFICATION_INDEX_JSON` to `audit/constants.py`. Reused `validate_score_artifact` (Parquet schema), `dataset_spec` / `dataset_for_regime` (client identity), `prepared_root_for_regime` (partition root), `ExperimentLocator` (canonical checkpoint), `AuditStatus` / `ScoringStage` / `SCORING_STAGES`, `MODEL_CHECKPOINT` / `SCORING_MANIFEST_FILE` / `SCORING_SENTINEL`, `hash_file`. Tests: `tests/unit/audit/test_score_manifest_verifier.py` (16 cases). `make test-unit`: 673 passed, 9 skipped, 1 pre-existing failure unrelated to T02 (`test_baseline_role_docs_are_current`, reproduces on clean tree). Live run on `outputs/scores/{a,b,c}/seed_*`: **40 / 40 cells PASS** (5 Regime A + 5 Regime B + 30 Regime C). | Start T03 (Metric Reproducer). |
| 012 | T03 | NOT_STARTED | DONE | Implemented `src/datp/audit/metric_reproducer.py` with `reproduce_cell_metrics(cell_dir, base_dir, *, config=None)` and `reproduce_all_cells(base_dir, *, config=None, write_reports=False)`. Added `MetricCheckCode` enum (9 atomic checks), `MetricCheckResult` / `BaselineReproductionResult` / `CellReproductionResult` pydantic schemas (extra='forbid', frozen=True). Added `SCALAR_METRIC_TOLERANCE=0.01`, `COVERAGE_RATIO_TOLERANCE=0.001`, `RECOMPUTED_METRICS_JSON`, `RECOMPUTED_METRICS_INDEX_JSON` to `audit/constants.py`. Reused canonical functions: `derive_threshold` (`baselines/common/thresholds.py`), `compute_client_metrics` + `build_evaluation_result` (`evaluation/metrics.py`), `ScoreProvider` + `read_score_column` (`evaluation/score_loading.py`), `iter_score_cells` + `ScoreCellLocation` (`audit/discovery.py`), `ExperimentLocator.for_main` (`artifacts/paths.py`), `compose_config` (`config/compose.py`), `Baseline`/`Regime`/`AuditStatus`/`ScoringStage` enums. Stored-scalar lookup falls back to `aggregate_metrics` for legacy fields (`max_min_fpr_gap`). Tests: `tests/unit/audit/test_metric_reproducer.py` (12 cases — pass on match, scalar breach FAIL, eligible-count exact mismatch FAIL, eligible-ID set mismatch FAIL, confusion exact mismatch FAIL, coverage just-inside PASS, coverage just-outside FAIL, missing one baseline → PARTIAL with missing_baselines populated, missing all baselines reports cleanly, missing cal directory raises, multi-cell reproduce_all writes index, tolerance constants pinned to plan). `make test-unit` (targeted `tests/unit/audit/`): 87 passed. Live run on `outputs/scores/{a,b,c}/seed_*`: **40/40 cells PASS** — Regime A 5 seeds × 4 baselines (B1/B2/B3/B4); Regime B 5 seeds × 3 baselines (B1/B2/B4); Regime C 30 cells (5 seeds × 6 α) × 3 baselines (B1/B2/B4). `recomputed_metrics.json` written per cell + `outputs/scores/recomputed_metrics_index.json`. | Start T04 (Reuse Verdict Checker). |
| 013 | T04 | NOT_STARTED | DONE | Implemented `src/datp/audit/verdicts.py` with `compute_reuse_verdict` and `compute_all_verdicts`. Added `ReuseVerdict` enum to `core/enums.py`. Added `CELL_VERDICT_JSON`/`CELL_VERDICTS_JSON` to `audit/constants.py`. Tests: `tests/unit/audit/test_verdicts.py` (10 cases). 97 audit tests pass. Live run: **40/40 cells VERIFIED_REUSE_SAFE**; `outputs/scores/cell_verdicts.json` written. | Start T05 (q-Sensitivity Analysis). |
| — | — | — | — | (Deduplicated — merged into entry 014 below.) | — |
| 014 | T05 | NOT_STARTED | DONE | Implemented `src/datp/analyses/q_sensitivity.py` with `run_q_sensitivity(base_dir, *, q_grid, config=None, write_outputs=False) → QSensitivityResult`. Added `AnalysisConfig(q_grid: list[float])` to `config/models.py` and `analysis: {q_grid: [0.90, 0.95, 0.975, 0.99]}` to `conf/config.yaml`. Added `ANALYSIS_DIR` to `artifacts/directories.py`. Created `src/datp/analyses/__init__.py` package. Reused `derive_threshold()`, `ScoreProvider`, `compute_client_metrics()`, `build_evaluation_result()` from canonical modules. Handles `"iid"` alpha (math.inf) and all numeric alpha strings. Validation: q=0.95 reproduces stored cv_fpr exactly (max deviation=0.000000 on live data). Tests: `tests/unit/analyses/test_q_sensitivity.py` (10 cases — empty q_grid raises, missing verdicts raises, blocked cell skipped, row count correct, reference_q reproduces, monotonicity, 4-q distinct, write_outputs creates CSV+PNG, cell count, BASE_CONFIG has q_grid). 705 unit tests pass (1 pre-existing doc failure unrelated). Live run on 40 SAFE cells: **480 rows** (40 cells × 4 q values × 3 baselines); `outputs/analysis/q_sensitivity_table.csv` + `outputs/analysis/q_sensitivity_heatmap.png` written. | Start T06. |
| 015 | N/A | — | — | **Status Drift Correction (2026-05-24):** Fixed `ticket_inventory.md` T04/T05 from `NOT_STARTED` → `DONE`. Fixed `ticket_progress.md` "Next recommended action" from "Start T04" → "Start T06". Deduplicated T05 progress entry (was listed twice as entry 014). All T01–T05 individual ticket files already read `DONE` with resolution records. No audits folder existed — created `docs/tickets/audits/T01_T05_audit.md`. | Proceed with T01–T05 audit then T06–T10. |
| 016 | T01-T05 | — | AUDITED | **T01–T05 Batch Audit (2026-05-24):** All 5 tickets audited — code, tests, configs, enums, constants verified. All 113 targeted tests pass. Verdicts: T01=PASS, T02=PASS, T03=PASS, T04=PASS, T05=PASS. Audit file: `docs/tickets/audits/T01_T05_audit.md`. | Start T06. |

## Previous-Ticket Check Log

| Entry | Requested Ticket | Previous Tickets Checked | Result | Action Taken |
|---|---|---|---|---|
| 001 | N/A | N/A | N/A | N/A |
| 002 | T01 | None (T01 is the first ticket) | OK — no previous tickets to check | Proceeded with T01 implementation. |
| 003 | T02 | T01 | OK — T01 status `DONE` (auditor verdict `PASS_WITH_MINOR_NOTES`); no human intervention pending | Proceeded with T02 implementation. |
| 004 | T03 | T01, T02 | OK — T01 `DONE` (PASS_WITH_MINOR_NOTES); T02 `DONE` (PASS, clean); no human intervention pending | Proceeded with T03 implementation. |
| 005 | T04 | T01–T03 | OK — T01/T02/T03 all `DONE`; no human intervention pending | Proceeded with T04 implementation. |
| 006 | T05 | T01–T04 | OK — T01–T04 all `DONE`; 40/40 cells VERIFIED_REUSE_SAFE; no human intervention pending | Proceeded with T05 implementation. |
| 007 | T06 | T01–T05 | OK — T01–T05 all audited PASS; 40/40 cells VERIFIED_REUSE_SAFE; no human intervention pending | Proceeded with T06 implementation. |
| 017 | T06 | NOT_STARTED | DONE | Calibration-size sweep: `src/datp/analyses/calibration_sweep.py`. n_cal grid [50,100,250,500,1000,5000], 100 fixed-seed repeats. B2 percentile from subsample, FPR on held-out test_benign. Median/IQR over repeats. Config fields: `cal_sweep_n_cal`, `cal_sweep_n_repeats`, `cal_sweep_seed_base`. Tests: 9 cases. | Start T07. |
| 018 | T07 | NOT_STARTED | DONE | τ-Shrink: `src/datp/analyses/tau_shrink.py`. Interpolation τ_k(λ)=λτ_k_local+(1−λ)τ_global, λ∈[0,0.25,0.5,0.75,1.0] from config. Endpoint verification λ=0↔B1, λ=1↔B2 within tolerance. No post-hoc selection. Tests: 8 cases. | Start T08. |
| 019 | T08 | NOT_STARTED | DONE | B2-conf: `conformal_threshold()` in `baselines/common/thresholds.py` + `src/datp/analyses/b2_conf.py`. k = ceil((n+1)*(1-alpha)), alpha=1-q from config. k>n→conservative max. Empirical benign coverage. Tests: 7 cases. | Start T09. |
| 020 | T09 | NOT_STARTED | DONE | B-FedStatsBenign: `src/datp/analyses/fedstats_benign.py`. Per-client (n_i,μ_i,σ²_i), weighted global mean, pooled variance (within+between), between_ratio. τ(k)=μ_global+k·σ_global, k∈[0,5] step 0.01. k* = argmin|exceedance−target|, tie-break larger k. NO attack labels. Tests: 8 cases. | Start T10. |
| 021 | T10 | NOT_STARTED | DONE | B4 Feature Ablation: `src/datp/analyses/b4_ablation.py`. All subsets: 4 singles, 6 pairs, 4 triples, full. Reuses `compute_fingerprints()` from b4.py. Full 4-feature reproduces canonical B4 within tolerance. Contingency vs device family (ARI). Tests: 9 cases. | Start T11. |