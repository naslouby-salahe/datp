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
4. Update the move/test plan if needed.
5. Update imports directly.
6. Move or refactor code/tests.
7. Delete obsolete old files only after imports are corrected.
8. Run Ruff.
9. Run Pyright when imports/types changed.
10. Run impacted tests.
11. Re-audit for stale paths, wrappers, redirects, and aliases.
12. Update workflow state and handoff.

Do not make broad uncontrolled edits.

Do not stop after the first successful command if stale paths, wrappers, redirects, aliases, skipped tests, or scientific risks remain.

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
- [ ] Plans/maps were updated if reality contradicted them.
- [ ] Imports were updated directly.
- [ ] No redirect modules were added.
- [ ] No wrapper modules were added.
- [ ] No wrapper classes were added.
- [ ] No compatibility aliases were added.
- [ ] No old package shells remain unless documented as real current owners.
- [ ] No old-path preservation tests were added.
- [ ] Obsolete files were deleted when safe.
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
remaining stale paths
remaining wrappers or redirects if any
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
checks still pass after related packets
scientific contract remains valid
```
