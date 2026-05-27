# Refactor Map

This file records the intended responsibility boundaries for the DATP codebase.

It is not a wish list. It must be updated only after inspecting real code.

---

## Boundary rule

Code belongs where its responsibility lives, not where it currently happens to be located.

---

## Living project map

The operational project map lives at:

```text
AI Workflow/state/PROJECT_MAP.md
```

`REFACTOR_MAP.md` defines intended ownership.

`PROJECT_MAP.md` records current repository reality.

Both must stay aligned.

Update `PROJECT_MAP.md`:

1. after initial inventory;
2. after every Graphify refresh;
3. after major package moves;
4. after ownership decisions;
5. after deleted wrappers or compatibility shells;
6. after test-structure changes;
7. before final review.

If `REFACTOR_MAP.md` and `PROJECT_MAP.md` disagree, inspect the real repository and update the stale file.

---

## Target responsibility map

| Responsibility | Expected home | Belongs here | Does not belong here |
|---|---|---|---|
| Artifacts | `src/datp/artifacts` or current canonical artifact module | Artifact names, run markers, atomic writes, path identity, score/result/checkpoint/log conventions. | Scientific hyperparameters, training loops. |
| Config/schema validation | `src/datp/config` or validation subpackage | Hydra schema, machine profile validation, resource bounds, dataset feature-count checks. | Baseline logic, score computations. |
| Training | `src/datp/training` | FedAvg encoder training, model construction, local training loops, deterministic seed setup at entry points. | Thresholding, reporting, downstream analysis. |
| Scoring | `src/datp/scoring` if created, otherwise current canonical scoring owner recorded in `PROJECT_MAP.md` | Reconstruction-error generation, score artifact writing, score schema. | Threshold choice, final metrics. |
| Thresholding | `src/datp/thresholding` if created, otherwise current canonical threshold owner recorded in `PROJECT_MAP.md` | B1/B2/B3/B4 threshold derivation, calibration-pending handling, threshold application. | Training, score generation. |
| Metrics | `src/datp/metrics` if created, otherwise current canonical metric owner recorded in `PROJECT_MAP.md` | CV(FPR), CV(TPR), Macro-F1, worst-client BA, coverage ratio, bootstrap CI support. | Report formatting, file path construction. |
| Analysis | `src/datp/analyses` | Mechanism analyses, stress tests, sensitivity analyses, post-score computations. | Training and upstream recomputation. |
| Reporting/export | `src/datp/reporting` or current canonical reporting package | Tables, figures, report artifacts, export formatting. | Raw metric computation if reusable elsewhere. |
| Tests only | `tests` | Fixtures, factories, test builders, test-only helpers. | Production constants and production logic. |
| Workflow state | `AI Workflow/state` | Project map, tool status, Graphify status, run ledger, check flags, handoffs. | Production implementation. |

---

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

---

## Explicit architecture questions

These are not decisions yet. They must be answered through real code inspection, tests, and scientific-contract review.

| Question | Why it matters | Decision status |
|---|---|---|
| Should scoring become a first-class `src/datp/scoring` package? | Scoring is the seam between training and thresholding. | `OPEN` |
| Should thresholding become a first-class `src/datp/thresholding` package? | B1–B4 and threshold variants may duplicate logic if thresholding stays scattered. | `OPEN` |
| Should metrics become a first-class `src/datp/metrics` package? | Prevent overlap between `evaluation`, `statistics`, and baseline serialization. | `OPEN` |
| Should eligibility be centralized? | Calibration-Pending behavior is scientifically critical. | `OPEN` |
| Should test fixtures be reorganized by domain? | Test duplication and stale fixtures can hide scientific drift. | `OPEN` |

Do not create new packages just because this file names them.

Create or move packages only after repository reality, import impact, tests, and scientific risk are inspected.

---

## Current map observations

| Area | Current observation | Decision | Packet | Status |
|---|---|---|---|---|
| Repository map | Initial map exists in `AI Workflow/state/PROJECT_MAP.md` but remains placeholder until real inventory and Graphify/inspection runs. | Run PKT-001 and update both maps. | PKT-001 | `OPEN` |
| Graphify | Graphify is useful but must be verified and refreshed repeatedly after architecture changes. | Record every run in `GRAPHIFY_STATUS.md` and `PROJECT_MAP.md`. | PKT-001 | `OPEN` |
| Sonar | Local Sonar is unreliable. | Keep Sonar optional/final only; do not block early refactors on it. | PKT-008 | `OPEN` |

---

## Move decision log

| Decision ID | Source | Target | Reason | Impacted imports/tests | Decision status |
|---|---|---|---|---|---|
| MAP-000 | TBD | TBD | Initial map not yet verified by real inspection. | TBD | `PENDING` |
