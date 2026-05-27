# Test Refactor Map

This file records the intended responsibility boundaries for the DATP `tests` package.

It is not a current-state map.

It is not a vague wish list.

It is the target architecture contract for reorganizing tests after the agent inspects the real test suite.

The current repository reality map lives in:

```text
AI Workflow/state/PROJECT_MAP.md
```

`TEST_REFACTOR_MAP.md` records intended test ownership.

`PROJECT_MAP.md` records current repository reality.

If both disagree, inspect the real repository first, then update the stale file.

---

## Scope

This map applies only to:

```text
tests
```

It is linked to the `src/datp` ownership refactor, but it must not silently change production behavior.

Tests must move with production ownership.

Tests must validate behavior, not preserve old internal paths.

---

## Non-negotiable test refactor rule

No backwards compatibility is allowed for internal test moves.

Do not leave:

```text
redirect tests
wrapper tests
alias-preservation tests
old package-path tests
old import-path tests
tests that validate old internal module names
tests that exist only to keep obsolete paths alive
```

Do not create tests whose only purpose is to prove old paths still import.

Do not mark failing import tests as skipped.

Do not mark failing import tests as xfailed.

Do not weaken tests to make the refactor pass.

Update every import properly.

Move test files to the new ownership.

Delete obsolete test folders after imports are corrected.

---

## Test ownership rule

Tests must mirror the responsibility of the production code they verify.

Old production ownership:

```text
src/datp/baselines
src/datp/training
src/datp/models
src/datp/pipeline
src/datp/sweep
src/datp/audit
```

New production ownership:

```text
src/datp/thresholding
src/datp/federated
src/datp/modeling
src/datp/experiments
src/datp/validation
src/datp/scoring
```

Therefore tests must move from old ownership to new ownership.

---

## Required old-to-new test ownership mapping

```text
tests/unit/baselines        -> tests/unit/thresholding
tests/unit/training         -> tests/unit/federated and tests/unit/scoring
tests/unit/models           -> tests/unit/modeling
tests/unit/pipeline         -> tests/unit/experiments
tests/unit/sweep            -> tests/unit/experiments
tests/unit/audit            -> tests/unit/validation
tests/unit/analyses/common  -> tests/unit/analyses
tests/unit/analyses/threshold_variants -> tests/unit/thresholding/variants
tests/unit/analyses/comparators        -> tests/unit/thresholding/comparators

tests/integration/baselines -> tests/integration/thresholding
tests/integration/training  -> tests/integration/federated and tests/integration/scoring
tests/integration/sweep     -> tests/integration/experiments
tests/integration/diagnostic -> tests/integration/experiments or tests/integration/data depending on the verified behavior

tests/e2e/regime_a -> tests/e2e/regimes/test_regime_a_e2e.py
tests/e2e/regime_b -> tests/e2e/regimes/test_regime_b_e2e.py
tests/e2e/regime_c -> tests/e2e/regimes/test_regime_c_e2e.py
```

---

## Target `tests` structure with file responsibilities

```text
tests
├── conftest.py                         # Global pytest lifecycle hooks: Ray shutdown, MLflow cleanup, heap release, shared test environment safety.

├── fixtures                            # Test-only builders and reusable payloads. No production logic.
│   ├── __init__.py
│   ├── artifacts.py                    # Synthetic output/checkpoint/result/manifest path helpers.
│   ├── configs.py                      # Small valid config builders for unit/integration tests.
│   ├── dataframes.py                   # Synthetic pandas/polars dataframe builders.
│   ├── datasets.py                     # Synthetic N-BaIoT/CICIoT/Edge-IIoT raw and processed dataset builders.
│   ├── federated.py                    # Synthetic FL client data and federated runtime fixtures.
│   ├── metrics_payloads.py             # Valid metrics/result JSON payloads. Replacement for `payloads.py`.
│   ├── scores.py                       # Synthetic score-cell builders, scoring manifests, and reconstruction-error parquet writers.
│   └── thresholds.py                   # Threshold inputs, eligible/pending clients, and comparison fixtures.

├── e2e                                 # End-to-end smoke tests only. Heavy by default; do not run casually.
│   ├── conftest.py                     # Tiny raw-data fixtures for E2E tests only.
│   ├── diagnostic
│   │   └── test_diagnostic_e2e.py      # Tiny diagnostic pipeline E2E: prepare -> train -> score -> threshold -> evaluate.
│   └── regimes
│       ├── test_regime_a_e2e.py        # Tiny Regime A E2E using N-BaIoT-style physical-device split.
│       ├── test_regime_b_e2e.py        # Tiny Regime B E2E using CICIoT-style external validation flow.
│       └── test_regime_c_e2e.py        # Tiny Regime C E2E using Dirichlet virtual-client partition.

├── integration                         # Cross-package behavior tests. Verifies stage seams and artifact contracts.
│   ├── data
│   │   ├── datasets
│   │   │   ├── ciciot2023
│   │   │   │   └── test_prepare_ciciot2023.py     # CICIoT schema, cap, parquet output, calibration/eval flags.
│   │   │   ├── edge_iiotset
│   │   │   │   └── test_edge_iiotset_spec.py      # Edge-IIoTset spec and dataset-contract integration checks.
│   │   │   └── nbaiot
│   │   │       └── test_prepare_nbaiot.py         # N-BaIoT device count, feature count, split ratios, no-leak checks.
│   │   ├── regimes
│   │   │   ├── test_regime_a_prepare.py           # Regime A preparation contract if separate from dataset prepare.
│   │   │   ├── test_regime_b_prepare.py           # Regime B preparation contract and CICIoT client layout.
│   │   │   └── test_regime_c_partition.py         # Regime C alpha levels, manifests, JS divergence, mixtures.
│   │   ├── test_data_audit.py                     # Dataset audit JSON/schema integration behavior.
│   │   └── test_prepare_load_path_consistency.py  # Prepared-data path consistency with client-data loading.

│   ├── federated
│   │   ├── test_communication.py        # Model and threshold communication-cost calculations.
│   │   ├── test_fl_simulation.py        # Tiny Flower/Ray/FedAvg simulation smoke tests.
│   │   └── test_train_once.py           # Shared training invariant: one checkpoint/score path across B1-B4.

│   ├── scoring
│   │   ├── test_score_artifacts.py      # Score parquet files, score manifest, score column schema.
│   │   └── test_score_loading.py        # Loading saved score artifacts from canonical paths.

│   ├── thresholding
│   │   ├── test_baseline_scope.py       # B3/B4 allowed-regime restrictions and threshold-scope behavior.
│   │   ├── test_result_layout.py        # Result paths are baseline-specific; score/checkpoint paths are shared.
│   │   └── test_threshold_pipeline.py   # Saved scores -> thresholds -> evaluation, without training calls.

│   ├── experiments
│   │   ├── test_diagnostic_workflow.py  # Diagnostic orchestration stage behavior.
│   │   ├── test_executor.py             # Experiment executor lifecycle and stage ordering.
│   │   ├── test_sweep.py                # Sweep orchestration without running heavy experiments.
│   │   └── test_preflight_validator.py  # Experiment preflight validation.

│   ├── validation
│   │   ├── test_scientific_invariants.py     # No retraining per baseline and no downstream training calls.
│   │   ├── test_score_manifest_validation.py # Score manifest reuse-safety validation.
│   │   └── test_result_validation.py         # Result completeness and metrics file validation.

│   └── reporting
│       └── test_report_build_integration.py  # Reporting consumes existing artifacts; no upstream recomputation.

├── unit                                # Unit tests mirror new `src/datp` package ownership.
│   ├── app
│   │   └── cli
│   │       └── test_status.py           # CLI status command behavior.

│   ├── artifacts
│   │   ├── test_artifacts.py            # Artifact constants and descriptors.
│   │   ├── test_paths.py                # Canonical path builders.
│   │   └── test_results_exist.py        # Result-existence semantics.

│   ├── config
│   │   ├── test_config_preview.py       # Config preview/compose behavior.
│   │   └── test_config_validation.py    # Typed config validation rules.

│   ├── core
│   │   ├── test_device.py               # Device resolution and CUDA/CPU behavior.
│   │   ├── test_log_rotation.py         # Logging setup and rotation behavior.
│   │   └── test_seeds.py                # Deterministic seeding.

│   ├── domain
│   │   ├── test_artifacts.py            # Artifact domain vocabulary.
│   │   ├── test_baselines.py            # Baseline enum and labels.
│   │   ├── test_regimes.py              # Regime enum and labels.
│   │   └── test_thresholds.py           # Threshold-scope vocabulary.

│   ├── data
│   │   ├── io
│   │   │   ├── test_audit.py            # Dataset-level audit helpers.
│   │   │   ├── test_schemas.py          # Dataframe/parquet schemas.
│   │   │   └── test_storage.py          # Parquet read/write behavior.
│   │   ├── datasets
│   │   │   ├── ciciot2023
│   │   │   │   └── test_prepare.py      # CICIoT preparation units.
│   │   │   ├── edge_iiotset
│   │   │   │   └── test_spec.py         # Edge-IIoTset spec units.
│   │   │   └── nbaiot
│   │   │       ├── test_family_map.py   # N-BaIoT family/device metadata.
│   │   │       └── test_prepare.py      # N-BaIoT preparation units.
│   │   ├── regimes
│   │   │   ├── test_regime_a.py         # Regime A units.
│   │   │   ├── test_regime_b.py         # Regime B units.
│   │   │   └── test_regime_c.py         # Regime C units.
│   │   ├── test_canonical_owners.py     # Data ownership and path conflict checks.
│   │   └── test_paths_conflict.py       # Guard against conflicting data paths.

│   ├── modeling
│   │   ├── test_activations.py          # Activation factory behavior.
│   │   ├── test_autoencoder.py          # Autoencoder shape/forward behavior.
│   │   ├── test_cuda_placement.py       # Model placement behavior.
│   │   └── test_factories.py            # Model construction from config.

│   ├── federated
│   │   ├── protocols
│   │   │   ├── test_fedavg.py           # Canonical FedAvg protocol behavior.
│   │   │   ├── test_fedprox.py          # FedProx stress protocol behavior.
│   │   │   └── test_fedrep.py           # FedRep/FedPer-style protocol behavior.
│   │   ├── test_catalog.py              # Federated protocol registry.
│   │   ├── test_checkpoints.py          # Shared checkpoint save/load behavior.
│   │   ├── test_clients.py              # FL client wrapper behavior.
│   │   ├── test_communication.py        # Communication accounting units.
│   │   ├── test_convergence.py          # Convergence window/threshold logic.
│   │   ├── test_determinism.py          # Federated deterministic behavior.
│   │   ├── test_local_training.py       # Local AE training loop.
│   │   ├── test_parameters.py           # Parameter serialization/deserialization.
│   │   ├── test_runtime.py              # Federated runtime/resource checks.
│   │   ├── test_simulation.py           # Simulation helper units.
│   │   ├── test_strategies.py           # FL strategy construction.
│   │   └── test_types.py                # Federated dataclasses/types.

│   ├── scoring
│   │   ├── test_generation.py           # Reconstruction-error generation from trained model.
│   │   ├── test_loading.py              # Load saved cal/test score artifacts.
│   │   ├── test_manifest.py             # Scoring manifest validation.
│   │   ├── test_provider.py             # ScoreProvider access patterns.
│   │   └── test_schemas.py              # Score artifact schema and score column validation.

│   ├── thresholding
│   │   ├── strategies
│   │   │   ├── test_b0_centralized.py   # B0 centralized reference comparator.
│   │   │   ├── test_b1_global.py        # B1 shared/global threshold.
│   │   │   ├── test_b2_personalized.py  # B2 per-client threshold.
│   │   │   ├── test_b3_family.py        # B3 family/group threshold.
│   │   │   └── test_b4_cluster.py       # B4 fingerprint-cluster threshold.
│   │   ├── variants
│   │   │   ├── test_b2_conformal.py     # Split-conformal B2 variant.
│   │   │   ├── test_calibration_size_sweep.py # Calibration-size sensitivity.
│   │   │   ├── test_q_sensitivity.py    # Quantile sensitivity.
│   │   │   └── test_tau_shrinkage.py    # Threshold shrinkage variant.
│   │   ├── comparators
│   │   │   └── test_fedstats_benign.py  # Benign-only FedStats threshold comparator.
│   │   ├── test_eligibility.py          # Calibration eligibility and Calibration-Pending fallback.
│   │   ├── test_evaluation_helpers.py   # Threshold application helpers.
│   │   ├── test_metrics_serialization.py # Threshold/result metric serialization.
│   │   ├── test_return_types.py         # Threshold result dataclasses.
│   │   └── test_thresholds.py           # Shared threshold math.

│   ├── evaluation
│   │   ├── test_artifact_validation.py  # Evaluation artifact preconditions.
│   │   ├── test_confusion.py            # Confusion matrix/count helpers.
│   │   ├── test_eligibility.py          # Evaluation-time coverage/client inclusion.
│   │   ├── test_metric_keys.py          # Metric key names.
│   │   ├── test_metrics.py              # CV(FPR), Macro-F1, BA, client/global metrics.
│   │   └── test_ranking.py              # Baseline ranking/comparison helpers.

│   ├── experiments
│   │   ├── stages
│   │   │   ├── test_prepare_data.py     # Data-preparation stage orchestration.
│   │   │   ├── test_train_encoder.py    # Shared FL encoder training stage orchestration.
│   │   │   ├── test_generate_scores.py  # Score-generation stage orchestration.
│   │   │   ├── test_derive_thresholds.py # Threshold stage orchestration.
│   │   │   ├── test_evaluate_results.py # Evaluation stage orchestration.
│   │   │   └── test_build_report.py     # Report stage orchestration.
│   │   ├── test_console.py              # Experiment console/progress output.
│   │   ├── test_diagnostic.py           # Diagnostic workflow units.
│   │   ├── test_executor.py             # Executor units.
│   │   ├── test_models.py               # Experiment dataclasses.
│   │   ├── test_sweep.py                # Sweep units.
│   │   └── test_validator.py            # Preflight validator units.

│   ├── analyses
│   │   ├── test_cells.py                # Analysis-cell discovery/filtering.
│   │   ├── test_evaluation.py           # Analysis-specific metric helpers.
│   │   ├── test_io.py                   # Analysis CSV/JSON I/O.
│   │   ├── test_plotting.py             # Analysis plotting helpers.
│   │   ├── test_runners.py              # Analysis runner wrapper behavior.
│   │   ├── test_types.py                # Analysis result dataclasses.
│   │   ├── mechanism
│   │   │   ├── test_b3_preservation.py  # B3 preservation analysis.
│   │   │   ├── test_b4_cluster_ablation.py # B4 feature ablation.
│   │   │   ├── test_js_divergence_benefit.py # JS divergence vs benefit analysis.
│   │   │   ├── test_per_client_cdf.py   # Per-client CDF/failure-mode analysis.
│   │   │   └── test_threshold_shift.py  # Threshold shift analysis.
│   │   ├── robustness
│   │   │   ├── test_alert_burden.py     # Alert-burden suppression/reporting.
│   │   │   ├── test_regime_c_severity.py # Regime C severity analysis.
│   │   │   └── test_stress_test_absorption.py # Stress-test absorption analysis.
│   │   └── temporal
│   │       └── test_temporal_recalibration.py # Chronological recalibration analysis.

│   ├── validation
│   │   ├── test_ciciot_homogeneity.py   # CICIoT homogeneity validation.
│   │   ├── test_convergence.py          # Convergence artifact validation.
│   │   ├── test_datasets.py             # Dataset schema/count validation.
│   │   ├── test_discovery.py            # Run/cell/result discovery.
│   │   ├── test_metric_reproducer.py    # Metric recomputation from artifacts.
│   │   ├── test_regime_c_alpha_audit.py # Regime C alpha coverage validation.
│   │   ├── test_results.py              # Result completeness validation.
│   │   ├── test_score_manifest.py       # Score manifest verifier.
│   │   ├── test_shared_invariants.py    # Shared training and no-retraining checks.
│   │   ├── test_threshold_parity.py     # Threshold recomputation parity.
│   │   └── test_verdicts.py             # Validation verdict types/composition.

│   ├── reporting
│   │   ├── test_build_validation.py     # Report build preconditions.
│   │   ├── test_figure_sidecars.py      # Figure sidecar metadata.
│   │   ├── test_figures.py              # Figure generation units.
│   │   └── test_tables.py               # Table generation units.

│   ├── statistics
│   │   ├── test_bootstrap.py            # Bootstrap and CI utilities.
│   │   ├── test_cv.py                   # Coefficient-of-variation utilities.
│   │   ├── test_divergence.py           # JS divergence and distances.
│   │   ├── test_effect_size.py          # Effect-size helpers.
│   │   ├── test_spearman.py             # Spearman correlation helpers.
│   │   └── test_wilcoxon.py             # Wilcoxon signed-rank helpers.

│   └── test_makefile_targets.py         # Lightweight Makefile target sanity checks only.
```

---

## Forbidden outcomes

Do not leave:

```text
tests/unit/baselines
tests/unit/training
tests/unit/models
tests/unit/pipeline
tests/unit/sweep
tests/unit/audit
tests/integration/baselines
tests/integration/training
tests/integration/sweep
```

unless the agent proves the matching production package still exists after the production refactor.

If the production package was moved, the matching tests must move too.

Do not leave tests that import:

```text
datp.baselines
datp.training
datp.models
datp.pipeline
datp.sweep
datp.audit
datp.analyses.common
datp.analyses.threshold_variants
datp.analyses.comparators
```

after the production code has moved.

Update those imports to the new canonical paths.

---

## Completion rule

This map is enforced only when:

1. The real tests were inspected.
2. Test moves were recorded in `TEST_MOVE_PLAN.md`.
3. Production imports were updated first or in the same packet.
4. Test imports were updated.
5. Old test folders were deleted.
6. No tests preserve old internal paths.
7. Ruff passed.
8. Pyright passed.
9. Impacted tests passed.
10. `PROJECT_MAP.md` reflects current test reality.
11. A later re-audit confirms no stale old-path tests remain.