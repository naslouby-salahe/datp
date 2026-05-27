# Refactor Map

This file records the intended responsibility boundaries for the DATP `src/datp` package.

It is not a current-state map.

It is not a vague wish list.

It is the target architecture contract that guides the `src/datp` structure refactor after the agent inspects the real code.

The current repository reality map lives in:

```text
AI Workflow/state/PROJECT_MAP.md
```

`REFACTOR_MAP.md` records intended ownership.

`PROJECT_MAP.md` records current repository reality.

If both disagree, inspect the real repository first, then update the stale file.

---

## Scope

This map applies only to:

```text
src/datp
```

Do not use this map to refactor, restructure, or discuss non-`src/datp` packages.

Tests may be updated only as necessary to keep moved `src/datp` code covered.

---

## Non-negotiable refactor rule

No backwards compatibility is allowed for internal package moves.

Do not leave:

```text
redirect modules
wrapper modules
wrapper classes
compatibility aliases
old package shells
old files that only import from the new files
old tests that keep obsolete import paths alive
```

Do not create files whose only purpose is to preserve old internal paths.

Do not create classes whose only purpose is to wrap renamed or moved classes.

Do not create aliases whose only purpose is backwards compatibility.

Update every import properly.

Update tests properly.

Delete obsolete modules after imports are corrected.

---

## Boundary rule

Code belongs where its responsibility lives, not where it currently happens to be located.

Do not create vague folders such as:

```text
helpers
utils
misc
shared
common
```

unless the ownership is explicit and unavoidable.

Every file must have exactly one reason to exist.

---

## Scientific architecture rule

The package structure must protect DATP's scientific identity:

```text
data preparation
→ federated training
→ score generation
→ threshold derivation
→ evaluation
→ post hoc analysis
→ reporting
→ validation
```

For the main DATP comparison:

```text
B1, B2, B3, and B4 share the same trained encoder and the same score artifacts.
Only threshold calibration scope changes.
```

Never allow downstream packages to call training.

Forbidden dependency direction:

```text
thresholding/evaluation/analyses/reporting/validation → federated training
```

Allowed stage direction:

```text
data → federated → scoring → thresholding → evaluation → analyses/reporting/validation
```

---

## Target `src/datp` structure with file responsibilities

```text
src/datp
├── __init__.py                         # Package metadata and lightweight runtime dependency checks only.

├── app                                 # Application entrypoints only. No scientific logic.
│   ├── __init__.py
│   └── cli
│       ├── __init__.py
│       ├── __main__.py                 # Main `python -m datp` entrypoint.
│       ├── audit.py                    # CLI commands for validation/audit runs.
│       ├── config.py                   # CLI commands for config preview and validation.
│       ├── diagnostic.py               # CLI commands for diagnostic experiment flows.
│       ├── report.py                   # CLI commands for report/table/figure generation.
│       ├── status.py                   # CLI commands for run/artifact status inspection.
│       └── sweep.py                    # CLI commands for launching controlled experiment sweeps.

├── conf                                # Hydra YAML configuration assets. No Python logic.
│   ├── __init__.py
│   ├── config.yaml                     # Root/default experiment configuration.
│   └── regime
│       ├── a.yaml                      # Regime A config: N-BaIoT natural device split.
│       ├── b.yaml                      # Regime B config: CICIoT2023 validation regime.
│       ├── c.yaml                      # Regime C config: N-BaIoT Dirichlet severity sweep.
│       └── d.yaml                      # Regime D config: external validation dataset regime.

├── config                              # Python-side config composition and typed schemas.
│   ├── __init__.py
│   ├── compose.py                      # Hydra composition helpers and resolved config loading.
│   └── models.py                       # Typed config objects and config validation rules.

├── core                                # Cross-cutting technical primitives. No experiment policy.
│   ├── __init__.py
│   ├── device.py                       # CPU/CUDA device selection and runtime device checks.
│   ├── errors.py                       # Shared error formatting and project-specific exceptions.
│   ├── identity.py                     # Run identity, seed/alpha labels, canonical naming helpers.
│   ├── logging.py                      # Structured logging setup and log configuration.
│   ├── provenance.py                   # Provenance capture for configs, artifacts, and runs.
│   ├── seeds.py                        # Deterministic seeding for Python, NumPy, Torch, CUDA.
│   └── tracking.py                     # Optional experiment tracking integration helpers.

├── domain                              # Canonical scientific vocabulary and closed-set enums.
│   ├── __init__.py
│   ├── artifacts.py                    # Artifact type names and canonical artifact concepts.
│   ├── baselines.py                    # Baseline enum: B0, B1, B2, B3, B4, and allowed comparators.
│   ├── datasets.py                     # Dataset identifiers and dataset-level constants.
│   ├── regimes.py                      # Regime identifiers and regime semantics.
│   └── thresholds.py                   # Threshold method identifiers and threshold-scope vocabulary.

├── data                                # Dataset preparation, schemas, partitions, and processed data contracts.
│   ├── __init__.py
│   ├── artifacts.py                    # Data artifact descriptors produced by preparation.
│   ├── catalog.py                      # Dataset registry and dataset lookup.
│   ├── contracts.py                    # Processed-data contract definitions.
│   ├── manifests.py                    # Data manifest creation and validation.
│   ├── paths.py                        # Canonical data path construction.
│   ├── sampling.py                     # Sampling, client construction, and split sampling helpers.
│   ├── scaling.py                      # Feature scaling utilities.
│   ├── splits.py                       # Train/cal/test split logic.
│   ├── io
│   │   ├── __init__.py
│   │   ├── audit.py                    # Dataset-level audit helpers.
│   │   ├── schemas.py                  # Parquet/dataframe schema definitions.
│   │   └── storage.py                  # Parquet read/write helpers and storage validation.
│   ├── datasets
│   │   ├── __init__.py
│   │   ├── ciciot2023
│   │   │   ├── __init__.py
│   │   │   ├── prepare.py              # CICIoT2023 raw-to-processed preparation.
│   │   │   └── spec.py                 # CICIoT2023 dataset specification.
│   │   ├── edge_iiotset
│   │   │   ├── __init__.py
│   │   │   ├── prepare.py              # Edge-IIoTset raw-to-processed preparation.
│   │   │   └── spec.py                 # Edge-IIoTset dataset specification.
│   │   └── nbaiot
│   │       ├── __init__.py
│   │       ├── prepare.py              # N-BaIoT raw-to-processed preparation.
│   │       └── spec.py                 # N-BaIoT dataset specification and device/family metadata.
│   └── regimes
│       ├── __init__.py
│       ├── catalog.py                  # Regime-to-dataset preparation registry.
│       ├── prepare.py                  # Generic regime preparation dispatcher.
│       ├── regime_a.py                 # Regime A partition and preparation logic.
│       ├── regime_b.py                 # Regime B partition and preparation logic.
│       └── regime_c.py                 # Regime C Dirichlet partition and preparation logic.

├── artifacts                           # Canonical output paths, files, markers, and run layout.
│   ├── __init__.py
│   ├── constants.py                    # Artifact filenames such as metrics, model, manifest.
│   ├── directories.py                  # Canonical output directory names.
│   ├── markers.py                      # IN_PROGRESS, DONE, ABORTED marker handling.
│   ├── paths.py                        # Result/checkpoint/score/log path builders.
│   ├── results.py                      # Result existence and result-file helpers.
│   └── run_formatting.py               # Run-id and path-segment formatting.

├── modeling                            # Neural model definitions only.
│   ├── __init__.py
│   ├── activations.py                  # Activation factories/helpers.
│   ├── autoencoder.py                  # DATP autoencoder architecture.
│   └── factories.py                    # Model construction from typed config.

├── federated                           # Federated training, client simulation, and FL protocols.
│   ├── __init__.py
│   ├── catalog.py                      # Training protocol registry.
│   ├── checkpoints.py                  # Checkpoint save/load for shared encoder training.
│   ├── clients.py                      # FL client wrappers and client dataset binding.
│   ├── communication.py                # Communication-cost accounting for model/threshold payloads.
│   ├── convergence.py                  # Convergence checks and round-level convergence summaries.
│   ├── local_training.py               # Local AE training loop used by FL clients.
│   ├── parameters.py                   # Model parameter serialization/deserialization.
│   ├── runtime.py                      # FL runtime setup, resource checks, execution environment.
│   ├── simulation.py                   # Flower/Ray simulation orchestration.
│   ├── strategies.py                   # Strategy construction and FedAvg-compatible strategy helpers.
│   ├── types.py                        # Federated training dataclasses and typed results.
│   └── protocols
│       ├── __init__.py
│       ├── fedavg.py                   # Canonical FedAvg training protocol.
│       ├── fedprox.py                  # FedProx stress-test protocol.
│       └── fedrep.py                   # FedRep/FedPer-style personalization fallback protocol.

├── scoring                             # Reconstruction-error score generation and loading.
│   ├── __init__.py
│   ├── generation.py                   # Generate per-client reconstruction-error score artifacts.
│   ├── loading.py                      # Load saved score artifacts from canonical paths.
│   ├── provider.py                     # ScoreProvider abstraction for cal/test score access.
│   └── schemas.py                      # Score artifact schema and score column validation.

├── thresholding                        # DATP core: threshold derivation, variants, and comparators.
│   ├── __init__.py
│   ├── eligibility.py                  # Calibration eligibility and Calibration-Pending handling.
│   ├── evaluation_helpers.py           # Shared threshold evaluation helpers.
│   ├── metrics_serialization.py        # Serialize threshold/evaluation metrics.
│   ├── thresholds.py                   # Shared quantile/global/local threshold utilities.
│   ├── types.py                        # ThresholdResult and thresholding dataclasses.
│   ├── strategies
│   │   ├── __init__.py
│   │   ├── b0_centralized.py           # Centralized AE reference comparator.
│   │   ├── b1_global.py                # Shared/global threshold strategy.
│   │   ├── b2_personalized.py          # Per-client threshold strategy.
│   │   ├── b3_family.py                # Family/group mean threshold strategy.
│   │   └── b4_cluster.py               # Fingerprint cluster threshold strategy.
│   ├── variants
│   │   ├── __init__.py
│   │   ├── b2_conformal.py             # Split-conformal B2 threshold variant.
│   │   ├── calibration_size_sweep.py   # Calibration-size sensitivity/fallback analysis.
│   │   ├── q_sensitivity.py            # Quantile sensitivity sweep.
│   │   └── tau_shrinkage.py            # Local-global threshold shrinkage variant.
│   └── comparators
│       ├── __init__.py
│       └── fedstats_benign.py          # Benign-only federated statistics threshold comparator.

├── evaluation                          # Metric computation after scores and thresholds exist.
│   ├── __init__.py
│   ├── artifact_validation.py          # Validate required score/threshold/result artifacts before eval.
│   ├── confusion.py                    # Confusion matrix and vectorized count helpers.
│   ├── eligibility.py                  # Evaluation-time client inclusion and coverage helpers.
│   ├── metric_keys.py                  # Canonical metric key names.
│   ├── metrics.py                      # Client/global metrics, CV(FPR), Macro-F1, BA, etc.
│   └── ranking.py                      # Ranking/comparison helpers for baselines and regimes.

├── experiments                         # Stage orchestration. No low-level scientific implementation.
│   ├── __init__.py
│   ├── console.py                      # Console progress rendering for experiment stages.
│   ├── diagnostic.py                   # Diagnostic experiment workflow.
│   ├── executor.py                     # Main stage executor and run lifecycle handling.
│   ├── models.py                       # Experiment/stage execution dataclasses.
│   ├── sweep.py                        # Multi-regime, multi-seed sweep runner.
│   ├── validator.py                    # Preflight validation for experiment runs.
│   └── stages
│       ├── __init__.py
│       ├── prepare_data.py             # Stage: data preparation.
│       ├── train_encoder.py            # Stage: shared FL encoder training.
│       ├── generate_scores.py          # Stage: score artifact generation from trained encoder.
│       ├── derive_thresholds.py        # Stage: B1-B4 threshold derivation from saved scores.
│       ├── evaluate_results.py         # Stage: metric computation from thresholds and scores.
│       └── build_report.py             # Stage: report/table/figure generation.

├── analyses                            # Post hoc analyses over verified score/result artifacts.
│   ├── __init__.py
│   ├── cells.py                        # Analysis-cell discovery and filtering.
│   ├── evaluation.py                   # Analysis-specific metric helper functions.
│   ├── io.py                           # Analysis input/output helpers.
│   ├── plotting.py                     # Shared plotting utilities for analyses.
│   ├── runners.py                      # Reusable analysis runner scaffolding.
│   ├── types.py                        # Analysis dataclasses and result types.
│   ├── mechanism
│   │   ├── __init__.py
│   │   ├── b3_preservation.py          # Analyze what B3 preserves or loses.
│   │   ├── b4_cluster_ablation.py      # Analyze B4 clustering/fingerprint ablations.
│   │   ├── js_divergence_benefit.py    # Relate JS divergence/severity to DATP benefit.
│   │   ├── per_client_cdf.py           # Per-client score/error distribution analysis.
│   │   └── threshold_shift.py          # Threshold movement and scope-shift analysis.
│   ├── robustness
│   │   ├── __init__.py
│   │   ├── alert_burden.py             # Alert burden / operational false-positive analysis.
│   │   ├── regime_c_severity.py        # Regime C severity sweep analysis.
│   │   └── stress_test_absorption.py   # FedProx/Ditto/FedRep absorption analysis.
│   └── temporal
│       ├── __init__.py
│       └── temporal_recalibration.py   # Chronological recalibration analysis.

├── validation                          # Scientific and artifact invariant checks.
│   ├── __init__.py
│   ├── constants.py                    # Validation constants and audit thresholds.
│   ├── convergence.py                  # Validate convergence artifacts and convergence claims.
│   ├── datasets.py                     # Validate dataset schemas, counts, and regime assumptions.
│   ├── discovery.py                    # Discover runs, cells, score dirs, and result dirs.
│   ├── invariants.py                   # Check shared-training and no-retraining invariants.
│   ├── metric_reproducer.py            # Recompute metrics from artifacts and compare to saved results.
│   ├── results.py                      # Validate result completeness and non-empty metrics files.
│   ├── schemas.py                      # Validation output schemas.
│   ├── score_manifest.py               # Verify score manifests and score artifact consistency.
│   ├── verdicts.py                     # Validation verdict types and verdict combination logic.
│   └── writers.py                      # Write validation reports and audit outputs.

├── reporting                           # Paper-facing outputs: figures, tables, and report builds.
│   ├── __init__.py
│   ├── build.py                        # End-to-end report artifact build command logic.
│   ├── engine.py                       # Shared reporting engine and render orchestration.
│   ├── figures.py                      # Figure generation from result/statistic artifacts.
│   ├── tables.py                       # Table generation from result/statistic artifacts.
│   ├── validation.py                   # Validate report artifacts before use.
│   └── templates
│       └── table_main.tex.j2           # LaTeX table template.

└── statistics                          # Pure statistical utilities. No DATP orchestration.
    ├── __init__.py
    ├── bootstrap.py                    # Bootstrap and CI utilities.
    ├── constants.py                    # Statistical constants.
    ├── cv.py                           # Coefficient-of-variation helpers.
    ├── divergence.py                   # JS divergence and distribution distance helpers.
    ├── effect_size.py                  # Cliff's delta / effect-size helpers.
    ├── enums.py                        # Statistical test/method enums if truly needed.
    ├── spearman.py                     # Spearman correlation helpers.
    └── wilcoxon.py                     # Wilcoxon signed-rank helpers.
```

---

## Canonical move decisions

| Current location | Target location | Reason |
|---|---|---|
| `src/datp/cli` | `src/datp/app/cli` | CLI is application entrypoint code, not domain logic. |
| `src/datp/models` | `src/datp/modeling` | Avoid confusion with config models and experiment models. |
| `src/datp/training` | `src/datp/federated` | Current package mostly owns FL clients, protocols, runtime, simulation, strategies, and checkpoints. |
| `src/datp/baselines` | `src/datp/thresholding` | B1-B4 are threshold-scope strategies, not generic ML baselines. |
| `src/datp/analyses/threshold_variants` | `src/datp/thresholding/variants` | These are threshold variants, not generic analyses. |
| `src/datp/analyses/comparators` | `src/datp/thresholding/comparators` | FedStats benign is a threshold comparator. |
| `src/datp/evaluation/score_loading.py` | `src/datp/scoring/loading.py` | Score loading belongs to the scoring stage boundary. |
| `src/datp/training/scoring.py` | `src/datp/scoring/generation.py` | Score generation should not stay buried in training. |
| `src/datp/baselines/common/scoring.py` | `src/datp/scoring` | Avoid duplicated scoring assumptions. |
| `src/datp/pipeline` | `src/datp/experiments` | Pipeline code is experiment-stage orchestration. |
| `src/datp/sweep` | `src/datp/experiments` | Sweep execution is experiment orchestration. |
| `src/datp/audit` | `src/datp/validation` | The package validates artifacts, invariants, manifests, metrics, and results. |
| `src/datp/analyses/common` | `src/datp/analyses` | Flatten analysis primitives; avoid a junk-drawer `common` package. |

---

## Naming decisions

| Old name | New name |
|---|---|
| `b0.py` | `b0_centralized.py` |
| `b1.py` | `b1_global.py` |
| `b2.py` | `b2_personalized.py` |
| `b3.py` | `b3_family.py` |
| `b4.py` | `b4_cluster.py` |
| `training/local.py` | `federated/local_training.py` |
| `pipeline/_console.py` and `sweep/_console.py` | `experiments/console.py` |
| `pipeline/training.py` | `experiments/stages/train_encoder.py` if it orchestrates training; otherwise move real training logic to `federated`. |
| `sweep/run_sweep.py` | `experiments/sweep.py` |
| `sweep/data_preparation.py` | `experiments/stages/prepare_data.py` |

---

## Refactor constraints

The agent must not perform the move blindly.

Before moving code, it must:

1. Inspect imports.
2. Inspect tests.
3. Identify public CLI entrypoints.
4. Identify package cycles.
5. Identify scientific-stage risks.
6. Declare file locks.
7. Update `MOVE_PLAN.md`.
8. Update `TEST_IMPACT_MAP.md`.
9. Run targeted checks after each move batch.

After moving code, it must:

1. Delete old modules.
2. Update imports.
3. Update tests.
4. Update config references if any.
5. Update package `__init__.py` files only when needed.
6. Run Ruff.
7. Run Pyright.
8. Run impacted tests.
9. Update `PROJECT_MAP.md`.
10. Mark the packet `REAUDIT_REQUIRED`, not `DONE`, until a later audit confirms the structure.

---

## Forbidden outcomes

Do not leave:

```text
src/datp/baselines/main/b1.py importing from src/datp/thresholding/strategies/b1_global.py
src/datp/training/__init__.py redirecting to src/datp/federated
src/datp/models/__init__.py redirecting to src/datp/modeling
src/datp/audit/__init__.py redirecting to src/datp/validation
old modules that exist only for backwards compatibility
old wrapper classes that preserve old APIs
old compatibility aliases
old tests that import obsolete internal paths
duplicate score-loading code
duplicate eligibility logic
duplicate metric serialization logic
duplicate baseline/regime enums
```

Internal backwards compatibility is not required.

Correct imports and tests instead.

---

## Open verification questions

The agent must answer these from real code before implementation:

| Question | Required evidence |
|---|---|
| Does `src/datp/training/scoring.py` generate scores, load scores, or both? | Inspect file content and imports. |
| Does `src/datp/evaluation/score_loading.py` overlap with baseline scoring? | Inspect file content and imports. |
| Does `src/datp/baselines/common/training.py` actually train, or only adapt model loading/evaluation? | Inspect file content and imports. |
| Does `src/datp/pipeline/training.py` contain orchestration only, or domain training logic? | Inspect file content and imports. |
| Do any CLI commands import old paths directly? | Search all CLI imports. |
| Are baseline/regime enums duplicated across `core`, `artifacts`, `audit`, `pipeline`, and `statistics`? | Search enum definitions and string literals. |
| Do tests import implementation internals that will move? | Search test imports. |
| Does any downstream module call training or recompute scores? | Search calls into federated/training/scoring from thresholding/evaluation/analyses/reporting/validation. |

---

## Completion rule

This map is considered enforced only when:

1. The real code was inspected.
2. The move plan was updated.
3. Imports were updated.
4. Old internal paths were deleted.
5. No wrappers or redirects remain.
6. Tests were updated.
7. Ruff passed.
8. Pyright passed.
9. Impacted tests passed.
10. `PROJECT_MAP.md` reflects current reality.
11. Scientific-contract audit confirms no DATP invariant was broken.
12. A later re-audit confirms no stale paths remain.