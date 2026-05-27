# Session Management Policy

Long AI sessions become token-expensive and noisy. Every session must be managed as a work unit with explicit state.

## Keep the same session when

- working on the same work packet;
- editing the same files;
- debugging the same issue;
- reviewing the same diff;
- the context is still useful;
- the session is not too long, repetitive, or noisy.

## Start a new session when

- starting a new work packet;
- moving to a different package;
- switching from implementation to final review;
- switching tools or roles;
- changing models;
- after a quota warning;
- after a packet is completed;
- the session repeats itself;
- the session hallucinates;
- the session relies on outdated assumptions.

## Required new-session startup

1. Read `AI_WORKFLOW_READINESS.md`.
2. Read `MODEL_COST_POLICY.md`.
3. Read `REFACTOR_WORKBOARD.md`.
4. Read the active packet file.
5. Run:

```bash
git status --short
```

6. Continue from written progress, not from memory.

## Required end-of-session handoff

Before ending a session, update the workflow files and record:

- what was completed;
- what remains;
- changed files;
- locked files;
- commands run;
- tests/checks run;
- deferred checks;
- failures;
- quota/tool issues;
- scientific risks;
- next action.

Use `SESSION_HANDOFF_TEMPLATE.md`.

## Session naming

Use descriptive session names when the tool supports it:

```text
DATP-PKT-001-repo-map
DATP-PKT-002-pattern-ledger
DATP-PKT-003-artifacts-paths
DATP-final-hostile-review
```

## Session anti-patterns

- Do not keep a session alive because it “might remember something”. Written files are the source of truth.
- Do not allow one session to rewrite decisions made by another without updating the board and audit trail.
- Do not let multiple tools edit the same files at the same time.
- Do not use expensive models because the current session became messy. Start a clean cheap session first.
