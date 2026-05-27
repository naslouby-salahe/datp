# PKT-002 — Tests Structure Ownership Refactor

## Packet identity

| Field | Value |
|---|---|
| Packet ID | `PKT-002` |
| Title | `tests` structure ownership refactor |
| Owner/tool | VS Code Copilot + DeepSeek V4 Pro unless escalated |
| Status | `READY_AFTER_PKT_001` |
| Created | After target test structure decision |
| Last updated | `TODO` |

---

## Purpose

Refactor the `tests` package so it mirrors the new `src/datp` responsibility-based architecture.

The target test structure is defined in:

```text
AI Workflow/TEST_REFACTOR_MAP.md
```

The concrete test move plan is defined in:

```text
AI Workflow/TEST_MOVE_PLAN.md
```

This packet must remove stale test ownership around old production packages such as:

```text
baselines
training
models
pipeline
sweep
audit
```

and replace them with:

```text
thresholding
federated
modeling
experiments
validation
scoring
```

---

## Scope

### In scope

```text
tests
AI Workflow/TEST_REFACTOR_MAP.md
AI Workflow/TEST_MOVE_PLAN.md
AI Workflow/TEST_IMPACT_MAP.md
AI Workflow/state/PROJECT_MAP.md
AI Workflow/AUDIT_CODE.md
AI Workflow/PATTERN_LEDGER.md
AI Workflow/SCIENTIFIC_CONTRACT_AUDIT.md
AI Workflow/REFACTOR_WORKBOARD.md
```

### Out of scope

```text
production code refactor except import fixes required by already-moved production code
paper editing
result editing
dataset editing
scientific config changes
training runs
full E2E runs by default
new scientific baselines
new functionality
backwards-compatibility tests
redirect tests
wrapper tests
alias-preservation tests
```

---

## Hard boundary

Do not restructure anything outside `tests` unless it is required to update imports for already-moved `src/datp` code.

Do not use this packet to perform the main production package refactor.

If production code has not moved yet, prepare the test move plan but do not fake passing imports.

---

## No-backwards-compatibility rule

No internal backwards compatibility is allowed.

Do not create:

```text
redirect tests
wrapper tests
alias-preservation tests
old package-path tests
tests that only validate obsolete import paths
tests that keep obsolete package names alive
```

Do not preserve old internal test paths.

Do not preserve old production import paths.

Do not keep obsolete test folders alive.

Fix all imports directly.

Move tests to the new ownership.

Delete obsolete test folders after imports are corrected.

---

## Required reading

Before editing:

```text
AI Workflow/REFACTOR_MAP.md
AI Workflow/MOVE_PLAN.md
AI Workflow/TEST_REFACTOR_MAP.md
AI Workflow/TEST_MOVE_PLAN.md
AI Workflow/TEST_IMPACT_MAP.md
AI Workflow/SCIENTIFIC_CONTRACT_AUDIT.md
AI Workflow/state/PROJECT_MAP.md
```

Then inspect the real tests under:

```text
tests
```

Do not rely only on the target tree.

---

## File locks

Declare locks in:

```text
AI Workflow/REFACTOR_WORKBOARD.md
```

before editing.

Initial lock set:

| File/directory | Reason | Lock owner | Status |
|---|---|---|---|
| `tests` | Test structure ownership refactor. | DeepSeek V4 Pro | `PENDING` |
| `AI Workflow/TEST_REFACTOR_MAP.md` | Target test ownership map maintenance. | DeepSeek V4 Pro | `PENDING` |
| `AI Workflow/TEST_MOVE_PLAN.md` | Test move execution ledger. | DeepSeek V4 Pro | `PENDING` |
| `AI Workflow/TEST_IMPACT_MAP.md` | Impacted tests and commands. | DeepSeek V4 Pro | `PENDING` |
| `AI Workflow/state/PROJECT_MAP.md` | Current test reality after each move batch. | DeepSeek V4 Pro | `PENDING` |
| `AI Workflow/SCIENTIFIC_CONTRACT_AUDIT.md` | Scientific invariant coverage audit. | DeepSeek V4 Pro | `PENDING` |

No other locks are allowed unless justified in the workboard.

---

## Pre-change audit

Run or inspect:

```bash
git status --short
find tests -maxdepth 4 -type f | sort
rg "from datp\.|import datp\." tests
rg "datp\.baselines|datp\.training|datp\.models|datp\.pipeline|datp\.sweep|datp\.audit|datp\.analyses\.common|datp\.analyses\.threshold_variants|datp\.analyses\.comparators" tests
rg "skip|xfail|pytest\.skip|pytest\.mark\.skip|pytest\.mark\.xfail" tests
```

Record findings in:

```text
AI Workflow/AUDIT_CODE.md
AI Workflow/PATTERN_LEDGER.md
AI Workflow/TEST_IMPACT_MAP.md
AI Workflow/state/PROJECT_MAP.md
```

---

## Implementation order

Use the move batches from:

```text
AI Workflow/TEST_MOVE_PLAN.md
```

Recommended order:

1. Move CLI and modeling tests.
2. Move training tests to federated and scoring.
3. Move baseline tests to thresholding.
4. Move threshold variant and comparator tests.
5. Move pipeline and sweep tests to experiments.
6. Move audit tests to validation.
7. Flatten analysis common tests.
8. Clean E2E regime folders.
9. Consolidate repeated fixtures.

Do not do all batches in one uncontrolled edit.

Run targeted checks after each risky batch.

---

## Required test package rules

### `tests/unit/federated`

May test:

```text
FL clients
FedAvg/FedProx/FedRep protocols
Flower/Ray simulation helpers
local training loop
model parameter serialization
shared encoder checkpoints
training convergence
```

Must not test:

```text
B1-B4 threshold choice
final metric computation
post hoc analysis
reporting
```

### `tests/unit/scoring`

May test:

```text
reconstruction-error generation
score artifact schema
score loading
score provider abstraction
score manifest validation
```

Must not test:

```text
threshold selection
baseline comparison
final reporting claims
```

### `tests/unit/thresholding`

May test:

```text
B0-B4 threshold strategies
threshold variants
threshold comparators
calibration eligibility
Calibration-Pending fallback
threshold application helpers
threshold result serialization
```

Must not test:

```text
FL training
score generation
report building
```

### `tests/unit/experiments`

May test:

```text
stage orchestration
sweep orchestration
diagnostic workflows
preflight validation
console progress
```

Must not test:

```text
low-level model training internals
threshold math
metric math
dataset-specific parsing
```

### `tests/unit/validation`

May test:

```text
scientific invariant checks
artifact validation
score manifest validation
result validation
metric reproduction
dataset assumption validation
verdict writing
```

Must not test:

```text
primary implementation logic
training
threshold computation
reporting output generation
```

---

## Forbidden implementation patterns

Do not create tests like this:

```python
def test_old_baselines_import_still_works():
    import datp.baselines
```

Do not create tests like this:

```python
def test_old_training_import_redirects():
    from datp.training import run_fl_training
```

Do not create tests like this:

```python
OldName = NewName
```

Do not create tests like this:

```python
class OldTestName(NewTestName):
    pass
```

Do not leave files like these after production packages move:

```text
tests/unit/baselines/main/test_threshold_strategies.py
tests/unit/training/test_scoring.py
tests/unit/models/test_model.py
tests/unit/pipeline/test_executor.py
tests/unit/sweep/test_sweep.py
tests/unit/audit/test_verdicts.py
```

unless the agent proves the production packages still exist and are still canonical.

Do not mark import-related tests as skipped or xfailed.

Fix imports correctly.

Delete obsolete test folders.

---

## Required checks

After each test move batch:

```bash
python -m ruff check src/datp tests
python -m pyright
python -m pytest <impacted-test-paths>
```

Use the impacted paths from:

```text
AI Workflow/TEST_IMPACT_MAP.md
AI Workflow/TEST_MOVE_PLAN.md
```

Do not run full E2E by default.

Do not run training.

Do not run experiment sweeps.

For E2E structure-only moves, run collection first:

```bash
python -m pytest --collect-only tests/e2e
```

Run actual E2E only if directly required and explicitly approved.

---

## Scientific audit requirements

After moving tests that touch scoring, thresholding, federated, experiments, or validation, update:

```text
AI Workflow/SCIENTIFIC_CONTRACT_AUDIT.md
```

Must verify that tests still cover:

1. No retraining per B1-B4 baseline.
2. B1-B4 derive from shared score artifacts.
3. Score paths are baseline-independent for B1-B4.
4. Checkpoint paths are baseline-independent for B1-B4.
5. Result paths are baseline-specific.
6. Threshold/result stage does not call training.
7. Reporting does not call training.
8. Analysis does not recompute scores unless explicitly valid.
9. Calibration-Pending behavior remains covered.
10. Baseline labels keep the same meaning.
11. Regime labels keep the same meaning.
12. CV(FPR) coverage remains covered.

---

## Acceptance criteria

1. `tests` follows the responsibility structure in `TEST_REFACTOR_MAP.md`, or every deviation is documented with evidence.
2. No old-path import tests remain.
3. No redirect tests remain.
4. No wrapper tests remain.
5. No alias-preservation tests remain.
6. No obsolete test folders remain after production package moves.
7. Test imports are updated to canonical production paths.
8. Impacted tests are updated and passing.
9. Ruff passes for `src/datp` and impacted tests.
10. Pyright passes or remaining issues are documented with exact reasons.
11. Scientific-contract audit is updated.
12. `PROJECT_MAP.md` records current test reality after moves.
13. `TEST_MOVE_PLAN.md` records completed and deferred moves.
14. `TEST_IMPACT_MAP.md` records impacted tests and commands.
15. Packet is marked `REAUDIT_REQUIRED`, not `DONE`, until a later audit confirms no stale test paths remain.

---

## Handoff requirement

Before stopping, update:

```text
AI Workflow/state/HANDOFFS.md
```

Include:

```text
current git status
test move batches completed
test move batches not started
files changed
commands run
tests run
checks failed
checks deferred
scientific risks
remaining stale test imports if any
remaining old test folders if any
remaining wrappers if any
remaining redirects if any
remaining compatibility aliases if any
next exact action
```