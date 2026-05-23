# CLAUDE.md — Operating Contract for the DATP Repository

This file is the primary operating contract for Claude Code in this repository. All agents, coding work, and review decisions must be consistent with the rules below.

---

## 1. Project Identity

This repository implements the **Device-Aware Threshold Personalization (DATP)** framework: a controlled federated-learning study on IoT malware detection that isolates threshold calibration scope as the primary experimental variable under device heterogeneity.

The source of truth for all scientific decisions is `Blueprint.md`. This file adds engineering rules, quality gates, and execution constraints derived from that blueprint and from the post-experiment audit of 113 runs (Apr 12–15, 2026).

---

## 2. Scientific Contract — Invariants That Must Never Drift

These invariants define the paper's controlled design. Violating any one of them invalidates the threshold-policy attribution claim.

### 2.1 The Controlled Comparison Ladder

**B1, B2, B3, B4 share the same AE architecture, the same FedAvg protocol, the same local epoch count, and the same random seeds. The sole variable across B1–B4 is how the reconstruction-error threshold is computed and scoped.**

- B0 is the centralized reference comparator. It violates FL by pooling all data. It is never described as a guaranteed upper bound.
- B0 is never placed in any sentence claiming a single-variable controlled design.

### 2.2 Threshold Aggregation Rules (Locked)

| Baseline | Formula | Notes |
|---|---|---|
| B0 | percentile₀.₉₅(∪ᵢ Eᵢ) | Centralized, pooled |
| B1 | (1/K_elig) × Σ τᵢ | Simple arithmetic mean of eligible local thresholds |
| B2 | τᵢ = percentile₀.₉₅(Eᵢ) | Local only; zero threshold uplink |
| B3 | (1/\|elig in f\|) × Σ τᵢ within family | Regime A only |
| B4 | (1/\|elig in c\|) × Σ τᵢ within cluster | Eligible clients only; K selection/sensitivity, cluster stability, no-p95 ablation, and p95 circularity risk are audit-tracked |

These formulas are frozen. No weighting by sample size on B1/B3/B4 aggregation — that would introduce a second confound.
B1 uses the simple arithmetic mean of eligible local thresholds.

### 2.3 Calibration-Pending Policy (Locked)

Any client with fewer than n_min = 100 benign calibration samples is Calibration-Pending. All such clients fall back to τ_global (the B1 value) unconditionally in every strategy. Calibration-Pending clients are never silently merged into personalized metric arrays; they must be flagged and counted separately in every result.

### 2.4 Metric Eligibility (Locked)

Primary dispersion metrics — CV(FPR), CV(TPR), worst-client BA, 10th-percentile macro-F1 — are computed over **eligible clients only**. Every main-body result reporting CV(FPR) must include the coverage ratio in parentheses (e.g., "B2 CV(FPR) = X (coverage: K_elig/K_total)").

### 2.5 Primary Endpoint (Locked)

The paper has **one confirmatory main-body claim**: Regime A, B1 vs. B2, CV(FPR), assessed via bootstrap CI on per-seed Δₛ. No secondary or exploratory result may be elevated to primary-claim language.

### 2.6 Scope Boundaries (Locked)

Out of scope by design — no code, no prose, no experiment should address these:
- Open-world or zero-day detection
- Adversarial evasion or data/model poisoning
- Personalization of AE model weights in the main study
- Differential privacy or formal privacy mechanisms
- On-device hardware evaluation
- Concept drift or temporal distribution shift
- A third dataset in the main body

### 2.7 Causal Language Constraint

Never use "proves", "confirms", "establishes" for the decomposition analysis. Always use "is consistent with", "provides evidence of separable contribution patterns", or equivalent. 

---

## 3. Engineering Invariants — What Must Not Drift

These rules are engineering pre-conditions for scientific trustworthiness.

### 3.1 Config and Schema Validation

- All config validation runs **before** any training starts. A mismatch between `model.input_dim` and `dataset.feature_count` must fail at validation time, not inside a Ray actor at runtime.
- `check_resource_bounds(cfg)` and `validate_machine_profile()` are called at startup.
- Unknown config keys, missing required keys, and null required values fail validation. No silent runtime defaults for scientific or execution parameters.
- Every long run must be preceded by `datp config preview` to produce `resolved_config.yaml` before execution.
- **Strict Rule: No hidden defaults / config is the source of truth.** Scientific, reporting, training, resource, logging, diagnostic, and data-preparation values must not be hardcoded in code. Enums/constants are allowed only for identity, artifact names, metric keys, schema keys, and stable labels. Tests must be adapted when code changes.

### 3.2 Shared Training Architecture (Critical — Largest Correctness Issue)

**Train once per (dataset, regime, seed, α); derive B1/B2/B3/B4 from the same checkpoint.**

The shared FL encoder is the primary artifact for a fixed `(dataset, regime, seed, α, model-config, federation-config, manifest)`. After training, per-client score artifacts — one reconstruction-error array for `cal`, `test_benign`, and `test_attack` per client — are persisted to disk. All threshold strategies (B1/B2/B3/B4) are derived from those shared score artifacts without retraining.

The pipeline stages are hard boundaries: `prepare → train → score → threshold/result → report`. No stage may skip a boundary or recompute the stage above it.

This applies to all regimes:
- Regime A: one FL training pass per seed; B1/B2/B3/B4 from shared scores
- Regime B: one FL training pass per seed; B1/B2/B4 from shared scores
- Regime C: one FL training pass per (α, seed); B1/B2/B4 from shared scores at that cell

### 3.3 Determinism

Determinism is a **tested property**, not a documented claim. A determinism test — running the same experiment twice with the same seed and asserting `metrics.json` is byte-identical — must exist before any long campaign begins. Seeds must be fixed for Python `random`, NumPy, PyTorch CPU, and PyTorch CUDA. On CUDA: `cudnn.deterministic = True`, `cudnn.benchmark = False`.

### 3.4 Storage Format

Intermediate artifacts use **Parquet**, not CSV. The CSV format dominated processed storage in the prior run (`data/processed` at ~400 GB; `test_attack.csv` alone at 367 GB). Evaluation-only attack files are the first compression target. Large processed artifacts must be regenerable from raw data plus manifest metadata.

### 3.5 Sweep Automation

**Multi-run campaigns are never launched manually.** `run_sweep.py` enumerates (baseline, regime, seed, α) combinations, skips completed runs, and launches the next pending one automatically. Manual launch is permitted only for single diagnostic runs.

### 3.6 Convergence Settings

- `rounds_initial = 40`, `rounds_max = 150`, `relative_threshold = 0.005`, `window = 10`
- Convergence criterion: relative change between the start and end of the last 10 rounds of FedAvg-weighted mean benign validation loss < 0.005. `relative_change = |loss[-1] - loss[0]| / |loss[0]|` over the window.
- Log actual convergence round for every run. Convergence summary includes `rounds_initial`, `rounds_max`, `relative_threshold`, `window`, `actual_rounds_run`, `convergence_round`, `convergence_status`, and `weighted_validation_loss_per_round`.

### 3.7 Fail-Fast and Observability

- Write `ABORTED.txt` in a `finally` block on any unclean exit; include the last completed round and exception.
- Include `baseline`, `seed`, and `round` in every simulation exception message.
- Log rotation on `outputs/logs/` — unbounded log files are not acceptable.
- Collision-proof run IDs: training run IDs use `<regime>_seed<N>[_alpha<α>]_<timestamp_ms>` (no `<baseline>` — training runs are shared across B1–B4 per §3.2). Baseline appears only in downstream result and log directory paths, not in the shared training identity.
- Pre-create no success-shaped placeholder files. Write `metrics.json.tmp`, rename atomically on success only.

### 3.8 Caching and Memory

- Replace unbounded `_CSV_CACHE` with an LRU cache (maxsize=16 or configured).
- `RAY_memory_usage_threshold=0.90`, not 0.99.
- `max_concurrent` must be derived from available RAM, not hardcoded.

### 3.9 Data Validation Completeness

- CICIoT2023 schema audit must validate more than the first CSV header. One representative file is not enough to certify a heterogeneous raw dump.
- `_validate_paths()` must preflight `test_benign` and `test_attack` in addition to `train`, `cal`, and `scaler.pkl` — before any round starts, not after all training rounds complete.
- Manifest loading must be self-validating at the serialization boundary. `PartitionManifest.load()` must reject malformed data on read — callers must not depend on remembering to call `_validate_manifest()` after load.

### 3.10 Return Type and CV Contracts

- Bare `-> dict` return types in baselines and evaluation code are bugs. Use `TypedDict` models (`BaselineResult` at minimum).
- `cv(arr, ddof)` must have exactly one implementation in `statistics/`. Any parallel CV implementation with different `ddof` semantics is a scientific reproducibility bug.
- NaN-producing conditions must be documented per function with one explicit policy per module: either return `math.nan`, raise, or encode missingness explicitly.

### 3.11 Compilation and Concurrency

- `torch.compile` mode for tabular MLPs must be `reduce-overhead`, not `max-autotune`. The latter is the wrong cost profile for sub-30K parameter models with orchestration-dominant round times.
- Compiled models must be cached per Ray actor lifetime — not recompiled on every `fit()` and `evaluate()` call.
- `RunContext.result_path` must never default to `Path()` (which resolves to the current working directory). The default must be `Path | None`.

### 3.12 Canonical Modules for Constants, Enums, and Error Formatting

All domain string literals, artifact filenames, and dataset layout constants are centralized in canonical modules. Runtime code must import from these modules rather than using inline literals.

| Module | Contains |
|---|---|
| `src/datp/core/enums.py` | Domain enums: `Baseline`, `Regime`, `ScoringStage`, `ClientStatus`, `PipelineStage`, `ThresholdAggregationMethod`, `ThresholdSource`, `NormalizationScope`, `ArtifactKind`, `AuditStatus`, `WarningCode`; derived maps: `REGIME_BASELINES`, `ISOLATED_BASELINES`, `MAIN_BODY_BASELINES`, `THRESHOLD_AGGREGATION_BY_BASELINE`, `BASELINE_THRESHOLD_SOURCE` |
| `src/datp/core/errors.py` | Structured error formatting: `fmt()`, `fmt_missing()`, `fmt_constraint()` |
| `src/datp/artifacts/constants.py` | Artifact file names and markers: `MODEL_CHECKPOINT`, `SCALER_FILE`, `METRICS_FILE`, `MANIFEST_FILE`, etc. |
| `src/datp/audit/constants.py` | Audit artifact filenames: `BASELINE_INVARIANTS_JSON`, `RUN_MANIFEST_CSV`, `AUDIT_SCHEMA_VERSION`, etc. |
| `src/datp/data/catalog.py` | Data-layer `DatasetID` enum (`nbaiot`, `ciciot2023`) and canonical `DatasetSpec` model |
| `src/datp/data/splits.py` | Data-layer `Split` enum and split artifact filenames (`train.parquet`, `cal.parquet`, `test_benign.parquet`, `test_attack.parquet`) |
| `src/datp/data/paths.py` | Raw/processed/prepared roots and `regime_c_prepared_dir()` |
| `src/datp/data/regimes/catalog.py` | Canonical `DATASET_BY_REGIME` mapping (regime→dataset) |
| `src/datp/data/datasets/nbaiot/spec.py` | N-BaIoT layout: `DEVICE_DIRS`, `DEVICE_FAMILY_MAP`, `SPLIT_RATIOS`, `FEATURE_COUNT` |
| `src/datp/data/datasets/ciciot2023/spec.py` | CICIoT2023 layout: `FEATURE_COLUMNS`, `LABEL_COLUMN`, `NUM_CLIENTS`, `CAL_FRACTION`, cap policy |
| `src/datp/data/manifests.py` | Partition manifest hashing, validation, and IO |
| `src/datp/baselines/common/data_loading.py` | Shared client-data loading: `load_client_data()`, `discover_client_dirs()`, tensor helpers, `compute_reconstruction_errors()`, `release_freed_heap()` (public — renamed from `_release_freed_heap`) |
| `src/datp/baselines/common/thresholds.py` | Threshold functions: `percentile_threshold()`, `arithmetic_mean_threshold()` |
| `src/datp/baselines/common/fl_config.py` | Shared FL config builder: `build_fl_training_config()` |
| `src/datp/baselines/common/scoring.py` | Shared score loading: `load_main_cal_errors()` |
| `src/datp/baselines/common/evaluation_helpers.py` | Shared evaluation: `compute_client_metrics_with_auroc()` |
| `src/datp/config/compose.py` | `BASE_CONFIG` — single source of truth for all scientific/protocol defaults |

Rules:
- No governance document references (`CLAUDE.md`, `spec.md`, `Blueprint.md`) in runtime error messages. These references belong in docstrings and comments only.
- Runtime error messages use `fmt()`, `fmt_missing()`, or `fmt_constraint()` from `core.errors` for consistent formatting.
- Scientific parameters (`n_min`, `q`, `cap`, `b4_random_state`, `fedavgm_momentum`, `encoder_dims`, `regime_c_n_clients`, `js_divergence_n_bins`) must flow from `BASE_CONFIG` in `config/compose.py`. No module-level constants for scientific parameters except as derived from `BASE_CONFIG`.
- Dataset-specific layout constants (`SPLIT_RATIOS`, `CAL_FRACTION`, `DEVICE_DIRS`, `FEATURE_COLUMNS`) belong in their respective `spec.py` modules, not in `BASE_CONFIG`.
- No inline default method parameters for values that affect scientific meaning. Such values must be sourced from `BASE_CONFIG` or passed explicitly.
- No private-function cross-package imports. Functions used across packages must be public (no leading underscore). `release_freed_heap()` in `baselines/common/data_loading.py` is public; do not add an underscore-prefixed alias.
- The threshold utility module is `baselines/common/thresholds.py` (renamed from `estimators.py`). References to `estimators.py` in any file are stale and must be corrected.
- Console helpers (`print_banner`, `print_section_header`, `print_step_start`, `print_step_error`, `print_completion`, `print_summary`, `step_context`) are exposed via `datp.pipeline` public `__init__` re-exports. CLI code imports them from `datp.pipeline`, not from `datp.pipeline._console` directly.
- The `DATASET_BY_REGIME` map in `data/regimes/catalog.py` and `THRESHOLD_AGGREGATION_BY_BASELINE` in `core/enums.py` are the single source of truth for regime→dataset and baseline→aggregation-method mappings. Do not duplicate these in `audit/results.py` or `reporting/build.py`.
- Regime baseline lists for reporting must be derived from `REGIME_BASELINES[Regime.X]` in `core/enums.py`. Do not hardcode `("b0", "b1", "b2", ...)` tuples in any module.
- `compute_fingerprints()` in `baselines/main/b4.py` requires an explicit `q` parameter. Do not restore an implicit `BASE_CONFIG.threshold.q` read inside the function body.

### 3.13 Library Standards and Boundaries

- Config composition standard: Hydra + Pydantic v2. Scientific defaults live in `src/datp/conf/`; validation lives in `src/datp/config/models.py`.
- Internal structured-object standard: `@attrs.define(frozen=True, slots=True)` for lightweight, immutable, internal value objects (metric results, threshold communication payloads, run identities). Do not use `@dataclass` anywhere in `src/datp/`. Pydantic v2 owns boundary validation; attrs owns internal modeling; do not duplicate either role.
- CLI standard: Typer commands with Rich console output routed through `src/datp/pipeline/__init__.py` re-exports (`print_banner`, `print_section_header`, `print_step_start`, `print_step_error`, `print_completion`, `print_summary`, `step_context`). The implementation lives in `src/datp/pipeline/_console.py` but CLI modules must import from `datp.pipeline` (the public package), not `datp.pipeline._console` (private submodule). Do not add new argparse command trees; do not `print()` from command flows — use the Rich helpers.
- Logging standard: structlog-backed logging via `src/datp/core/logging.py`. Do not add ad hoc `logging.basicConfig()` or module-local logging setups. Use event+kwargs log calls, never f-string-formatted messages.
- Tabular contract standard: Pandera for DataFrame validation, PyArrow-backed Parquet for processed artifacts (enforced by `data/common/storage.py:assert_no_csv_artifacts`), joblib for scaler serialization, cachetools `LRUCache` for bounded in-process caches.
- Atomic write standard: `artifacts.markers.write_metrics_atomic` (for `metrics.json`) and `artifacts.markers.write_json_atomic` (for arbitrary JSON: contingency, demotion, etc.). Do not hand-roll tmp-file-plus-rename patterns in call sites.
- Reporting standard: Jinja2 templates for LaTeX table rendering (`src/datp/reporting/templates/`). Templates own row/column joining via `{{ columns | join(' & ') }}` — do not pre-join in Python.
- Results-audit standard: `make audit-results` is the canonical operator command. It delegates to the Typer audit implementation and writes the required CSV/JSON/Markdown artifacts under `artifacts/audit/`. Use the CLI form only for direct CLI testing or programmatic integration.
- Tracking standard: MLflow. It is acceptable for tracking to degrade to a no-op when unavailable, but W&B-controlled sweeps are not part of the repository contract.
- Metrics standard: scikit-learn metrics for confusion, balanced accuracy, macro-F1, AUROC, and clustering support. Do not introduce a parallel torchmetrics stack for the same offline evaluation path.
- Training boundary: `lightning` is allowed only for isolated AE training flows (for example B0). The Flower-based shared FL runner remains custom; replacing it with Lightning orchestration would change the experiment control surface.
- Workflow boundary: `datp sweep` / `run_sweep.py` remain the authoritative orchestration path. Do not introduce Dagster or Prefect pipelines for the main study.

---

## 4. Phase Gates

Work proceeds through phases in order. A gate must pass before the next phase begins.

| Phase | Gate Conditions |
|---|---|
| 0 — Environment | All imports succeed; two-client Flower simulation completes; seed fixture confirmed; same-seed reruns produce bit-identical output |
| 1 — Data | All partitions verified; calibration counts logged; any client below n_min=100 flagged; JS divergence saved; scalers serialized; CICIoT2023 cap at 50,000 confirmed |
| 2 — Centralized/Local | B0 AUC-ROC ≥ 0.90; both threshold functions (`percentile_threshold`, `arithmetic_mean_threshold`) pass unit tests |
| 3 — Federated Training | FL simulation completes; convergence rule applied and convergence round logged; B1 per-device FPR dispersion inspected; null-finding contingency decision recorded in `outputs/phase3_diagnostic/contingency_decision.json` before proceeding to Phase 4 |
| 4 — Full Matrix | All main runs complete and logged; bootstrap CIs computed; Figures 1–4 and Tables 3–4 generated |
| 5 — Writing | Pre-submission checklist in Blueprint §6 Phase 5 passes completely |

If Phase 3 shows no FPR dispersion, consult Blueprint §1.4 (Null-Finding Contingency) before proceeding to Phase 4. Do not invest Phase 4 compute before recording the contingency decision.

---

## 5. Documentation Rules

- The **Documentation Agent** owns all documentation. No other agent modifies `docs/`, `EXPERIMENT_GUIDE.md`, or paper section drafts.
- Documentation reflects only what is **actually implemented and verified**. Never document planned or aspirational behavior as present.
- `EXPERIMENT_GUIDE.md` must show the full merged config chain for each important run type. A user must not need to read seven YAML files to understand "B1 + Regime A".
- `VERSIONING.md` explains why key dependencies are pinned (especially `flwr`, Ray, `torch`).
- Every figure and table in the paper must reference a specific run output file. Placeholder numbers are never committed to paper drafts.

---

## 6. Agent Roles (Summary)

Detailed agent definitions are in `.claude/agents/`. Quick reference:

| Agent | Primary Responsibility |
|---|---|
| Orchestrator | Routes tasks; tracks phase gates; never writes code |
| Coding Agent | Implements per Blueprint + CLAUDE.md rules |
| Review Agent | Reviews against repo rules, not generic clean-code advice |
| Drift Agent | Watches for scientific, config, and architectural drift |
| Test/QA Agent | Owns execution gates and the determinism test suite |
| Sweep Guard Agent | Blocks long runs if P0 prerequisites are not satisfied |
| Documentation Agent | Documents only what is actually implemented |
| Scientific Contract Agent | Protects controlled-experiment invariants |
| Spec/Ticket Agent | Translates Blueprint phases into executable tickets |

---

## 7. Meta-Rules

**Temporary postmortem and review files** are consumed at the start of the next work cycle: lessons are extracted into durable rules (this file, AGENTS.md, agent definitions), and the source file is deleted. No temporary analysis file is preserved in the repository after extraction is complete.

**No architecture layers not required by the spec.** The suggested project structure in the REVIEW is a reorganization of existing responsibilities, not the addition of new tiers. If a proposed module is empty after mapping current code, it is not created.

**No causal overstatements.** Use "is consistent with", "evaluates whether", "tests whether" rather than "confirms", "proves", "establishes" — in code comments, log messages, and paper prose.

**Baseline audit warning rule.** B0 is a centralized reference and must pass the AUROC/PR-AUC sanity gate before paper generation. B3 is diagnostic and taxonomy too coarse warnings must not be hidden. Paper generation must not overclaim any baseline.

<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan
<!-- SPECKIT END -->

## 8. Durable Spec and Task References

The following files in `docs/` are the canonical implementation-ready artifacts derived from Blueprint.md and the Apr 2026 engineering audit. They extend and detail this file but never contradict it.

| File | Purpose |
|---|---|
| `docs/spec.md` | Formal specification: full scientific contract, module boundaries, dataset specs, baseline formulas |
| `docs/gates.md` | Phase gate conditions and acceptance criteria with testable verification commands |
| `docs/tasks.md` | Implementation-ready tickets, dependency order, agent ownership, and gate relevance |
| `docs/engineering-rules.md` | Durable engineering rules extracted from the Apr 2026 113-run audit |

All agents must read `docs/spec.md` before acting on any task that touches threshold logic, baseline definitions, data processing, or the FL training path.
