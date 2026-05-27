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
6. Read `REFACTOR_WORKBOARD.md`.
7. Read `REFACTOR_MAP.md`.
8. Read `AI Workflow/state/PROJECT_MAP.md`.
9. Read the active packet under `packets/`.
10. Run:

```bash
git status --short
```

The session must continue from written progress, not from memory.

`AI_WORKFLOW_READINESS.md` is intentionally kept. It owns tool, resource, quality-gate, Sonar, CodeScene, and Graphify readiness assumptions.

---

## File index

| File | Purpose |
|---|---|
| `AI_WORKFLOW_READINESS.md` | Tool inventory, WSL constraints, readiness checklist, safe command policy, Sonar policy, Graphify policy. |
| `MODEL_COST_POLICY.md` | Model tiers, allowed commands, expensive-model bans, escalation rules. |
| `SESSION_POLICY.md` | Rules for continuing, starting, ending, and handing off AI sessions. |
| `REFACTOR_WORKBOARD.md` | Main packet board, file locks, current status, repeated re-audit tracking. |
| `AUDIT_CODE.md` | Living audit log for architectural, technical, quality, and scientific findings. |
| `REFACTOR_MAP.md` | Intended responsibility map and package-boundary decisions. |
| `state/PROJECT_MAP.md` | Living repository reality map updated after Graphify runs, package moves, ownership decisions, and final review. |
| `PATTERN_LEDGER.md` | Cross-package repeated-pattern ledger. Local duplicate fixes are not enough. |
| `MOVE_PLAN.md` | Planned code moves, deleted modules, import/test impact, and completion evidence. |
| `SCIENTIFIC_CONTRACT_AUDIT.md` | DATP scientific invariants and stage-boundary audit gates. |
| `TEST_IMPACT_MAP.md` | Impacted tests, targeted commands, deferred checks, skipped/xfail cleanup. |
| `PACKET_TEMPLATE.md` | Template for new work packets. |
| `ORCHESTRATOR_PROMPT.md` | Autonomous workflow prompt executed by `Start_My_Agent`. |
| `QUICK_START_COMMANDS.md` | Human-facing quick start and safe command reference. |
| `SESSION_HANDOFF_TEMPLATE.md` | Required handoff format before ending any AI session. |
| `packets/PKT-000-readiness-and-inventory.md` | First packet to initialize and verify the workflow. |
| `state/TOOL_STATUS.md` | Actual tool availability and limitations. |
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
- Sonar is optional because local Sonar has been unreliable. It must not block early refactoring and must not be claimed as passing unless it actually ran successfully.
- CodeScene is useful when available, but it must not be claimed as passing unless it actually ran.
- Graphify should be refreshed repeatedly during architecture-changing refactors and must update `state/PROJECT_MAP.md`.
- Claude Opus, Codex `gpt-5.5`, Codex `gpt-5.5 high`, and expensive Gemini Ultra/Pro-style models are disallowed unless explicitly approved.
- The workflow must not run training, heavy experiments, Ray/Flower-heavy jobs, or full E2E suites casually.
- No wrappers, redirects, compatibility aliases, or dead old modules should remain just to preserve old paths.
- Fixed DATP science wins over cleanup convenience.

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
5. after deleted wrappers or compatibility shells;
6. after test-structure changes;
7. before final hostile review.

If `REFACTOR_MAP.md` and `PROJECT_MAP.md` disagree, inspect the real repository and update the stale file.

---

## Completion definition

The workflow is not complete until all packets have:

1. implementation evidence;
2. test evidence;
3. static-check evidence;
4. scientific-contract evidence;
5. project-map updates;
6. handoff evidence;
7. at least one later re-audit after integration.
