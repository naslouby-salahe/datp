# Refactor Map

This file records the intended responsibility boundaries for the DATP codebase. It is not a wish list; it must be updated only after inspecting real code.

## Boundary rule

Code belongs where its responsibility lives, not where it currently happens to be located.

## Target responsibility map

| Responsibility | Expected home | Belongs here | Does not belong here |
|---|---|---|---|
| Artifacts | `src/datp/artifacts` or current canonical artifact module | Artifact names, run markers, atomic writes, path identity, score/result/checkpoint/log conventions. | Scientific hyperparameters, training loops. |
| Config/schema validation | `src/datp/config` or validation subpackage | Hydra schema, machine profile validation, resource bounds, dataset feature-count checks. | Baseline logic, score computations. |
| Training | `src/datp/training` | FedAvg encoder training, model construction, local training loops, deterministic seed setup at entry points. | Thresholding, reporting, downstream analysis. |
| Scoring | `src/datp/scoring` | Reconstruction-error generation, score artifact writing, score schema. | Threshold choice, final metrics. |
| Thresholding | `src/datp/thresholding` | B1/B2/B3/B4 threshold derivation, calibration-pending handling, threshold application. | Training, score generation. |
| Metrics | `src/datp/metrics` | CV(FPR), CV(TPR), Macro-F1, worst-client BA, coverage ratio, bootstrap CI support. | Report formatting, file path construction. |
| Analysis | `src/datp/analyses` | Mechanism analyses, stress tests, sensitivity analyses, post-score computations. | Training and upstream recomputation. |
| Reporting/export | `src/datp/reporting` or current canonical reporting package | Tables, figures, report artifacts, export formatting. | Raw metric computation if reusable elsewhere. |
| Tests only | `tests` | Fixtures, factories, test builders, test-only helpers. | Production constants and production logic. |

## Dependency direction

Preferred direction:

```text
config/schema + artifacts + shared domain types
        ↓
training → scoring → thresholding/results → metrics/analysis → reporting/export
```

Forbidden direction:

```text
thresholding/results/analysis/reporting → training
```

Downstream code must not call training to recompute upstream artifacts.

## Current map observations

| Area | Current observation | Decision | Packet | Status |
|---|---|---|---|---|
| Repository map | Not inspected yet. | Run PKT-001. | PKT-001 | `OPEN` |

## Move decision log

| Decision ID | Source | Target | Reason | Impacted imports/tests | Decision status |
|---|---|---|---|---|---|
| MAP-000 | TBD | TBD | Initial map not yet built. | TBD | `PENDING` |
