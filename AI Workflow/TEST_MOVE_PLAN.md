# Test Move Plan

This file records concrete test movement plans for the DATP test suite.

It is separate from:

```text
AI Workflow/MOVE_PLAN.md
```

because `MOVE_PLAN.md` is scoped to `src/datp`, while this file is scoped to:

```text
tests
```

---

## Scope

This move plan applies only to:

```text
tests
```

Tests must move with production ownership.

Tests must not preserve old internal paths.

---

## No-backwards-compatibility rule

No backwards compatibility is allowed for internal test moves.

Do not leave:

```text
redirect tests
wrapper tests
alias-preservation tests
old-path import tests
tests that only validate obsolete package names
tests that keep obsolete import paths alive
```

Update all imports directly.

Move tests to the new ownership.

Delete obsolete test folders after imports are corrected.

Do not mark moved tests as skipped or xfailed.

---

## Target architecture source

The annotated target test tree lives in:

```text
AI Workflow/TEST_REFACTOR_MAP.md
```

The current repository reality map lives in:

```text
AI Workflow/state/PROJECT_MAP.md
```

`PROJECT_MAP.md` must record completed moves only after the real repository changes.

---

## Test move batches

### Batch T1 — CLI and modeling test ownership

| Move ID | Source | Target | Reason | Status |
|---|---|---|---|---|
| TMOVE-001 | `tests/unit/cli` | `tests/unit/app/cli` | CLI is now an application entrypoint layer. | `PLANNED` |
| TMOVE-002 | `tests/unit/models/test_model.py` | `tests/unit/modeling/test_autoencoder.py` | Autoencoder belongs to modeling. | `PLANNED` |
| TMOVE-003 | `tests/unit/models/test_cuda_placement.py` | `tests/unit/modeling/test_cuda_placement.py` | Model placement belongs to modeling. | `PLANNED` |
| TMOVE-004 | `tests/unit/training/test_factories.py` | `tests/unit/modeling/test_factories.py` or `tests/unit/federated/test_factories.py` | Decide after inspecting whether the factory builds models or federated objects. | `TO_INSPECT` |

Required checks:

```bash
python -m ruff check src/datp tests
python -m pyright
python -m pytest tests/unit/app/cli tests/unit/modeling
```

---

### Batch T2 — Training tests to federated/scoring

| Move ID | Source | Target | Reason | Status |
|---|---|---|---|---|
| TMOVE-005 | `tests/unit/training/protocols/test_fedprox.py` | `tests/unit/federated/protocols/test_fedprox.py` | FedProx protocol belongs under federated. | `PLANNED` |
| TMOVE-006 | `tests/unit/training/protocols/test_fedrep.py` | `tests/unit/federated/protocols/test_fedrep.py` | FedRep protocol belongs under federated. | `PLANNED` |
| TMOVE-007 | Add `tests/unit/federated/protocols/test_fedavg.py` if missing | `tests/unit/federated/protocols/test_fedavg.py` | Canonical FedAvg protocol should have explicit test ownership. | `TO_INSPECT` |
| TMOVE-008 | `tests/unit/training/test_catalog.py` | `tests/unit/federated/test_catalog.py` | Federated protocol registry belongs under federated. | `PLANNED` |
| TMOVE-009 | `tests/unit/training/test_convergence.py` | `tests/unit/federated/test_convergence.py` | Convergence belongs under federated. | `PLANNED` |
| TMOVE-010 | `tests/unit/training/test_determinism.py` | `tests/unit/federated/test_determinism.py` | Federated deterministic behavior belongs under federated. | `PLANNED` |
| TMOVE-011 | `tests/unit/training/test_local.py` | `tests/unit/federated/test_local_training.py` | Local client training loop belongs under federated. | `PLANNED` |
| TMOVE-012 | `tests/unit/training/test_parameters.py` | `tests/unit/federated/test_parameters.py` | Parameter serialization belongs under federated. | `PLANNED` |
| TMOVE-013 | `tests/unit/training/test_runtime.py` | `tests/unit/federated/test_runtime.py` | Federated runtime checks belong under federated. | `PLANNED` |
| TMOVE-014 | `tests/unit/training/test_simulation.py` | `tests/unit/federated/test_simulation.py` | Simulation helpers belong under federated. | `PLANNED` |
| TMOVE-015 | `tests/unit/training/test_types.py` | `tests/unit/federated/test_types.py` | Federated dataclasses belong under federated. | `PLANNED` |
| TMOVE-016 | `tests/unit/training/test_scoring.py` | `tests/unit/scoring/test_generation.py` or `tests/unit/scoring/test_schemas.py` | Scoring is a separate stage after training; split by actual behavior. | `TO_INSPECT` |
| TMOVE-017 | `tests/integration/training/test_comm_overhead.py` | `tests/integration/federated/test_communication.py` | Communication-cost integration belongs under federated. | `PLANNED` |
| TMOVE-018 | `tests/integration/training/test_fl_simulation.py` | `tests/integration/federated/test_fl_simulation.py` | FL simulation integration belongs under federated. | `PLANNED` |
| TMOVE-019 | `tests/integration/training/test_train_once.py` | `tests/integration/federated/test_train_once.py` | Shared-training invariant belongs under federated integration. | `PLANNED` |
| TMOVE-020 | `tests/integration/training/test_score_artifacts.py` | `tests/integration/scoring/test_score_artifacts.py` | Score artifacts belong under scoring. | `PLANNED` |

Required checks:

```bash
python -m ruff check src/datp tests
python -m pyright
python -m pytest tests/unit/federated tests/unit/scoring tests/integration/federated tests/integration/scoring
```

Scientific checks:

```text
B1-B4 must still share score artifacts.
Training tests must not become thresholding tests.
Scoring tests must not trigger threshold derivation unless explicitly testing the stage seam.
```

---

### Batch T3 — Baseline tests to thresholding

| Move ID | Source | Target | Reason | Status |
|---|---|---|---|---|
| TMOVE-021 | `tests/unit/baselines/main/test_baseline_b0.py` | `tests/unit/thresholding/strategies/test_b0_centralized.py` | B0 is centralized reference comparator. | `PLANNED` |
| TMOVE-022 | `tests/unit/baselines/main/test_threshold_strategies.py` | Split into `tests/unit/thresholding/strategies/test_b1_global.py`, `test_b2_personalized.py`, `test_b3_family.py`, `test_b4_cluster.py` | B1-B4 strategy tests should be explicit. | `TO_SPLIT` |
| TMOVE-023 | `tests/unit/baselines/main/test_b4_clustering.py` | `tests/unit/thresholding/strategies/test_b4_cluster.py` | B4 clustering belongs under thresholding strategy. | `PLANNED` |
| TMOVE-024 | `tests/unit/baselines/main/test_thresholds.py` | `tests/unit/thresholding/test_thresholds.py` | Shared threshold math belongs under thresholding. | `PLANNED` |
| TMOVE-025 | `tests/unit/baselines/main/test_return_types.py` | `tests/unit/thresholding/test_return_types.py` | Threshold result types belong under thresholding. | `PLANNED` |
| TMOVE-026 | `tests/unit/baselines/common/test_training.py` | `tests/unit/thresholding/test_evaluation_helpers.py` or `tests/unit/federated` | Decide after inspecting what it actually verifies. | `TO_INSPECT` |
| TMOVE-027 | `tests/integration/baselines/main/test_baseline_scope.py` | `tests/integration/thresholding/test_baseline_scope.py` | Baseline scope/restriction behavior belongs under thresholding. | `PLANNED` |
| TMOVE-028 | `tests/integration/baselines/main/test_result_layout.py` | `tests/integration/thresholding/test_result_layout.py` | Result layout and shared score/checkpoint semantics belong under thresholding integration. | `PLANNED` |

Required checks:

```bash
python -m ruff check src/datp tests
python -m pyright
python -m pytest tests/unit/thresholding tests/integration/thresholding
```

Scientific checks:

```text
B1-B4 semantics must not change.
Calibration-Pending behavior must not change.
B3/B4 regime restrictions must remain covered.
Score/checkpoint paths must remain shared across B1-B4.
```

---

### Batch T4 — Threshold variants and comparators

| Move ID | Source | Target | Reason | Status |
|---|---|---|---|---|
| TMOVE-029 | `tests/unit/analyses/threshold_variants/test_b2_conformal.py` | `tests/unit/thresholding/variants/test_b2_conformal.py` | B2 conformal is a threshold variant. | `PLANNED` |
| TMOVE-030 | `tests/unit/analyses/threshold_variants/test_calibration_size_sweep.py` | `tests/unit/thresholding/variants/test_calibration_size_sweep.py` | Calibration-size sensitivity belongs under threshold variants. | `PLANNED` |
| TMOVE-031 | `tests/unit/analyses/threshold_variants/test_q_sensitivity.py` | `tests/unit/thresholding/variants/test_q_sensitivity.py` | Quantile sensitivity belongs under threshold variants. | `PLANNED` |
| TMOVE-032 | `tests/unit/analyses/threshold_variants/test_tau_shrinkage.py` | `tests/unit/thresholding/variants/test_tau_shrinkage.py` | Tau shrinkage belongs under threshold variants. | `PLANNED` |
| TMOVE-033 | `tests/unit/analyses/comparators/test_fedstats_benign.py` | `tests/unit/thresholding/comparators/test_fedstats_benign.py` | FedStats benign is a threshold comparator. | `PLANNED` |

Required checks:

```bash
python -m ruff check src/datp tests
python -m pyright
python -m pytest tests/unit/thresholding/variants tests/unit/thresholding/comparators
```

---

### Batch T5 — Pipeline and sweep tests to experiments

| Move ID | Source | Target | Reason | Status |
|---|---|---|---|---|
| TMOVE-034 | `tests/unit/pipeline/test_diagnostic.py` | `tests/unit/experiments/test_diagnostic.py` | Diagnostic workflow is experiment orchestration. | `PLANNED` |
| TMOVE-035 | `tests/unit/pipeline/test_executor.py` | `tests/unit/experiments/test_executor.py` | Executor belongs under experiments. | `PLANNED` |
| TMOVE-036 | `tests/unit/pipeline/test_models.py` | `tests/unit/experiments/test_models.py` | Experiment dataclasses belong under experiments. | `PLANNED` |
| TMOVE-037 | `tests/unit/sweep/test_data_preparation.py` | `tests/unit/experiments/stages/test_prepare_data.py` | Data preparation stage belongs under experiments/stages. | `PLANNED` |
| TMOVE-038 | `tests/unit/sweep/test_sweep.py` | `tests/unit/experiments/test_sweep.py` | Sweep runner belongs under experiments. | `PLANNED` |
| TMOVE-039 | `tests/integration/sweep` | `tests/integration/experiments` | Sweep integration belongs under experiments. | `TO_INSPECT` |
| TMOVE-040 | `tests/integration/diagnostic/test_smoke_env.py` | `tests/integration/federated/test_flower_smoke_env.py` | If it validates Flower/Ray environment, it belongs under federated. | `TO_INSPECT` |
| TMOVE-041 | `tests/integration/diagnostic/test_prepare_load_path_consistency.py` | `tests/integration/data/test_prepare_load_path_consistency.py` | If it validates prepare/load data paths, it belongs under data integration. | `TO_INSPECT` |

Required checks:

```bash
python -m ruff check src/datp tests
python -m pyright
python -m pytest tests/unit/experiments tests/integration/experiments tests/integration/data tests/integration/federated
```

---

### Batch T6 — Audit tests to validation

| Move ID | Source | Target | Reason | Status |
|---|---|---|---|---|
| TMOVE-042 | `tests/unit/audit/test_ciciot_homogeneity.py` | `tests/unit/validation/test_ciciot_homogeneity.py` | CICIoT homogeneity is validation. | `PLANNED` |
| TMOVE-043 | `tests/unit/audit/test_metric_reproducer.py` | `tests/unit/validation/test_metric_reproducer.py` | Metric reproduction is validation. | `PLANNED` |
| TMOVE-044 | `tests/unit/audit/test_regime_c_alpha_audit.py` | `tests/unit/validation/test_regime_c_alpha_audit.py` | Regime C alpha coverage is validation. | `PLANNED` |
| TMOVE-045 | `tests/unit/audit/test_results_audit.py` | `tests/unit/validation/test_results.py` | Result audit belongs under validation. | `PLANNED` |
| TMOVE-046 | `tests/unit/audit/test_score_manifest_verifier.py` | `tests/unit/validation/test_score_manifest.py` | Score manifest verification is validation. | `PLANNED` |
| TMOVE-047 | `tests/unit/audit/test_shared_invariants.py` | `tests/unit/validation/test_shared_invariants.py` | Shared invariants are validation. | `PLANNED` |
| TMOVE-048 | `tests/unit/audit/test_threshold_parity.py` | `tests/unit/validation/test_threshold_parity.py` | Threshold parity audit is validation. | `PLANNED` |
| TMOVE-049 | `tests/unit/audit/test_verdicts.py` | `tests/unit/validation/test_verdicts.py` | Verdict composition belongs under validation. | `PLANNED` |

Required checks:

```bash
python -m ruff check src/datp tests
python -m pyright
python -m pytest tests/unit/validation tests/integration/validation
```

---

### Batch T7 — Analysis common flattening

| Move ID | Source | Target | Reason | Status |
|---|---|---|---|---|
| TMOVE-050 | `tests/unit/analyses/common/test_cells.py` | `tests/unit/analyses/test_cells.py` | Analysis-cell helpers move out of common. | `PLANNED` |
| TMOVE-051 | `tests/unit/analyses/common/test_evaluation.py` | `tests/unit/analyses/test_evaluation.py` | Analysis evaluation helpers move out of common. | `PLANNED` |
| TMOVE-052 | `tests/unit/analyses/common/test_io.py` | `tests/unit/analyses/test_io.py` | Analysis I/O helpers move out of common. | `PLANNED` |
| TMOVE-053 | `tests/unit/analyses/common/test_plotting.py` | `tests/unit/analyses/test_plotting.py` | Analysis plotting helpers move out of common. | `PLANNED` |
| TMOVE-054 | `tests/unit/analyses/common/test_runners.py` | `tests/unit/analyses/test_runners.py` | Analysis runners move out of common. | `PLANNED` |
| TMOVE-055 | `tests/unit/analyses/common/test_types.py` | `tests/unit/analyses/test_types.py` | Analysis types move out of common. | `PLANNED` |
| TMOVE-056 | `tests/unit/analyses/conftest.py` | Keep or split into `tests/fixtures/scores.py` | Shared score-cell builders should become fixtures if reused elsewhere. | `TO_INSPECT` |

Required checks:

```bash
python -m ruff check src/datp tests
python -m pyright
python -m pytest tests/unit/analyses
```

---

### Batch T8 — E2E folder cleanup

| Move ID | Source | Target | Reason | Status |
|---|---|---|---|---|
| TMOVE-057 | `tests/e2e/regime_a/test_regime_a_e2e.py` | `tests/e2e/regimes/test_regime_a_e2e.py` | Group regime E2E tests under a shared regimes folder. | `PLANNED` |
| TMOVE-058 | `tests/e2e/regime_b/test_regime_b_e2e.py` | `tests/e2e/regimes/test_regime_b_e2e.py` | Group regime E2E tests under a shared regimes folder. | `PLANNED` |
| TMOVE-059 | `tests/e2e/regime_c/test_regime_c_e2e.py` | `tests/e2e/regimes/test_regime_c_e2e.py` | Group regime E2E tests under a shared regimes folder. | `PLANNED` |

Required checks:

```bash
python -m ruff check tests/e2e
python -m pytest tests/e2e/diagnostic tests/e2e/regimes -m e2e
```

Do not run E2E by default unless the packet explicitly authorizes it.

For structure-only E2E moves, collection-only is acceptable first:

```bash
python -m pytest --collect-only tests/e2e
```

---

### Batch T9 — Fixtures cleanup

| Move ID | Source | Target | Reason | Status |
|---|---|---|---|---|
| TMOVE-060 | `tests/fixtures/payloads.py` | `tests/fixtures/metrics_payloads.py` | Name should describe metrics/result payloads. | `PLANNED` |
| TMOVE-061 | Repeated local score builders in tests | `tests/fixtures/scores.py` | Avoid duplicated score-cell fixture logic. | `TO_INSPECT` |
| TMOVE-062 | Repeated config builders in tests | `tests/fixtures/configs.py` | Avoid duplicated test config setup. | `TO_INSPECT` |
| TMOVE-063 | Repeated synthetic data builders in tests | `tests/fixtures/datasets.py` and `tests/fixtures/dataframes.py` | Avoid duplicated dataset/dataframe setup. | `TO_INSPECT` |
| TMOVE-064 | Repeated client-data builders in tests | `tests/fixtures/federated.py` | Avoid duplicated FL test setup. | `TO_INSPECT` |

Required checks:

```bash
python -m ruff check tests
python -m pyright
python -m pytest tests/unit tests/integration --ignore=tests/e2e
```

Run targeted tests first before broad package tests.

---

## Deleted/retired test folders ledger

| Old folder | Replacement | Reason | Imports updated | Status |
|---|---|---|---|---|
| `tests/unit/baselines` | `tests/unit/thresholding` | Baselines moved to thresholding ownership. | `PENDING` | `PLANNED` |
| `tests/unit/training` | `tests/unit/federated` and `tests/unit/scoring` | Training split into federated and scoring ownership. | `PENDING` | `PLANNED` |
| `tests/unit/models` | `tests/unit/modeling` | Models renamed to modeling. | `PENDING` | `PLANNED` |
| `tests/unit/pipeline` | `tests/unit/experiments` | Pipeline renamed to experiments. | `PENDING` | `PLANNED` |
| `tests/unit/sweep` | `tests/unit/experiments` | Sweep merged into experiments. | `PENDING` | `PLANNED` |
| `tests/unit/audit` | `tests/unit/validation` | Audit renamed to validation. | `PENDING` | `PLANNED` |
| `tests/unit/analyses/common` | `tests/unit/analyses` | Analysis common flattened. | `PENDING` | `PLANNED` |
| `tests/unit/analyses/threshold_variants` | `tests/unit/thresholding/variants` | Threshold variants belong under thresholding. | `PENDING` | `PLANNED` |
| `tests/unit/analyses/comparators` | `tests/unit/thresholding/comparators` | Threshold comparators belong under thresholding. | `PENDING` | `PLANNED` |
| `tests/integration/baselines` | `tests/integration/thresholding` | Threshold integration behavior belongs under thresholding. | `PENDING` | `PLANNED` |
| `tests/integration/training` | `tests/integration/federated` and `tests/integration/scoring` | Training split into federated and scoring. | `PENDING` | `PLANNED` |
| `tests/integration/sweep` | `tests/integration/experiments` | Sweep belongs under experiments. | `PENDING` | `PLANNED` |

---

## Import impact checklist

For every test move:

1. Search all imports in the moved tests.
2. Update production imports to new canonical package paths.
3. Update fixture imports.
4. Update `pytest` path references in workflow files.
5. Update test package paths in `TEST_IMPACT_MAP.md`.
6. Remove stale old-path imports.
7. Remove old test folders after imports are fixed.
8. Do not add redirect tests.
9. Do not add wrapper tests.
10. Do not add alias-preservation tests.
11. Run targeted tests.
12. Run Ruff.
13. Run Pyright.
14. Update `PROJECT_MAP.md`.
15. Mark the batch `REAUDIT_REQUIRED`.

---

## Scientific test coverage checklist

After moving tests, verify the new structure still covers:

1. B1-B4 do not retrain.
2. B1-B4 share score artifacts.
3. Checkpoint paths are baseline-independent for B1-B4.
4. Score paths are baseline-independent for B1-B4.
5. Result paths remain baseline-specific.
6. Calibration-Pending behavior remains covered.
7. B3 regime restrictions remain covered.
8. B4 clustering behavior remains covered.
9. Score artifact schema remains covered.
10. Metric recomputation/parity remains covered.
11. Report generation does not recompute upstream artifacts.
12. E2E tests remain marked and heavy by default.

---

## Completion rule

No test move batch is `DONE` after the first passing check.

Use:

```text
REAUDIT_REQUIRED
```

until a later pass confirms:

1. No stale old test folders remain.
2. No old internal import-path tests remain.
3. No redirect tests remain.
4. No wrapper tests remain.
5. No alias-preservation tests remain.
6. Impacted tests pass.
7. Ruff passes.
8. Pyright passes.
9. `PROJECT_MAP.md` reflects actual test reality.
10. Scientific-contract test coverage remains valid.