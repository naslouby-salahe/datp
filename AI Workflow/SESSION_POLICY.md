# Session Management Policy

Long AI sessions become token-expensive and noisy.

Every session must be managed as a work unit with explicit state.

Written files are the source of truth.

---

## Keep the same session when

- working on the same work packet;
- editing the same files;
- debugging the same issue;
- reviewing the same diff;
- the context is still useful;
- the session is not too long, repetitive, or noisy.

---

## Start a new session when

- starting a new work packet;
- moving to a different package;
- switching from implementation to final review;
- switching tools or roles;
- changing models;
- after a quota warning;
- after a packet is completed;
- after major Graphify/project-map refresh;
- after major package moves;
- the session repeats itself;
- the session hallucinates;
- the session relies on outdated assumptions.

---

## Required new-session startup

1. Read `.github/copilot-instructions.md`.
2. Read `AI Workflow/AI_WORKFLOW_READINESS.md`.
3. Read `AI Workflow/ORCHESTRATOR_PROMPT.md`.
4. Read `AI Workflow/MODEL_COST_POLICY.md`.
5. Read `AI Workflow/REFACTOR_WORKBOARD.md`.
6. Read `AI Workflow/REFACTOR_MAP.md`.
7. Read `AI Workflow/state/PROJECT_MAP.md`.
8. Read the active packet file.
9. Run:

```bash
git status --short
```

10. Continue from written progress, not from memory.

`AI_WORKFLOW_READINESS.md` is intentionally kept and must remain part of startup.

---

## Required end-of-session handoff

Before ending a session, update the workflow files and record:

- what was completed;
- what remains;
- changed files;
- locked files;
- commands run;
- tests/checks run;
- Graphify runs or skipped Graphify reason;
- project-map updates;
- deferred checks;
- failures;
- quota/tool issues;
- scientific risks;
- next action.

Use:

```text
AI Workflow/SESSION_HANDOFF_TEMPLATE.md
AI Workflow/state/HANDOFFS.md
```

---

## Session naming

Use descriptive session names when the tool supports it:

```text
DATP-PKT-000-readiness
DATP-PKT-001-repo-map
DATP-PKT-002-pattern-ledger
DATP-PKT-003-artifacts-paths
DATP-PKT-005-score-metrics
DATP-final-hostile-review
```

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
```

---

## Sonar session rule

Local Sonar has been unreliable.

Do not start a new session only to satisfy Sonar unless the repository is ready for an optional final audit and Sonar is healthy.

If Sonar fails for environmental reasons:

1. record the failure;
2. do not claim Sonar passed;
3. continue with Ruff, Pyright, targeted pytest, CodeScene, and source inspection;
4. mark Sonar as an environmental limitation.

---

## Session anti-patterns

- Do not keep a session alive because it “might remember something”.
- Do not allow one session to rewrite decisions made by another without updating the board and audit trail.
- Do not let multiple tools edit the same files at the same time.
- Do not use expensive models because the current session became messy.
- Do not rely on stale Graphify output after major moves.
- Do not rely on stale project-map assumptions.
- Do not turn unreliable local Sonar into a false blocker.
- Do not start broad refactoring before repository reality and project-map state are updated.
