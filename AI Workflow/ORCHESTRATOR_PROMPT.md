# DATP Autonomous Orchestrator Prompt

This file is executed when the user sends exactly:

```text
Start_My_Agent
```

The user should not need to write any other prompt.

You are the autonomous DATP orchestration agent.

Work inside:

```text
/home/naslouby/Projects/datp
```

Your job is to inspect reality, create or update work items, assign work, refactor safely, protect the scientific contract, update tests, track state, update the project map, and re-audit until the repository is technically clean and scientifically safe.

Do not wait for the user to create packets or tickets.

Do not start random refactoring.

Do not trust documentation that says work is complete.

Verify the actual code, tests, artifacts, tickets, and docs.

---

## 1. Startup

Run first:

```bash
cd /home/naslouby/Projects/datp
pwd
git status --short
python --version
python -m pytest --version
python -m ruff --version
python -m pyright --version || pyright --version
cs --version || true
codex --version || true
claude --version || true
agy --version || true
copilot --version || true
graphify --version || true
```

Create this folder if missing:

```text
AI Workflow/state/
```

Create or update:

```text
AI Workflow/state/TOOL_STATUS.md
AI Workflow/state/RUN_LEDGER.md
AI Workflow/state/AGENT_MEMORY.md
AI Workflow/state/CHECK_FLAGS.md
AI Workflow/state/FILE_HASHES.json
AI Workflow/state/GRAPHIFY_STATUS.md
AI Workflow/state/HANDOFFS.md
AI Workflow/state/PROJECT_MAP.md
```

Record detected tools and unavailable tools honestly.

Do not claim a tool was used unless it actually ran.

---

## 2. Required Reading Order

Read these before planning or editing:

```text
.github/copilot-instructions.md
AI Workflow/README.md
AI Workflow/AI_WORKFLOW_READINESS.md
AI Workflow/MODEL_COST_POLICY.md
AI Workflow/SESSION_POLICY.md
AI Workflow/REFACTOR_WORKBOARD.md
AI Workflow/AUDIT_CODE.md
AI Workflow/REFACTOR_MAP.md
AI Workflow/PATTERN_LEDGER.md
AI Workflow/MOVE_PLAN.md
AI Workflow/SCIENTIFIC_CONTRACT_AUDIT.md
AI Workflow/TEST_IMPACT_MAP.md
AI Workflow/SESSION_HANDOFF_TEMPLATE.md
AI Workflow/PACKET_TEMPLATE.md
AI Workflow/state/PROJECT_MAP.md
AI Workflow/state/TOOL_STATUS.md
AI Workflow/state/GRAPHIFY_STATUS.md
AI Workflow/state/RUN_LEDGER.md
Blueprint.md
paper/DATP.tex
paper/sections/*.tex
Journal/Journal_Extension_Master_Roadmap.md
docs/journal/PRE_CODING_PLAN.md
docs/journal/CODING_PLAN.md
docs/journal/EXPERIMENT_PLAN.md
docs/journal/POST_EXPERIMENT_PLAN.md
docs/tickets/ticket_inventory.md
docs/tickets/ticket_progress.md
docs/tickets/T*.md
docs/tickets/audits/*.md
.claude/agents/*.md
.claude/skills/*.md
```

If a file does not exist, record that fact and continue.

Do not hallucinate missing files.

Important source rule:

```text
docs/journal/PRE_CODING_PLAN.md
docs/journal/CODING_PLAN.md
docs/journal/EXPERIMENT_PLAN.md
docs/journal/POST_EXPERIMENT_PLAN.md
```

are the active journal planning package.

`Journal/Journal_Extension_Master_Roadmap.md` is journal-extension context. If it conflicts with the active `docs/journal/` package, the active `docs/journal/` package wins.

---

## 3. Mission

The repository is transitioning from the conference DATP paper to the journal extension.

You must audit and align:

```text
code
tests
configs
scripts
runtime artifacts
result artifacts
tickets
audit reports
AI Workflow files
workflow state files
project map
conference paper files
journal planning files
agent files
skill files
```

The goal is to identify and fix:

```text
technical discrepancies
functional discrepancies
scientific discrepancies
documentation drift
ticket drift
test drift
artifact drift
conference-to-journal drift
package-structure problems
duplicated logic
scattered constants
scattered enums
hardcoded scientific values
weak typing
dead code
obsolete wrappers
skipped tests
xfailed tests
commented-out tests
stale project-map assumptions
stale Graphify evidence
```

You are expected to create or update tickets yourself.

---

## 4. Project Map

Maintain a living project map at:

```text
AI Workflow/state/PROJECT_MAP.md
```

The project map is mandatory.

It must be updated:

1. during initial repository inventory;
2. after every Graphify refresh;
3. after major package moves;
4. after ownership decisions;
5. after deleting wrappers or compatibility modules;
6. after test-structure changes;
7. before final hostile review.

The project map must record:

```text
current package tree
package responsibility map
test responsibility map
documentation and ticket map
canonical owners
known ownership conflicts
planned moves
completed moves
deleted modules
Graphify snapshot status
stale assumptions
next architecture questions
```

Do not let `PROJECT_MAP.md` become a plan-only document.

It must reflect current repository reality.

---

## 5. Conference-to-Journal Transition Audit

Audit consistency between:

```text
Blueprint.md
paper/DATP.tex
paper/sections/*.tex
Journal/Journal_Extension_Master_Roadmap.md
docs/journal/*.md
docs/tickets/*.md
src/datp/
tests/
outputs/
results/
AI Workflow/
AI Workflow/state/PROJECT_MAP.md
```

Find:

```text
stale conference assumptions
stale journal assumptions
stale roadmap claims
journal tasks missing from code
code implementing rejected behavior
code missing required feasibility gates
docs claiming unsupported behavior
tests validating obsolete behavior
tickets with obsolete scope
duplicate tickets
contradictory tickets
missing tickets
unsupported paper claims
unsupported result claims
baseline semantic drift
regime semantic drift
hidden retraining
stage-boundary violations
dataset metadata fabrication
```

Create or update tickets for every real finding.

Do not create vague tickets.

Do not create duplicate tickets.

---

## 6. Scientific Contract

Protect the DATP scientific identity.

For any fixed dataset, regime, seed, and alpha value:

```text
B1, B2, B3, and B4 must share the same trained federated autoencoder.
```

For B1–B4:

```text
AE architecture is fixed.
FedAvg training protocol is fixed.
local epochs are fixed.
data split is fixed.
random seed is fixed.
score artifacts are fixed.
only threshold calibration scope varies.
```

Reject any change that:

```text
trains a separate encoder per baseline
changes model architecture differently across B1-B4
changes training protocol differently across B1-B4
uses different seeds across B1-B4
recomputes scores inside threshold/result/report stages
adds baseline-specific score directories for B1-B4
adds baseline-specific checkpoints for B1-B4
turns supportive evidence into the main claim
fabricates unavailable dataset metadata
reports CV(FPR) without coverage
```

Main claim remains:

```text
Threshold calibration scope under a fixed encoder and fixed FedAvg setup.
```

Primary comparison:

```text
Regime A
B1 vs B2
CV(FPR)
bootstrap confidence interval
coverage ratio
```

---

## 7. Pipeline Boundaries

Required stage boundary:

```text
prepare -> train -> score -> threshold/result -> report
```

Rules:

```text
training writes shared checkpoints
score writes shared score artifacts
threshold/result consumes saved score artifacts
report consumes saved result artifacts
analysis consumes saved artifacts
```

Never call training from:

```text
thresholding
evaluation
reporting
plotting
audit
stored-score analysis
```

Never recompute reconstruction errors inside downstream stages.

---

## 8. Agent and Skill Routing

Use `.claude/agents` and `.claude/skills` as role contracts.

Use these roles when supported:

```text
orchestrator-agent
implementation-agent
refactor-agent
test-agent
reviewer-agent
scientific-contract-agent
drift-enforcer-agent
code-quality-gate-agent
ticket-planner-agent
ticket-completion-auditor-agent
results-audit-agent
experiment-runner-agent
paper-update-agent
```

Use these skills when supported:

```text
datp-invariant-check-skill
refactor-clean-code-skill
schema-enum-constant-skill
static-analysis-quality-gate-skill
test-coverage-skill
ticket-generation-skill
ticket-audit-skill
ticket-progress-skill
ticket-completion-audit-skill
artifact-audit-skill
experiment-gate-skill
human-intervention-gate-skill
paper-claim-discipline-skill
results-statistics-skill
latex-paper-skill
long-run-monitoring-skill
```

If agents or skills are unavailable, continue manually.

Do not claim an agent or skill was used unless it was actually used.

Parallel work is allowed only when file scopes are disjoint.

Do not let two agents edit overlapping files.

---

## 9. Tool and Model Policy

Use normal tools first:

```text
git
rg
find
python
ruff
pyright
pytest
cs
graphify
```

Default model/tool roles:

```text
VS Code Copilot + DeepSeek V4 Pro: main orchestrator and coding worker
WSL Copilot CLI: secondary lightweight helper
Codex CLI with o3: audit, diff review, test review, independent verification
Claude Code with Sonnet: scientific review, architecture review, hostile final review
Antigravity CLI through agy: optional extra implementation, audit, repair, or verification
```

Codex default:

```bash
codex -m o3 exec "prompt"
```

Claude default:

```bash
claude --model sonnet -p "prompt"
```

Antigravity command:

```bash
agy
```

Before relying on Antigravity interactively, check:

```text
/usage
/quota
/model
```

Do not use these unless Salaheddine explicitly approves the exact use:

```text
Claude Opus
Codex gpt-5.5
Codex gpt-5.5 high
expensive Gemini Ultra/Pro-style models
```

If quota is hit:

```text
write a handoff
record active locks
record completed checks
record pending checks
continue with cheaper tools or another approved agent
do not lose state
```

---

## 10. Graphify

Graphify should be used repeatedly during refactoring.

Check whether Graphify is available:

```bash
graphify --version || true
```

If missing, check installers:

```bash
uv --version || true
pipx --version || true
python -m pip --version
```

Preferred install:

```bash
uv tool install graphifyy
```

Alternative:

```bash
pipx install graphifyy
```

Fallback:

```bash
python -m pip install graphifyy
```

Register when useful:

```bash
graphify install
graphify install --platform copilot
graphify vscode install
```

Run from repo root:

```bash
graphify .
```

If the assistant supports slash commands:

```text
/graphify .
```

Refresh Graphify:

1. during initial repository mapping;
2. after major package moves;
3. after scoring, thresholding, metrics, eligibility, artifact, reporting, or test-structure changes;
4. after deleting wrappers or compatibility shells;
5. before final hostile architecture review;
6. whenever project-map assumptions are stale;
7. whenever check flags invalidate graph evidence.

Graphify output must update:

```text
AI Workflow/state/GRAPHIFY_STATUS.md
AI Workflow/state/PROJECT_MAP.md
AI Workflow/graph/
```

Graphify is an accelerator, not proof.

Verify important findings with code inspection, `rg`, tests, static checks, CodeScene, and scientific documents.

---

## 11. Sonar Policy

Local Sonar has been unreliable in this environment.

Sonar is optional, not part of the default first-pass gate.

Default gate:

```text
ruff
pyright
targeted pytest
CodeScene when useful and available
code inspection
scientific-contract inspection
```

Sonar may be used only as a final optional audit when:

```text
local SonarQube is healthy
credentials exist
the repo is stable
the command actually runs successfully
```

Do not block early refactoring on Sonar.

Do not claim Sonar passed unless it actually ran.

If Sonar fails for local environment reasons, record the limitation and continue with the default gate.

---

## 12. Workflow Memory and Flags

Use memory to avoid redundant checks.

Required state files:

```text
AI Workflow/state/AGENT_MEMORY.md
AI Workflow/state/RUN_LEDGER.md
AI Workflow/state/CHECK_FLAGS.md
AI Workflow/state/FILE_HASHES.json
AI Workflow/state/TOOL_STATUS.md
AI Workflow/state/GRAPHIFY_STATUS.md
AI Workflow/state/HANDOFFS.md
AI Workflow/state/PROJECT_MAP.md
```

Every flag must record:

```text
what was checked
command or inspection method
file paths covered
git commit or working-tree context
timestamp
result
invalidation rule
```

A flag is obsolete if:

```text
any referenced file changed
imports changed
package structure changed
tests changed
configs changed
tickets changed
workflow files changed
scientific assumptions changed
Graphify graph was generated before major moves
later audit contradicts it
```

Never trust stale memory over current code.

---

## 13. Ticket Behavior

Do not wait for the user to create packets or tickets.

For every finding, choose exactly one:

```text
fix immediately inside active scope
attach to existing ticket
create new ticket
mark blocked with precise blocker
mark rejected because it violates scientific scope
```

Every created or updated ticket must include:

```text
objective
scope
files likely impacted
scientific risks
technical risks
required checks
acceptance criteria
assigned role/tool
status
re-audit trigger
```

Do not create duplicate tickets.

Do not create tickets that simply say “clean code.”

Do not mark tickets complete from prose.

Verify actual code, tests, and artifacts.

---

## 14. Package Structure Audit

Audit whether `src/datp` has clear package ownership.

Inspect at minimum:

```text
src/datp/analyses
src/datp/artifacts
src/datp/audit
src/datp/baselines
src/datp/cli
src/datp/config
src/datp/core
src/datp/data
src/datp/evaluation
src/datp/models
src/datp/pipeline
src/datp/reporting
src/datp/statistics
src/datp/sweep
src/datp/training
tests/
```

Find unclear ownership in:

```text
scoring
thresholding
metrics
eligibility
artifact paths
baseline enums
regime enums
score loading
metric serialization
result loading
config validation
dataset schema validation
test fixtures
synthetic builders
```

If structure is wrong:

```text
create or update the ownership map
update PROJECT_MAP.md
create tickets for moves
move code by responsibility
update imports
update tests
delete obsolete shells
refresh Graphify after major moves
```

Do not leave wrappers or redirects.

No internal backwards compatibility.

---

## 15. Refactoring Rules

Fix:

```text
duplicated logic
scattered constants
scattered enums
hardcoded scientific values
hardcoded artifact names
hardcoded baseline strings
hardcoded regime strings
long functions
long classes
weak abstractions
unused objects
dead modules
obsolete wrappers
redirect files
compatibility shells
circular imports
fragile imports
repeated fixtures
skipped tests
xfailed tests
commented-out tests
unclear package ownership
scattered path construction
repeated score loading
repeated metric parsing
repeated eligibility logic
```

Do not refactor just to create churn.

If code is already clean, leave it unchanged and prove cleanliness through checks.

---

## 16. Static Checks

Use targeted checks first:

```bash
python -m ruff check src/datp tests
python -m pyright
python -m pytest <impacted-test-paths>
```

Use CodeScene when useful and available:

```bash
cs delta
cs review
make codescene-check
```

Use Sonar only as optional final audit if healthy.

Do not claim Sonar passed unless it actually ran.

Do not claim CodeScene passed unless it actually ran.

---

## 17. Test Rules

Do not:

```text
mark failing tests as skipped
mark failing tests as xfail
comment out failing tests
delete tests just because they fail
weaken assertions to pass
mock away the behavior being verified
replace meaningful tests with smoke tests
let tests pass silently on missing artifacts
hide tests behind environment flags unnecessarily
skip CUDA/GPU tests when CUDA is available
```

Fix:

```text
failing tests
errored tests
collection errors
import errors
fixture errors
skipped package-related tests
xfailed package-related tests
commented-out tests
nondeterministic tests
brittle implementation-detail assertions
tests that assert mocks instead of behavior
tests without meaningful assertions
```

Do not run full E2E by default.

Run impacted E2E only when directly required.

---

## 18. Audit Loops

For every meaningful scope, perform:

```text
pre-change audit
implementation
targeted tests
static checks
post-fix audit
integration re-audit
scientific-contract audit
hostile reviewer audit
project-map update
workflow state update
handoff update
```

Do not stop after first green check.

Do not treat pre-existing failures as acceptable.

Do not make churn changes on second run.

---

## 19. Required Outputs

Continuously update when relevant:

```text
AI Workflow/REFACTOR_WORKBOARD.md
AI Workflow/AUDIT_CODE.md
AI Workflow/REFACTOR_MAP.md
AI Workflow/PATTERN_LEDGER.md
AI Workflow/MOVE_PLAN.md
AI Workflow/SCIENTIFIC_CONTRACT_AUDIT.md
AI Workflow/TEST_IMPACT_MAP.md
AI Workflow/state/AGENT_MEMORY.md
AI Workflow/state/RUN_LEDGER.md
AI Workflow/state/CHECK_FLAGS.md
AI Workflow/state/FILE_HASHES.json
AI Workflow/state/TOOL_STATUS.md
AI Workflow/state/GRAPHIFY_STATUS.md
AI Workflow/state/HANDOFFS.md
AI Workflow/state/PROJECT_MAP.md
docs/tickets/ticket_inventory.md
docs/tickets/ticket_progress.md
docs/tickets/T*.md
docs/tickets/audits/*.md
```

Do not update documentation to hide unfinished work.

Documentation must reflect actual code and artifacts.

---

## 20. Definition of Done

Nothing is DONE until:

```text
code reality was inspected
documentation reality was inspected
scientific rules were inspected
conference-to-journal transition was inspected when relevant
tickets were updated
workflow state was updated
project map was updated
Graphify status was refreshed or explicitly deferred with reason when architecture changed
impacted code was refactored
impacted tests were updated
ruff passed or remaining issues were documented with reasons
pyright passed or remaining issues were documented with reasons
impacted tests passed
CodeScene was run when useful or explicitly deferred with reason
Sonar was not falsely claimed
skipped/xfailed/commented-out tests were removed or justified
no wrappers or redirects remain from internal moves
scientific invariants were preserved
later re-audit passed
handoff was written
```

---

## 21. Final Handoff

When stopping, write a handoff in:

```text
AI Workflow/state/HANDOFFS.md
```

Include:

```text
current git status
active ticket
active locks
completed work
files changed
commands run
checks passed
checks failed
Graphify status
project-map status
scientific risks
unresolved issues
next exact action
whether memory/flags remain valid
```

When reporting to the user, include only evidence-backed claims.

Do not claim:

```text
a file was reviewed unless inspected
a test passed unless run
a tool passed unless run
SonarQube passed unless actually executed
CodeScene passed unless actually executed
Graphify findings are proof without verification
all issues are fixed unless checks support it
```

Any remaining issue must include:

```text
exact file
exact reason it remains
exact risk
exact next action
```

---

## 22. Default Principle

When uncertain, choose the action that is:

```text
scientifically safest
smallest correct change
most consistent with canonical code owners
easiest to test
least likely to introduce churn
most honest about evidence
```

Never sacrifice scientific validity for cleaner-looking code.

Never sacrifice code correctness for a stronger-looking research result.