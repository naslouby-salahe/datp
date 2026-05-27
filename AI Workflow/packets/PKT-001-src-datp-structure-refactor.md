# PKT-001 — `src/datp` Structure Ownership Refactor

## Packet identity

| Field | Value |
|---|---|
| Packet ID | `PKT-001` |
| Title | `src/datp` structure ownership refactor |
| Owner/tool | VS Code Copilot + DeepSeek V4 Pro unless escalated |
| Status | `READY_AFTER_PKT_000` |
| Created | After target structure decision |
| Last updated | `TODO` |

---

## Purpose

Refactor only `src/datp` into the target responsibility-based package structure defined in:

```text
AI Workflow/REFACTOR_MAP.md
```

This packet must make package ownership clearer while preserving DATP scientific behavior.

The target structure is not optional, but the agent must inspect real code before each move and may split moves into safe batches.

---

## Scope

### In scope

```text
src/datp
tests impacted by moved src/datp code
AI Workflow/MOVE_PLAN.md
AI Workflow/REFACTOR_MAP.md
AI Workflow/state/PROJECT_MAP.md
AI Workflow/TEST_IMPACT_MAP.md
AI Workflow/SCIENTIFIC_CONTRACT_AUDIT.md
AI Workflow/AUDIT_CODE.md
AI Workflow/PATTERN_LEDGER.md
```

### Out of scope

```text
non-src/datp package restructuring
paper editing
result editing
dataset editing
scientific config changes unless required to fix broken imports
training runs
full E2E runs by default
new scientific baselines
new functionality
backwards-compatibility wrappers
redirect modules
wrapper classes
compatibility aliases
```

---

## Hard boundary

Do not discuss, refactor, or restructure anything outside `src/datp` except tests/imports required by moved `src/datp` code.

Do not rename non-`src/datp` folders.

Do not change paper, result, data, artifact, or journal files.

---

## No-backwards-compatibility rule

No internal backwards compatibility is allowed.

Do not create:

```text
redirect modules
wrapper modules
wrapper classes
compatibility aliases
old package shells
old files that only import from new files
temporary backwards-compatible internal paths
```

Do not preserve old internal paths.

Do not keep old package names alive.

Do not keep old modules alive.

Fix all imports and tests directly.

Delete obsolete modules after imports are corrected.

---

## Required reading

Before editing:

```text
AI Workflow/REFACTOR_MAP.md
AI Workflow/MOVE_PLAN.md
AI Workflow/SCIENTIFIC_CONTRACT_AUDIT.md
AI Workflow/TEST_IMPACT_MAP.md
AI Workflow/state/PROJECT_MAP.md
```

Then inspect the real code under:

```text
src/datp
```

Do not rely only on the target tree.

---

## File locks

Declare locks in `AI Workflow/REFACTOR_WORKBOARD.md` before editing.

Initial lock set:

| File/directory | Reason | Lock owner | Status |
|---|---|---|---|
| `src/datp` | Package ownership refactor. | DeepSeek V4 Pro | `PENDING` |
| `tests` | Update imports/tests affected by moved `src/datp` code only. | DeepSeek V4 Pro | `PENDING` |
| `AI Workflow/REFACTOR_MAP.md` | Target ownership map maintenance. | DeepSeek V4 Pro | `PENDING` |
| `AI Workflow/MOVE_PLAN.md` | Move execution ledger. | DeepSeek V4 Pro | `PENDING` |
| `AI Workflow/state/PROJECT_MAP.md` | Current reality map after each move batch. | DeepSeek V4 Pro | `PENDING` |
| `AI Workflow/TEST_IMPACT_MAP.md` | Impacted tests and commands. | DeepSeek V4 Pro | `PENDING` |
| `AI Workflow/SCIENTIFIC_CONTRACT_AUDIT.md` | Scientific invariant audit. | DeepSeek V4 Pro | `PENDING` |

No other locks are allowed unless justified in the workboard.

---

## Pre-change audit

Run or inspect:

```bash
git status --short
find src/datp -maxdepth 3 -type f | sort
rg "from datp\.|import datp\." src/datp tests
rg "B0|B1|B2|B3|B4|baseline|Regime|regime|threshold|score|training|scoring|metrics|eligible|n_min" src/datp tests
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
AI Workflow/MOVE_PLAN.md
```

Recommended order:

1. Move `cli` to `app/cli`.
2. Move `models` to `modeling`.
3. Move `training` to `federated`, except inspect `training/scoring.py` separately.
4. Extract `scoring`.
5. Move `baselines` to `thresholding`.
6. Move threshold variants and comparators into `thresholding`.
7. Merge `pipeline` and `sweep` into `experiments`.
8. Rename `audit` to `validation`.
9. Flatten `analyses/common`.
10. Centralize domain enums only after duplicate enum/string ownership is confirmed.

Do not do all batches in one uncontrolled edit.

Run targeted checks after each risky batch.

---

## Required package rules

### `federated`

May own:

```text
FL clients
FedAvg/FedProx/FedRep protocols
Flower/Ray simulation
local training loop
model parameter serialization
shared encoder checkpoints
training convergence
```

Must not own:

```text
B1-B4 threshold choice
final metric computation
post hoc analysis
reporting
```

### `scoring`

May own:

```text
reconstruction-error generation
score artifact schema
score loading
score provider abstraction
```

Must not own:

```text
threshold selection
baseline comparison
final reporting claims
```

### `thresholding`

May own:

```text
B0-B4 threshold strategies
threshold variants
threshold comparators
calibration eligibility
Calibration-Pending fallback
threshold application helpers
threshold result serialization
```

Must not own:

```text
FL training
score generation
report building
```

### `evaluation`

May own:

```text
confusion counts
client metrics
global metrics
CV(FPR)
Macro-F1
worst-client BA
metric key names
baseline ranking helpers
```

Must not own:

```text
score generation
threshold derivation
training
paper formatting
```

### `experiments`

May own:

```text
stage orchestration
sweep orchestration
diagnostic workflows
preflight validation
console progress
```

Must not own:

```text
low-level model training internals
threshold math
metric math
dataset-specific parsing
```

### `validation`

May own:

```text
scientific invariant checks
artifact validation
score manifest validation
result validation
metric reproduction
dataset assumption validation
verdict writing
```

Must not own:

```text
primary implementation logic
training
threshold computation
reporting output generation
```

---

## Forbidden implementation patterns

Do not create files like these if they only redirect to new locations:

```text
src/datp/baselines/main/b1.py
src/datp/training/__init__.py
src/datp/models/__init__.py
src/datp/audit/__init__.py
```

Do not create code like this:

```python
from datp.thresholding.strategies.b1_global import *
```

Do not create code like this:

```python
class OldBaselineName(NewBaselineName):
    pass
```

Do not create compatibility aliases like this:

```python
OldName = NewName
```

Do not preserve old internal paths.

Do not keep compatibility shells.

Do not mark import-related tests as skipped or xfailed.

Fix imports correctly.

Delete obsolete files.

---

## Required checks

After each move batch:

```bash
python -m ruff check src/datp tests
python -m pyright
python -m pytest <impacted-test-paths>
```

Use the impacted paths from:

```text
AI Workflow/TEST_IMPACT_MAP.md
```

Do not run full E2E by default.

Do not run training.

Do not run experiment sweeps.

---

## Optional checks

Use when helpful:

```bash
cs delta
cs review
uv run vulture src/datp tests --min-confidence 80
uv run refurb src/datp tests
uv run semgrep scan --config auto src/datp tests
```

Interpret optional findings carefully:

```text
Vulture findings are suspects, not proof.
Refurb suggestions are optional and must improve clarity.
Semgrep findings require triage.
```

---

## Scientific audit requirements

After moving scoring, thresholding, federated, experiments, or validation code, update:

```text
AI Workflow/SCIENTIFIC_CONTRACT_AUDIT.md
```

Must verify:

1. No retraining per B1-B4 baseline.
2. B1-B4 derive from shared score artifacts.
3. Threshold/result stage does not call training.
4. Report stage does not call training.
5. Analysis stage does not recompute scores unless explicitly documented and scientifically valid.
6. Calibration-Pending behavior remains unchanged.
7. Baseline labels keep the same meaning.
8. Regime labels keep the same meaning.
9. CV(FPR) reporting still includes coverage where required.

---

## Acceptance criteria

1. `src/datp` follows the responsibility structure in `REFACTOR_MAP.md`, or every deviation is documented with evidence.
2. No wrappers remain.
3. No redirects remain.
4. No compatibility aliases remain.
5. No wrapper classes remain.
6. No old internal package shells remain.
7. Imports are updated across production and impacted tests.
8. Impacted tests are updated and passing.
9. Ruff passes for `src/datp` and impacted tests.
10. Pyright passes or remaining issues are documented with exact reasons.
11. Scientific-contract audit is updated.
12. `PROJECT_MAP.md` records current reality after moves.
13. `MOVE_PLAN.md` records completed and deferred moves.
14. `TEST_IMPACT_MAP.md` records impacted tests and commands.
15. Packet is marked `REAUDIT_REQUIRED`, not `DONE`, until a later audit confirms no stale imports, wrappers, redirects, or compatibility aliases remain.

---

## Handoff requirement

Before stopping, update:

```text
AI Workflow/state/HANDOFFS.md
```

Include:

```text
current git status
move batches completed
move batches not started
files changed
commands run
tests run
checks failed
checks deferred
scientific risks
remaining stale imports
remaining wrappers if any
remaining redirects if any
remaining compatibility aliases if any
next exact action
```