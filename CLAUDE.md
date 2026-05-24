# CLAUDE.md

## Purpose

This file is the non-negotiable execution contract for the DATP journal-extension work.

Every agent must follow this file before reading task-specific instructions.

## Active Planning Sources

The active planning package is limited to:

1. `docs/journal/PRE_CODING_PLAN.md`
2. `docs/journal/CODING_PLAN.md`
3. `docs/journal/EXPERIMENT_PLAN.md`
4. `docs/journal/POST_EXPERIMENT_PLAN.md`

`Journal/Journal_Extension_Master_Roadmap.md` is archived context only.

If archive material conflicts with the four active planning files, the four active files win.

## Scientific Scope

DATP is a controlled study of threshold calibration scope under fixed federated representation learning.

The scientific variable is threshold calibration.

The following must remain fixed unless the active planning files explicitly authorize otherwise:

1. Autoencoder architecture
2. FedAvg training setup
3. Dataset definitions
4. Regime definitions
5. Splits
6. Seeds
7. Shared score artifacts
8. Evaluation protocol

## Baseline Discipline

Main controlled baselines:

1. B1: shared/global threshold
2. B2: per-client threshold
3. B3: family/group threshold
4. B4: fingerprint-cluster threshold

Reference or restricted baselines:

1. B0: centralized reference comparator only
2. B5: local-only ablation, not a core claim baseline
3. FedRep-AE or FedPer-AE fallback only if explicitly required and correctly implemented

Do not invent new baselines.

Do not rename baselines casually.

Do not promote B5 into the abstract, core claim, or main figure captions.

## Stage Boundaries

The pipeline stages are:

1. prepare
2. score
3. threshold/result
4. report

A downstream stage must not silently recompute upstream artifacts.

Thresholding must not retrain.

Reporting must not recompute scores.

Evaluation must read canonical score and result artifacts.

## Shared-Training Rule

For a fixed dataset, regime, seed, and alpha when applicable:

1. Train the FL encoder once.
2. Save shared checkpoints and scores.
3. Derive B1, B2, B3, and B4 from the same score artifacts.
4. Never retrain per threshold baseline inside the same fixed cell.

This rule is mandatory.

## Implementation Quality Rules

Every implementation must include a refactoring pass.

Before adding new code, always ask:

1. Does this already exist?
2. Should this be an enum?
3. Should this be a constant?
4. Should this be a config value?
5. Should this be a schema or typed object?
6. Can existing logic be reused?
7. Can duplicated logic be removed?
8. Can this be expressed with fewer, clearer lines?
9. Can this be made easier to test?
10. Can this be made impossible to misuse?

Do not create random helper functions, constants, enums, paths, schemas, or classes without checking the existing code first.

Prefer:

1. Enums over loose strings
2. Constants over repeated literals
3. Schemas over unstructured dictionaries
4. Typed objects over argument-heavy functions
5. Shared utilities over duplicated local logic
6. Config-driven behavior over hardcoded scientific parameters
7. Clear small functions over dense procedural blocks
8. Existing canonical modules over new parallel modules

## Greenfield Rule

Implement as greenfield by default.

Do not preserve backward compatibility just because old code exists.

Backward compatibility is required only for:

1. Scientific invariants
2. Canonical artifact paths
3. Valid existing result formats when still scientifically active
4. Active documentation contracts
5. Public commands still required by the active plans

Dead code, obsolete tests, stale compatibility wrappers, and outdated interfaces should be removed when they conflict with clean design.

## Comment Discipline

Minimize comments.

Use comments only when they explain a non-obvious scientific or operational constraint.

Do not add comments that merely repeat the code.

Prefer clearer names, enums, schemas, and smaller functions instead of explanatory comments.

## Testing Discipline

Every implementation task must include test impact analysis.

Before adding new tests, check existing tests.

Prefer adapting existing tests when they already cover the behavior.

Add new tests only when existing tests cannot cleanly cover the scenario.

Delete or rewrite tests that validate obsolete behavior.

Tests must cover normal cases, boundary cases, failure cases, weird cases, missing artifacts, invalid configs, and scientific-invariant violations.

The goal is to catch experiment-breaking issues before real experiments run.

## Test Execution Discipline

Do not run the full test suite after every small edit.

For large or breaking work:

1. Make all planned code changes first.
2. Update tests after the implementation stabilizes.
3. Run targeted tests during development only when useful.
4. Run the full required suite at the end.
5. If tests fail, fix the issue and rerun the relevant failing tests.
6. Rerun the full required suite only after targeted failures are fixed.

Test runs must be practical, not wasteful.

## Experiment Discipline

Do not start experiments before the required gates are satisfied.

Do not run expensive experiments to discover bugs that unit or integration tests should have caught.

Before experiments:

1. Validate configs.
2. Validate dataset paths.
3. Validate schema assumptions.
4. Validate artifact paths.
5. Validate seeds.
6. Validate GPU or CPU expectations.
7. Validate result overwrite and resume behavior.
8. Validate logs and failure markers.

## Long-Running Commands

Long-running commands must be monitored.

The running agent must maintain a progress record containing:

1. Command executed
2. Start time
3. Current stage
4. Completed cells
5. Failed cells
6. Retried cells
7. Last checked log
8. Current risk
9. Next action

If a command fails, inspect logs, identify the root cause, fix it if safe, and rerun only the necessary command.

If the failure indicates a scientific, architectural, or planning issue, stop and write a precise repair request instead of guessing.

## Artifact Rules

Use canonical artifact paths.

Do not scatter outputs.

Do not treat empty files, temporary files, or partial files as complete results.

Result existence requires valid non-empty expected files.

Atomic writes should use temporary files and final rename where appropriate.

## Claim Discipline

Do not overclaim.

Allowed claims must match actual evidence.

Do not claim:

1. Poisoning robustness
2. Backdoor robustness
3. Evasion robustness
4. Formal differential privacy
5. Secure aggregation guarantees
6. Real hardware deployment readiness
7. Concept drift handling
8. Zero-day detection

unless those claims are directly tested and approved by the active plans.

## Documentation Discipline

Do not create extra planning files unless explicitly requested.

Keep the active journal planning package limited to the four files in `docs/journal`.

When implementation changes behavior, update the relevant existing documentation only if it is still active and required.