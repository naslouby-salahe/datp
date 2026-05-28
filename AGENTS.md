# DATP Agent Map

## Purpose

This file defines the agent workflow for DATP.

The project uses specialist agents, but no ticket is complete until implementation, refactoring, testing, quality, scientific invariants, and ticket completion all pass.

## Behavioral Guidelines

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

### 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

### 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

### 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

### 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.

## Core Rule

A ticket is not DONE because code was written.

A ticket is DONE only when:

1. The implementation matches the ticket.
2. The code is refactored.
3. The tests are sufficient.
4. Static analysis is clean.
5. Quality gate passes.
6. Scientific invariants are preserved.
7. Drift check passes when applicable.
8. Ticket completion audit passes.
9. Ticket progress is updated.

## Agents

## Orchestrator Agent

Path:

`./.claude/agents/orchestrator-agent.md`

Owns:

1. Workflow coordination.
2. Agent routing.
3. Ticket sequence.
4. Quality-gate enforcement.
5. Progress enforcement.
6. Drift escalation.

Runs:

1. At the start of each ticket.
2. Between specialist agents.
3. Before final completion.

## Implementation Agent

Path:

`./.claude/agents/implementation-agent.md`

Owns:

1. Ticket implementation.
2. Existing owner inspection.
3. Behavior implementation.
4. Config/schema/enum/constant-aware coding.
5. Clean handoff to refactor and test agents.

Runs:

1. After orchestrator confirms ticket scope.
2. Before refactor.
3. During repair loops when implementation root causes are found.

## Refactor Agent

Path:

`./.claude/agents/refactor-agent.md`

Owns:

1. Code cleanup.
2. Complexity reduction.
3. Duplication removal.
4. Ownership correction.
5. Dead-code removal.
6. Naming improvements.
7. Utility and object boundary correction.

Runs:

1. After implementation.
2. During audit-and-fix loops.
3. Whenever CodeScene, SonarLint, or readability issues remain.

## Test Agent

Path:

`./.claude/agents/test-agent.md`

Owns:

1. Unit tests.
2. Integration tests.
3. Regression tests.
4. Edge-case tests.
5. Test refactoring.
6. Test static-analysis quality.

Runs:

1. After implementation.
2. After refactoring.
3. During repair loops.
4. Before quality gate.

## Code Quality Gate Agent

Path:

`./.claude/agents/code-quality-gate-agent.md`

Owns:

1. Pylance/Pyright issues.
2. SonarLint/SonarQube issues.
3. CodeScene issues.
4. Complexity gates.
5. Dead code.
6. Duplicate code.
7. Duplicate literals.
8. Hardcoded values.
9. Scattered constants.
10. Scattered enums.
11. Scattered config.
12. Scattered schemas.
13. Wrong utilities.
14. Wrong object boundaries.
15. Misplaced scripts.
16. Missing test coverage.
17. Invalid defaults in input/config models.

Runs:

1. After every ticket implementation.
2. After every refactor.
3. After every repair.
4. Before ticket completion audit.
5. Before DONE status is allowed.

Canonical commands (see `CLAUDE.md` → "Mandatory Quality Gate" and `docs/quality/QUALITY_TOOLS.md`):

- `make quality-audit-tools-check` — verify every quality tool is callable.
- `make quality-audit-local` — full audit: ruff, ruff format, pyright, pytest+coverage, pysonar upload to local SonarQube, cs delta.
- `make sonar-up` / `make sonar-down` / `make sonar-health` — local SonarQube Community Build lifecycle (Docker, `http://localhost:9000`).
- `make codescene-check` — CodeScene delta on current changes.

Secrets (`SONAR_TOKEN`, `CS_ACCESS_TOKEN`) live only in `.env.local` (gitignored). Never echo, log, or commit token values.

## Ticket Completion Auditor Agent

Path:

`./.claude/agents/ticket-completion-auditor-agent.md`

Owns:

1. Acceptance-criteria verification.
2. DONE eligibility.
3. Evidence validation.
4. Ticket progress status recommendation.
5. Completion blockers.

Runs:

1. After quality gate passes.
2. Before ticket status is changed to DONE.
3. During audit-only requests.

## Drift Enforcer Agent

Path:

`./.claude/agents/drift-enforcer-agent.md`

Owns:

1. Roadmap drift.
2. Ticket drift.
3. Paper-scope drift.
4. Scientific-scope drift.
5. Claim drift.
6. Experiment-scope drift.

Runs:

1. When code changes scientific behavior.
2. When experiments, metrics, baselines, datasets, claims, or paper artifacts are touched.
3. During final no-drift audits.

## Scientific Contract Agent

Path:

`./.claude/agents/scientific-contract-agent.md`

Owns:

1. DATP invariants.
2. Threshold-scope isolation.
3. Shared-training invariant.
4. Baseline semantics.
5. Dataset/regime semantics.
6. Claim boundaries.

Runs:

1. When implementation touches scientific behavior.
2. Before experiment execution.
3. Before paper/result updates.
4. During final no-drift audits.

## Experiment Runner Agent

Path:

`./.claude/agents/experiment-runner-agent.md`

Owns:

1. Experiment command execution.
2. Long-run monitoring.
3. Artifact verification.
4. Retry handling within allowed scope.

Runs only after:

1. Implementation passes.
2. Refactor passes.
3. Tests pass.
4. Code quality gate passes.
5. Scientific contract passes.

## Results Audit Agent

Path:

`./.claude/agents/results-audit-agent.md`

Owns:

1. Metrics validation.
2. Table validation.
3. Figure validation.
4. Bootstrap/statistical result checks.
5. Artifact consistency.

Runs:

1. After experiment results exist.
2. Before paper update.
3. Before final result claims.

## Paper Update Agent

Path:

`./.claude/agents/paper-update-agent.md`

Owns:

1. Paper edits.
2. Claim discipline.
3. Figure/table integration.
4. Page budget.
5. Citation-safe wording.

Runs only after:

1. Results audit passes.
2. Scientific contract passes.
3. Claim evidence exists.

## Ticket Workflow

For every ticket:

1. Orchestrator reads ticket and progress.
2. Implementation agent implements the ticket.
3. Refactor agent cleans changed and related code.
4. Test agent adds, adapts, or deletes tests.
5. Code quality gate agent audits the affected surface.
6. Ticket completion auditor verifies DONE eligibility.
7. Drift enforcer runs when scientific or roadmap scope is touched.
8. Orchestrator updates ticket progress.

## Status Rules

Use:

1. `NOT_STARTED` when work has not begun.
2. `IN_PROGRESS` when implementation or repair is active.
3. `BLOCKED_QUALITY` when implementation works but quality gate fails.
4. `BLOCKED_DRIFT` when scope or scientific meaning is unclear.
5. `BLOCKED_HUMAN` only when external human evidence is genuinely required.
6. `DONE` only when all gates pass.

## Prohibited Completion

Do not mark DONE if:

1. Static analysis failed.
2. Type checking failed.
3. Tests failed.
4. Coverage is insufficient.
5. Refactor is incomplete.
6. Dead code remains.
7. Duplicate literals remain.
8. Config/enum/constant/schema ownership is scattered.
9. Hardcoded scientific values remain.
10. DATP invariants are not checked.
11. Drift check is required but missing.
12. Progress files are stale.