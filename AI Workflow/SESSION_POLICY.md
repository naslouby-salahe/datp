# Session Management Policy

Long AI sessions become token-expensive and noisy.

Every session must be managed as a resumable work unit with explicit state.

Written files are the source of truth.

Chat memory is not a reliable source of truth.

The next `Start_My_Agent` run must be able to continue without human guidance.

---

## Canonical launcher

The canonical launcher is:

```text
Start_My_Agent
```

The legacy alias below is accepted only for compatibility with older notes:

```text
StartMyAgent
```

Normalize the legacy alias internally to `Start_My_Agent`.

---

## Session source of truth

The following files define session continuity:

```text
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
```

Do not rely on chat memory.

Do not rely on model memory.

Do not rely on unstated assumptions.

---

## Keep the same session when

- working on the same work packet;
- editing the same small file group;
- debugging the same issue;
- reviewing the same diff;
- the context is still useful;
- the session is not too long, repetitive, or noisy;
- the current batch is not complete;
- no model/tool switch is needed.

---

## Start a new session when

- starting a new work packet;
- moving to a different package;
- switching from implementation to final review;
- switching tools or roles;
- changing models;
- after a quota warning;
- after a timeout risk;
- after a packet is completed;
- after major Graphify/project-map refresh;
- after major package moves;
- after deleting wrappers or compatibility shells;
- after test-structure changes;
- the session repeats itself;
- the session hallucinates;
- the session relies on outdated assumptions;
- the session starts ignoring the active cursor;
- the session starts asking the user what to do next during autonomous execution.

Before starting a new session, write a handoff and update the active cursor.

---

## Required new-session startup

At the start of every new session, run:

```bash
cd /home/naslouby/Projects/datp
pwd
git status --short
```

Then read:

```text
.github/copilot-instructions.md
AI Workflow/AI_WORKFLOW_READINESS.md
AI Workflow/ORCHESTRATOR_PROMPT.md
AI Workflow/CLEAN_CODE_RULES.md
AI Workflow/MODEL_COST_POLICY.md
AI Workflow/SESSION_POLICY.md
AI Workflow/state/ACTIVE_CURSOR.md
AI Workflow/state/HANDOFFS.md
AI Workflow/state/RUN_LEDGER.md
AI Workflow/state/AGENT_MEMORY.md
AI Workflow/state/CHECK_FLAGS.md
AI Workflow/state/PROJECT_MAP.md
AI Workflow/state/TOOL_STATUS.md
AI Workflow/state/GRAPHIFY_STATUS.md
AI Workflow/REFACTOR_WORKBOARD.md
AI Workflow/REFACTOR_MAP.md
AI Workflow/PATTERN_LEDGER.md
AI Workflow/MOVE_PLAN.md
AI Workflow/TEST_IMPACT_MAP.md
```

Then read the active packet or active ticket from `ACTIVE_CURSOR.md`.

Continue from written progress, not from memory.

`AI_WORKFLOW_READINESS.md` is intentionally kept and must remain part of startup.

---

## Required scientific session startup

Before any production or scientific edit, read:

```text
Blueprint.md
CLAUDE.md
docs/journal/PRE_CODING_PLAN.md
docs/journal/CODING_PLAN.md
docs/journal/EXPERIMENT_PLAN.md
docs/journal/POST_EXPERIMENT_PLAN.md
```

Treat archived roadmap content as lower priority:

```text
Journal/Journal_Extension_Master_Roadmap.md
```

If archived content conflicts with active journal files, active journal files win.

Record any conflict in:

```text
AI Workflow/state/CHECK_FLAGS.md
AI Workflow/SCIENTIFIC_CONTRACT_AUDIT.md
```

---

## Required end-of-session handoff

Before ending a session, update the workflow files and record:

- what was completed;
- what remains;
- changed files;
- inspected files;
- locked files;
- commands run;
- tests/checks run;
- Graphify runs or skipped Graphify reason;
- project-map updates;
- deferred checks;
- failures;
- quota/tool issues;
- scientific risks;
- assumptions made;
- blockers;
- next exact action.

Use:

```text
AI Workflow/SESSION_HANDOFF_TEMPLATE.md
AI Workflow/state/HANDOFFS.md
AI Workflow/state/ACTIVE_CURSOR.md
AI Workflow/state/RUN_LEDGER.md
AI Workflow/REFACTOR_WORKBOARD.md
```

The handoff is mandatory before:

```text
manual stop
quota stop
timeout
tool crash
model switch
tool switch
packet switch
hard blocker
scientific blocker
final completion
```

---

## Active cursor rule

`ACTIVE_CURSOR.md` is the single most important resume file.

It must be updated:

1. after startup;
2. after every meaningful batch;
3. after any command failure;
4. after any check failure;
5. after any file edit group;
6. after any tool switch;
7. after any model switch;
8. before any session stop;
9. after any hard blocker;
10. after any packet transition.

The cursor must always tell the next agent exactly what to do next.

Bad next action:

```text
Continue refactoring.
```

Good next action:

```text
Run python -m pytest tests/unit/training/test_runtime.py, then fix the failing import in src/datp/training/runtime.py if the failure reproduces.
```

---

## File-lock rule

Before editing files, inspect:

```text
AI Workflow/REFACTOR_WORKBOARD.md
AI Workflow/state/ACTIVE_CURSOR.md
AI Workflow/state/HANDOFFS.md
git status --short
```

If a prior session left locks:

1. verify whether the lock is current;
2. check whether files have changed;
3. continue the locked batch or release the lock with evidence;
4. record the decision.

Do not edit over unresolved locks.

Do not leave locks stale.

---

## Session naming

Use descriptive session names when the tool supports it:

```text
DATP-PKT-000-readiness
DATP-PKT-001-repo-map
DATP-PKT-002-pattern-ledger
DATP-PKT-003-artifacts-paths
DATP-PKT-005-score-metrics
DATP-PKT-006-calibration-eligibility
DATP-PKT-009-quality-gate
DATP-final-hostile-review
```

---

## Model-switch rule

Before switching models:

1. update `ACTIVE_CURSOR.md`;
2. write a handoff;
3. record why the switch is needed;
4. record current files in scope;
5. record current locks;
6. record last command and result;
7. record next exact command.

Do not switch models with unrecorded edits.

Do not switch models to avoid documenting a blocker.

---

## Tool-switch rule

Before switching from Copilot to Claude, Codex, Antigravity, WSL Copilot CLI, or another tool:

1. record current objective;
2. record files in scope;
3. record exact prompt or command to use;
4. record expected output;
5. record checks already run;
6. record checks still required;
7. record scientific constraints relevant to the task.

Do not ask another tool to make broad changes without handing it the scientific contract and current packet boundaries.

---

## Graphify session rule

Graphify should be refreshed in a fresh or clearly bounded session when:

1. initial repository mapping starts;
2. major package moves finish;
3. scoring, thresholding, metrics, eligibility, artifacts, or reporting ownership changes;
4. test structure changes significantly;
5. wrappers or compatibility shells are deleted;
6. final hostile architecture review starts.

After Graphify runs, update:

```text
AI Workflow/state/GRAPHIFY_STATUS.md
AI Workflow/state/PROJECT_MAP.md
AI Workflow/state/CHECK_FLAGS.md
AI Workflow/state/RUN_LEDGER.md
AI Workflow/state/ACTIVE_CURSOR.md
```

If Graphify is unavailable, record the limitation.

Do not claim Graphify evidence exists unless it actually ran.

---

## Sonar session rule

Local Sonar has been unreliable.

Do not start a new session only to satisfy Sonar unless the repository is ready for an optional final audit and Sonar is healthy.

If Sonar fails for environmental reasons:

1. record the failure;
2. do not claim Sonar passed;
3. continue with Ruff, Pyright, targeted pytest, CodeScene, optional Vulture/Refurb/Semgrep, and source inspection;
4. mark Sonar as an environmental limitation.

---

## Quality-gate session rule

Prefer targeted checks during implementation:

```bash
python -m ruff check src/datp tests
python -m pyright
python -m pytest <impacted-test-paths>
```

Use package-level tests when justified.

Avoid full E2E by default.

Avoid training and heavy experiments unless explicitly authorized.

Record all commands and results in:

```text
AI Workflow/state/RUN_LEDGER.md
AI Workflow/state/ACTIVE_CURSOR.md
```

---

## Hard-blocker session rule

If a hard blocker is reached, do not ask the user immediately.

First try safe fallback work:

1. inspect files manually;
2. reduce scope;
3. run targeted checks instead of broad checks;
4. skip optional tools and record limitation;
5. switch to another approved tool if useful;
6. continue another unblocked packet;
7. create or update a ticket.

If no safe fallback remains, write:

```text
blocker
evidence
attempted fallbacks
files affected
commands run
next exact resume step
```

Update:

```text
AI Workflow/state/ACTIVE_CURSOR.md
AI Workflow/state/HANDOFFS.md
AI Workflow/state/RUN_LEDGER.md
AI Workflow/state/CHECK_FLAGS.md
```

Then stop.

---

## Session anti-patterns

- Do not keep a session alive because it “might remember something”.
- Do not allow one session to rewrite decisions made by another without updating the board and audit trail.
- Do not let multiple tools edit the same files at the same time.
- Do not use expensive models because the current session became messy.
- Do not rely on stale Graphify output after major moves.
- Do not rely on stale project-map assumptions.
- Do not rely on stale active-cursor assumptions.
- Do not turn unreliable local Sonar into a false blocker.
- Do not start broad refactoring before repository reality and project-map state are updated.
- Do not stop without writing a handoff.
- Do not stop without updating `ACTIVE_CURSOR.md`.
- Do not ask the user what to do next during `Start_My_Agent`.

---

## Resume command format

Every handoff must end with:

```text
Resume command:
Start_My_Agent

Next exact action:
<one executable command or one concrete inspection/edit action>
```

The next action must be specific enough for another agent to execute immediately.