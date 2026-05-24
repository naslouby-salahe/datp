# AUDIT_CODE.md

## 1. Audit Scope

- **Repository:** `/home/naslouby/Projects/datp`
- **Branch:** `journal/datp-extension`
- **Timestamp:** 2026-05-24 (re-run; previous pass same day)
- **Ticket boundary:** Last completed = **T16** (stabilization pass closed). T17 and later **NOT STARTED**. Audit treats the codebase as it exists at the close of T16; it does not anticipate or imply T17 implementation.
- **Mode:** **AUDIT-ONLY.** No source files were modified. No tests were modified. No configs were modified. No documentation was modified except this file (`AUDIT_CODE.md`).
- **Tooling executed this pass:** `ruff` (PASS — 0 issues), `pyright` (PASS — 0 errors/warnings/informations), `pytest tests/unit --collect-only` (794 tests), `pytest tests/integration --collect-only` (69 tests). CodeScene/pysonar status carried over from prior pass (server availability re-confirmed below).
- **Idempotent re-run delta:** 19 new findings (CC-005..010, ARCH-004..006, TEST-008..010, E2E-001..002, DOC-001..005) added from the second sweep; all 30 prior findings re-verified and retain stable IDs and `OPEN` status. No previously-OPEN finding has flipped state.
- **Subagent lanes (parallel, read-only):** Lane A (ownership + architecture), Lane B (audit package + analyses), Lane C (tests + fixtures), Lane D (constants + dead code + docs + drift), Lane E (assert/except/magic-literal/imports gap sweep — new), Lane F (test/docs gap sweep — new). Findings deduplicated and merged.

## 2. Executive Summary

| Severity | Count |
|---|---|
| CRITICAL | 1 |
| HIGH     | 5 |
| MEDIUM   | 15 |
| LOW      | 21 |
| INFO     | 7 |
| **TOTAL** | **49** |

(HIGH count corrected from prior pass's `4` to actual `5` — `DUP-002` was always HIGH but was undercounted; severities of individual findings are unchanged.)

Headline issues (unchanged from prior pass; all re-verified):
1. **DRIFT-001 / OWN-002 (CRITICAL):** `audit/_threshold_result` re-implements B4 dispatch without the silhouette guard present in canonical `derive_threshold`. Under `b4_regime_a_mode="silhouette"`, the audit will recompute B4 thresholds with the static `b4_k_regime_a` and silently disagree with the main pipeline. Verified: `src/datp/audit/results.py:570` passes `k_regime_a=cfg.threshold.b4_k_regime_a` unconditionally; canonical `src/datp/baselines/common/thresholds.py:93-98` switches on `b4_regime_a_mode`.
2. **DUP-001 (HIGH):** `DemotionDecision` enum is defined twice (`core/enums.py:58` **and** `audit/enums.py:67`). Verified again this pass.
3. **OWN-001 (HIGH):** Threshold dispatch (B1/B2/B3/B4) is duplicated between `baselines/common/thresholds.py::derive_threshold` and `audit/results.py::_threshold_result`. Maintenance is two-sited.
4. **GOD-001 (HIGH):** `src/datp/audit/results.py` is 1957 lines, 73 top-level decls; CodeScene reports many Complex Method / Large Method / Excess Arguments smells. Re-confirmed via `wc -l`.
5. **STRUCT-001 (HIGH):** `src/datp/thresholding/` exists as an empty directory; declared ownership in CLAUDE.md is not realized. Re-verified empty.

New gap-sweep additions this pass (none upgrade the verdict; details in §§ 5–9):
- 6 additional clean-code findings (CC-005 assert misuse in `training/fl/runner.py` + `audit/datasets.py`; CC-006 wide `except Exception`; CC-007 bare `95` percentile scatter; CC-008 duplicated `1e-12` / `1e-9` epsilons; CC-009 unjustified stdlib function-level imports; CC-010 inconsistent `noqa: PLC0415` discipline).
- 3 architecture findings (ARCH-004 `scripts/sensitivity_shared_threshold.py` duplicating analyses scope; ARCH-005 `scripts/extract_files.py` unrelated dev utility; ARCH-006 `evaluation/__init__.py` unique `__getattr__` lazy loader).
- 3 test findings (TEST-008 641-LoC `test_ciciot_prepare.py`; TEST-009 586-LoC `test_baseline_b0.py`; TEST-010 5 inline `pytest.skip` in `test_data_ciciot.py`).
- 2 e2e findings (E2E-001 silent skip on missing raw data; E2E-002 unmarked slow determinism test).
- 5 docs findings (DOC-001 README silent on conditional scope; DOC-002 unzip without precondition check; DOC-003 PRE_CODING_PLAN cross-ref gap; DOC-004 GC/GD groups without ticket pointers; DOC-005 confirmation that no docs reference the empty `datp.thresholding` path).

**Verdict:** **YELLOW** — cleanup recommended before T17. Tools are green; structural/ownership debt is real but contained.

## 3. Tool Results

| Tool | Command | Status | Summary |
|---|---|---|---|
| Ruff | `ruff check src/ tests/` | **PASS** | "All checks passed!" 0 issues. Re-run this pass; identical output. |
| Pyright | `pyright` (pyrightconfig.json scope) | **PASS** | "0 errors, 0 warnings, 0 informations". Re-run this pass; identical output. |
| pytest unit collect-only | `pytest tests/unit --collect-only -q` | **PASS** | 794 tests collected in 17.62 s (this pass). |
| pytest integration collect-only | `pytest tests/integration --collect-only -q` | **PASS** | 69 tests collected in 12.94 s (this pass). |
| Quality tools availability | `make quality-audit-tools-check` | **PASS** | 13/13 checks passed (ruff, pyright, pytest, coverage, pysonar, docker, docker-compose, cs, all configs). |
| CodeScene CLI | `cs review <files>` on hotspots; `cs delta` against base | **PASS (ran)** | Found code-health smells in hotspots — see § 10. Health scores: `audit/results.py` **5.73**, `reporting/build.py` **6.13**, `audit/score_manifest.py` **7.99**, `audit/metric_reproducer.py` **8.78**, `analyses/regime_c_severity.py` **8.81**, `analyses/b4_ablation.py` **9.04**, `analyses/tau_shrink.py` **9.04**, `baselines/common/thresholds.py` **9.68**. |
| pysonar (Python scanner) | `pysonar --help` (presence) | **AVAILABLE — not pushed** | Tool callable. Full `pysonar -t $SONAR_TOKEN --project-key=...` not run in audit-only because it uploads to the local SonarQube server and would create/modify a Sonar project. Local Sonar server confirmed `UP` at `http://localhost:9000`. Re-run during the next mutating ticket. |
| SonarQube Community Build server | `curl /api/system/status` | **UP** | Server status `UP`, version 26.5.0.122743. No scan executed in audit-only. |

> **Tool-blocked:** None blocked the audit; pysonar full-scan was deferred intentionally to avoid mutating the Sonar server during a read-only pass.

## 4. Scientific Drift Risk Audit

- **DRIFT-001** — see § 5 / `OWN-002`. **CRITICAL.** Audit recomputes B4 threshold without silhouette guard. Concrete violation of "B1–B4 derive from shared score artifacts with consistent calibration."
- **DRIFT-002 (INFO, no current violation):** No code references baselines beyond B0–B5. No new aggregation, privacy, poisoning, backdoor, evasion, or concept-drift mechanisms detected. No T17+ artefacts created. Regime D never appears in source.
- **DRIFT-003 (INFO):** `audit/results.py:330-340` and `audit/schemas.py:331` correctly enforce CICIoT2023 homogeneity-claim guards (`HOMOGENEOUS`/`HETEROGENEOUS`/`BLOCKED_PENDING_RUN`).
- **DRIFT-004 (INFO):** Shared-training rule is upheld by package layout: there is a single `training/fl/scoring.py` and a single `derive_threshold()`. The drift surface is concentrated in the audit duplication (DRIFT-001).
- **DRIFT-005 (MEDIUM, latent):** `audit/results.py::_process_b0_sanity` and `_process_score_hashes` correctly guard against treating B0 like B1–B4. Tests do not yet assert the negative ("B0 must not appear in cell_verdicts"); see `TEST-006`.

## 5. Ownership and Architecture Findings

### Finding ID: STRUCT-001
- Severity: HIGH
- Category: Structural / declared-vs-realized ownership
- Affected file(s): [src/datp/thresholding/](src/datp/thresholding/) (empty directory; no `.py` files)
- Evidence: `ls -la src/datp/thresholding/` shows only `.` and `..`. Threshold derivation actually lives in [src/datp/baselines/common/thresholds.py](src/datp/baselines/common/thresholds.py) (110 LoC). `derive_threshold`, `arithmetic_mean_threshold`, `conformal_threshold` all live under `baselines/`.
- Why this is not clean: CLAUDE.md § "Thresholding ownership" states `src/datp/thresholding/` should own threshold strategies, results, calibration-pending logic, eligibility, fallback, serialization, and B1–B4 dispatch. The directory exists but is empty; ownership is dispersed in `baselines/common/` and `audit/`.
- Scientific drift risk: Concentrates the dispatch-duplication issue (OWN-001/OWN-002). A canonical thresholding package would force single-sited dispatch.
- Recommended fix: Either (a) populate `src/datp/thresholding/` with the canonical owners and refactor consumers, or (b) delete the empty directory and update CLAUDE.md to reflect actual ownership in `baselines/common/`. Do not silently keep a misleading stub.
- Tests to add or update: Adapt `tests/unit/baselines/main/test_thresholds.py` import paths if (a) is chosen.
- Tool evidence: filesystem inspection.
- Status: OPEN

### Finding ID: OWN-001
- Severity: HIGH
- Category: Duplicated baseline-dispatch logic
- Affected file(s): [src/datp/baselines/common/thresholds.py:67-110](src/datp/baselines/common/thresholds.py#L67-L110), [src/datp/audit/results.py:537-574](src/datp/audit/results.py#L537-L574)
- Evidence: Both `derive_threshold(...)` (canonical) and `_threshold_result(...)` (audit) contain the same `if baseline == Baseline.B1 / B2 / B3 / B4` chain calling `b1.compute / b2.compute / b3.compute / b4.compute` with parallel keyword arguments.
- Why this is not clean: Two sites must stay in lock-step; any change to baseline `compute()` signatures (k-candidates, n_init, regime forwarding, random_state) requires editing both.
- Scientific drift risk: Audit silently produces non-matching thresholds when the canonical dispatch is updated without `_threshold_result` being updated — exactly the situation already present in OWN-002.
- Recommended fix: Have `audit/results.py::_threshold_result` delegate to `derive_threshold(baseline, cal_errors, n_min, q, tau_global=tau_global, regime=regime, threshold_cfg=cfg.threshold)`. Keep only audit-only post-processing local.
- Tests to add or update: Add a parameterized test that asserts `_threshold_result(...)` == `derive_threshold(...)` across B1/B2/B3/B4 × Regime.A/B/C using identical inputs.
- Tool evidence: grep on `if baseline ==` in `src/datp/`.
- Status: OPEN

### Finding ID: OWN-002 (= DRIFT-001)
- Severity: **CRITICAL**
- Category: Duplicated dispatch with divergent logic (B4 silhouette mode)
- Affected file(s): [src/datp/baselines/common/thresholds.py:92-106](src/datp/baselines/common/thresholds.py#L92-L106), [src/datp/audit/results.py:562-573](src/datp/audit/results.py#L562-L573)
- Evidence:
  - Canonical (`thresholds.py:93-98`): `mode = threshold_cfg.b4_regime_a_mode; k_for_a = 0 if regime == Regime.A and mode == "silhouette" else threshold_cfg.b4_k_regime_a` then passes `k_regime_a=k_for_a`.
  - Audit (`results.py:570`): passes `k_regime_a=cfg.threshold.b4_k_regime_a` **unconditionally** — no silhouette check.
- Why this is not clean: Audit will derive B4 thresholds with a fixed k for Regime A even when the experiment used silhouette-selected k. The recomputed `cv_fpr`, `coverage_ratio`, `mean_fpr` will not match the stored values, and the cell will be flagged FAIL — or, worse, drift may be hidden by tolerance buckets.
- Scientific drift risk: **CRITICAL.** Violates "B1–B4 derive from shared score artifacts" — the audit no longer reproduces what the pipeline computed. Direct contradiction of CLAUDE.md § Shared-Training Rule.
- Recommended fix: Same as OWN-001 (delegate to `derive_threshold`). The duplication is the root cause.
- Tests to add or update: Add a regression test that runs `_threshold_result(B4, Regime.A, ...)` with `b4_regime_a_mode="silhouette"` and asserts the returned threshold equals `derive_threshold(...)`.
- Tool evidence: Read of both files (verified; not an agent claim — confirmed inline at audit time).
- Status: OPEN

### Finding ID: ARCH-001
- Severity: MEDIUM
- Category: Naming collision / ownership clarity
- Affected file(s): [src/datp/baselines/common/eligibility.py](src/datp/baselines/common/eligibility.py), [src/datp/evaluation/eligibility.py](src/datp/evaluation/eligibility.py)
- Evidence: Two modules share the file basename. The first owns calibration-time eligibility (`identify_eligible`, n_min), the second owns evaluation-time filtering (`filter_eligible_metrics`).
- Why this is not clean: Identical basename invites mis-imports and obscures that they cover different stages. Per CLAUDE.md § "Eligibility ownership" the duplication of names is a flagged risk.
- Scientific drift risk: Low — current usages are correct, but a future contributor importing the wrong module would silently change the boundary between calibration and reporting.
- Recommended fix: Rename `baselines/common/eligibility.py` → `baselines/common/calibration_eligibility.py` (or move into the proposed `thresholding/` package); keep `evaluation/eligibility.py` as the reporting filter.
- Tests to add or update: Update imports in `tests/unit/baselines/main/test_threshold_strategies.py` and any e2e tests.
- Status: OPEN

### Finding ID: ARCH-002
- Severity: INFO
- Category: Baseline thinness
- Affected file(s): `baselines/main/b0.py` (~436 LoC), `b1.py` (~35), `b2.py` (~32), `b3.py` (~79), `b4.py` (~226)
- Evidence: Line counts per file.
- Why this is not clean: Not unclean — sizes match responsibilities. B1/B2 are thin wrappers; B3 owns family aggregation; B4 owns clustering and silhouette selection; B0 owns its centralized pipeline. No action required.
- Status: OPEN (informational)

### Finding ID: ARCH-003
- Severity: INFO
- Category: Score reading consolidation
- Affected file(s): [src/datp/evaluation/score_loading.py](src/datp/evaluation/score_loading.py), [src/datp/baselines/common/scoring.py](src/datp/baselines/common/scoring.py), [src/datp/data/common/storage.py:42](src/datp/data/common/storage.py#L42), [src/datp/audit/results.py:162](src/datp/audit/results.py#L162)
- Evidence: Grep `pl.read_parquet` shows only two raw parquet reads: `data/common/storage.py:42` (generic loader) and `audit/results.py:162` (single label-column reader). All score reads otherwise go through `read_score_column()` / `ScoreProvider`.
- Status: OPEN (informational — score ownership is clean)

### Finding ID: ARCH-004
- Severity: MEDIUM
- Category: Misplaced script duplicating package CLI / analyses scope
- Affected file(s): [scripts/sensitivity_shared_threshold.py](scripts/sensitivity_shared_threshold.py) (~360 LoC)
- Evidence: Script (1) hardcodes scientific parameters (`Q = 0.95`, `N_MIN = 100`, `N_BOOTSTRAP = 10_000`, `BOOTSTRAP_SEED = 42`, `SEEDS = [0..4]`, `REGIME = "a"`) instead of using `config/models.py`; (2) uses `pandas.read_parquet` directly instead of canonical `score_loading.read_score_column` / `ScoreProvider`; (3) writes to ad-hoc path `outputs/sensitivity/shared_threshold_variants/` (not via `artifacts/directories.py`); (4) reimplements bootstrap CI instead of calling `src/datp/statistics/bootstrap.py:bootstrap_ci`; (5) no CLI entry under `src/datp/cli/`.
- Why this is not clean: A scientific analysis sits outside the package and bypasses every canonical ownership boundary the rest of the codebase respects. It is exactly the "misplaced scripts that duplicate package CLI/service behavior" pattern called out in CLAUDE.md § Implementation Quality Rules.
- Scientific drift risk: MEDIUM — bypasses canonical bootstrap and config; if anyone runs it and treats its outputs as evidence, the numbers are not produced via the audited code path.
- Recommended fix: Promote into `src/datp/analyses/shared_threshold_sensitivity.py`, wire to `datp` CLI under `report` or `analyze`, replace hardcoded constants with config fields, and reuse canonical bootstrap / score-loading.
- Tests to add or update: Unit tests once promoted into `analyses/`; nothing to change while it remains a script.
- Tool evidence: file inspection.
- Status: OPEN

### Finding ID: ARCH-005
- Severity: LOW
- Category: Unrelated developer utility shipped under `scripts/`
- Affected file(s): [scripts/extract_files.py](scripts/extract_files.py) (~56 LoC)
- Evidence: Concatenates `*.py / *.yaml / *.yml` under `src/` into `extracted.txt`. Not invoked by Makefile, tests, CLI, or sweep.
- Why this is not clean: Dev-only utility lives next to scientific scripts. Either belongs in a developer-tools folder or should be removed.
- Recommended fix: Move to `scripts/dev/` or delete.
- Status: OPEN

### Finding ID: ARCH-006
- Severity: LOW
- Category: Non-uniform `__init__.py` pattern
- Affected file(s): [src/datp/evaluation/__init__.py](src/datp/evaluation/__init__.py)
- Evidence: Uses module-level `__getattr__` for lazy attribute access (lines 23, 26, 34 with `noqa: PLC0415`). Every other package under `src/datp/` uses eager imports.
- Why this is not clean: A one-of-its-kind lazy pattern surprises future maintainers and shifts import failures from `import datp.evaluation` to first attribute access — harder to diagnose. Pattern may be legitimate if it breaks a heavy import chain, but no justification comment exists.
- Scientific drift risk: None.
- Recommended fix: Either add a one-line comment justifying the lazy loader, or replace with conventional eager imports if the lazy load is not actually saving startup cost.
- Status: OPEN

## 6. Clean-Code Findings

### Finding ID: GOD-001
- Severity: HIGH
- Category: God module / size
- Affected file(s): [src/datp/audit/results.py](src/datp/audit/results.py) (1957 LoC, 73 top-level decls)
- Evidence: `wc -l` = 1957; CodeScene "Lines of Code in a Single File" smell; "Overall code health score 5.73"; large methods: `_compute_aggregate_stats` LoC=117 cc=17, `run_results_audit` LoC=114 cc=11, `_compute_client_metric_row` LoC=85 cc=12, `_build_seed_deltas` LoC=76, `_process_run` LoC=74; argument-heavy functions: `_process_run` 10 args, `_recon_summary` 9, `_build_partition_audit` 8, `_compute_client_metric_row` 8.
- Why this is not clean: One module owns warning emission, accumulator state, threshold reconstruction, per-attack rows, per-client rows, B0 sanity checks, score-hash bookkeeping, homogeneity processing, partition audit, recomputation records, and final orchestration. Splitting protects future correctness.
- Scientific drift risk: Indirect — concentrated state increases the chance that a refactor breaks one path (e.g., OWN-002) without breaking another.
- Recommended fix: Split into sub-modules along the existing record categories: `audit/accumulator.py`, `audit/warning_emission.py`, `audit/threshold_records.py`, `audit/client_metrics.py`, `audit/partition.py`, `audit/run_orchestration.py`. Keep `results.py` as a thin assembler.
- Tool evidence: CodeScene `cs review src/datp/audit/results.py`.
- Status: OPEN

### Finding ID: GOD-002
- Severity: MEDIUM
- Category: Long methods / complex methods in reporting
- Affected file(s): [src/datp/reporting/build.py](src/datp/reporting/build.py) (818 LoC, health 6.13)
- Evidence: CodeScene reports `build_figures` cc=39 LoC=188, `build_stats` cc=11 LoC=85, `build_all` cc=11, `_check_heterogeneity_context` cc=12 args=6, `_common_eligible_fprs` cc=11, `_client_metrics_from_payload` cc=11, `_assert_metric_matches` cc=9 args=5.
- Why this is not clean: `build_figures` is a 188-line function with cyclomatic complexity 39 — far over the project's stated 5–7 decision-point threshold.
- Recommended fix: Decompose `build_figures` into per-figure builders (`_build_figure_1`, `_build_figure_2`, …) inside `reporting/figures.py`, leaving `build.py` as a coordinator.
- Status: OPEN

### Finding ID: AUD-001 (= GOD-003)
- Severity: MEDIUM
- Category: Flat schema / 59-arg construction
- Affected file(s): [src/datp/audit/schemas.py:247-309](src/datp/audit/schemas.py#L247-L309) (`SeedDeltaRecord`, 60 fields), [src/datp/audit/results.py:1610-1667](src/datp/audit/results.py#L1610-L1667) (constructor call site)
- Evidence: `SeedDeltaRecord` has `regime, alpha, seed`, plus `b{1,2,4}_*` for 13 metrics, plus 10 deltas, plus `b{1,2,4}_convergence_round`, `b{1,2,4}_tau_global`, plus `coverage_ratio`, `status` = 60 fields total. Construction site assigns all by keyword.
- Why this is not clean: Flat schema makes adding/removing a baseline or metric an n-site change. Hard to express invariants ("B2 must always have a tau_global because B2 always depends on B1").
- Scientific drift risk: A new metric requires editing schema + builder + tests; risk of forgetting a baseline column.
- Recommended fix: Introduce a `BaselineMetricBlock` (cv_fpr, cv_tpr, macro_f1_mean, macro_f1_p10, auroc_mean, pr_auc_mean, mean_fpr, std_fpr, iqr_fpr, worst_client_*4, convergence_round, tau_global) and `SeedDeltaRecord` becomes `{regime, alpha, seed, b1, b2, b4, deltas, coverage_ratio, status}`. CSV serialization can flatten on write.
- Status: OPEN

### Finding ID: AUD-002
- Severity: MEDIUM
- Category: Overloaded context object
- Affected file(s): [src/datp/audit/results.py:659-689](src/datp/audit/results.py#L659-L689) (`_RunContext`)
- Evidence: 31 fields mixing identity (regime, baseline, seed, alpha, run_id), paths (data_root, score_root, checkpoint, partition_path), hashes (split_hash, model_hash, training_hash, preprocessing_hash), payloads (metrics, partition_payload, metadata, normalized_clients), counts (client_count, train_count, calibration_count, test_count), convergence state, and invariant_key.
- Why this is not clean: Hard to mock; hard to reason about which subset each helper actually uses; many helpers take the whole context only to read 2–3 fields.
- Recommended fix: Split into `RunIdentity`, `RunPaths`, `RunHashes`, `RunPayload`, `RunCounts`, `RunConvergence`; have `_RunContext` compose these.
- Status: OPEN

### Finding ID: AUD-003
- Severity: MEDIUM
- Category: Accumulator god-object
- Affected file(s): [src/datp/audit/results.py:632-657](src/datp/audit/results.py#L632-L657) (`_AuditAccumulator`)
- Evidence: 21 fields: 12 record lists, 4 nested dicts, 1 panel dict, warnings list, missing_confusion_warned set, partition_audits dict.
- Why this is not clean: Nested dict types like `dict[tuple[Regime,int,str|None], dict[Baseline, dict[tuple[str,str], str]]]` are opaque; no type-safe accessor; correctness depends on every caller using consistent keys.
- Recommended fix: Wrap nested dicts in small accessor classes (`InvariantStore`, `ScoreHashStore`) with typed `put` / `get`. Consider splitting record lists by domain (data vs. metrics vs. quality).
- Status: OPEN

### Finding ID: AUD-004
- Severity: MEDIUM
- Category: Inconsistent warning emission pattern
- Affected file(s): [src/datp/audit/results.py:133-144](src/datp/audit/results.py#L133-L144) (`_emit_warning`), call sites at lines 725, 794, 891, 912, 1062, 1226, 1389, 1404, 1418, 1514, 1724, 1730
- Evidence: Helper `_emit_warning` exists but most callers still construct `WarningRecord(...)` and call `acc.warnings.append(...)` directly.
- Why this is not clean: The helper is the documented owner of warning construction; bypassing it splits maintenance and risks divergent fields.
- Recommended fix: Make `_emit_warning` the sole construction path; convert remaining call sites; consider per-warning helpers (`_warn_b1_not_pooled`, etc.).
- Status: OPEN

### Finding ID: CC-001
- Severity: INFO
- Category: Package-import side effect
- Affected file(s): [src/datp/__init__.py:35-43](src/datp/__init__.py#L35-L43)
- Evidence: `configure_runtime_env()` invoked at module load; sets `RAY_ACCEL_ENV_VAR_OVERRIDE_ON_ZERO`.
- Why this is acknowledged: T16 audit recorded this as intentional. Re-stated here for traceability. No drift risk.
- Recommended fix: Keep, but verify the call is idempotent and add a one-line comment near the call explaining why import-time mutation is required.
- Status: OPEN (intentional design)

### Finding ID: CC-002
- Severity: LOW
- Category: Magic literal default
- Affected file(s): [src/datp/analyses/q_sensitivity.py:172](src/datp/analyses/q_sensitivity.py#L172)
- Evidence: `reference_q = config.threshold.q if config is not None else 0.95`
- Why this is not clean: Hardcoded `0.95` mirrors the configured default; should reference a single canonical constant (e.g., `DEFAULT_THRESHOLD_Q`) so a config-default change updates everywhere.
- Recommended fix: Centralize the default in `config/models.py` and import it.
- Status: OPEN

### Finding ID: CC-003
- Severity: LOW
- Category: Long argument lists
- Affected file(s): `audit/results.py` (15 functions ≥ 5 args, several ≥ 8), `analyses/b4_ablation.py::_cluster_and_evaluate` (10 args), `analyses/tau_shrink.py::_evaluate_shrink_lambda` (9 args), `reporting/build.py::_load_results` (6 args)
- Evidence: CodeScene "Excess Number of Function Arguments" output cited in § 10.
- Recommended fix: Group related params into dataclasses (e.g., `BaselineEvaluationContext`, `ClusterParams`). Cross-references AUD-001/002/003.
- Status: OPEN

### Finding ID: CC-004
- Severity: LOW
- Category: Manual CSV writing in analyses
- Affected file(s): `analyses/q_sensitivity.py:201-219`, `analyses/b3_preservation.py:134`, `analyses/b4_ablation.py:331-347`
- Evidence: Each analysis defines its own fieldnames list and DictWriter loop; no shared CSV writer in `audit/writers.py` is reused.
- Recommended fix: Either reuse `audit/writers._write_csv` (if generic enough) or extract a `analyses/_csv.py` writer; centralize fieldname registries.
- Status: OPEN

### Finding ID: CC-005
- Severity: MEDIUM
- Category: `assert` used for runtime validation in production code
- Affected file(s): [src/datp/audit/datasets.py:72](src/datp/audit/datasets.py#L72), [src/datp/audit/datasets.py:119](src/datp/audit/datasets.py#L119), [src/datp/training/fl/runner.py:215](src/datp/training/fl/runner.py#L215), [src/datp/training/fl/runner.py:391](src/datp/training/fl/runner.py#L391), [src/datp/training/fl/runner.py:392](src/datp/training/fl/runner.py#L392) (plus the two prior sites: `audit/datasets.py:124`, `audit/results.py:553`)
- Evidence: `assert family_map is not None`, `assert cap_policy.total is not None and ...`, `assert regime is not None, "regime must be set in config"` (twice), `assert base_dir is not None or output_locator is not None`. Two type-narrowing asserts at `audit/datasets.py:118` and `audit/results.py:1650` are excluded — those are safe.
- Why this is not clean: All five are runtime invariant checks that disappear under `python -O`. CLAUDE.md § "Mandatory Quality Gate" forbids using `assert` for runtime validation in production code.
- Scientific drift risk: LOW (these asserts guard configuration sanity; under `-O` they would silently allow a misconfigured run). Indirect risk only.
- Recommended fix: Replace with explicit `raise ValueError(fmt(...))` using the project's `datp.core.errors.fmt` helper.
- Tests to add or update: Add tests that pass `None` for the relevant arguments and assert a `ValueError` is raised.
- Tool evidence: grep `^\s*assert ` in src/.
- Status: OPEN

### Finding ID: CC-006
- Severity: LOW
- Category: Broad `except Exception` without justification or logging
- Affected file(s): [src/datp/audit/datasets.py:235](src/datp/audit/datasets.py#L235), [src/datp/core/provenance.py:43](src/datp/core/provenance.py#L43), [src/datp/data/datasets/ciciot2023/prepare.py:63](src/datp/data/datasets/ciciot2023/prepare.py#L63), [src/datp/pipeline/training.py:33](src/datp/pipeline/training.py#L33), [src/datp/pipeline/training.py:79](src/datp/pipeline/training.py#L79)
- Evidence: 17 `except Exception` sites total in src/. Most either log+account, append to a warnings list, or re-raise as `RuntimeError` — acceptable. The five above either swallow silently with no logging (`audit/datasets.py:235` returns `None`; `core/provenance.py:43` returns sentinel "GIT_UNAVAILABLE"), retry without distinguishing parse vs IO error (`ciciot2023/prepare.py:63` with `ignore_errors=True`), or wrap `FileLock` acquisition where the actual exception space is much narrower (`pipeline/training.py:33,79`).
- Why this is not clean: Silent swallowing of `Exception` masks programming errors (AttributeError, KeyError) the same as the expected I/O error. Acceptable for the `FileLock` cases if narrowed to `(OSError, TimeoutError)`. The `audit/datasets.py:235` case is the highest-priority cleanup: an invalid JSON manifest will be silently treated as "missing", which can hide an audit failure.
- Recommended fix: Narrow to the specific exception class expected; if the swallow is truly intentional, add a `# noqa: BLE001` with an inline justification comment (per the pattern already used at `audit/score_manifest.py:331` and `artifacts/markers.py:86`).
- Status: OPEN

### Finding ID: CC-007
- Severity: MEDIUM
- Category: Scattered scientific magic literal — bare `95` percentile and duplicated epsilons
- Affected file(s): [src/datp/audit/results.py:514](src/datp/audit/results.py#L514), [src/datp/audit/results.py:524](src/datp/audit/results.py#L524), [src/datp/statistics/divergence.py:49](src/datp/statistics/divergence.py#L49) (bare `95`); [src/datp/statistics/divergence.py:21](src/datp/statistics/divergence.py#L21), [src/datp/statistics/divergence.py:72](src/datp/statistics/divergence.py#L72), [src/datp/analyses/js_divergence_benefit.py:41](src/datp/analyses/js_divergence_benefit.py#L41), [src/datp/analyses/js_divergence_benefit.py:75](src/datp/analyses/js_divergence_benefit.py#L75) (duplicate `1e-12` smoothing + `1e-9` bin epsilon); [src/datp/audit/results.py:1577](src/datp/audit/results.py#L1577) (`_RECOMPUTATION_EPSILON = 1e-9` module-private when `audit/constants.py` owns the related tolerances)
- Evidence: `np.percentile(..., 95)` appears three times with no named constant. `_EPS = 1e-12` and `lower + 1e-9` are duplicated between `statistics/divergence.py` and `analyses/js_divergence_benefit.py` even though the JS-divergence analysis claims to reuse the statistics module.
- Why this is not clean: Bare scientific percentile values and epsilons should live as named constants in canonical owner modules (`audit/constants.py`, `evaluation/metric_keys.py`, or a new `statistics/constants.py`). Duplication risks divergent values if one site is updated.
- Scientific drift risk: MEDIUM — if a future contributor changes one site's `1e-12` to `1e-15` (or the `95` to `90`) and not the other, results in one figure/table will silently disagree with results in another.
- Recommended fix: Introduce `JS_LAPLACE_SMOOTHING = 1e-12`, `JS_BIN_EPSILON = 1e-9`, `P95_PERCENTILE = 95` (or `EXTREME_PERCENTILE = 95`) in the appropriate `constants.py`; remove duplicates from `analyses/js_divergence_benefit.py` by importing from `statistics/divergence.py`.
- Status: OPEN

### Finding ID: CC-008 (= part of CC-007)
- Severity: LOW
- Category: Duplicated module-level epsilon constant
- Affected file(s): see CC-007 (covers the `1e-12` / `1e-9` duplication specifically).
- Status: OPEN (cross-reference)

### Finding ID: CC-009
- Severity: LOW
- Category: Unjustified function-level stdlib imports (likely leftovers)
- Affected file(s): [src/datp/analyses/b3_preservation.py:59](src/datp/analyses/b3_preservation.py#L59) (`import json` nested), [src/datp/reporting/build.py:78](src/datp/reporting/build.py#L78) and [reporting/build.py:98](src/datp/reporting/build.py#L98) (`import math` nested, twice), [src/datp/training/fl/scoring.py:77](src/datp/training/fl/scoring.py#L77) (`import json` nested)
- Evidence: Four nested `import` of stdlib modules with no `noqa: PLC0415` and no inline justification. Other nested imports in `audit/` carry `# noqa: PLC0415` because they break circular dependencies or defer heavy load (polars); these four imports are stdlib only and have no such justification.
- Why this is not clean: Nested stdlib imports without justification are dead weight: they pay an attribute-lookup cost on every call and obscure intent. Either they are stale leftovers from a refactor or they hide a circular dependency that should be made explicit.
- Recommended fix: Hoist the four imports to module scope. If hoisting reveals a circular import, add `noqa: PLC0415` plus a one-line comment explaining the dependency cycle.
- Status: OPEN

### Finding ID: CC-010
- Severity: LOW
- Category: Inconsistent `noqa: PLC0415` discipline across analyses/pipeline/cli vs audit/
- Affected file(s): function-level imports without `noqa: PLC0415` in [src/datp/analyses/tau_shrink.py:42](src/datp/analyses/tau_shrink.py#L42), [tau_shrink.py:167](src/datp/analyses/tau_shrink.py#L167), [analyses/b2_conf.py:36](src/datp/analyses/b2_conf.py#L36), [baselines/common/thresholds.py:17](src/datp/baselines/common/thresholds.py#L17), [baselines/common/thresholds.py:78-81](src/datp/baselines/common/thresholds.py#L78-L81), [pipeline/models.py:18](src/datp/pipeline/models.py#L18), [pipeline/executor.py:173](src/datp/pipeline/executor.py#L173), [evaluation/metrics.py:186](src/datp/evaluation/metrics.py#L186), [cli/audit.py:22-23](src/datp/cli/audit.py#L22-L23), [cli/__init__.py:42](src/datp/cli/__init__.py#L42), [cli/__init__.py:51-52](src/datp/cli/__init__.py#L51-L52), [pipeline/training.py:114-115](src/datp/pipeline/training.py#L114-L115), [pipeline/training.py:123](src/datp/pipeline/training.py#L123), [pipeline/training.py:143](src/datp/pipeline/training.py#L143), [artifacts/markers.py:28](src/datp/artifacts/markers.py#L28)
- Evidence: `audit/` modules consistently mark intentional function-level imports with `# noqa: PLC0415`. The 14 sites above use the same pattern (deliberately deferred imports for circular-dependency or lazy-heavy reasons) without the marker. Ruff currently does not flag them (rule not enabled globally), so the markers in `audit/` are advisory documentation only.
- Why this is not clean: The presence of `noqa: PLC0415` in one part of the codebase and its absence elsewhere makes the markers look load-bearing when they are not — and future enabling of `PLC0415` will lint-fail every site in the second group.
- Recommended fix: Either (a) enable `PLC0415` in `pyproject.toml` and mark all intentional sites uniformly, or (b) remove the existing markers and document the convention once. Pick one rule.
- Status: OPEN

### Finding ID: DOC-001
- Severity: MEDIUM
- Category: README silent on conditional scope
- Affected file(s): [README.md](README.md)
- Evidence: README documents only B0–B4, Regimes A/B/C, and the 135-cell matrix. No mention of FedProx, Ditto/FedRep-AE, Edge-IIoTset/Regime D, Regime B-b, the temporal probe, or T17+ work. Journal plans (`EXPERIMENT_PLAN.md:30-38`, `POST_EXPERIMENT_PLAN.md:79-90`) all keep these as `Pending` / `Conditional`.
- Why this is not clean: An external reader assumes README = full scope. The conditional gates are scientifically important caveats and should be summarized.
- Scientific drift risk: LOW. CLAIM discipline is upheld in the journal plans themselves.
- Recommended fix: Add a short "Out of scope (yet)" or "Conditional extensions" subsection to the README pointing at `docs/journal/*.md` and `docs/tickets/`.
- Status: OPEN

### Finding ID: DOC-002
- Severity: LOW
- Category: Documentation instruction without precondition check
- Affected file(s): [README.md:98-103](README.md#L98-L103)
- Evidence: README instructs `unzip -q results/metrics/full_metrics.zip -d outputs`. If `full_metrics.zip` is absent in the checkout, the instruction silently fails.
- Recommended fix: Either gate via a Make target (`make restore-metrics`) that checks for the archive, or add a one-line README note instructing users to verify the archive's existence.
- Status: OPEN

### Finding ID: DOC-003
- Severity: LOW
- Category: Internal cross-reference gap in planning doc
- Affected file(s): [docs/journal/PRE_CODING_PLAN.md:506](docs/journal/PRE_CODING_PLAN.md), [docs/journal/PRE_CODING_PLAN.md:533](docs/journal/PRE_CODING_PLAN.md)
- Evidence: Section 7 (Gate 0 Exit Checklist) and Section 8 (Phase 0 Discovery Findings) are not cross-referenced via anchor links; readers must manually match `GA-XX` IDs.
- Recommended fix: Add inline anchor references between Section 7 items and Section 8 findings.
- Status: OPEN

### Finding ID: DOC-004
- Severity: LOW
- Category: Plan-section → ticket-ID linkage gap
- Affected file(s): [docs/journal/CODING_PLAN.md:103](docs/journal/CODING_PLAN.md), [docs/journal/CODING_PLAN.md:126](docs/journal/CODING_PLAN.md)
- Evidence: Group GC (Edge-IIoTset / Regime D) and Group GD (Conditional CICIoT2023 B-b) describe scope but do not pointer to the implementing tickets (T21–T22 and T23–T24 respectively).
- Recommended fix: Annotate each group with the ticket IDs (`See: T21, T22` etc.); the `Coding Plan Group Mapping` table already in `ticket_inventory.md` provides the reverse mapping.
- Status: OPEN

### Finding ID: DOC-005
- Severity: INFO
- Category: Confirmation — no docs reference `datp.thresholding`
- Affected file(s): n/a
- Evidence: `grep -rn "datp.thresholding" docs/` returns zero hits. Combined with STRUCT-001 (empty directory exists) and CLAUDE.md § "Thresholding ownership" still listing `src/datp/thresholding/` as canonical owner, the docs/code mismatch is internal to CLAUDE.md only.
- Recommended fix: Aligned by Batch B1 (populate or delete the empty package).
- Status: OPEN (confirmation)

## 7. Test Hygiene Findings

### Finding ID: TEST-001
- Severity: MEDIUM
- Category: Persistent failing test
- Affected file(s): [tests/unit/docs/test_baseline_docs.py:15](tests/unit/docs/test_baseline_docs.py) — `test_baseline_role_docs_are_current`
- Evidence: T16 audit note records this test has failed since T02; checks that snippets ("B1 uses the simple arithmetic mean", "B3 is diagnostic", "taxonomy too coarse", "no-p95", "circularity risk", "cluster stability", "must not overclaim") are present in `README.md` / `COMMANDS.md`.
- Why this is not clean: The failure has been documented across multiple ticket audits and not fixed. It must be either resolved (update docs) or removed/parameterized — leaving a known-failing test is a CLAUDE.md § Testing Discipline violation.
- Recommended fix: Update the docs to include the required snippets; do **not** add `xfail`.
- Status: OPEN

### Finding ID: TEST-002
- Severity: INFO (downgraded from MEDIUM after verification)
- Category: Stale-import suspicion — **false positive**
- Affected file(s): `tests/e2e/regime_{a,b,c}/test_*.py`, `tests/e2e/diagnostic/test_*.py`, several unit tests
- Evidence: Imports `from datp.baselines.common.eligibility import ...` and `from datp.baselines.common.thresholds import derive_threshold` are widespread. Source modules exist at those paths.
- Conclusion: These imports are **canonical**, not stale. The audit prompt listed them as imports to inspect; verification confirms they remain valid. Action: re-evaluate if/when ARCH-001 (rename) or STRUCT-001 (move into `thresholding/`) is executed.
- Status: NEEDS_CONFIRMATION (depends on whether the empty `thresholding/` directory is filled)

### Finding ID: TEST-003
- Severity: LOW
- Category: Missing parametrization in large test modules
- Affected file(s): [tests/unit/evaluation/test_evaluation.py](tests/unit/evaluation/test_evaluation.py) (785 LoC), [tests/unit/audit/test_results_audit.py](tests/unit/audit/test_results_audit.py) (666 LoC), [tests/unit/audit/test_metric_reproducer.py](tests/unit/audit/test_metric_reproducer.py) (420 LoC)
- Evidence: No `@pytest.mark.parametrize` in these modules despite many sibling tests sharing identical setup and looping over B1/B2/B3/B4 inline.
- Recommended fix: Parametrize over `Baseline` enum; extract shared helpers (`_write_scores`, `_make_eval_result`) into a module-local `conftest.py` or `tests/fixtures/`.
- Status: OPEN

### Finding ID: TEST-004
- Severity: LOW
- Category: Duplicated fixture builders
- Affected file(s): `tests/unit/baselines/main/test_baseline_b0.py`, `tests/unit/audit/test_metric_reproducer.py`, `tests/unit/evaluation/test_evaluation.py`, `tests/unit/audit/test_results_audit.py`
- Evidence: Each defines its own `_write_scores` / `_make_synthetic_client` / `_deterministic_scores` / `_make_eval_result` helper.
- Recommended fix: Extract a single `tests/fixtures/synthetic_data.py` and import.
- Status: OPEN

### Finding ID: TEST-005
- Severity: MEDIUM
- Category: Missing malformed-input edge cases
- Affected file(s): tests under `tests/unit/audit/`, `tests/unit/evaluation/`
- Evidence: No tests for missing Parquet columns, missing baseline within a cell (B1 present, B2 absent), corrupted JSON in metrics manifest, mismatched benign/attack array lengths, division-by-zero edges in CV computation.
- Recommended fix: Add the negative tests above; CLAUDE.md § Testing Discipline explicitly requires them.
- Status: OPEN

### Finding ID: TEST-006
- Severity: MEDIUM
- Category: Weak coverage of shared-training invariant
- Affected file(s): [tests/unit/audit/test_shared_invariants.py](tests/unit/audit/test_shared_invariants.py) (228 LoC)
- Evidence: Module tests provenance-hash equality (split, model, scoring code, metrics code) across baselines but does not assert that B1/B2/B3/B4 actually share the same calibration score artifact, and does not assert that threshold derivation does **not** retrain the encoder.
- Why this is not clean: The test name implies shared-training is enforced; the code only checks hash strings, not actual data flow. A regression introducing per-baseline retraining would pass.
- Recommended fix: Add tests asserting (a) `ScoreProvider` returns identical bytes/hashes per cell across B1–B4; (b) `derive_threshold` for B2/B3/B4 receives the B1 `tau_global` and does not call any training path; (c) `_threshold_result(B0, ...)` returns `None` (B0 has no threshold derivation path).
- Status: OPEN

### Finding ID: TEST-007
- Severity: LOW
- Category: Inline `pytest.skip` density in regime-C unit tests
- Affected file(s): [tests/unit/data/regimes/test_regime_c.py](tests/unit/data/regimes/test_regime_c.py) (9 inline `pytest.skip` calls)
- Evidence: 9 skip calls guarding optional `flwr_datasets` import or synthetic-partition failures.
- Why this is not clean: Many silent skips can mask real failures; consider one module-level skipif on `flwr_datasets` import.
- Recommended fix: Convert to a single module-level `pytest.importorskip("flwr_datasets")` plus parametrized cases.
- Status: OPEN

### Finding ID: TEST-008
- Severity: MEDIUM
- Category: Large test module > 500 LoC + inline skips (not in TEST-003)
- Affected file(s): [tests/unit/data/datasets/ciciot2023/test_ciciot_prepare.py](tests/unit/data/datasets/ciciot2023/test_ciciot_prepare.py) (641 LoC)
- Evidence: Monolithic procedural file; mixes prepare/schema/leakage/cap/benign-row scenarios in one module without class grouping. Contains 5 in-file `pytest.skip` calls at lines 112, 186, 250, 285, 312 that mask coverage when sampled rows don't satisfy preconditions.
- Why this is not clean: Same smell as TEST-003 (lack of parametrization, length) plus the silent-skip pattern of TEST-010.
- Recommended fix: Split by scenario class (prepare, schema, leakage, cap); replace inline skips with deterministic fixtures sized to satisfy the precondition.
- Status: OPEN

### Finding ID: TEST-009
- Severity: LOW
- Category: Large single-baseline test module — candidate for parametrization
- Affected file(s): [tests/unit/baselines/main/test_baseline_b0.py](tests/unit/baselines/main/test_baseline_b0.py) (586 LoC)
- Evidence: 586-LoC, all B0-focused. The pattern across the other baseline tests is similarly single-baseline-per-file.
- Recommended fix: Consider extracting the shared scoring/threshold/eval scaffolding into a parametrized baseline-conformance suite and keeping each `test_baseline_bX.py` for baseline-specific behavior only.
- Status: OPEN

### Finding ID: TEST-010
- Severity: MEDIUM
- Category: Inline `pytest.skip` masking integration coverage
- Affected file(s): [tests/integration/data/ciciot2023/test_data_ciciot.py:112](tests/integration/data/ciciot2023/test_data_ciciot.py#L112), [test_data_ciciot.py:186](tests/integration/data/ciciot2023/test_data_ciciot.py#L186), [test_data_ciciot.py:250](tests/integration/data/ciciot2023/test_data_ciciot.py#L250), [test_data_ciciot.py:285](tests/integration/data/ciciot2023/test_data_ciciot.py#L285), [test_data_ciciot.py:312](tests/integration/data/ciciot2023/test_data_ciciot.py#L312)
- Evidence: 5 inline `pytest.skip("Category dir not found")` / `"Client file too small ..."` / `"No benign rows found ..."` / `"Insufficient rows ..."` / `"Not enough benign rows ..."` calls that conditionally skip on data shape.
- Why this is not clean: Tests can "pass" while testing nothing; the skips are silent in CI logs. Sibling pattern to TEST-007.
- Recommended fix: Replace with deterministic synthetic fixtures sized to satisfy preconditions; let real-data tests live in `tests/e2e/` where skip-on-missing-data is acceptable.
- Status: OPEN

### Finding ID: E2E-001
- Severity: LOW
- Category: Silent skip across all e2e tests when raw data absent
- Affected file(s): [tests/e2e/conftest.py:30](tests/e2e/conftest.py#L30), [conftest.py:37](tests/e2e/conftest.py#L37), [conftest.py:64](tests/e2e/conftest.py#L64), [conftest.py:74](tests/e2e/conftest.py#L74)
- Evidence: Four `pytest.skip(...)` calls in fixtures that fire when `data/raw/N-BaIoT/` or `data/raw/CIC_IOT_Dataset2023/` are missing. In CI environments without raw data the entire e2e suite is silently NO-OP.
- Why this is not clean: A reviewer reading "e2e: 28 passed" can't tell from the summary that all 28 were skips. No marker / no fail-on-skip toggle.
- Recommended fix: Define a `@pytest.mark.requires_raw_data` marker registered in `pyproject.toml`, and surface "X tests skipped due to missing raw data" in the run summary.
- Status: OPEN

### Finding ID: E2E-002
- Severity: LOW
- Category: Unmarked slow determinism test in e2e
- Affected file(s): [tests/e2e/regime_a/test_regime_a_e2e.py:199](tests/e2e/regime_a/test_regime_a_e2e.py#L199)
- Evidence: `test_determinism` runs the FL pipeline twice; rest of e2e suite is single-pass. No `@pytest.mark.slow` and no time budget.
- Recommended fix: Tag with `@pytest.mark.slow` and document the time budget; expose a `make test-e2e-fast` that excludes the slow mark.
- Status: OPEN

## 8. Dead Code and Unused Code Findings

### Finding ID: DEAD-001 (= DUP-001)
- Severity: HIGH
- Category: Duplicate enum / dead symbol
- Affected file(s): [src/datp/core/enums.py:58-60](src/datp/core/enums.py#L58-L60), [src/datp/audit/enums.py:67-69](src/datp/audit/enums.py#L67-L69)
- Evidence:
  - `core/enums.py:58: class DemotionDecision(enum.StrEnum):`
  - `audit/enums.py:67: class DemotionDecision(enum.StrEnum):`
  - `grep -rn "DemotionDecision" src/ tests/` returns only the two class definitions; **zero callers**.
- Why this is not clean: T16 stabilization audit (lines 19, 71-76 of `docs/tickets/audits/T16_refactor_clean_code_audit.md`) explicitly claimed `DemotionDecision` was moved from `core/enums.py` → `audit/enums.py`. The duplicate in `core/enums.py` survives. The class is also unused. Both true at the same time = a dead duplicate.
- Scientific drift risk: None today; risk is divergence if the enum acquires members in only one of the two definitions.
- Recommended fix: Delete the unused duplicate in `core/enums.py` (or both, since no callers exist). Update T16 audit notes to reflect actual state.
- Tool evidence: grep.
- Status: OPEN

### Finding ID: DEAD-002
- Severity: LOW
- Category: Empty / aspirational package
- Affected file(s): [src/datp/thresholding/](src/datp/thresholding/)
- Evidence: Directory exists but contains zero files. Already captured in STRUCT-001; called out here for the "dead code" lens.
- Recommended fix: Delete the directory or populate it; see STRUCT-001.
- Status: OPEN

### Finding ID: DEAD-003
- Severity: INFO
- Category: Verification of "no-dead-code" claim
- Affected file(s): n/a
- Evidence: `ruff check src/ tests/ --select F401,F811,F841` returns "All checks passed!" — no unused imports, redefinitions, or unused locals.
- Status: OPEN (confirmation)

## 9. Duplication and Pattern Findings

### Finding ID: DUP-002
- Severity: HIGH
- Category: Threshold dispatch (see OWN-001 / OWN-002)
- Affected file(s): `baselines/common/thresholds.py:67-110`, `audit/results.py:537-574`
- Evidence: see OWN-001. Listed here as the duplication lens.
- Recommended fix: see OWN-001.
- Status: OPEN

### Finding ID: DUP-003
- Severity: LOW
- Category: Per-baseline scalar lists in records / panels
- Affected file(s): `audit/results.py:166-184` (`_CellPanel`), `audit/schemas.py:247-309` (`SeedDeltaRecord`)
- Evidence: `_CellPanel` fields (cv_fpr, cv_tpr, macro_f1_mean, …, tau_global, coverage_ratio — 16 fields) are repeated in `SeedDeltaRecord` once per baseline (b1_*, b2_*, b4_*).
- Recommended fix: Extract `CellMetrics` (16 fields) and reuse in both. See AUD-001.
- Status: OPEN

### Finding ID: DUP-004
- Severity: LOW
- Category: Repeated CSV writing patterns in analyses
- Affected file(s): see CC-004.
- Status: OPEN

### Finding ID: DUP-005
- Severity: INFO
- Category: Magic-literal scatter — already centralized
- Affected file(s): n/a (verified clean)
- Evidence: Greps for `"metrics.json"`, `"manifest.json"`, `"model.pt"`, `"scaler.pkl"`, `scoring_manifest.json`, `BINARY_ATTACK_LABEL`, `BLOCKED_PENDING_RUN`, `VERIFIED_REUSE_SAFE`, `"cv_fpr"`, `"coverage_ratio"`, `outputs/`, `results/`, `scores/`, `checkpoints/` resolve to canonical sources in `artifacts/constants.py`, `audit/constants.py`, `evaluation/metric_keys.py`, `core/identity.py`. No scattering detected outside owners.
- Status: OPEN (confirmation that the constants discipline holds)

## 10. File-Level Hotspots

Ranked by CodeScene health score and finding density:

| Rank | File | CS Health | Main problems | Recommended direction | Risk |
|---|---|---|---|---|---|
| 1 | [src/datp/audit/results.py](src/datp/audit/results.py) (1957 LoC) | **5.73** | God module; 5 large methods (LoC 74–117, cc up to 17); 15 functions with ≥5 args; dispatch duplicated (OWN-001/002); inconsistent warning emission (AUD-004); nested dict accumulator (AUD-003); B4 silhouette divergence (CRITICAL). | Split per § GOD-001; route `_threshold_result` through `derive_threshold`; standardize `_emit_warning`. | HIGH |
| 2 | [src/datp/reporting/build.py](src/datp/reporting/build.py) (818 LoC) | **6.13** | `build_figures` cc=39 LoC=188; `build_stats` 85 LoC; several 5-arg helpers. | Split per § GOD-002 into per-figure builders. | MEDIUM |
| 3 | [src/datp/audit/schemas.py](src/datp/audit/schemas.py) (432 LoC) | n/a (mostly pydantic) | `SeedDeltaRecord` 60 fields; `_CellPanel` schema duplicated. | Introduce `BaselineMetricBlock` / `CellMetrics`. | MEDIUM |
| 4 | [src/datp/audit/datasets.py](src/datp/audit/datasets.py) (499 LoC) | n/a | `assert` used for runtime invariant on `expected_client_count` (line 124) and `family_map` (line 553 in results). | Replace `assert` with explicit `raise` to survive `python -O`. | LOW |
| 5 | [src/datp/audit/metric_reproducer.py](src/datp/audit/metric_reproducer.py) (651 LoC) | **7.99** | `_build_baseline_checks` 78 LoC; `reproduce_cell_metrics` 70 LoC; `_scalar_check` cc=10 args=5. | Decompose into per-baseline check builders. | MEDIUM |
| 6 | [src/datp/audit/score_manifest.py](src/datp/audit/score_manifest.py) (624 LoC) | n/a | Several long methods; `base_dir / "scores" / RECOMPUTED_METRICS_INDEX_JSON` and `relative_to(base_dir / "scores")` (lines 492, 648) bypass `artifacts/directories.SCORES_DIR`. | Route through `SCORES_DIR` constant. | LOW |
| 7 | [src/datp/analyses/tau_shrink.py](src/datp/analyses/tau_shrink.py) (388 LoC) | **9.04** | `_evaluate_shrink_lambda` 9 args; `_prepare_cell_baselines` 7 args. | Group into a config object. | LOW |
| 8 | [src/datp/analyses/b4_ablation.py](src/datp/analyses/b4_ablation.py) (373 LoC) | **8.78** | `_cluster_and_evaluate` 10 args cc=11; `run_b4_ablation` cc=9 LoC=82. | Argument grouping; extract clustering helper. | LOW |
| 9 | [src/datp/analyses/regime_c_severity.py](src/datp/analyses/regime_c_severity.py) (184 LoC) | **8.81** | `_compute_alpha_metrics` cc=13. | Extract per-metric helpers. | LOW |
| 10 | [src/datp/sweep/run_sweep.py](src/datp/sweep/run_sweep.py) (356 LoC) | n/a | Reviewed; not flagged by CS. | None now. | INFO |

## 11. Required Refactor Backlog

> Audit-only: these are recommendations, not applied changes.

**Batch A — No-drift safety fixes (must precede any audit re-run on `b4_regime_a_mode="silhouette"`):**
- A1. Route `audit/results.py::_threshold_result` through `baselines/common/thresholds.py::derive_threshold` (fixes OWN-001, OWN-002, DUP-002, DRIFT-001).
- A2. Add regression test asserting parity of `_threshold_result` and `derive_threshold` for all B × Regime combinations.

**Batch B — Ownership fixes:**
- B1. Resolve `src/datp/thresholding/` (populate or delete). Update CLAUDE.md to match (STRUCT-001, DEAD-002).
- B2. Remove the `DemotionDecision` duplicate from `core/enums.py` (or both if unused) (DUP-001 / DEAD-001).
- B3. Rename `baselines/common/eligibility.py` → `baselines/common/calibration_eligibility.py` (ARCH-001).
- B4. Route remaining `base_dir / "scores"` literals through `SCORES_DIR` (audit/score_manifest.py:492, 648; audit/metric_reproducer.py:648).

**Batch C — Duplication and complexity:**
- C1. Split `audit/results.py` per GOD-001.
- C2. Decompose `reporting/build.py::build_figures` (GOD-002).
- C3. Extract `BaselineMetricBlock` / `CellMetrics` shared by `_CellPanel` and `SeedDeltaRecord` (AUD-001, DUP-003).
- C4. Standardize warning emission via `_emit_warning` (AUD-004).
- C5. Group long argument lists into dataclasses (CC-003, AUD-002, AUD-003).

**Batch D — Test cleanup:**
- D1. Fix or remove `test_baseline_role_docs_are_current` (TEST-001).
- D2. Add malformed-input edge-case tests (TEST-005).
- D3. Strengthen `test_shared_invariants` with actual data-flow assertions (TEST-006).
- D4. Parametrize `Baseline` loops; extract shared synthetic-data builders (TEST-003, TEST-004).
- D5. Convert per-test skips in `test_regime_c.py`, `test_data_ciciot.py`, and `test_ciciot_prepare.py` to deterministic fixtures or a single module skipif (TEST-007, TEST-008, TEST-010).
- D6. Split / parametrize `test_baseline_b0.py` (TEST-009).
- D7. Add `requires_raw_data` and `slow` markers; surface skipped counts (E2E-001, E2E-002).

**Batch E — Documentation cleanup:**
- E1. Update T16 audit notes to reflect that the `DemotionDecision` duplicate was not fully resolved.
- E2. Update CLAUDE.md § Thresholding ownership to match actual layout, or align after B1.
- E3. Add an "Out of scope (yet)" subsection to README pointing at the journal plans (DOC-001).
- E4. Either gate the `unzip` instruction behind a Make target with archive existence check, or annotate (DOC-002).
- E5. Add anchor cross-references between PRE_CODING_PLAN §7 and §8 (DOC-003); annotate CODING_PLAN groups GC/GD with implementing ticket IDs (DOC-004).

**Batch F — Hygiene fixes:**
- F1. Replace 5 runtime-validation `assert` statements with explicit `raise ValueError(fmt(...))` (CC-005).
- F2. Narrow or annotate the 5 unjustified `except Exception` sites; convert `audit/datasets.py:235` to a typed `JSONDecodeError`-or-narrower except, with logging (CC-006).
- F3. Centralize `1e-12`, `1e-9`, and `95` percentile literals in a single constants owner; import everywhere (CC-007, CC-008).
- F4. Hoist 4 unjustified stdlib nested imports (CC-009); decide on a single repository-wide `noqa: PLC0415` convention (CC-010).
- F5. Promote `scripts/sensitivity_shared_threshold.py` into `analyses/`, wire to CLI, replace hardcoded scientific parameters with config fields (ARCH-004); move or delete `scripts/extract_files.py` (ARCH-005).
- F6. Either justify or replace the `__getattr__` lazy loader in `evaluation/__init__.py` (ARCH-006).

## 12. Idempotency Notes

- This file is the single canonical audit artifact (`AUDIT_CODE.md`). Re-running the audit prompt updates findings by stable IDs (`OWN-001`, `AUD-001`, `TEST-001`, …) rather than appending new sections.
- IDs are reused when the underlying issue persists; new IDs increment within their prefix when a new root cause is found.
- Section ordering and headings are fixed per the audit contract; re-runs replace contents within each section, never duplicate sections.
- Status fields are restricted to `OPEN`, `NEEDS_CONFIRMATION`, `TOOL_BLOCKED`. There is no `CLOSED` status because audit-only cannot fix issues.
- Tool results are only included when commands actually ran; tools that were available but intentionally not exercised (pysonar full scan) are recorded with status "AVAILABLE — not pushed".
- T17 boundary: this audit explicitly does not start, plan, or imply T17 work. `Next recommended action` in `docs/tickets/ticket_progress.md` remains "MANUAL APPROVAL REQUIRED before T17".

### Re-run delta (2026-05-24, second pass)

The second pass added 19 new finding IDs without modifying any prior finding:

- CC-005, CC-006, CC-007, CC-008, CC-009, CC-010
- ARCH-004, ARCH-005, ARCH-006
- TEST-008, TEST-009, TEST-010
- E2E-001, E2E-002
- DOC-001, DOC-002, DOC-003, DOC-004, DOC-005

Re-verified that all prior findings remain accurate (filesystem state, line numbers, tool outputs all match). Executive summary count updated from 30 → 49. Verdict unchanged (YELLOW). No prior finding was reassigned a new ID. No section was duplicated; each new finding was inserted into the section dictated by its category (§5 Ownership for ARCH-*, §6 Clean-Code for CC-* and DOC-*, §7 Tests for TEST-* and E2E-*). The hotspot table (§10) and tool table (§3) are stable across the two passes. The Refactor Backlog (§11) gained a new Batch F for the hygiene findings introduced this pass.

## 13. Final Audit Verdict

**YELLOW — cleanup recommended before T17.**

Static analysis is green (ruff, pyright). Tests collect cleanly (794 unit + 69 integration). CodeScene reports specific complexity hotspots, primarily in `audit/results.py` and `reporting/build.py`. The audit module duplicates threshold dispatch and contains one concrete divergence with the canonical path (silhouette guard absent), which qualifies as a scientific-drift risk if any future experiment uses `b4_regime_a_mode="silhouette"`. Two duplicate-enum and one empty-package finding indicate residue from the T16 stabilization pass that did not fully land.

The codebase is **not GREEN** because:
- OWN-002 / DRIFT-001 is a concrete divergence between audit and pipeline.
- DUP-001 contradicts the T16 audit's own resolution claim.
- STRUCT-001 leaves declared ownership unrealized.
- `audit/results.py` is large enough (1957 LoC, health 5.73) that any T17 work touching it will fight the complexity.

Once Batch A and Batch B are completed (small, surgical edits), the verdict should move to GREEN. Batches C/D/E remain valuable but are non-blocking for scientific integrity.
