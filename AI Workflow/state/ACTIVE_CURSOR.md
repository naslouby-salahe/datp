# Active Cursor

This file is the canonical resume point for `Start_My_Agent`.

The next agent must read this file before planning new work.

Do not leave this file vague.

Do not rely on chat memory.

Do not restart from scratch if this file contains a valid next action.

---

## Current phase

`DISCOVERY`

Allowed values:

```text
DISCOVERY
PLANNING
IMPLEMENTATION
TESTING
REAUDIT
HANDOFF
BLOCKED
COMPLETE
```

---

## Active packet

`PKT-000-readiness-and-inventory`

---

## Active ticket

`NONE`

---

## Active goal

Initialize or resume the DATP autonomous workflow, verify repository and tool reality, protect the scientific contract, then continue to the next safe packet without human interaction.

---

## Last completed step

`NONE`

---

## Next exact step

Run startup verification from `AI Workflow/ORCHESTRATOR_PROMPT.md`, record exact results in workflow state, then continue with the highest-priority unresolved packet.

---

## Blockers

- None recorded.

---

## Repository root

```text
/home/naslouby/Projects/datp
```

---

## Launcher

Canonical launcher:

```text
Start_My_Agent
```

Legacy alias accepted only for compatibility:

```text
StartMyAgent
```

---

## Files currently in scope

```text
.github/copilot-instructions.md
AI Workflow/AI_WORKFLOW_READINESS.md
AI Workflow/CLEAN_CODE_RULES.md
AI Workflow/ORCHESTRATOR_PROMPT.md
AI Workflow/MODEL_COST_POLICY.md
AI Workflow/SESSION_POLICY.md
AI Workflow/SESSION_HANDOFF_TEMPLATE.md
AI Workflow/QUICK_START_COMMANDS.md
AI Workflow/state/ACTIVE_CURSOR.md
AI Workflow/state/HANDOFFS.md
AI Workflow/state/RUN_LEDGER.md
AI Workflow/state/AGENT_MEMORY.md
AI Workflow/state/CHECK_FLAGS.md
AI Workflow/state/PROJECT_MAP.md
AI Workflow/state/TOOL_STATUS.md
AI Workflow/state/GRAPHIFY_STATUS.md
AI Workflow/state/FILE_HASHES.json
AI Workflow/REFACTOR_WORKBOARD.md
AI Workflow/AUDIT_CODE.md
AI Workflow/PATTERN_LEDGER.md
```

---

## File locks

| File/directory | Lock status | Reason | Next action |
|---|---|---|---|
| `NONE` | `NONE` | `NONE` | `NONE` |

---

## Commands already run

```text
NONE
```

---

## Commands still required

```bash
cd /home/naslouby/Projects/datp
pwd
git status --short
python --version
python -m pytest --version
python -m ruff --version
python -m pyright --version || pyright --version
cs --version || true
graphify --version || true
uv run vulture --version || vulture --version || true
uv run refurb --version || refurb --version || true
uv run semgrep --version || semgrep --version || true
```

---

## Checks already run

- None recorded.

---

## Checks still required

- Repository root check.
- Git status check.
- Python version check.
- pytest version check.
- Ruff version check.
- Pyright version check.
- Optional CodeScene availability check.
- Optional Graphify availability check.
- Optional Vulture availability check.
- Optional Refurb availability check.
- Optional Semgrep availability check.
- Workflow state consistency check.
- Packet inventory check.
- Ticket inventory check.
- File-lock check.
- Handoff consistency check.

---

## Scientific checks still required

- Confirm `Blueprint.md` exists.
- Confirm `CLAUDE.md` exists.
- Confirm `docs/journal/PRE_CODING_PLAN.md` exists.
- Confirm `docs/journal/CODING_PLAN.md` exists.
- Confirm `docs/journal/EXPERIMENT_PLAN.md` exists.
- Confirm `docs/journal/POST_EXPERIMENT_PLAN.md` exists.
- Confirm archived `Journal/Journal_Extension_Master_Roadmap.md` does not override the active four-file journal package.
- Confirm no production edit happens before startup gates pass.
- Confirm DATP threshold-scope identity remains locked.
- Confirm B1 through B4 shared-score invariant remains locked.
- Confirm no per-baseline retraining is introduced.
- Confirm thresholding and evaluation do not call training.
- Confirm stage boundaries remain preserved.
- Confirm no unsupported poisoning, evasion, formal privacy, hardware, concept-drift, or zero-day claims are introduced.

---

## Quality checks still required

- Ruff targeted check after first code batch.
- Pyright after first code batch.
- Impacted pytest after first code batch.
- Wrapper and redirect audit after any package move.
- Compatibility alias audit after any package move.
- Old import path audit after any package move.
- Skipped-test audit after test changes.
- Duplicate enum and constant audit after refactors.
- Optional Graphify refresh when ownership maps change.
- Optional CodeScene, Vulture, Refurb, Semgrep when useful and available.

---

## Current assumptions

| Assumption | Evidence | Invalidation rule |
|---|---|---|
| `Start_My_Agent` is canonical launcher. | Workflow files standardize it. | Invalidate if `.github/copilot-instructions.md` changes launcher. |
| `StartMyAgent` is legacy alias only. | Older notes mention it. | Invalidate if alias is removed from launcher contract. |
| No active blocker is recorded yet. | This initial cursor has no blocker. | Invalidate after any failed command or unsafe git state. |
| PKT-000 is the default starting packet if no valid cursor exists. | Orchestrator default packet policy. | Invalidate if packet inventory changes. |

---

## Last handoff pointer

```text
AI Workflow/state/HANDOFFS.md
```

No handoff recorded in this template state.

---

## Required state files to inspect next

```text
AI Workflow/state/HANDOFFS.md
AI Workflow/state/RUN_LEDGER.md
AI Workflow/state/AGENT_MEMORY.md
AI Workflow/state/CHECK_FLAGS.md
AI Workflow/state/PROJECT_MAP.md
AI Workflow/state/TOOL_STATUS.md
AI Workflow/state/GRAPHIFY_STATUS.md
AI Workflow/state/FILE_HASHES.json
AI Workflow/REFACTOR_WORKBOARD.md
AI Workflow/PATTERN_LEDGER.md
docs/tickets/ticket_inventory.md
docs/tickets/ticket_progress.md
docs/tickets/human_interventions.md
```

---

## Next safe packet if startup passes

```text
AI Workflow/packets/PKT-000-readiness-and-inventory.md
```

After PKT-000 passes, continue automatically to the next unresolved safe packet.

Do not stop merely because readiness completed.

---

## Required handoff behavior

Before any stop, update:

```text
AI Workflow/state/HANDOFFS.md
AI Workflow/state/RUN_LEDGER.md
AI Workflow/REFACTOR_WORKBOARD.md
```

The handoff must include:

```text
current git status
active packet
active ticket
completed work
files changed
commands run
checks run
checks failed
checks deferred
scientific risks
blockers
next exact action
resume command
```

---

## Resume command

```text
Start_My_Agent
```