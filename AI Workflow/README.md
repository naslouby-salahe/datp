# DATP AI Workflow

This folder defines the controlled, budget-aware, mostly autonomous AI refactoring workflow for the DATP repository.

The goal is not random cleanup. The workflow is global-aware: it must understand the repository, detect repeated patterns across packages, promote cross-cutting problems into work packets, refactor real code, update tests, and repeatedly audit the result while preserving DATP scientific correctness.

The normal launcher command is:

```text
Start_My_Agent
```

---

## Target repository

```text
/home/naslouby/Projects/datp
```

---

## Required startup order for any AI session

1. Read `.github/copilot-instructions.md`.
2. Read `AI_WORKFLOW_READINESS.md`.
3. Read `ORCHESTRATOR_PROMPT.md`.
4. Read `MODEL_COST_POLICY.md`.
5. Read `SESSION_POLICY.md`.
6. Read `CLEAN_CODE_RULES.md`.
7. Read `REFACTOR_WORKBOARD.md`.
8. Read `REFACTOR_MAP.md`.
9. Read `AI Workflow/state/PROJECT_MAP.md`.
10. Read the active packet under `packets/`.
11. Run:

```bash
git status --short
```

The session must continue from written progress, not from memory.

`AI_WORKFLOW_READINESS.md` is intentionally kept. It owns tool, resource, quality-gate, Sonar, CodeScene, Graphify, Vulture, Refurb, and Semgrep readiness assumptions.

`CLEAN_CODE_RULES.md` is the canonical clean-code and refactor rulebook. It owns the repeated rules for enums, constants, dataclasses, package ownership, utility ownership, no backwards compatibility, tests moving with code, static tools, evidence, and re-audit behavior.

---

## File index

| File | Purpose |
|---|---|
| `AI_WORKFLOW_READINESS.md` | Tool inventory, WSL constraints, readiness checklist, safe command policy, Sonar policy, Graphify policy, optional Vulture/Refurb/Semgrep policy. |
| `CLEAN_CODE_RULES.md` | Canonical clean-code and refactor rules: enums, constants, dataclasses, utility ownership, duplication removal, no wrappers/redirects, test movement, evidence, and re-audit rules. |
| `MODEL_COST_POLICY.md` | Model tiers, allowed commands, expensive-model bans, escalation rules. |
| `SESSION_POLICY.md` | Rules for continuing, starting, ending, and handing off AI sessions. |
| `REFACTOR_WORKBOARD.md` | Main packet board, file locks, current status, repeated re-audit tracking. |
| `AUDIT_CODE.md` | Living audit log for architectural, technical, quality, security, modernization, clean-code, and scientific findings. |
| `REFACTOR_MAP.md` | Intended responsibility map and package-boundary decisions. |
| `state/PROJECT_MAP.md` | Living repository reality map updated after Graphify runs, package moves, ownership decisions, tool-state changes, and final review. |
| `PATTERN_LEDGER.md` | Cross-package repeated-pattern ledger. Local duplicate fixes are not enough. |
| `MOVE_PLAN.md` | Planned code moves, deleted modules, import/test impact, and completion evidence. |
| `SCIENTIFIC_CONTRACT_AUDIT.md` | DATP scientific invariants and stage-boundary audit gates. |
| `TEST_IMPACT_MAP.md` | Impacted tests, targeted commands, deferred checks, skipped/xfail cleanup, optional-tool retest policy. |
| `PACKET_TEMPLATE.md` | Template for new work packets. |
| `ORCHESTRATOR_PROMPT.md` | Autonomous workflow prompt executed by `Start_My_Agent`. |
| `QUICK_START_COMMANDS.md` | Human-facing quick start and safe command reference. |
| `SESSION_HANDOFF_TEMPLATE.md` | Required handoff format before ending any AI session. |
| `packets/PKT-000-readiness-and-inventory.md` | First packet to initialize and verify the workflow. |
| `state/TOOL_STATUS.md` | Actual tool availability, installed versions, unavailable tools, and limitations. |
| `state/RUN_LEDGER.md` | Chronological run and command ledger. |
| `state/GRAPHIFY_STATUS.md` | Graphify availability, runs, failures, and snapshot references. |
| `state/CHECK_FLAGS.md` | Cached check flags with invalidation rules. |
| `state/FILE_HASHES.json` | File hashes used to invalidate stale checks. |
| `state/HANDOFFS.md` | Session handoffs. |
| `state/AGENT_MEMORY.md` | Evidence-backed workflow memory. |

---

## Non-negotiables

- `Start_My_Agent` is the normal launch command.
- DeepSeek V4 Pro in VS Code Copilot is the main orchestrator and main coding worker.
- Normal tools come before AI token spending: `git`, `rg`, `python`, `ruff`, `pyright`, `pytest`, and optionally `cs`.
- `CLEAN_CODE_RULES.md` is mandatory for all refactor, audit, packet, and review work.
- Closed domain concepts must use canonical enums after boundary parsing.
- Stable names must use canonical constants instead of scattered string literals.
- Structured value groups must use dataclasses or typed domain objects instead of long primitive argument lists, repeated dictionaries, or duplicate tuple shapes.
- Utility code must have an owner. No vague dumping-ground `utils`, `helpers`, `misc`, or `common` modules unless ownership is explicit and unavoidable.
- Repeated patterns must be promoted to `PATTERN_LEDGER.md` and fixed at the canonical owner, not patched locally in every package.
- Vulture, Refurb, and Semgrep are approved optional tools.
- Vulture, Refurb, and Semgrep must be checked first, installed if missing, verified after install, and flagged in workflow state.
- Vulture findings are suspects, not proof.
- Refurb suggestions are optional and must not reduce scientific clarity.
- Semgrep findings must be triaged as security/static-analysis signals.
- Repomix, Git worktrees, CodeQL, and deptry are not part of this workflow unless explicitly approved later.
- Sonar is optional because local Sonar has been unreliable. It must not block early refactoring and must not be claimed as passing unless it actually ran successfully.
- CodeScene is useful when available, but it must not be claimed as passing unless it actually ran.
- Graphify should be refreshed repeatedly during architecture-changing refactors and must update `state/PROJECT_MAP.md`.
- Claude Opus, Codex `gpt-5.5`, Codex `gpt-5.5 high`, and expensive Gemini Ultra/Pro-style models are disallowed unless explicitly approved.
- The workflow must not run training, heavy experiments, Ray/Flower-heavy jobs, or full E2E suites casually.
- No wrappers, redirects, compatibility aliases, or dead old modules should remain just to preserve old paths.
- Tests must move with production code and must not preserve obsolete internal import paths.
- Fixed DATP science wins over cleanup convenience.

---

## Approved optional tool commands

Check:

```bash
uv run vulture --version || vulture --version || true
uv run refurb --version || refurb --version || true
uv run semgrep --version || semgrep --version || true
```

Install if missing:

```bash
uv add --dev vulture refurb semgrep
```

Run when useful:

```bash
uv run vulture src/datp tests --min-confidence 80
uv run refurb src/datp tests
uv run semgrep scan --config auto src/datp tests
```

Record availability and results in:

```text
AI Workflow/state/TOOL_STATUS.md
AI Workflow/state/RUN_LEDGER.md
AI Workflow/state/CHECK_FLAGS.md
```

---

## Project map rule

`REFACTOR_MAP.md` describes intended ownership.

`state/PROJECT_MAP.md` records current repository reality.

Both must stay aligned.

Update `state/PROJECT_MAP.md`:

1. after initial inventory;
2. after every Graphify refresh;
3. after major package moves;
4. after ownership decisions;
5. after Vulture/Refurb/Semgrep materially affect findings or cleanup plans;
6. after deleted wrappers or compatibility shells;
7. after enum, constant, dataclass, schema, artifact, scoring, thresholding, or test ownership changes;
8. after test-structure changes;
9. before final hostile review.

If `REFACTOR_MAP.md` and `PROJECT_MAP.md` disagree, inspect the real repository and update the stale file.

---

## Clean-code enforcement rule

Every packet must check the affected scope against:

```text
AI Workflow/CLEAN_CODE_RULES.md
```

At minimum, the packet must verify:

```text
no wrappers or redirects
no old import paths preserved
no duplicated enums/constants
no duplicated typed structures
no repeated primitive argument groups
no vague utility dumping grounds
no local duplicate fixes when a canonical owner is needed
no unjustified skipped/xfailed/commented tests
no hidden scientific parameter constants
no downstream call into training from thresholding/evaluation/reporting/analysis/validation
```

A packet may stop with `REAUDIT_REQUIRED`, but it must not claim `DONE` until a later re-audit confirms the rules still hold after integration.

---

## Completion definition

The workflow is not complete until all packets have:

1. implementation evidence;
2. test evidence;
3. static-check evidence;
4. optional-tool evidence when used;
5. clean-code rule evidence;
6. scientific-contract evidence;
7. project-map updates;
8. handoff evidence;
9. at least one later re-audit after integration.