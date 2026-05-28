# DATP Workflow Audit Protocol

This file defines the mandatory audit loop for DATP AI workflow tasks.

Every substantial task must be audited in at least five passes before it can be marked complete.

The audit is not a formality.

The audit is the mechanism that protects scientific validity while code, tests, tickets, and manuscript artifacts evolve.

---

## 1. Applicability

Use this protocol for:

1. Code changes.
2. Test changes.
3. Config changes.
4. Dataset preparation changes.
5. Experiment-runner changes.
6. Threshold-analysis changes.
7. Result-generation changes.
8. Reporting changes.
9. Paper or LaTeX changes.
10. Ticket generation.
11. Ticket completion.
12. Agent or workflow changes.
13. Refactoring.
14. Package moves.
15. Output artifact changes.
16. Any task touching DATP scientific scope.

For trivial typo-only changes, record why this protocol is not required.

---

## 2. Audit Verdicts

Allowed verdicts:

| Verdict | Meaning |
|---|---|
| `PASS` | No blocking issue remains. |
| `PASS_WITH_DOCUMENTED_NON_BLOCKING_LIMITATION` | Remaining limitation is documented, scoped, and does not invalidate the task. |
| `REAUDIT_REQUIRED` | Work may be correct, but structural or scientific scope changed enough that another audit must run later. |
| `BLOCKED_HUMAN` | User action, dataset placement, credential, decision, or manual review is required. |
| `BLOCKED_TECHNICAL` | Tool, environment, dependency, or infrastructure issue prevents completion. |
| `BLOCKED_SCIENTIFIC` | Scope, claim, protocol, or evidence ambiguity prevents safe completion. |
| `FAIL` | A blocking issue exists and must be fixed before completion. |

Forbidden verdicts:

```text
mostly done
probably okay
looks good
seems fine
should pass
not checked but assumed
```

---

## 3. Required Evidence

Each audit pass must record:

1. Files inspected.
2. Commands run, if any.
3. Tool availability limitations.
4. Evidence found.
5. Problems found.
6. Fixes applied or tickets created.
7. Residual risk.
8. Verdict.
9. Invalidation rule.

Do not cite memory alone as evidence.

Do not cite stale reports alone as evidence.

Do not cite a ticket status alone as evidence.

---

## 4. Pass 1 — Source Hierarchy and Inventory Audit

Goal:

> Prove the agent is working from actual repository reality and the correct source hierarchy.

Required checks:

1. Confirm repository root.
2. Inspect `git status --short`.
3. Inspect relevant files directly.
4. Confirm whether referenced files exist.
5. Confirm active `docs/journal/` package exists.
6. Confirm roadmap-only files are not revived.
7. Confirm ticket inventory and progress are read.
8. Confirm workflow state files are read or created.
9. Confirm no missing file is hallucinated.
10. Confirm no stale path is treated as current.

Required source hierarchy check:

1. Actual code and artifacts.
2. Active `docs/journal/` package.
3. Tickets.
4. Audit reports.
5. Workflow files.
6. Agents and skills.
7. Archived roadmap.
8. Conference paper and blueprint.

Pass fails if:

1. Work starts from memory.
2. A nonexistent file is used as proof.
3. Archived roadmap content overrides active journal files.
4. A ticket is trusted without code evidence.
5. A missing tool is claimed as available.
6. A file path is guessed.

Output fields:

```text
Pass 1 verdict:
Files inspected:
Commands run:
Missing files:
Source conflicts:
Resolution:
Invalidation rule:
```

---

## 5. Pass 2 — Scientific Invariant Audit

Goal:

> Prove the change preserves DATP's scientific identity.

Required checks:

1. B1 semantics unchanged.
2. B2 semantics unchanged.
3. B3 semantics unchanged.
4. B4 semantics unchanged.
5. B0 remains reference only.
6. `B-FedStatsBenign` remains a benign-only comparator.
7. `B-LaridiFaithful` is not conflated with benign-only DATP.
8. FedProx and personalization comparators remain stress tests.
9. Regime A remains confirmatory.
10. Regime B-a remains a boundary condition.
11. Regime B-b remains conditional.
12. Regime C remains supportive/exploratory severity evidence.
13. Regime D remains conditional external validation.
14. Threshold-scope-only ladder remains isolated.
15. Shared-training requirement remains intact.
16. Stage boundaries remain intact.
17. Config-driven scientific parameters remain intact.
18. Calibration-pending logic remains intact.
19. Coverage ratio remains paired with CV(FPR).
20. No forbidden claim appears in comments, docs, tests, reports, tables, or manuscript text.

Pass fails if:

1. Training becomes baseline-specific inside B1–B4.
2. Threshold analysis calls training.
3. A downstream module recomputes upstream artifacts.
4. A stress test is treated as a core baseline.
5. Dataset partition semantics are overstated.
6. A claim exceeds evidence.
7. Any forbidden scope is introduced silently.

Output fields:

```text
Pass 2 verdict:
Scientific invariants checked:
Files inspected:
Drift found:
Fixes required:
Claims affected:
Invalidation rule:
```

---

## 6. Pass 3 — Code and Architecture Audit

Goal:

> Prove implementation quality improved without creating wrappers, redirects, duplication, or hidden scientific behavior.

Required checks:

1. Module ownership is clear.
2. Constants are centralized.
3. Enums are centralized.
4. Schemas or typed objects are used for structured payloads.
5. Scientific parameters come from config.
6. Artifact paths use canonical builders.
7. Metric keys use canonical owners.
8. No duplicate logic remains in touched scope.
9. No duplicate literals remain in touched scope.
10. No dead compatibility wrappers remain.
11. No redirect modules remain.
12. No alias-preservation code remains.
13. No overgrown utility module was created.
14. No hidden I/O was added inside pure computation.
15. No hidden computation was added inside reporting.
16. Long argument lists are replaced with typed objects where appropriate.
17. Complex functions are decomposed by domain responsibility.
18. Tests are not used to preserve obsolete paths.
19. No comments are used to excuse unclear names.
20. Static analysis findings are fixed or documented with evidence.

Suggested tools when available:

```text
python -m ruff check src/datp tests
python -m pyright
python -m pytest --collect-only tests
vulture src/datp tests
refurb src/datp tests
semgrep scan
```

Use only tools that exist.

Do not claim a tool passed if it did not run.

Pass fails if:

1. A wrapper or redirect is added without explicit user approval.
2. Duplicate patterns remain in the touched scope.
3. Hardcoded scientific parameters remain.
4. Static findings are ignored.
5. Code is shorter but less clear.
6. Refactoring changes scientific behavior silently.

Output fields:

```text
Pass 3 verdict:
Code files inspected:
Architecture issues:
Quality tools run:
Findings fixed:
Findings deferred:
Invalidation rule:
```

---

## 7. Pass 4 — Tests, Artifacts, and Reproducibility Audit

Goal:

> Prove behavior is tested and artifacts remain reproducible.

Required checks:

1. Existing tests were inspected before adding new tests.
2. Impacted tests were updated.
3. Obsolete tests were removed instead of preserved by wrappers.
4. New behavior has positive, negative, boundary, and missing-artifact tests where relevant.
5. Determinism-sensitive code uses explicit seeds.
6. CUDA behavior is not skipped silently when CUDA is required.
7. Test imports use canonical production paths.
8. Test structure matches current production ownership.
9. Full e2e is not run unnecessarily when targeted tests are enough.
10. Long e2e tests are only run when impacted or explicitly required.
11. Result files are non-empty.
12. Temporary files do not count as results.
13. `metrics.json` is atomic-written only on success.
14. Score manifests exist where required.
15. Resolved configs exist where required.
16. Artifact lineage is complete for reported results.
17. Skip/resume markers are interpreted correctly.
18. `ABORTED.txt` is written on unclean exits where the runner owns that behavior.
19. No placeholder manifests, placeholder metrics, or placeholder datasets exist.
20. Result reuse is verified before stored-score analysis.

Suggested commands when relevant:

```text
python -m pytest --collect-only tests
python -m pytest tests/unit/<impacted-area>
python -m pytest tests/integration/<impacted-area>
python -m ruff check src/datp tests
python -m pyright
```

Pass fails if:

1. Tests pass by preserving old wrappers.
2. Tests skip required behavior without reason.
3. Metrics are generated without lineage.
4. Result files are empty.
5. Artifacts contradict configs.
6. A reported result cannot be reproduced from canonical artifacts.

Output fields:

```text
Pass 4 verdict:
Tests inspected:
Tests run:
Artifacts inspected:
Lineage status:
Missing coverage:
Invalidation rule:
```

---

## 8. Pass 5 — Claims, Paper, and Documentation Audit

Goal:

> Prove the written narrative is narrower than the evidence.

Required checks:

1. Abstract does not overclaim.
2. Conclusion does not overclaim.
3. Figure captions match visuals.
4. Table titles match contents.
5. Results text matches metrics.
6. Limitations include scope boundaries.
7. Regime statuses are correctly labeled.
8. Stress tests are not core causal evidence.
9. B0 and B5 are scoped correctly.
10. B4 is not framed as privacy.
11. `B-FedStatsBenign` is not called Laridi faithful.
12. Ditto fallback is labeled honestly.
13. FedBN rejection is preserved unless the active plan changes.
14. Edge-IIoTset claims are conditional on feasibility/results.
15. CICIoT2023 B-b claims are conditional on feasibility/results.
16. Temporal experiment claims do not become concept-drift claims.
17. Privacy wording remains bounded.
18. Hardware/deployment wording remains bounded.
19. Conference-to-journal overlap is disclosed where required.
20. Citation-critical statements are source-verified.

Pass fails if:

1. The paper claims unsupported superiority.
2. The journal extension hides failed or null outcomes.
3. A reviewer could reasonably say the controlled variable is no longer isolated.
4. A claim is based on archived roadmap context instead of active evidence.
5. A table, figure, or claim lacks backing artifacts.

Output fields:

```text
Pass 5 verdict:
Documents inspected:
Claims checked:
Overclaims found:
Fixes required:
Remaining limitations:
Invalidation rule:
```

---

## 9. Cross-Pass Final Gate

Final status is the strictest blocking verdict across all five passes.

Rules:

1. Any `FAIL` means final `FAIL`.
2. Any `BLOCKED_HUMAN` means final `BLOCKED_HUMAN`.
3. Any `BLOCKED_TECHNICAL` means final `BLOCKED_TECHNICAL`.
4. Any `BLOCKED_SCIENTIFIC` means final `BLOCKED_SCIENTIFIC`.
5. Any unresolved `REAUDIT_REQUIRED` means final `REAUDIT_REQUIRED`.
6. `PASS_WITH_DOCUMENTED_NON_BLOCKING_LIMITATION` is allowed only if the limitation does not affect the task's acceptance criteria.
7. `PASS` is allowed only when all five passes pass.

---

## 10. Final Audit Report Template

Use this template in final handoffs:

```text
# Final Audit Report

Task:
Scope:
Git status before:
Git status after:

## Pass 1 — Source hierarchy and inventory
Verdict:
Evidence:
Issues:
Resolution:

## Pass 2 — Scientific invariants
Verdict:
Evidence:
Issues:
Resolution:

## Pass 3 — Code and architecture
Verdict:
Evidence:
Issues:
Resolution:

## Pass 4 — Tests, artifacts, reproducibility
Verdict:
Evidence:
Issues:
Resolution:

## Pass 5 — Claims, paper, documentation
Verdict:
Evidence:
Issues:
Resolution:

## Final verdict
Verdict:
Files changed:
Tests run:
Tools run:
Tickets updated:
State updated:
Remaining blockers:
Next safe action:
```

Do not shorten this template when the task touches scientific scope.

---

## 11. Invalidation Rules

An audit becomes stale if any of these change after the audit:

1. Code under `src/datp/`.
2. Tests under `tests/`.
3. Configs under `src/datp/conf/`.
4. Data preparation code.
5. Baseline or comparator code.
6. Threshold code.
7. Training code.
8. Reporting code.
9. Result artifacts.
10. Figure/table sidecars.
11. Journal planning files.
12. Tickets.
13. Workflow files.
14. Agents or skills.
15. Package structure.
16. Import paths.
17. Scientific assumptions.
18. Dataset availability.
19. Tool availability.
20. User scope decision.

When invalidated, rerun the relevant audit passes.

Do not reuse stale PASS verdicts.