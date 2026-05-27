# DATP AI Workflow

This folder defines the controlled, budget-aware, mostly autonomous AI refactoring workflow for the DATP repository.

The goal is not random cleanup. The workflow is global-aware: it must understand the repository, detect repeated patterns across packages, promote cross-cutting problems into work packets, refactor real code, update tests, and repeatedly audit the result while preserving DATP scientific correctness.

## Target repository

```text
/home/naslouby/Projects/datp
```

## Required startup order for any AI session

1. Read `AI_WORKFLOW_READINESS.md`.
2. Read `MODEL_COST_POLICY.md`.
3. Read `SESSION_POLICY.md`.
4. Read `REFACTOR_WORKBOARD.md`.
5. Read the active packet under `packets/`.
6. Run:

```bash
git status --short
```

The session must continue from written progress, not from memory.

## File index

| File | Purpose |
|---|---|
| `AI_WORKFLOW_READINESS.md` | Tool inventory, WSL constraints, readiness checklist, safe command policy. |
| `MODEL_COST_POLICY.md` | Model tiers, allowed commands, expensive-model bans, escalation rules. |
| `SESSION_POLICY.md` | Rules for continuing, starting, ending, and handing off AI sessions. |
| `REFACTOR_WORKBOARD.md` | Main packet board, file locks, current status, repeated re-audit tracking. |
| `AUDIT_CODE.md` | Living audit log for architectural, technical, quality, and scientific findings. |
| `REFACTOR_MAP.md` | Repository responsibility map and package-boundary decisions. |
| `PATTERN_LEDGER.md` | Cross-package repeated-pattern ledger. Local duplicate fixes are not enough. |
| `MOVE_PLAN.md` | Planned code moves, deleted modules, import/test impact, and completion evidence. |
| `SCIENTIFIC_CONTRACT_AUDIT.md` | DATP scientific invariants and stage-boundary audit gates. |
| `TEST_IMPACT_MAP.md` | Impacted tests, targeted commands, deferred checks, skipped/xfail cleanup. |
| `PACKET_TEMPLATE.md` | Template for new work packets. |
| `ORCHESTRATOR_PROMPT.md` | Prompt to give to VS Code Copilot + DeepSeek V4 Pro. |
| `SESSION_HANDOFF_TEMPLATE.md` | Required handoff format before ending any AI session. |
| `packets/PKT-000-readiness-and-inventory.md` | First packet to initialize and verify the workflow. |

## Non-negotiables

- DeepSeek V4 Pro in VS Code Copilot is the main orchestrator and main coding worker.
- Normal tools come before AI token spending: `git`, `python`, `ruff`, `pyright`, `pytest`, and optionally `cs`.
- Sonar is intentionally excluded and must not block this workflow.
- Claude Opus, Codex `gpt-5.5`, Codex `gpt-5.5 high`, and expensive Gemini Ultra/Pro-style models are disallowed unless explicitly approved.
- The workflow must not run training, heavy experiments, Ray/Flower-heavy jobs, or full e2e suites casually.
- No wrappers, redirects, compatibility aliases, or dead old modules should remain just to preserve old paths.
- Fixed DATP science wins over cleanup convenience.

## Completion definition

The workflow is not complete until all packets have implementation evidence, test evidence, audit evidence, and at least one later re-audit after integration.
