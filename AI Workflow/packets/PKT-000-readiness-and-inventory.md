# PKT-000 — Readiness and Inventory

## Packet identity

| Field | Value |
|---|---|
| Packet ID | `PKT-000` |
| Title | Readiness and inventory |
| Owner/tool | VS Code Copilot + DeepSeek V4 Pro |
| Status | `READY` |
| Created | Initial workflow setup |
| Last updated | `TODO` |

---

## Purpose

Initialize the workflow from the real repository state before any broad refactoring starts.

PKT-000 is not allowed to change production code.

PKT-000 must only:

1. verify repository state;
2. verify tool availability;
3. install approved missing optional tools only: Vulture, Refurb, Semgrep;
4. record tool status;
5. record Git status;
6. update workflow state files;
7. update `PROJECT_MAP.md`;
8. update the workboard;
9. identify stale workflow rules;
10. create or update the next packet from real findings.

PKT-000 must not edit:

```text
src/datp/**
tests/**
paper/**
results/**
data/**
artifacts/**
outputs/**
docs/journal/**
Journal/**
Blueprint.md
CLAUDE.md
```

The only non-workflow files PKT-000 may edit are:

```text
pyproject.toml
uv.lock
docs/tickets/ticket_inventory.md
docs/tickets/ticket_progress.md
docs/tickets/human_interventions.md
```

`pyproject.toml` and `uv.lock` may be edited only if installing Vulture, Refurb, or Semgrep.

---

## Scope

### In scope

- verify repository root;
- verify current git status;
- record existing uncommitted changes;
- verify required tool availability and versions;
- check Vulture availability;
- check Refurb availability;
- check Semgrep availability;
- install Vulture, Refurb, and Semgrep only if missing;
- verify installed approved optional tools;
- inspect active project docs enough to confirm scientific anchors;
- inspect workflow files for stale or contradictory rules;
- inspect project tree enough to update `PROJECT_MAP.md`;
- initialize/update workboard, audit, map, pattern ledger, move plan, scientific audit, and test impact map;
- create or select next packet from real findings.

### Out of scope

- production code refactoring;
- package restructuring;
- source-code deletion;
- test rewriting;
- paper editing;
- result regeneration;
- dataset modification;
- artifact modification;
- training runs;
- full pytest;
- full E2E tests;
- Ray jobs;
- Flower jobs;
- experiment sweeps;
- expensive model escalation;
- Sonar setup;
- Sonar blocking.

---

## File locks

| File/directory | Reason | Lock owner | Status |
|---|---|---|---|
| `AI Workflow/**` | Initial workflow setup, readiness records, state files, project map, workboard, audit files. | DeepSeek V4 Pro | `PENDING` |
| `.claude/agents/**` | Only if workflow contradictions must be corrected. | DeepSeek V4 Pro | `PENDING` |
| `.claude/skills/**` | Only if workflow contradictions must be corrected. | DeepSeek V4 Pro | `PENDING` |
| `.claude/settings.json` | Only if permissions must allow approved tools. | DeepSeek V4 Pro | `PENDING` |
| `pyproject.toml` | Only if Vulture, Refurb, or Semgrep are missing. | DeepSeek V4 Pro | `CONDITIONAL` |
| `uv.lock` | Only if Vulture, Refurb, or Semgrep are missing. | DeepSeek V4 Pro | `CONDITIONAL` |
| `docs/tickets/ticket_inventory.md` | Only if readiness findings require ticket updates. | DeepSeek V4 Pro | `CONDITIONAL` |
| `docs/tickets/ticket_progress.md` | Only if readiness findings require ticket progress updates. | DeepSeek V4 Pro | `CONDITIONAL` |
| `docs/tickets/human_interventions.md` | Only if readiness findings reveal human action is required. | DeepSeek V4 Pro | `CONDITIONAL` |

Do not lock or edit production code during PKT-000.

---

## Required commands

Run before any edit:

```bash
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

If Vulture, Refurb, or Semgrep are missing:

```bash
uv add --dev vulture refurb semgrep
uv run vulture --version
uv run refurb --version
uv run semgrep --version
```

Optional inspection only:

```bash
python -m ruff check src/datp tests
python -m pyright
```

Do not run:

```bash
python -m pytest
python -m pytest tests/e2e
make quality-audit-local
make sonar-up
make sonar-health
graphify .
```

unless PKT-000 explicitly records why the command is safe and necessary.

---

## Required file updates

PKT-000 must update:

```text
AI Workflow/state/TOOL_STATUS.md
AI Workflow/state/RUN_LEDGER.md
AI Workflow/state/CHECK_FLAGS.md
AI Workflow/state/PROJECT_MAP.md
AI Workflow/state/GRAPHIFY_STATUS.md
AI Workflow/REFACTOR_WORKBOARD.md
AI Workflow/AUDIT_CODE.md
AI Workflow/TEST_IMPACT_MAP.md
```

PKT-000 may update these only if real findings require it:

```text
AI Workflow/REFACTOR_MAP.md
AI Workflow/PATTERN_LEDGER.md
AI Workflow/MOVE_PLAN.md
AI Workflow/SCIENTIFIC_CONTRACT_AUDIT.md
AI Workflow/state/AGENT_MEMORY.md
AI Workflow/state/HANDOFFS.md
docs/tickets/ticket_inventory.md
docs/tickets/ticket_progress.md
docs/tickets/human_interventions.md
```

PKT-000 may update these only if optional approved tools are installed:

```text
pyproject.toml
uv.lock
```

---

## Required records

### Tool status

Record in `AI Workflow/state/TOOL_STATUS.md`:

```text
Python version
pytest version
Ruff version
Pyright version
CodeScene availability
Graphify availability
Vulture availability
Refurb availability
Semgrep availability
Codex availability if checked
Claude availability if checked
Antigravity availability if checked
Copilot CLI availability if checked
Sonar status as optional/unreliable-local
tools installed during PKT-000
tools unavailable
environment limitations
```

### Run ledger

Record in `AI Workflow/state/RUN_LEDGER.md`:

```text
date/time if available
packet ID
commands run
command outputs or summaries
files changed
install actions
checks skipped
reason for skipped checks
current git status
next action
```

### Check flags

Record in `AI Workflow/state/CHECK_FLAGS.md`:

```text
tool availability flags
installed-tool flags
git-status flag
project-map freshness flag
Graphify freshness flag
Sonar optional-status flag
invalidation rules
```

### Project map

Record in `AI Workflow/state/PROJECT_MAP.md`:

```text
current top-level structure
current production package map
current test map
workflow-control-plane map
known ownership conflicts
stale assumptions
tooling status summary
next architecture questions
PKT-001 focus
```

Do not pretend the project map is complete after PKT-000.

Mark incomplete areas as `TO_AUDIT`.

### Graphify status

Record in `AI Workflow/state/GRAPHIFY_STATUS.md`:

```text
whether graphify exists
version if available
whether graphify was run
if not run, why not
when it should run next
```

During PKT-000, Graphify may be checked but should not be run unless explicitly justified.

---

## Approved optional tools

PKT-000 may install only these:

```text
vulture
refurb
semgrep
```

Preferred install command:

```bash
uv add --dev vulture refurb semgrep
```

After install, verify:

```bash
uv run vulture --version
uv run refurb --version
uv run semgrep --version
```

Do not install:

```text
Repomix
Git worktrees
CodeQL
deptry
```

Do not add configuration for excluded tools.

---

## Sonar rule

Local Sonar has been unreliable.

During PKT-000:

- do not run Sonar as a blocker;
- do not start SonarQube;
- do not run `make quality-audit-local`;
- do not claim Sonar passed;
- record Sonar as optional final-only tooling.

Allowed PKT-000 Sonar record:

```text
Sonar is present in repository files but is not part of the default first-pass gate because local Sonar has been unreliable. It remains optional final-only if healthy.
```

---

## Git safety

Before editing, run:

```bash
git status --short
```

If uncommitted changes exist:

1. record them in `RUN_LEDGER.md`;
2. record them in `HANDOFFS.md` if ending the session;
3. avoid overwriting unknown user changes;
4. do not run destructive Git commands.

Forbidden unless Salaheddine explicitly requests:

```bash
git reset
git clean
git checkout -- .
git restore .
git push
git commit
```

No automatic commits.

No automatic pushes.

---

## First-run inspection checklist

PKT-000 must inspect enough to answer:

| Question | Required outcome |
|---|---|
| Is the repo root correct? | Record `pwd`. |
| Is the working tree clean or dirty? | Record `git status --short`. |
| Are required tools callable? | Record versions or unavailable status. |
| Are Vulture, Refurb, and Semgrep available? | Check, install if missing, verify, flag. |
| Is Sonar still optional? | Record optional/unreliable-local status. |
| Is CodeScene available? | Record status. |
| Is Graphify available? | Record status and whether run is deferred. |
| Do workflow files contradict the approved tool list? | Record findings. |
| Do agent/skill files still require Sonar as mandatory? | Record and fix only workflow/agent/skill contradictions. |
| Does `PROJECT_MAP.md` exist and reflect current tree? | Update from current visible repository reality. |
| What is the next real packet? | Update `REFACTOR_WORKBOARD.md`. |

---

## First-run forbidden edits

Do not edit:

```text
src/datp/**
tests/**
paper/**
results/**
data/**
artifacts/**
outputs/**
docs/journal/**
Journal/**
Blueprint.md
CLAUDE.md
README.md
Makefile
sonar-project.properties
docker-compose.sonarqube.yml
scripts/**
```

Do not move files.

Do not delete files.

Do not refactor code.

Do not rewrite tests.

Do not weaken tests.

Do not modify result artifacts.

Do not modify paper artifacts.

---

## Acceptance criteria

- [ ] Repository root confirmed.
- [ ] Git status recorded.
- [ ] Existing uncommitted changes recorded.
- [ ] Tool versions recorded.
- [ ] Vulture checked.
- [ ] Refurb checked.
- [ ] Semgrep checked.
- [ ] Missing approved optional tools installed if needed.
- [ ] Installed tools verified after installation.
- [ ] `TOOL_STATUS.md` updated.
- [ ] `RUN_LEDGER.md` updated.
- [ ] `CHECK_FLAGS.md` updated.
- [ ] `PROJECT_MAP.md` updated from current repository reality.
- [ ] `GRAPHIFY_STATUS.md` updated.
- [ ] `REFACTOR_WORKBOARD.md` updated.
- [ ] `AUDIT_CODE.md` updated with real initial findings or explicit no-finding-yet entries.
- [ ] `TEST_IMPACT_MAP.md` updated.
- [ ] Sonar recorded as optional/unreliable-local, not default blocker.
- [ ] No production code changed.
- [ ] No tests changed.
- [ ] No paper/results/data/artifact files changed.
- [ ] Next packet selected or created.
- [ ] Session handoff written.
- [ ] PKT-000 marked `REAUDIT_REQUIRED`, not `DONE`, until PKT-001 validates the project map.

---

## Completion status rule

PKT-000 must not be marked `DONE` immediately after the first run.

Use:

```text
REAUDIT_REQUIRED
```

because PKT-001 must validate whether the project map and ownership inventory are correct.

PKT-000 can become `DONE` only after PKT-001 confirms:

```text
tool assumptions are still valid
project map is accurate enough for refactoring
workflow contradictions are resolved
next packets are grounded in real repository structure
```

---

## Re-audit trigger

Re-audit PKT-000 after PKT-001 completes because the repository map may change readiness assumptions.

Also re-audit PKT-000 if:

```text
pyproject.toml changes
uv.lock changes
workflow files change
agent/skill files change
tool availability changes
Graphify is installed or run
Sonar policy changes
approved optional tool list changes
```

---

## Handoff requirements

Before stopping, write a handoff entry in:

```text
AI Workflow/state/HANDOFFS.md
```

Include:

```text
packet ID
current status
git status
commands run
tools checked
tools installed
files changed
checks skipped and why
Sonar status
Graphify status
Vulture status
Refurb status
Semgrep status
project-map status
next packet
next exact action
```