# Quick Start Commands

This file is the minimal human-facing entry point for the DATP AI workflow.

The normal user command is only:

```text
Start_My_Agent
```

Legacy alias accepted for compatibility only:

```text
StartMyAgent
```

Prefer the canonical command:

```text
Start_My_Agent
```

Do not manually paste the full orchestrator prompt unless Copilot fails to follow the launcher contract.

---

## 1. Enter repository

Run from WSL:

```bash
cd /home/naslouby/Projects/datp
pwd
git status --short
```

Expected repository:

```text
/home/naslouby/Projects/datp
```

---

## 2. Start the autonomous workflow

In VS Code Copilot Chat, switch to **Agent Mode**.

Then type exactly:

```text
Start_My_Agent
```

That single keyword must trigger the workflow.

Expected behavior:

1. Copilot reads `.github/copilot-instructions.md`.
2. Copilot executes `AI Workflow/ORCHESTRATOR_PROMPT.md`.
3. The orchestrator reads workflow state first.
4. The orchestrator reads `AI Workflow/state/ACTIVE_CURSOR.md`.
5. The orchestrator reads `AI Workflow/state/HANDOFFS.md`.
6. The orchestrator resumes from the last recorded point.
7. The orchestrator checks the real repository.
8. The orchestrator checks whether required tools exist.
9. The orchestrator installs missing approved optional tools only when allowed.
10. The orchestrator flags installed/available tools in workflow state.
11. The orchestrator reads `AI Workflow/CLEAN_CODE_RULES.md`.
12. The orchestrator reads scientific anchors.
13. The orchestrator updates workflow state.
14. The orchestrator updates the project map.
15. The orchestrator creates or updates tickets.
16. The orchestrator assigns work to the correct agent/tool role when supported.
17. The orchestrator performs audit, implementation, testing, review, and re-audit loops.
18. The orchestrator updates `AI Workflow/state/ACTIVE_CURSOR.md` before any stop.
19. The orchestrator writes a handoff before any stop.

Do not paste `ORCHESTRATOR_PROMPT.md` manually during normal use.

---

## 3. Required workflow files

Before launching, these files should exist:

```text
.github/copilot-instructions.md
AI Workflow/AI_WORKFLOW_READINESS.md
AI Workflow/CLEAN_CODE_RULES.md
AI Workflow/ORCHESTRATOR_PROMPT.md
AI Workflow/MODEL_COST_POLICY.md
AI Workflow/SESSION_POLICY.md
AI Workflow/README.md
AI Workflow/REFACTOR_WORKBOARD.md
AI Workflow/REFACTOR_MAP.md
AI Workflow/PATTERN_LEDGER.md
AI Workflow/MOVE_PLAN.md
AI Workflow/SCIENTIFIC_CONTRACT_AUDIT.md
AI Workflow/SCIENTIFIC_DRIFT_LOCK.md
AI Workflow/TEST_IMPACT_MAP.md
AI Workflow/PACKET_TEMPLATE.md
AI Workflow/SESSION_HANDOFF_TEMPLATE.md
AI Workflow/QUICK_START_COMMANDS.md
AI Workflow/state/ACTIVE_CURSOR.md
AI Workflow/state/PROJECT_MAP.md
AI Workflow/state/HANDOFFS.md
AI Workflow/state/RUN_LEDGER.md
AI Workflow/state/AGENT_MEMORY.md
AI Workflow/state/CHECK_FLAGS.md
AI Workflow/state/TOOL_STATUS.md
AI Workflow/state/GRAPHIFY_STATUS.md
AI Workflow/state/FILE_HASHES.json
```

`AI_WORKFLOW_READINESS.md` is intentionally kept.

It owns environment, tool, resource, Sonar, CodeScene, Graphify, Vulture, Refurb, and Semgrep readiness assumptions.

`CLEAN_CODE_RULES.md` is intentionally separate.

It owns the recurring clean-code and refactor rules for enums, constants, dataclasses, utility ownership, package ownership, no backwards compatibility, test movement, static tools, and re-audits.

`ACTIVE_CURSOR.md` is intentionally separate.

It owns resumability and tells the next session exactly where to continue.

---

## 4. Initialize workflow state files

Run this once if the state folder does not exist:

```bash
mkdir -p "AI Workflow/state"
touch "AI Workflow/state/ACTIVE_CURSOR.md"
touch "AI Workflow/state/TOOL_STATUS.md"
touch "AI Workflow/state/RUN_LEDGER.md"
touch "AI Workflow/state/AGENT_MEMORY.md"
touch "AI Workflow/state/CHECK_FLAGS.md"
touch "AI Workflow/state/GRAPHIFY_STATUS.md"
touch "AI Workflow/state/HANDOFFS.md"
touch "AI Workflow/state/PROJECT_MAP.md"
test -f "AI Workflow/state/FILE_HASHES.json" || printf '{}\n' > "AI Workflow/state/FILE_HASHES.json"
```

State files are allowed to start empty.

The agent must populate them with evidence after `Start_My_Agent`.

---

## 5. Initialize active cursor

Only run this if `AI Workflow/state/ACTIVE_CURSOR.md` is empty:

```bash
cat > "AI Workflow/state/ACTIVE_CURSOR.md" <<'EOF'
# Active Cursor

This file is the canonical resume point for `Start_My_Agent`.

## Current phase

`DISCOVERY`

## Active packet

`PKT-000-readiness-and-inventory`

## Active ticket

`NONE`

## Active goal

Initialize workflow state, verify repository and tool reality, inspect scientific anchors, then continue to the first safe active packet without human interaction.

## Last completed step

`NONE`

## Next exact step

Run startup verification commands from `AI Workflow/ORCHESTRATOR_PROMPT.md`, record results in workflow state, then continue with PKT-000.

## Blockers

- None recorded.

## Files currently in scope

- `.github/copilot-instructions.md`
- `AI Workflow/ORCHESTRATOR_PROMPT.md`
- `AI Workflow/AI_WORKFLOW_READINESS.md`
- `AI Workflow/CLEAN_CODE_RULES.md`
- `AI Workflow/SESSION_POLICY.md`
- `AI Workflow/state/ACTIVE_CURSOR.md`
- `AI Workflow/state/HANDOFFS.md`
- `AI Workflow/state/RUN_LEDGER.md`
- `AI Workflow/state/CHECK_FLAGS.md`
- `AI Workflow/state/TOOL_STATUS.md`

## File locks

| File/directory | Lock status | Reason | Next action |
|---|---|---|---|
| `NONE` | `NONE` | `NONE` | `NONE` |

## Commands already run

```text
NONE
```

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

## Checks already run

- None recorded.

## Checks still required

- Startup tool reality check.
- Repository status check.
- Scientific anchor existence check.
- Workflow state consistency check.

## Scientific checks still required

- Confirm `Blueprint.md` exists.
- Confirm `CLAUDE.md` exists.
- Confirm `docs/journal/PRE_CODING_PLAN.md` exists.
- Confirm `docs/journal/CODING_PLAN.md` exists.
- Confirm `docs/journal/EXPERIMENT_PLAN.md` exists.
- Confirm `docs/journal/POST_EXPERIMENT_PLAN.md` exists.
- Confirm archived roadmap does not override active journal package.
- Confirm no production changes happen before startup gates pass.

## Resume command

```text
Start_My_Agent
```
EOF
```

---

## 6. Safe default checks

These are the default safe checks for routine refactoring:

```bash
git status --short
python -m ruff check src/datp tests
python -m pyright
python -m pytest <impacted-test-paths>
```

Use targeted tests first.

Do not run the full test suite by default.

Do not run full E2E by default.

Do not run training or heavy experiments unless explicitly authorized.

---

## 7. Clean-code rulebook

The canonical clean-code file is:

```text
AI Workflow/CLEAN_CODE_RULES.md
```

Use it before and after refactors.

Minimum things it requires the agent to check:

```text
no wrappers
no redirects
no compatibility aliases
no old package shells
no old-path preservation tests
canonical enums for closed concepts
canonical constants for stable labels and artifact names
dataclasses or typed objects for structured values
no duplicate typed shapes
no vague utility dumping grounds
tests move with production code
no skipped/xfailed/commented-out tests hiding failures
static tools are signals, not proof
scientific behavior must not drift
```

---

## 8. Optional extra tools: check, install, flag

Approved optional extra tools:

```text
Vulture
Refurb
Semgrep
```

Not approved for this workflow unless explicitly approved later:

```text
Repomix
Git worktrees
CodeQL
deptry
```

Check first:

```bash
uv run vulture --version || vulture --version || true
uv run refurb --version || refurb --version || true
uv run semgrep --version || semgrep --version || true
```

If any approved tool is missing, install all approved extras:

```bash
uv add --dev vulture refurb semgrep
```

Verify after installation:

```bash
uv run vulture --version
uv run refurb --version
uv run semgrep --version
```

Then update:

```text
AI Workflow/state/TOOL_STATUS.md
AI Workflow/state/RUN_LEDGER.md
AI Workflow/state/CHECK_FLAGS.md
AI Workflow/state/ACTIVE_CURSOR.md
```

Flag them as available only after verification.

---

## 9. Optional extra tool commands

Use these when useful:

```bash
uv run vulture src/datp tests --min-confidence 80
uv run refurb src/datp tests
uv run semgrep scan --config auto src/datp tests
```

Rules:

- Vulture findings are suspects, not proof.
- Refurb suggestions are optional and must improve clarity.
- Semgrep findings must be triaged.
- These tools do not replace Ruff, Pyright, pytest, CodeScene, Graphify, clean-code rule audit, or scientific-contract checks.
- If these tools cause code changes, run impacted tests afterward.

---

## 10. CodeScene

CodeScene is useful when available:

```bash
cs delta
cs review
make codescene-check
```

Use CodeScene as an additional quality signal for complexity, hotspots, and code-health issues.

Do not claim CodeScene passed unless it actually ran.

---

## 11. Sonar policy

Local Sonar has been unreliable in this environment.

Therefore, Sonar is not part of the default workflow gate.

Default gate:

```text
ruff
pyright
targeted pytest
CodeScene when useful and available
Vulture when useful and available
Refurb when useful and available
Semgrep when useful and available
code inspection
clean-code rule audit
scientific-contract inspection
```

Sonar may be used only as an optional final audit when:

```text
local SonarQube is healthy
credentials are available
the repository is stable enough for a final pass
the command actually runs successfully
```

Allowed optional Sonar commands:

```bash
make sonar-up
make sonar-health
make quality-audit-local
make sonar-down
```

Rules:

- Do not block early refactoring on Sonar.
- Do not trust unreliable local Sonar output over Ruff, Pyright, pytest, CodeScene, Vulture, Refurb, Semgrep, clean-code rule audit, and code inspection.
- Do not claim Sonar passed unless it actually ran.
- If Sonar fails because of local environment instability, record it as an environmental limitation.
- Do not replace a failed Sonar run with “manual Sonar equivalent review.”

---

## 12. Graphify setup

Graphify is useful for this repository because the workflow needs repeated architecture, dependency, documentation, ticket, and paper-transition audits.

Package:

```text
graphifyy
```

CLI command:

```text
graphify
```

Recommended install:

```bash
uv tool install graphifyy
```

Alternatives:

```bash
pipx install graphifyy
python -m pip install graphifyy
```

Register for assistants when useful:

```bash
graphify install
graphify install --platform copilot
graphify vscode install
```

Run from repository root:

```bash
graphify .
```

If the assistant supports slash commands:

```text
/graphify .
```

Graphify should be used repeatedly during the refactor, not only once.

Run or refresh Graphify:

1. during initial repository mapping;
2. after major package moves;
3. after moving scoring, thresholding, metrics, eligibility, artifacts, or reporting logic;
4. after deleting wrappers or compatibility shells;
5. after large test-structure changes;
6. before the final hostile architecture review;
7. whenever `AI Workflow/state/PROJECT_MAP.md` is stale;
8. whenever `AI Workflow/state/CHECK_FLAGS.md` marks graph evidence invalid.

Record Graphify status in:

```text
AI Workflow/state/GRAPHIFY_STATUS.md
AI Workflow/state/PROJECT_MAP.md
AI Workflow/graph/
AI Workflow/state/ACTIVE_CURSOR.md
```

Graphify is an accelerator, not proof.

---

## 13. Project map

The workflow must maintain a living project map at:

```text
AI Workflow/state/PROJECT_MAP.md
```

The project map must be updated regularly.

Update it:

1. after initial repository inventory;
2. after every Graphify refresh;
3. after every major move;
4. after any package ownership decision;
5. after ticket creation changes the roadmap;
6. after scientific-contract audit changes package ownership;
7. after wrapper or compatibility-shell deletion;
8. after enum, constant, dataclass, schema, artifact, scoring, thresholding, or test ownership changes;
9. before final review.

The project map must include:

```text
current package tree
responsibility of each package
known ownership problems
planned moves
completed moves
deleted wrappers
canonical owners for scoring, thresholding, metrics, artifacts, eligibility, reporting, enums, constants, dataclasses, and tests
test structure map
documentation/ticket map
Graphify snapshot date or status
Vulture/Refurb/Semgrep status when used
invalidated assumptions
```

Do not let the project map become a stale wish list.

It must reflect the current repository reality.

---

## 14. Optional helper commands

Use helpers only when useful.

Copilot CLI:

```bash
copilot -p "quick check prompt"
```

Codex with approved default model:

```bash
codex -m o3 exec "audit or verification prompt"
```

Claude with approved default model:

```bash
claude --model sonnet -p "scientific or architecture review prompt"
```

Antigravity:

```bash
agy
```

Inside Antigravity interactive sessions, check:

```text
/usage
/quota
/model
```

---

## 15. Expensive models require explicit approval

Do not use these by default:

```bash
claude --model opus -p "prompt"
codex -m gpt-5.5 exec "prompt"
codex -m "gpt-5.5 high" exec "prompt"
```

Also do not use expensive Gemini Ultra/Pro-style Antigravity models unless explicitly approved.

If a model hits quota:

1. stop cleanly;
2. update `AI Workflow/state/HANDOFFS.md`;
3. update `AI Workflow/state/ACTIVE_CURSOR.md`;
4. update active file locks;
5. record completed checks;
6. continue with cheaper approved tools if possible.

---

## 16. Manual fallback if launcher fails

Only if `Start_My_Agent` fails, manually tell Copilot:

```text
Read .github/copilot-instructions.md, then execute AI Workflow/ORCHESTRATOR_PROMPT.md exactly. Treat this as the Start_My_Agent launcher. Do not summarize the prompt. Start from repository reality, update workflow state, read AI Workflow/CLEAN_CODE_RULES.md, and follow the DATP scientific contract.
```

If this fallback is needed, record it in:

```text
AI Workflow/state/RUN_LEDGER.md
AI Workflow/state/CHECK_FLAGS.md
AI Workflow/state/HANDOFFS.md
AI Workflow/state/ACTIVE_CURSOR.md
```

---

## 17. First expected output from the agent

After `Start_My_Agent`, the agent should update or create:

```text
AI Workflow/state/ACTIVE_CURSOR.md
AI Workflow/state/TOOL_STATUS.md
AI Workflow/state/RUN_LEDGER.md
AI Workflow/state/AGENT_MEMORY.md
AI Workflow/state/CHECK_FLAGS.md
AI Workflow/state/FILE_HASHES.json
AI Workflow/state/GRAPHIFY_STATUS.md
AI Workflow/state/HANDOFFS.md
AI Workflow/state/PROJECT_MAP.md
AI Workflow/REFACTOR_WORKBOARD.md
AI Workflow/AUDIT_CODE.md
AI Workflow/REFACTOR_MAP.md
AI Workflow/PATTERN_LEDGER.md
AI Workflow/MOVE_PLAN.md
AI Workflow/SCIENTIFIC_CONTRACT_AUDIT.md
AI Workflow/TEST_IMPACT_MAP.md
docs/tickets/ticket_inventory.md
docs/tickets/ticket_progress.md
```

It should not start broad refactoring before it records repository reality, tool reality, workflow state, the clean-code rule status, the active cursor, and the first project map.

---

## 18. Completion reminder

A packet or ticket is not complete because the agent says it is complete.

Completion requires evidence:

```text
real files inspected
real tests inspected
real commands run
real issues fixed or documented
clean-code rules checked
workflow state updated
active cursor updated
project map updated
scientific invariants checked
optional tool findings triaged when used
handoff written
later re-audit scheduled or completed
```

---

## 19. Resume reminder

To resume after stopping Copilot, open VS Code Copilot Chat in Agent Mode and type:

```text
Start_My_Agent
```

The agent must read:

```text
AI Workflow/state/ACTIVE_CURSOR.md
AI Workflow/state/HANDOFFS.md
AI Workflow/state/RUN_LEDGER.md
AI Workflow/REFACTOR_WORKBOARD.md
```

Then continue from the recorded next exact action.

Do not ask the user what to do next.