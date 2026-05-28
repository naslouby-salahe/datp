# Packet Template

Copy this file to:

```text
AI Workflow/packets/PKT-XXX-short-name.md
```

before starting a new work packet.

A packet is not a rigid manual script.

A packet authorizes discovery-driven repair inside a controlled scope.

The agent must inspect the real repository, identify issues, fix what is in scope, update maps, run checks, and re-audit.

---

## Packet identity

| Field | Value |
|---|---|
| Packet ID | `PKT-XXX` |
| Title | `TODO` |
| Owner/tool | `DeepSeek V4 Pro unless otherwise recorded` |
| Status | `NOT_STARTED` |
| Created | `TODO` |
| Last updated | `TODO` |

---

## Purpose

State the exact refactoring/audit purpose.

Do not use vague cleanup language.

Bad:

```text
Clean the package.
```

Good:

```text
Inspect and repair ownership conflicts between scoring, federated training, thresholding, and their tests.
```

---

## Scope

### In scope

- `TODO`

### Out of scope

- training runs;
- heavy experiments;
- unrelated package cleanup;
- scientific baseline changes;
- paper/result/data edits unless explicitly authorized;
- backwards-compatibility wrappers;
- redirect modules;
- compatibility aliases;
- old package shells;
- old-path preservation tests.

---

## Planning rule

The following files are guardrails and ledgers, not blind instructions:

```text
AI Workflow/CLEAN_CODE_RULES.md
AI Workflow/REFACTOR_MAP.md
AI Workflow/TEST_REFACTOR_MAP.md
AI Workflow/MOVE_PLAN.md
AI Workflow/TEST_MOVE_PLAN.md
AI Workflow/TEST_IMPACT_MAP.md
AI Workflow/PATTERN_LEDGER.md
AI Workflow/state/PROJECT_MAP.md
```

The agent must:

```text
inspect the real code
confirm or reject planned moves
discover missing moves
update the plans
fix the code/tests
record evidence
```

If the plan is wrong, fix the plan.

If the real code is different from the plan, the real code wins until evidence is recorded and the plan is updated.

---

## Non-negotiable rule

No internal backwards compatibility.

Do not create or keep:

```text
redirect modules
wrapper modules
wrapper classes
compatibility aliases
old package shells
old files that only import from new files
tests that preserve old internal import paths
tests that validate old paths still work
```

Correct imports directly.

Update tests directly.

Delete obsolete files after imports are corrected.

---

## Clean-code rule

Every packet must enforce:

```text
AI Workflow/CLEAN_CODE_RULES.md
```

At minimum, the packet must check:

```text
canonical enum usage for closed concepts
canonical constants for stable names
dataclasses or typed objects for structured values
no duplicated typed shapes
no long primitive argument lists for domain concepts
no vague utility dumping grounds
no local duplicate fixes when a canonical owner is needed
no wrappers, redirects, compatibility aliases, or old shells
tests moved with production ownership
no old internal import paths preserved
no unjustified skipped/xfailed/commented-out tests
no hidden scientific parameters
no scientific behavior drift
```

Do not claim the packet is clean unless these were checked against the real files.

---

## File locks

Declare locks in:

```text
AI Workflow/REFACTOR_WORKBOARD.md
```

before editing.

| File/directory | Reason | Lock owner | Status |
|---|---|---|---|
| TBD | TBD | TBD | `PENDING` |

Do not let two agents edit overlapping files.

---

## Required reading

Before editing, read:

```text
AI Workflow/CLEAN_CODE_RULES.md
AI Workflow/REFACTOR_WORKBOARD.md
AI Workflow/AUDIT_CODE.md
AI Workflow/REFACTOR_MAP.md
AI Workflow/PATTERN_LEDGER.md
AI Workflow/MOVE_PLAN.md
AI Workflow/TEST_REFACTOR_MAP.md
AI Workflow/TEST_MOVE_PLAN.md
AI Workflow/TEST_IMPACT_MAP.md
AI Workflow/SCIENTIFIC_CONTRACT_AUDIT.md
AI Workflow/state/PROJECT_MAP.md
```

Then inspect the real files in scope.

Do not rely only on documentation.

---

## Pre-change discovery

Run or inspect commands appropriate to the packet.

Minimum:

```bash
git status --short
find <scope> -maxdepth 4 -type f | sort
rg "from datp\.|import datp\." <scope>
```

For package ownership packets, also run:

```bash
rg "datp\.baselines|datp\.training|datp\.models|datp\.pipeline|datp\.sweep|datp\.audit|datp\.analyses\.common|datp\.analyses\.threshold_variants|datp\.analyses\.comparators" src/datp tests
```

For clean-code packets, also run targeted searches for repeated patterns:

```bash
rg "B0|B1|B2|B3|B4|regime_a|regime_b|regime_c|metrics\.json|reconstruction_error|n_min|eligible|Calibration-Pending|outputs/|seed_|alpha_" src/datp tests
```

For test packets, also run:

```bash
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

## Discovery findings

| ID | Finding | Evidence | Risk | Decision | Status |
|---|---|---|---|---|---|
| TBD | TBD | TBD | TBD | TBD | `OPEN` |

---

## Implementation loop

Repeat until the packet reaches an evidence-backed stopping point:

1. Inspect the smallest relevant area.
2. Identify the real issue.
3. Decide the canonical owner.
4. Check `CLEAN_CODE_RULES.md`.
5. Update the move/test plan if needed.
6. Update imports directly.
7. Move or refactor code/tests.
8. Centralize enums/constants/dataclasses/schemas only when ownership is clear.
9. Delete obsolete old files only after imports are corrected.
10. Run Ruff.
11. Run Pyright when imports/types changed.
12. Run impacted tests.
13. Re-audit for stale paths, wrappers, redirects, aliases, duplicated enums/constants, and duplicated typed shapes.
14. Update workflow state and handoff.

Do not make broad uncontrolled edits.

Do not stop after the first successful command if stale paths, wrappers, redirects, aliases, skipped tests, duplicated closed concepts, duplicated constants, duplicated typed objects, or scientific risks remain.

---

## Scientific risk checklist

Mark every item as `NOT_TOUCHED`, `CHECKED_OK`, `RISK_FOUND`, or `FIXED`.

| Risk | Status | Evidence |
|---|---|---|
| B1-B4 retraining risk | `TODO` | `TODO` |
| Shared score artifact risk | `TODO` | `TODO` |
| Baseline-specific checkpoint risk | `TODO` | `TODO` |
| Score recomputation in downstream stage | `TODO` | `TODO` |
| Calibration-Pending behavior drift | `TODO` | `TODO` |
| Baseline semantic drift | `TODO` | `TODO` |
| Regime semantic drift | `TODO` | `TODO` |
| CV(FPR)/coverage reporting drift | `TODO` | `TODO` |
| Unsupported claim introduced | `TODO` | `TODO` |

---

## Clean-code risk checklist

Mark every item as `NOT_TOUCHED`, `CHECKED_OK`, `RISK_FOUND`, or `FIXED`.

| Risk | Status | Evidence |
|---|---|---|
| Closed concepts represented as scattered strings | `TODO` | `TODO` |
| Constants duplicated across packages | `TODO` | `TODO` |
| Structured value groups passed as primitives/dicts/tuples | `TODO` | `TODO` |
| Duplicate dataclasses/NamedTuples with same shape | `TODO` | `TODO` |
| Vague utility/common/helper ownership | `TODO` | `TODO` |
| Local duplicate fix instead of canonical owner | `TODO` | `TODO` |
| Wrapper/redirect/alias compatibility path | `TODO` | `TODO` |
| Tests preserving old internal paths | `TODO` | `TODO` |
| Skipped/xfailed/commented tests hiding failures | `TODO` | `TODO` |
| Hidden scientific parameter constants | `TODO` | `TODO` |

---

## Required checks

Default:

```bash
python -m ruff check src/datp tests
python -m pyright
python -m pytest <impacted-test-paths>
```

Use targeted tests first.

Use package-level tests when justified.

Do not run full E2E by default.

Do not run training or experiment sweeps unless explicitly authorized.

For E2E structure-only changes, use collection first:

```bash
python -m pytest --collect-only tests/e2e
```

---

## Optional checks

Use only when useful:

```bash
cs delta
cs review
uv run vulture src/datp tests --min-confidence 80
uv run refurb src/datp tests
uv run semgrep scan --config auto src/datp tests
```

Rules:

```text
Vulture findings are suspects, not proof.
Refurb suggestions are optional and must improve clarity.
Semgrep findings require triage.
Any change from these tools requires impacted tests.
```

---

## Commands run

| Command | Result | Notes |
|---|---|---|
| `TODO` | `TODO` | `TODO` |

---

## Tests/checks run

| Check | Result | Notes |
|---|---|---|
| `TODO` | `TODO` | `TODO` |

---

## Acceptance criteria

- [ ] Real code/tests were inspected.
- [ ] Issues were identified from evidence, not guessed.
- [ ] `CLEAN_CODE_RULES.md` was applied to the affected scope.
- [ ] Plans/maps were updated if reality contradicted them.
- [ ] Imports were updated directly.
- [ ] No redirect modules were added.
- [ ] No wrapper modules were added.
- [ ] No wrapper classes were added.
- [ ] No compatibility aliases were added.
- [ ] No old package shells remain unless documented as real current owners.
- [ ] No old-path preservation tests were added.
- [ ] Obsolete files were deleted when safe.
- [ ] Closed concepts use canonical enums or have a documented deferred owner.
- [ ] Stable labels/names use canonical constants or have a documented deferred owner.
- [ ] Structured value groups use dataclasses/typed objects where appropriate.
- [ ] Duplicate dataclass/NamedTuple shapes were merged or justified.
- [ ] Utility helpers have clear package ownership.
- [ ] Repeated patterns were recorded in `PATTERN_LEDGER.md`.
- [ ] Ruff passed or remaining issues are documented with exact reasons.
- [ ] Pyright passed or remaining issues are documented with exact reasons.
- [ ] Impacted tests passed or failures are documented with exact reasons.
- [ ] Scientific risks were reviewed.
- [ ] `PROJECT_MAP.md` was updated.
- [ ] `AUDIT_CODE.md` was updated.
- [ ] `PATTERN_LEDGER.md` was updated if repeated patterns were found.
- [ ] `TEST_IMPACT_MAP.md` was updated if tests changed.
- [ ] Workboard and handoff were updated.
- [ ] Packet is marked `REAUDIT_REQUIRED`, not `DONE`, unless later re-audit already passed.

---

## Stale-path audit

Run after ownership moves:

```bash
rg "datp\.baselines|datp\.training|datp\.models|datp\.pipeline|datp\.sweep|datp\.audit|datp\.analyses\.common|datp\.analyses\.threshold_variants|datp\.analyses\.comparators" src/datp tests
```

Any remaining old path must be documented as:

```text
real current owner
deferred move with reason
blocker with exact reason
```

It must not be a wrapper, redirect, alias, old package shell, or old-path preservation test.

---

## Clean-code re-audit

Run after meaningful refactors:

```bash
rg "B0|B1|B2|B3|B4|regime_a|regime_b|regime_c|metrics\.json|reconstruction_error|n_min|eligible|Calibration-Pending|outputs/|seed_|alpha_" src/datp tests
rg "utils|helpers|misc|common|shared" src/datp tests
rg "skip|xfail|pytest\.skip|pytest\.mark\.skip|pytest\.mark\.xfail" tests
```

Remaining matches are not automatically wrong, but each must have a clear owner or justification.

---

## Handoff

Before stopping, update:

```text
AI Workflow/state/HANDOFFS.md
```

Include:

```text
current git status
packet status
file locks
changed files
commands run
checks passed
checks failed
checks deferred
scientific risks
clean-code risks
remaining stale paths
remaining wrappers or redirects if any
remaining duplicated enums/constants/typed shapes if any
next exact action
```

---

## Completion status rule

Do not mark the packet `DONE` after the first successful pass.

Use:

```text
REAUDIT_REQUIRED
```

until a later re-audit confirms:

```text
no stale imports
no old wrappers
no redirects
no compatibility aliases
no obsolete test paths
no duplicated closed-concept enums
no duplicated canonical constants
no duplicated typed shapes
checks still pass after related packets
scientific contract remains valid
```