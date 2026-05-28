# DATP AI Workflow

This folder controls the AI-assisted workflow for the DATP repository.

The workflow has one purpose:

> Keep the codebase, tests, tickets, results, and manuscript aligned with the DATP scientific contract while improving implementation quality.

Correctness means both:

1. Software correctness.
2. Scientific correctness.

Never optimize one by breaking the other.

---

## Repository Root

All workflow execution starts from:

```text
/home/naslouby/Projects/datp
```

Do not operate from another directory.

Do not infer missing files from memory.

Do not create placeholder files to satisfy a plan.

Inspect the actual repository before planning, editing, testing, or reporting.

---

## Active Scientific Context

DATP has two layers of context.

### Conference anchor

The submitted conference paper is the fixed scientific anchor for the original DATP identity:

```text
Blueprint.md
paper/DATP.tex
paper/sections/
paper/DATP.pdf
```

The conference identity is:

> Device-Aware Threshold Personalization is a controlled threshold-calibration study for non-IID federated IoT anomaly detection.

The core comparison is not a general FL-IDS benchmark.

The core comparison is not a model-personalization study.

The core comparison is not a poisoning, privacy, hardware, evasion, or concept-drift study.

### Journal-extension operational package

The active journal package is limited to:

```text
docs/journal/PRE_CODING_PLAN.md
docs/journal/CODING_PLAN.md
docs/journal/EXPERIMENT_PLAN.md
docs/journal/POST_EXPERIMENT_PLAN.md
```

`Journal/Journal_Extension_Master_Roadmap.md` is archived input context only.

If `Journal/Journal_Extension_Master_Roadmap.md` conflicts with the four active `docs/journal/` files, the four active files win.

Do not revive stale roadmap-only files.

Do not create old roadmap files that were explicitly merged into the four-file package.

Do not use archived labels when the active plan replaced them.

---

## Mandatory Scientific Lock Files

Before any non-trivial workflow execution, read:

```text
AI Workflow/SCIENTIFIC_DRIFT_LOCK.md
AI Workflow/WORKFLOW_AUDIT_PROTOCOL.md
AI Workflow/SCIENTIFIC_CONTRACT_AUDIT.md
```

These files are not optional notes.

They define the scientific guardrails for agents, code changes, tests, tickets, results, and paper updates.

If they conflict with actual code, current code is inspected first, but the conflict must be recorded and resolved through a ticket or documented blocker.

---

## Source-of-Truth Hierarchy

Use this order when sources disagree:

1. Actual repository code, tests, configs, commands, artifacts, and command output.
2. `docs/journal/PRE_CODING_PLAN.md`
3. `docs/journal/CODING_PLAN.md`
4. `docs/journal/EXPERIMENT_PLAN.md`
5. `docs/journal/POST_EXPERIMENT_PLAN.md`
6. `docs/tickets/ticket_progress.md`
7. `docs/tickets/ticket_inventory.md`
8. Individual tickets under `docs/tickets/`
9. Audit reports under `docs/tickets/audits/`
10. `AI Workflow/SCIENTIFIC_DRIFT_LOCK.md`
11. `AI Workflow/WORKFLOW_AUDIT_PROTOCOL.md`
12. `AI Workflow/SCIENTIFIC_CONTRACT_AUDIT.md`
13. Other files under `AI Workflow/`
14. `.claude/agents/`
15. `.claude/skills/`
16. `Journal/Journal_Extension_Master_Roadmap.md`
17. `paper/DATP.tex`
18. `paper/sections/*.tex`
19. `Blueprint.md`
20. `CLAUDE.md`
21. `AGENTS.md`

Documentation that says work is complete is not proof.

Actual implementation, tests, artifacts, and commands are proof.

---

## Locked DATP Identity

The workflow must preserve these facts unless the user explicitly changes the scientific scope:

1. DATP isolates threshold calibration scope.
2. The mainline encoder is fixed inside the controlled comparison.
3. The mainline aggregation protocol is fixed inside the controlled comparison.
4. B1, B2, B3, and B4 differ by threshold policy, not by retraining.
5. For a fixed dataset, regime, seed, and alpha, training is shared where the protocol requires it.
6. Threshold policies derive from stored score artifacts.
7. Downstream stages do not trigger upstream recomputation.
8. Regime A is confirmatory.
9. Regime B-a is a near-homogeneous boundary check.
10. Regime B-b is conditional on feasibility.
11. Regime C is a severity sweep, not the primary confirmatory claim.
12. Regime D is external validation if feasibility gates pass.
13. CV(FPR) is the primary FPR-equity metric.
14. Coverage ratio must accompany CV(FPR).
15. B0 is a centralized reference comparator, not part of the B1–B4 threshold-only causal ladder.
16. B5 or local-only variants must not enter the core claim unless explicitly scoped as supplementary.
17. FedProx, Ditto, FedRep-AE, FedPer-AE, Laridi-style, or other stress-test comparators must not be presented as part of the B1–B4 causal ladder.
18. `B-FedStatsBenign` is a benign-only comparator, not a numbered DATP baseline.
19. `B-LaridiFaithful` uses anomaly-labeled calibration information only when explicitly permitted and must be clearly outside DATP's benign-only assumption.
20. FedBN is rejected for the main journal cycle if it requires BatchNorm changes to the frozen encoder.

---

## Forbidden Scientific Drift

Agents must stop and report before making or preserving any change that causes:

1. Training per threshold baseline.
2. Score recomputation inside threshold analysis.
3. Hidden architecture changes in the controlled comparison.
4. Hidden aggregation changes in the controlled comparison.
5. New unsupported claims in code comments, docs, reports, tables, figures, captions, abstract, or conclusion.
6. Regime B or Regime C treated as confirmatory.
7. Stress-test comparators treated as core baselines.
8. B4 treated as a privacy method.
9. `B-FedStatsBenign` treated as faithful Laridi.
10. `FedRep-AE/FedPer-AE fallback` called Ditto when Ditto was not implemented faithfully.
11. Edge-IIoTset or CICIoT2023 B-b used without feasibility evidence.
12. Concept drift claimed from one-shot recalibration or chronological MVE unless the active plan explicitly permits that wording.
13. Privacy, poisoning, backdoor, evasion, deployment, communication-cost, or hardware claims without direct evidence.
14. New datasets added beyond the active plan.
15. Metrics reported without lineage.
16. Result tables or figures generated manually instead of from canonical artifacts.
17. Placeholder metrics, placeholder manifests, placeholder datasets, or success-shaped empty files.
18. Post-hoc protocol edits after seeing results.
19. Manuscript updates before result freeze.
20. Tickets marked `DONE` from documentation alone.

---

## Required Workflow Loop

For every substantive task, run this loop:

1. Inspect actual files.
2. Identify source-of-truth conflicts.
3. Check scientific lock.
4. Check relevant tickets and plans.
5. Implement or update only authorized scope.
6. Refactor touched and directly related code.
7. Update tests.
8. Run targeted checks.
9. Run quality gates.
10. Run scientific drift audit.
11. Run ticket-completion audit.
12. Update workflow state.
13. Repeat until PASS or documented blocker.

Do not stop after one repair pass.

Do not mark work complete because one tool passed.

Do not mark work complete if any scientific uncertainty remains unresolved.

---

## Mandatory Five-Pass Audit

Before any final handoff for a workflow task, perform the five-pass audit from:

```text
AI Workflow/WORKFLOW_AUDIT_PROTOCOL.md
```

The five passes are:

1. Source hierarchy and inventory audit.
2. Scientific invariant audit.
3. Code and architecture audit.
4. Tests, artifacts, and reproducibility audit.
5. Claims, paper, and documentation audit.

A task may not be marked `DONE` until every required pass has a clear verdict.

Allowed final verdicts:

```text
PASS
PASS_WITH_DOCUMENTED_NON_BLOCKING_LIMITATION
BLOCKED_HUMAN
BLOCKED_TECHNICAL
FAIL
```

Do not invent a PASS.

---

## Workflow State

Maintain state under:

```text
AI Workflow/state/
```

Required files:

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

A state entry is valid only if it records:

1. What was checked.
2. Exact command or inspection method.
3. Files covered.
4. Git working-tree context.
5. Timestamp.
6. Result.
7. Invalidation rule.
8. Follow-up action.

A state entry becomes stale if any referenced file, test, config, artifact, ticket, workflow file, scientific assumption, or import path changes.

Never trust stale state over current evidence.

---

## Ticket Rules

Tickets must be evidence-based.

Every ticket must include:

1. Problem.
2. Evidence.
3. Scientific impact.
4. Technical impact.
5. Files likely affected.
6. Required implementation.
7. Required refactor.
8. Required tests.
9. Required audit.
10. Acceptance criteria.
11. Blocking conditions.
12. Human intervention requirements, if any.

Do not create vague tickets.

Do not create duplicate tickets.

Do not split one scientific invariant across scattered tickets without a dependency chain.

Do not mark a ticket `DONE` unless the actual code, tests, artifacts, and audit evidence prove it.

---

## Agent Usage

Use `.claude/agents/` and `.claude/skills/` as role contracts when available.

Do not claim an agent was used unless the environment actually used it.

Parallel work is allowed only for disjoint file scopes.

Do not let multiple agents edit overlapping files.

When agents are unavailable, execute the same responsibilities manually.

---

## Tool Rules

Before relying on a tool, check whether it exists.

Record tool status in:

```text
AI Workflow/state/TOOL_STATUS.md
```

Do not claim Sonar, CodeScene, Semgrep, Refurb, Vulture, Graphify, Codex, Claude, Copilot, Antigravity, or any model-specific tool passed unless it actually ran.

If a tool is unavailable:

1. Record it.
2. Use the strongest available substitute.
3. Do not hide the missing tool.
4. Do not treat the substitute as identical to the missing tool.

---

## Clean-Code Rules

Every code change must check for:

1. Duplicate logic.
2. Duplicate literals.
3. Scattered constants.
4. Scattered enums.
5. Scattered schemas.
6. Hardcoded scientific parameters.
7. Long argument lists.
8. Untyped dictionaries.
9. Unclear ownership.
10. Dead code.
11. Backward-compatibility wrappers.
12. Redirect modules.
13. Alias-preservation tests.
14. Obsolete tests.
15. Hidden I/O.
16. Hidden recomputation.
17. Overgrown utilities.
18. Comments that explain around bad names instead of fixing names.
19. Test setup duplication.
20. Missing negative and boundary tests.

No wrappers or redirects are allowed for package moves unless the user explicitly asks for backward compatibility.

Treat the repo as greenfield during refactors while preserving scientific behavior.

---

## Output Standard

Every final handoff must report:

1. Scope completed.
2. Files inspected.
3. Files changed.
4. Files intentionally not changed.
5. Tests run.
6. Quality tools run.
7. Scientific drift verdict.
8. Ticket status changes.
9. Remaining blockers.
10. Next safe action.

Do not provide vague summaries.

Do not claim certainty without evidence.

Do not hide unresolved scientific risks.