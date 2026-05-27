# Move Plan

This file records concrete code movement plans for `src/datp`.

Moving code is allowed, but it must be deliberate, inspected, tested, and finished cleanly.

---

## Scope

This move plan applies only to:

```text
src/datp
```

Tests may be updated only when required by moved `src/datp` code.

Do not use this file to plan changes outside `src/datp`.

---

## No-backwards-compatibility rule

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

Update all imports.

Update all impacted tests.

Delete obsolete modules.

Do not preserve old internal paths.

---

## Move rules

1. Move by responsibility, not by current location.
2. Inspect real code before moving.
3. Update imports and tests in the same packet.
4. Do not leave wrappers, redirects, compatibility aliases, or dead old modules.
5. Delete obsolete files only after imports/tests are updated.
6. Record affected tests and scientific risks before moving.
7. Re-audit moved areas after related packets finish.
8. Preserve DATP scientific invariants.
9. Do not run training, full E2E, or heavy experiments for structure-only moves.

---

## Target architecture source

The annotated target tree lives in:

```text
AI Workflow/REFACTOR_MAP.md
```

`AI Workflow/state/PROJECT_MAP.md` must record current reality and completed moves only.

---

## Move batches

### Batch 1 — Non-scientific shell moves

| Move ID | Source | Target | Reason | Status |
|---|---|---|---|---|
| MOVE-001 | `src/datp/cli` | `src/datp/app/cli` | CLI should be an application entrypoint layer, not domain logic. | `PLANNED` |
| MOVE-002 | `src/datp/models` | `src/datp/modeling` | Avoid ambiguity with config models and experiment models. | `PLANNED` |

Required checks:

```bash
python -m ruff check src/datp tests
python -m pyright
python -m pytest tests/unit/cli tests/unit/models
```

Adjust test paths after actual test relocation.

---

### Batch 2 — Training to federated ownership

| Move ID | Source | Target | Reason | Status |
|---|---|---|---|---|
| MOVE-003 | `src/datp/training/protocols` | `src/datp/federated/protocols` | FL protocols belong under federated training. | `PLANNED` |
| MOVE-004 | `src/datp/training/checkpoints.py` | `src/datp/federated/checkpoints.py` | Checkpoints are part of shared encoder training. | `PLANNED` |
| MOVE-005 | `src/datp/training/clients.py` | `src/datp/federated/clients.py` | FL clients belong under federated training. | `PLANNED` |
| MOVE-006 | `src/datp/training/communication.py` | `src/datp/federated/communication.py` | Communication accounting belongs with federated execution. | `PLANNED` |
| MOVE-007 | `src/datp/training/convergence.py` | `src/datp/federated/convergence.py` | Convergence is a federated-training concern. | `PLANNED` |
| MOVE-008 | `src/datp/training/factories.py` | `src/datp/modeling/factories.py` or `src/datp/federated/factories.py` | Decide after inspecting whether it builds models or training objects. | `TO_INSPECT` |
| MOVE-009 | `src/datp/training/local.py` | `src/datp/federated/local_training.py` | Local client training loop belongs under federated. | `PLANNED` |
| MOVE-010 | `src/datp/training/parameters.py` | `src/datp/federated/parameters.py` | Parameter serialization belongs to FL protocol/runtime. | `PLANNED` |
| MOVE-011 | `src/datp/training/runtime.py` | `src/datp/federated/runtime.py` | Runtime checks/setup belong to federated execution. | `PLANNED` |
| MOVE-012 | `src/datp/training/simulation.py` | `src/datp/federated/simulation.py` | Flower/Ray simulation belongs under federated. | `PLANNED` |
| MOVE-013 | `src/datp/training/strategies.py` | `src/datp/federated/strategies.py` | FL strategy construction belongs under federated. | `PLANNED` |
| MOVE-014 | `src/datp/training/types.py` | `src/datp/federated/types.py` | Federated dataclasses belong under federated. | `PLANNED` |
| MOVE-015 | `src/datp/training/catalog.py` | `src/datp/federated/catalog.py` | Training protocol registry belongs under federated. | `PLANNED` |

Required checks:

```bash
python -m ruff check src/datp tests
python -m pyright
python -m pytest tests/unit/training tests/integration/training
```

Adjust test paths after test relocation.

---

### Batch 3 — Scoring stage extraction

| Move ID | Source | Target | Reason | Status |
|---|---|---|---|---|
| MOVE-016 | `src/datp/training/scoring.py` | `src/datp/scoring/generation.py` | Score generation is a stage boundary after training. | `TO_INSPECT` |
| MOVE-017 | `src/datp/evaluation/score_loading.py` | `src/datp/scoring/loading.py` | Score loading belongs with score artifact access. | `PLANNED` |
| MOVE-018 | `src/datp/baselines/common/scoring.py` | `src/datp/scoring` | Remove duplicate scoring assumptions. | `TO_INSPECT` |

Required checks:

```bash
python -m ruff check src/datp tests
python -m pyright
python -m pytest tests/unit/evaluation tests/unit/training tests/integration/training
```

Scientific checks:

```text
No thresholding module may generate scores.
No evaluation module may recompute reconstruction errors.
No reporting or analysis module may call score generation.
```

---

### Batch 4 — Baselines to thresholding

| Move ID | Source | Target | Reason | Status |
|---|---|---|---|---|
| MOVE-019 | `src/datp/baselines/main/b0.py` | `src/datp/thresholding/strategies/b0_centralized.py` | B0 is the centralized reference comparator. | `PLANNED` |
| MOVE-020 | `src/datp/baselines/main/b1.py` | `src/datp/thresholding/strategies/b1_global.py` | B1 is shared/global thresholding. | `PLANNED` |
| MOVE-021 | `src/datp/baselines/main/b2.py` | `src/datp/thresholding/strategies/b2_personalized.py` | B2 is per-client thresholding. | `PLANNED` |
| MOVE-022 | `src/datp/baselines/main/b3.py` | `src/datp/thresholding/strategies/b3_family.py` | B3 is family/group thresholding. | `PLANNED` |
| MOVE-023 | `src/datp/baselines/main/b4.py` | `src/datp/thresholding/strategies/b4_cluster.py` | B4 is fingerprint-cluster thresholding. | `PLANNED` |
| MOVE-024 | `src/datp/baselines/common/calibration_eligibility.py` | `src/datp/thresholding/eligibility.py` | Calibration eligibility is thresholding-critical. | `PLANNED` |
| MOVE-025 | `src/datp/baselines/common/evaluation_helpers.py` | `src/datp/thresholding/evaluation_helpers.py` | Shared helper for applying thresholds. | `PLANNED` |
| MOVE-026 | `src/datp/baselines/common/metrics_serialization.py` | `src/datp/thresholding/metrics_serialization.py` | Threshold result serialization belongs with thresholding. | `PLANNED` |
| MOVE-027 | `src/datp/baselines/common/thresholds.py` | `src/datp/thresholding/thresholds.py` | Shared threshold math belongs with thresholding. | `PLANNED` |
| MOVE-028 | `src/datp/baselines/common/types.py` | `src/datp/thresholding/types.py` | ThresholdResult and related dataclasses belong with thresholding. | `PLANNED` |
| MOVE-029 | `src/datp/baselines/common/data_loading.py` | `src/datp/thresholding` or `src/datp/scoring` | Decide after inspecting whether it loads scores, data, or result artifacts. | `TO_INSPECT` |
| MOVE-030 | `src/datp/baselines/common/training.py` | `src/datp/federated` or remove | Decide after inspecting whether it violates threshold/training boundary. | `TO_INSPECT` |

Required checks:

```bash
python -m ruff check src/datp tests
python -m pyright
python -m pytest tests/unit/baselines tests/integration/baselines
```

Scientific checks:

```text
B1-B4 must not train.
B1-B4 must consume saved score artifacts.
B1-B4 must preserve baseline semantics.
Calibration-Pending behavior must remain unchanged.
```

---

### Batch 5 — Threshold variants and comparators

| Move ID | Source | Target | Reason | Status |
|---|---|---|---|---|
| MOVE-031 | `src/datp/analyses/threshold_variants/b2_conformal.py` | `src/datp/thresholding/variants/b2_conformal.py` | Conformal B2 is a threshold variant. | `PLANNED` |
| MOVE-032 | `src/datp/analyses/threshold_variants/calibration_size_sweep.py` | `src/datp/thresholding/variants/calibration_size_sweep.py` | Calibration-size sensitivity belongs with threshold variants. | `PLANNED` |
| MOVE-033 | `src/datp/analyses/threshold_variants/q_sensitivity.py` | `src/datp/thresholding/variants/q_sensitivity.py` | Quantile sensitivity belongs with threshold variants. | `PLANNED` |
| MOVE-034 | `src/datp/analyses/threshold_variants/tau_shrinkage.py` | `src/datp/thresholding/variants/tau_shrinkage.py` | Shrinkage thresholding belongs with threshold variants. | `PLANNED` |
| MOVE-035 | `src/datp/analyses/comparators/fedstats_benign.py` | `src/datp/thresholding/comparators/fedstats_benign.py` | Benign FedStats is a threshold comparator. | `PLANNED` |

Required checks:

```bash
python -m ruff check src/datp tests
python -m pyright
python -m pytest tests/unit/analyses/threshold_variants tests/unit/analyses/comparators
```

Adjust test paths after relocation.

---

### Batch 6 — Pipeline and sweep to experiments

| Move ID | Source | Target | Reason | Status |
|---|---|---|---|---|
| MOVE-036 | `src/datp/pipeline/_console.py` | `src/datp/experiments/console.py` | Shared experiment console rendering. | `PLANNED` |
| MOVE-037 | `src/datp/sweep/_console.py` | `src/datp/experiments/console.py` | Avoid duplicate console helpers. | `TO_MERGE` |
| MOVE-038 | `src/datp/pipeline/diagnostic.py` | `src/datp/experiments/diagnostic.py` | Diagnostic workflow is experiment orchestration. | `PLANNED` |
| MOVE-039 | `src/datp/pipeline/executor.py` | `src/datp/experiments/executor.py` | Executor is experiment orchestration. | `PLANNED` |
| MOVE-040 | `src/datp/pipeline/models.py` | `src/datp/experiments/models.py` | Stage/run dataclasses belong with experiments. | `PLANNED` |
| MOVE-041 | `src/datp/pipeline/enums.py` | `src/datp/domain` or `src/datp/experiments/models.py` | Decide after inspecting enum semantics. | `TO_INSPECT` |
| MOVE-042 | `src/datp/pipeline/training.py` | `src/datp/experiments/stages/train_encoder.py` | If orchestration only; otherwise split domain logic into federated. | `TO_INSPECT` |
| MOVE-043 | `src/datp/sweep/data_preparation.py` | `src/datp/experiments/stages/prepare_data.py` | Data-prep stage orchestration. | `PLANNED` |
| MOVE-044 | `src/datp/sweep/run_sweep.py` | `src/datp/experiments/sweep.py` | Sweep runner belongs to experiments. | `PLANNED` |
| MOVE-045 | `src/datp/sweep/validator.py` | `src/datp/experiments/validator.py` | Preflight validation for experiment runs. | `PLANNED` |

Required checks:

```bash
python -m ruff check src/datp tests
python -m pyright
python -m pytest tests/unit/pipeline tests/unit/sweep tests/integration/sweep tests/e2e/diagnostic
```

Do not run full E2E unless directly required and explicitly approved.

---

### Batch 7 — Audit to validation

| Move ID | Source | Target | Reason | Status |
|---|---|---|---|---|
| MOVE-046 | `src/datp/audit` | `src/datp/validation` | Package validates artifacts, invariants, manifests, metrics, datasets, and results. | `PLANNED` |

Required checks:

```bash
python -m ruff check src/datp tests
python -m pyright
python -m pytest tests/unit/audit
```

Adjust test paths after relocation.

---

### Batch 8 — Analysis flattening

| Move ID | Source | Target | Reason | Status |
|---|---|---|---|---|
| MOVE-047 | `src/datp/analyses/common/cells.py` | `src/datp/analyses/cells.py` | Analysis-cell primitive; avoid `common` junk drawer. | `PLANNED` |
| MOVE-048 | `src/datp/analyses/common/evaluation.py` | `src/datp/analyses/evaluation.py` | Analysis-specific evaluation helpers. | `PLANNED` |
| MOVE-049 | `src/datp/analyses/common/io.py` | `src/datp/analyses/io.py` | Analysis I/O helpers. | `PLANNED` |
| MOVE-050 | `src/datp/analyses/common/plotting.py` | `src/datp/analyses/plotting.py` | Analysis plotting helpers. | `PLANNED` |
| MOVE-051 | `src/datp/analyses/common/runners.py` | `src/datp/analyses/runners.py` | Analysis runner scaffolding. | `PLANNED` |
| MOVE-052 | `src/datp/analyses/common/types.py` | `src/datp/analyses/types.py` | Analysis dataclasses and result types. | `PLANNED` |

Required checks:

```bash
python -m ruff check src/datp tests
python -m pyright
python -m pytest tests/unit/analyses
```

---

## Deleted/retired modules ledger

| Module/file | Reason retired | Replacement | Imports updated | Tests updated | Status |
|---|---|---|---|---|---|
| `src/datp/baselines` | Replaced by explicit thresholding ownership. | `src/datp/thresholding` | `PENDING` | `PENDING` | `PLANNED` |
| `src/datp/training` | Replaced by explicit federated ownership. | `src/datp/federated` | `PENDING` | `PENDING` | `PLANNED` |
| `src/datp/models` | Replaced by modeling ownership. | `src/datp/modeling` | `PENDING` | `PENDING` | `PLANNED` |
| `src/datp/pipeline` | Replaced by experiment orchestration ownership. | `src/datp/experiments` | `PENDING` | `PENDING` | `PLANNED` |
| `src/datp/sweep` | Merged into experiment orchestration. | `src/datp/experiments` | `PENDING` | `PENDING` | `PLANNED` |
| `src/datp/audit` | Replaced by validation ownership. | `src/datp/validation` | `PENDING` | `PENDING` | `PLANNED` |
| `src/datp/analyses/common` | Flattened into analyses primitives. | `src/datp/analyses` | `PENDING` | `PENDING` | `PLANNED` |

---

## Import impact checklist

For every move:

1. Search all imports of the moved symbol/file.
2. Update production imports.
3. Update test imports.
4. Remove stale import aliases.
5. Remove old package files after imports are fixed.
6. Do not add compatibility wrappers.
7. Do not add redirect modules.
8. Do not add wrapper classes.
9. Run targeted import tests or impacted package tests.
10. Run `python -m pyright` when type boundaries are affected.
11. Run `python -m ruff check src/datp tests`.
12. Update `REFACTOR_MAP.md`, `PROJECT_MAP.md`, and this file.

---

## Scientific impact checklist

Before moving scoring, thresholding, evaluation, federated, experiments, or validation code, verify:

1. B1-B4 do not retrain.
2. Downstream stages do not call training.
3. Score artifacts remain shared.
4. Checkpoint paths remain baseline-independent for B1-B4.
5. Score paths remain baseline-independent for B1-B4.
6. Threshold/result paths remain baseline-specific only where scientifically correct.
7. Calibration-Pending behavior is preserved.
8. CV(FPR) coverage reporting is preserved.
9. Regime A/B/C/D semantics are preserved.

---

## Completion rule

No move batch is `DONE` after the first passing check.

Use:

```text
REAUDIT_REQUIRED
```

until a later pass confirms:

1. No stale imports.
2. No old wrappers.
3. No redirect modules.
4. No wrapper classes.
5. No duplicate modules.
6. Tests pass after integration.
7. `PROJECT_MAP.md` reflects actual current repository reality.
8. Scientific-contract audit remains valid.