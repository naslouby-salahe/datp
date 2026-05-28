# GitHub Copilot Instructions

This repository implements DATP: Device-Aware Threshold Personalization for federated IoT malware/anomaly detection.

Correctness in this repository means both:

1. Software correctness.
2. Scientific correctness.

Never optimize one by breaking the other.

These instructions apply to all Copilot work in this repository, not only to the autonomous launcher.

Use them for:

```text
normal coding
debugging
reviewing
testing
refactoring
documentation updates
ticket work
scientific audits
workflow audits
autonomous Start_My_Agent execution
```

Do not treat this file as only a launcher file.

---

## 0. Launcher Contract

When the user sends exactly:

```text
Start_My_Agent
```

treat it as the repository launcher command.

The legacy alias below is accepted only to avoid accidental non-triggering from older notes:

```text
StartMyAgent
```

If the user sends `StartMyAgent`, normalize it internally to:

```text
Start_My_Agent
```

Do not ask what it means.

Do not summarize these instructions.

Do not start random refactoring.

Do not wait for the user to create packets or tickets.

Do not ask the user what to do next.

Do not pause for confirmation, approval, or clarification.

Do not stop after readiness if safe work remains.

Immediately start the DATP autonomous workflow from the repository root:

```bash
cd /home/naslouby/Projects/datp
```

Then inspect, audit, create/update tickets, assign work, refactor safely, update tests, re-audit, update workflow state, update the active cursor, and write a precise handoff before any stop.

The keyword `Start_My_Agent` means:

- audit the codebase;
- audit the tests;
- audit scientific rules;
- audit the conference-to-journal transition;
- audit existing tickets;
- audit workflow state;
- resume from the last recorded cursor and handoff;
- detect technical and scientific discrepancies;
- create or update tickets;
- use available agents and skills;
- use tools and models cost-consciously;
- refactor safely when the active scope authorizes fixing;
- update tests;
- track progress;
- update `AI Workflow/state/ACTIVE_CURSOR.md`;
- re-audit after changes;
- continue until the active goal is complete or a hard blocker is reached;
- stop only with a precise handoff.

---

### 0.1 Required Copilot mode

`Start_My_Agent` is intended for VS Code Copilot **Agent Mode**.

Agent Mode must be able to:

```text
read files
edit files
run terminal commands
inspect command output
chain multiple actions
update workflow state
```

If the current Copilot mode cannot do those things, record the limitation in:

```text
AI Workflow/state/HANDOFFS.md
AI Workflow/state/RUN_LEDGER.md
AI Workflow/state/CHECK_FLAGS.md
AI Workflow/state/ACTIVE_CURSOR.md
```

Then continue with any safe inspection or planning work available.

Do not pretend autonomous execution is possible if the current mode cannot execute it.

---

### 0.2 Resume-first rule

Every `Start_My_Agent` run may be a resumed session.

Before planning new work, read:

```text
AI Workflow/state/ACTIVE_CURSOR.md
AI Workflow/state/HANDOFFS.md
AI Workflow/state/RUN_LEDGER.md
AI Workflow/state/AGENT_MEMORY.md
AI Workflow/state/CHECK_FLAGS.md
AI Workflow/state/FILE_HASHES.json
AI Workflow/state/PROJECT_MAP.md
AI Workflow/state/TOOL_STATUS.md
AI Workflow/state/GRAPHIFY_STATUS.md
AI Workflow/REFACTOR_WORKBOARD.md
AI Workflow/AUDIT_CODE.md
AI Workflow/PATTERN_LEDGER.md
AI Workflow/MOVE_PLAN.md
AI Workflow/TEST_IMPACT_MAP.md
docs/tickets/ticket_inventory.md
docs/tickets/ticket_progress.md
docs/tickets/human_interventions.md
```

Then determine:

```text
last active packet
last active ticket
last active goal
last completed step
last failed step
last edited files
active file locks
stale assumptions
stale project-map entries
deferred checks
scientific checks still pending
quality checks still pending
next exact safe action
```

Do not restart from zero unless the state files are missing, corrupt, or contradicted by repository reality.

If written state contradicts the repository, repository reality wins.

Record the contradiction in:

```text
AI Workflow/state/CHECK_FLAGS.md
AI Workflow/state/RUN_LEDGER.md
AI Workflow/state/ACTIVE_CURSOR.md
```

Then continue.

---

### 0.3 No-human-interaction rule

During autonomous execution, never ask clarifying questions.

Never pause for:

```text
approval
confirmation
manual packet selection
manual ticket creation
manual file ownership decisions
manual test selection
manual project-map updates
manual handoff writing
```

When information is missing:

1. inspect the repository;
2. inspect workflow state;
3. inspect the active scientific anchors;
4. infer the safest bounded action;
5. record the assumption in `AI Workflow/state/CHECK_FLAGS.md`;
6. continue with the smallest safe next step.

Only stop for a hard blocker.

Hard blockers include:

```text
risk of overwriting unexplained user edits
destructive deletion risk
missing scientific anchors
scientific ambiguity that cannot be resolved from anchors, code, artifacts, plans, or tickets
credentials, login, account, or payment requirements
external service requiring manual interaction
terminal/tool failure with no safe fallback
heavy training or experiments without explicit authorization
actions that would violate the DATP scientific contract
```

When blocked, write:

```text
exact blocker
command or action that failed
evidence
fallbacks attempted
remaining safe work
next command to resume
```

Update:

```text
AI Workflow/state/HANDOFFS.md
AI Workflow/state/RUN_LEDGER.md
AI Workflow/state/ACTIVE_CURSOR.md
AI Workflow/state/CHECK_FLAGS.md
```

---

### 0.4 Mandatory active cursor

The active cursor file is:

```text
AI Workflow/state/ACTIVE_CURSOR.md
```

It is the canonical resume pointer.

Update it:

```text
after startup
after every meaningful batch
after any command failure
after any check failure
after any file edit group
before switching tools or models
before changing packets
before any stop
after any blocker
```

The next `Start_My_Agent` run must be able to continue from `ACTIVE_CURSOR.md` without asking the user.

---

## 1. Repository Context

Work inside:

```text
/home/naslouby/Projects/datp
```

This project is transitioning from the conference DATP paper to the journal extension.

Conference anchors:

```text
Blueprint.md
paper/DATP.tex
paper/sections/
paper/DATP.pdf
```

Journal anchors:

```text
docs/journal/PRE_CODING_PLAN.md
docs/journal/CODING_PLAN.md
docs/journal/EXPERIMENT_PLAN.md
docs/journal/POST_EXPERIMENT_PLAN.md
docs/tickets/
docs/tickets/ticket_inventory.md
docs/tickets/ticket_progress.md
```

Archived journal-extension context:

```text
Journal/Journal_Extension_Master_Roadmap.md
```

The archived roadmap is context only.

If the archived roadmap conflicts with the active four-file journal package, the active four-file package wins.

Agent and skill anchors:

```text
.claude/agents/
.claude/skills/
.claude/settings.json
```

Workflow anchors:

```text
AI Workflow/
AI Workflow/state/
AI Workflow/state/ACTIVE_CURSOR.md
```

If `AI Workflow/state/` does not exist, create it.

If `AI Workflow/state/ACTIVE_CURSOR.md` does not exist, create it before doing autonomous work.

---

## 2. First Commands on `Start_My_Agent`

Run these first:

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
uv run vulture --version || vulture --version || true
uv run refurb --version || refurb --version || true
uv run semgrep --version || semgrep --version || true
```

Do not assume a tool exists.

Record tool availability in:

```text
AI Workflow/state/TOOL_STATUS.md
AI Workflow/state/RUN_LEDGER.md
AI Workflow/state/CHECK_FLAGS.md
AI Workflow/state/ACTIVE_CURSOR.md
```

Do not claim a tool exists unless the command proves it.

Do not claim a check passed unless it actually ran.

---

## 3. Required Reading Order

Read these before planning or editing:

1. `.github/copilot-instructions.md`
2. `AI Workflow/README.md`
3. `AI Workflow/AI_WORKFLOW_READINESS.md`
4. `AI Workflow/MODEL_COST_POLICY.md`
5. `AI Workflow/SESSION_POLICY.md`
6. `AI Workflow/state/ACTIVE_CURSOR.md`
7. `AI Workflow/state/HANDOFFS.md`
8. `AI Workflow/state/RUN_LEDGER.md`
9. `AI Workflow/state/AGENT_MEMORY.md`
10. `AI Workflow/state/CHECK_FLAGS.md`
11. `AI Workflow/state/PROJECT_MAP.md`
12. `AI Workflow/state/TOOL_STATUS.md`
13. `AI Workflow/state/GRAPHIFY_STATUS.md`
14. `AI Workflow/REFACTOR_WORKBOARD.md`
15. `AI Workflow/AUDIT_CODE.md`
16. `AI Workflow/REFACTOR_MAP.md`
17. `AI Workflow/PATTERN_LEDGER.md`
18. `AI Workflow/MOVE_PLAN.md`
19. `AI Workflow/SCIENTIFIC_CONTRACT_AUDIT.md`
20. `AI Workflow/SCIENTIFIC_DRIFT_LOCK.md`
21. `AI Workflow/TEST_IMPACT_MAP.md`
22. `AI Workflow/SESSION_HANDOFF_TEMPLATE.md`
23. `AI Workflow/PACKET_TEMPLATE.md`
24. `Blueprint.md`
25. `CLAUDE.md`
26. `paper/DATP.tex`
27. `paper/sections/*.tex`
28. `Journal/Journal_Extension_Master_Roadmap.md`
29. `docs/journal/PRE_CODING_PLAN.md`
30. `docs/journal/CODING_PLAN.md`
31. `docs/journal/EXPERIMENT_PLAN.md`
32. `docs/journal/POST_EXPERIMENT_PLAN.md`
33. `docs/tickets/ticket_inventory.md`
34. `docs/tickets/ticket_progress.md`
35. `docs/tickets/T*.md`
36. `docs/tickets/audits/*.md`
37. `.claude/agents/*.md`
38. `.claude/skills/*.md`

Important rule:

`Journal/Journal_Extension_Master_Roadmap.md` is journal-extension context, but if it conflicts with the active four-file package under `docs/journal/`, the active `docs/journal/` package wins.

Do not hallucinate missing files.

If a file does not exist, record that fact and continue with repository reality.

---

## 4. Source-of-Truth Order

Use sources in this order:

1. Actual repository code, tests, configs, scripts, generated artifacts, and command output.
2. `docs/journal/PRE_CODING_PLAN.md`
3. `docs/journal/CODING_PLAN.md`
4. `docs/journal/EXPERIMENT_PLAN.md`
5. `docs/journal/POST_EXPERIMENT_PLAN.md`
6. `docs/tickets/ticket_progress.md`
7. `docs/tickets/ticket_inventory.md`
8. Individual tickets under `docs/tickets/`
9. Audit reports under `docs/tickets/audits/`
10. `AI Workflow/`
11. `AI Workflow/state/ACTIVE_CURSOR.md`
12. `.claude/agents/`
13. `.claude/skills/`
14. `Journal/Journal_Extension_Master_Roadmap.md`
15. `paper/DATP.tex`
16. `paper/sections/*.tex`
17. `Blueprint.md`
18. `CLAUDE.md`
19. `AGENTS.md`

Do not trust documentation that says something is done.

Verify actual implementation, tests, outputs, and artifacts.

Do not hallucinate files, commands, agents, tickets, results, datasets, or previous work.

If a referenced file does not exist, adapt to the actual repository.

---

## 5. Conference-to-Journal Transition Audit

The first major audit must check the transition from the conference paper to the journal extension.

Audit for discrepancies between:

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
AI Workflow/state/ACTIVE_CURSOR.md
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

Create or update tickets for real findings.

Do not create vague tickets.

Do not create duplicate tickets.

Do not mark any ticket `DONE` from prose alone.

---

## 6. Agent and Skill Utilization

Use `.claude/agents` and `.claude/skills` as role contracts when supported.

Available agent roles include:

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

Available skills include:

```text
artifact-audit-skill
datp-invariant-check-skill
experiment-gate-skill
human-intervention-gate-skill
latex-paper-skill
long-run-monitoring-skill
paper-claim-discipline-skill
refactor-clean-code-skill
results-statistics-skill
schema-enum-constant-skill
static-analysis-quality-gate-skill
test-coverage-skill
ticket-audit-skill
ticket-completion-audit-skill
ticket-generation-skill
ticket-progress-skill
```

If agents or skills are unavailable, continue manually.

Do not claim an agent or skill was used unless it was actually used.

Parallel work is allowed only when file scopes are disjoint.

Do not let two agents edit overlapping files.

---

## 7. Workflow State and Memory

Use written state to avoid redundant checks and enable continuation after stopped sessions.

Required state files:

```text
AI Workflow/state/ACTIVE_CURSOR.md
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
timestamp if available
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
Vulture/Refurb/Semgrep was run before major moves
later audit contradicts it
```

Never trust stale memory over current code.

Never rely on chat history for continuation.

---

## 8. Graphify Usage

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

If slash commands are available:

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

Verify important findings with:

```text
rg
code inspection
ruff
pyright
pytest
CodeScene
Vulture
Refurb
Semgrep
scientific documents
actual artifacts
```

---

## 9. Model and Token Policy

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
vulture
refurb
semgrep
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

Do not use these unless explicitly approved for the exact task:

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
update ACTIVE_CURSOR.md
continue with cheaper tools or another approved agent
do not lose state
```

---

## 10. Ticket System Behavior

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

Do not create tickets that only say “clean code.”

Do not mark tickets complete from prose.

Verify actual code, tests, and artifacts.

---

## 11. Scientific Contract

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

## 12. Baseline and Comparator Meanings

Canonical baseline meanings:

| Label | Meaning | Scope |
|---|---|---|
| B0 | Centralized AE reference comparator | Reference only |
| B1 | Shared/global threshold | Core |
| B2 | Per-client threshold | Core primary comparator against B1 |
| B3 | Family/group threshold | Core variant where applicable |
| B4 | Fingerprint-cluster threshold | Core variant |
| B5 | Local-only bounding case | Supplementary or ablation only |
| B-FedStatsBenign | Benign-only federated-statistics comparator | Journal comparator |
| B-LaridiFaithful | Faithful Laridi-style comparator using anomaly-labeled summaries where permitted | Outside DATP benign-only assumption |
| FedProx | Aggregation stress test | Not main threshold ladder |
| Ditto | Personalization stress test only if faithfully implemented | Not main threshold ladder |
| FedRep-AE/FedPer-AE fallback | Fallback local-head/shared-representation comparator | Must not be called Ditto unless faithful |

Do not rename baselines casually.

Do not make B5 the headline.

Do not call `B-FedStatsBenign` faithful Laridi.

Do not call a FedRep/FedPer fallback Ditto.

Do not treat FedProx or personalization comparators as part of B1–B4 threshold-scope causal evidence.

---

## 13. Train Once, Derive Many

The mainline invariant is:

```text
for each fixed dataset/regime/seed/alpha:
    train shared FL encoder once
    save checkpoint once
    generate shared per-client score artifacts once
    derive B1-B4 thresholds from saved scores
    compute result metrics from saved scores and thresholds
```

Do not implement:

```text
for each baseline:
    train a new encoder
```

Do not hide baseline-specific retraining behind:

```text
runner convenience
CLI shortcuts
threshold functions
evaluation functions
analysis scripts
reporting scripts
audit scripts
```

---

## 14. Score Artifacts

Score artifacts are shared across B1–B4 for a fixed training cell.

Score paths must not be baseline-specific for B1–B4.

Score artifacts must include the expected score column:

```text
reconstruction_error
```

Score artifacts must separate:

```text
calibration scores
test benign scores
test attack scores
```

Thresholding consumes saved scores.

Evaluation consumes saved scores and thresholds.

Reporting consumes saved result artifacts.

Do not recompute reconstruction errors in downstream stages.

---

## 15. Artifact Layout

Artifact layout must remain canonical.

Expected shared training layout:

```text
outputs/checkpoints/<regime>/seed_<N>[/alpha_<alpha>]/
outputs/scores/<regime>/seed_<N>[/alpha_<alpha>]/
```

Expected baseline-specific result layout:

```text
outputs/results/<regime>/<baseline>/seed_<N>[/alpha_<alpha>]/
```

Expected logs layout:

```text
outputs/logs/<regime>/<baseline>/seed_<N>[/alpha_<alpha>]/
outputs/console_logs/
```

Expected files:

```text
model.pt
metrics.json
manifest.json
scaler.pkl
DONE.txt
IN_PROGRESS
ABORTED.txt
```

`metrics.json.tmp` is not a completed result.

A result exists only if `metrics.json` exists and is non-empty.

Do not treat `.tmp` placeholders as success.

---

## 16. Configuration Discipline

Scientific parameters must come from config.

Do not hide scientific values as module constants.

Config-driven values include:

```text
n_min
q
seeds
alpha values
rounds_initial
rounds_max
convergence_relative_threshold
batch size
feature count
dataset paths
threshold quantiles
cluster K when scientifically configured
```

Before a run, validate:

```text
cfg.model.input_dim == cfg.dataset.feature_count
dataset schema matches feature count
test_benign exists
test_attack exists
resource bounds are safe
resolved config is written
```

Do not silently fall back to values that change scientific behavior.

---

## 17. Determinism

At every experiment entrypoint, set seeds for:

```text
Python random
NumPy
PyTorch CPU
PyTorch CUDA when available
```

Do not introduce nondeterministic data splits.

Do not introduce nondeterministic clustering without controlled seeds.

Do not use random defaults without explicit configuration.

---

## 18. Dataset and Regime Discipline

Regime meanings:

| Regime | Meaning |
|---|---|
| Regime A | N-BaIoT natural physical-device split; confirmatory |
| Regime B-a | CICIoT2023 file-level pseudo-clients; boundary/external validation |
| Regime B-b | Conditional CICIoT2023 device-MAC or device-group repartition after feasibility gate |
| Regime C | N-BaIoT Dirichlet severity sweep; supportive/exploratory |
| Regime D | Conditional Edge-IIoTset external validation after feasibility gate |

Do not fabricate device identifiers.

Do not invent dataset metadata.

Do not treat pseudo-clients as physical devices.

Do not upgrade feasibility-gated regimes to confirmed regimes without evidence.

Do not use archived roadmap assumptions over active `docs/journal/` files.

---

## 19. Calibration-Pending Clients

Calibration-Pending handling is scientifically critical.

Clients with fewer than `n_min` benign calibration samples are Calibration-Pending.

Rules:

```text
Calibration-Pending clients receive the global fallback threshold.
Calibration-Pending clients are excluded from eligible-only aggregation.
Coverage ratio must be reported.
CV(FPR) must be interpreted with coverage.
```

Do not silently drop pending clients without reporting coverage.

Do not include pending clients in eligible-only calculations.

Do not change fallback behavior without a scientific ticket and audit.

---

## 20. Metrics and Reporting

Primary endpoint:

```text
CV(FPR)
```

Always report coverage ratio with CV(FPR).

Other metrics:

```text
CV(TPR)
Macro-F1
worst-client balanced accuracy
mean FPR
mean TPR
P10 Macro-F1 where required
IQR(FPR)
max-min FPR
```

Baseline comparisons require confidence intervals when used for claims.

Use seed-level deltas for bootstrap comparisons when required.

Do not overinterpret non-confirmatory regimes.

Do not write causal language for mechanism analyses unless the design supports causality.

---

## 21. Code Ownership and Structure

Maintain clear package ownership.

Audit these packages:

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
tests
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
rerun optional tools if cleanup claims depend on them
```

Do not leave wrappers or redirects.

No internal backwards compatibility.

---

## 22. Refactoring Rules

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

## 23. Clean Code Rules

Use:

```text
AI Workflow/CLEAN_CODE_RULES.md
```

as the canonical clean-code rulebook.

Mandatory checks:

```text
closed concepts use enums
stable names use canonical constants
structured values use dataclasses or typed objects
utilities have domain ownership
no wrappers
no redirects
no compatibility aliases
no old package shells
no old-path tests
no duplicate typed shapes
no hidden scientific constants
tests move with production code
no skipped/xfailed/commented-out tests hiding failures
```

Do not create vague `utils`, `helpers`, `common`, `misc`, or `shared` modules unless ownership is explicit and unavoidable.

---

## 24. Duplication and Hardcoded Values

Search for duplication in:

```text
score loading
metric parsing
path construction
artifact naming
baseline strings
regime strings
threshold eligibility
calibration-pending handling
result serialization
dataset schemas
fixture builders
CUDA/device checks
config fallbacks
```

Do not fix repeated problems locally one by one.

Promote repeated problems to:

```text
AI Workflow/PATTERN_LEDGER.md
AI Workflow/MOVE_PLAN.md
AI Workflow/TEST_IMPACT_MAP.md
docs/tickets/
```

---

## 25. Typing and Naming Rules

Prefer:

```text
enums
frozen dataclasses
typed config models
typed request objects
typed result objects
clear domain names
canonical path builders
explicit artifact descriptors
```

Avoid:

```text
untyped dictionaries
anonymous tuples
duplicate NamedTuple shapes
long primitive argument lists
internal str-or-enum unions
repeated parsing inside domain logic
isinstance-based enum normalization scattered across modules
```

Parse strings at boundaries.

Use typed domain values internally.

---

## 26. Complexity, Dead Code, and Wrappers

Reduce:

```text
deep nesting
long functions
long classes
high argument counts
wide branching
unused objects
dead imports
unreachable code
over-specified docstrings
comments that repeat code
```

Do not reduce complexity by:

```text
hiding scientific steps
collapsing meaningful stages
weakening names
using clever one-liners
using broad dynamic dispatch
adding magic defaults
adding side effects
```

Dead-code tools are only signals.

Vulture findings are suspects.

Verify before deletion.

---

## 27. Error Handling and Logging

Use explicit errors for:

```text
missing artifacts
empty metrics
invalid score schemas
invalid configs
missing datasets
wrong feature counts
unsafe stage transitions
scientific invariant violations
```

Do not swallow exceptions that indicate scientific or artifact corruption.

Do not log success before artifacts are actually complete.

Do not let logging imply unsupported claims.

---

## 28. Test Quality Rules

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
tests that preserve old internal import paths
tests that validate obsolete package names
```

Do not run full E2E by default.

Run impacted E2E only when directly required.

---

## 29. Required Test Scenarios

Test coverage must protect:

```text
shared training invariant
score artifact reuse
no per-baseline retraining
threshold derivation from saved scores
Calibration-Pending fallback
coverage ratio reporting
CV(FPR) computation
baseline-specific result paths
shared checkpoint paths
shared score paths
config validation
dataset schema validation
determinism
metric serialization
reporting sidecars
no placeholder results
```

When refactoring, update impacted tests.

Do not keep old tests alive solely to preserve obsolete paths.

---

## 30. Static Analysis and Quality Gates

Default required checks after code/test changes:

```bash
git status --short
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

Use optional extra tools when useful and available:

```bash
uv run vulture src/datp tests --min-confidence 80
uv run refurb src/datp tests
uv run semgrep scan --config auto src/datp tests
```

Use Sonar only as optional final audit if healthy.

Do not claim Sonar passed unless it actually ran.

Do not claim CodeScene passed unless it actually ran.

Do not claim Vulture, Refurb, or Semgrep passed unless they actually ran.

---

## 31. Refactor Workflow

For every meaningful scope, perform:

```text
pre-change audit
implementation
targeted tests
static checks
optional extra-tool checks when useful
post-fix audit
integration re-audit
scientific-contract audit
hostile reviewer audit
project-map update
workflow state update
active cursor update
handoff update
```

Do not stop after first green check.

Do not treat pre-existing failures as acceptable.

Do not make churn changes on second run.

When a packet authorizes fixing, do not stop at audit-only reporting.

Fix in the smallest safe batch, then re-audit.

---

## 32. Non-Negotiable Rejection Rules

Reject changes that:

```text
create wrappers
create redirects
create compatibility aliases
create old package shells
preserve old internal import paths
add old-path tests
weaken tests
skip failing tests
hide scientific constants
retrain per baseline
recompute scores downstream
change baseline semantics
change regime semantics
fabricate metadata
overclaim privacy
overclaim robustness
overclaim deployment
treat archived roadmap as active plan
ignore active cursor state
overwrite unexplained user work
```

---

## 33. Paper and Documentation Rules

Documentation must match actual code and artifacts.

Do not update docs to hide unfinished work.

Do not mark tickets complete from docs alone.

When editing paper or docs:

```text
separate direct evidence from supportive evidence
avoid unsupported causal language
avoid deployment/privacy/robustness overclaims
report coverage with CV(FPR)
keep Regime A confirmatory
keep Regime B/C/D scope correct
keep stress tests outside the B1-B4 causal ladder
keep archived roadmap as archived context
```

Do not use result wording that is stronger than the evidence.

---

## 34. Definition of Done

Nothing is `DONE` until:

```text
code reality was inspected
documentation reality was inspected
scientific rules were inspected
conference-to-journal transition was inspected when relevant
tickets were updated
workflow state was updated
active cursor was updated
project map was updated
move/test plans were updated when reality changed
Graphify status was refreshed or explicitly deferred with reason when architecture changed
Vulture/Refurb/Semgrep status was recorded if used
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

If later re-audit has not happened, use:

```text
REAUDIT_REQUIRED
```

not:

```text
DONE
```

---

## 35. Final Report and Handoff

When stopping, write a handoff in:

```text
AI Workflow/state/HANDOFFS.md
```

Also update:

```text
AI Workflow/state/ACTIVE_CURSOR.md
AI Workflow/state/RUN_LEDGER.md
AI Workflow/REFACTOR_WORKBOARD.md
```

Include:

```text
current git status
active packet
active ticket
active locks
completed work
files changed
commands run
checks passed
checks failed
Graphify status
Vulture/Refurb/Semgrep status
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
Vulture passed unless actually executed
Refurb passed unless actually executed
Semgrep passed unless actually executed
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

## 36. Default Principle

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

---

## AGENTS.md

The repository may also include `AGENTS.md`.

If present, use it as an additional role map.

If `AGENTS.md` conflicts with this file or the active scientific contract, this file and the scientific contract win.

---

## Purpose

The agent system exists to support disciplined, auditable, scientifically safe work.

Agents are not allowed to bypass repository reality, test results, or scientific constraints.

Agents must update workflow state and handoff files.

Agents must never create the appearance of progress without evidence.

---

## Behavioral Guidelines

Agents must:

```text
inspect first
act in the smallest safe batch
record evidence
update tests
update maps
update tickets
update active cursor
update handoff
re-audit
continue until done or blocked
```

Agents must not:

```text
hallucinate files
ignore existing state
overwrite user changes
skip scientific review
hide failed checks
create wrappers
keep old paths alive
mark tickets done from prose
ask the user what to do next during Start_My_Agent
```

---

## Core Rule

The real repository is the source of truth.

Plans, tickets, maps, reports, and handoffs are valid only after they match real code, tests, artifacts, and command output.

---

## Agents

### Orchestrator Agent

Owns:

```text
startup
state reading
cursor reading
packet selection
ticket coordination
role routing
handoff quality
final status
```

Must update:

```text
AI Workflow/state/ACTIVE_CURSOR.md
AI Workflow/state/HANDOFFS.md
AI Workflow/state/RUN_LEDGER.md
AI Workflow/REFACTOR_WORKBOARD.md
```

### Implementation Agent

Owns:

```text
small scoped code changes
direct import repair
test updates
no-wrapper enforcement
simple command verification
```

Must not make unsupported scientific changes.

### Refactor Agent

Owns:

```text
package ownership repair
duplication consolidation
constants/enums/dataclasses cleanup
module boundary cleanup
old-path deletion
```

Must not preserve backwards compatibility internally.

### Test Agent

Owns:

```text
targeted test updates
fixture cleanup
skipped/xfail audit
old-path test removal
behavior-focused assertions
```

Must not weaken tests to pass.

### Code Quality Gate Agent

Owns:

```text
Ruff
Pyright
targeted pytest
CodeScene when useful
Vulture when useful
Refurb when useful
Semgrep when useful
Sonar only if healthy and final-only
```

Must not claim tools passed unless they ran.

### Ticket Completion Auditor Agent

Owns:

```text
actual-code verification
actual-test verification
evidence-backed DONE status
dependency checks
re-audit status
```

Must not trust ticket prose.

### Drift Enforcer Agent

Owns:

```text
scientific drift detection
baseline semantics
regime semantics
claim discipline
stage boundaries
journal plan consistency
```

Must block unsafe scientific changes.

### Scientific Contract Agent

Owns:

```text
B1 versus B2 identity
shared-score invariant
fixed-encoder invariant
Calibration-Pending handling
CV(FPR) and coverage reporting
bootstrap comparison discipline
```

### Experiment Runner Agent

Owns:

```text
experiment readiness
run gates
resource checks
no accidental heavy jobs
artifact completion validation
```

Must not launch heavy experiments unless explicitly authorized.

### Results Audit Agent

Owns:

```text
metrics lineage
artifact validation
figure/table sidecars
result completeness
claim support
```

### Paper Update Agent

Owns:

```text
paper text updates
caption/table consistency
claim wording
IEEE/journal writing discipline
evidence qualification
```

Must not overclaim.

---

## Ticket Workflow

Tickets are execution units, not proof.

Ticket status must reflect actual verified state.

Every ticket must include:

```text
objective
scope
evidence
scientific risk
technical risk
required implementation
required tests
required audit
acceptance criteria
status
```

---

## Status Rules

Allowed statuses:

```text
NOT_STARTED
READY
IN_PROGRESS
BLOCKED
NEEDS_REPAIR
NEEDS_REAUDIT
REAUDIT_REQUIRED
DONE
```

`DONE` requires:

```text
implementation evidence
test evidence
static-check evidence
scientific-contract evidence
project-map update
handoff update
active cursor update
post-fix audit
later re-audit
```

---

## Prohibited Completion

Do not mark complete when:

```text
tests were not run and no valid reason is recorded
Ruff/Pyright were skipped without reason
scientific invariant was not checked
files were not inspected
workflow state was not updated
active cursor was not updated
handoff was not written
old wrappers remain
old redirects remain
old compatibility aliases remain
old-path tests remain
skipped tests hide failures
duplicate string/enum/constant/schema ownership is scattered
hardcoded scientific values remain
DATP invariants are not checked
drift check is required but missing
progress files are stale
```