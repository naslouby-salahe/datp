# DATP Full Validation, Implementation, Experiment, Audit, and Scientific Summary Loop

You are working on the DATP repository.

Your mission is to run, monitor, fix, implement, rerun, audit, summarize, and complete the full DATP validation and experiment workflow.

This prompt is idempotent. It may be reused if you stopped early, crashed, lost context, hit quota, or were interrupted. Every time you receive it, resume from the recorded state instead of restarting blindly.

Do not treat missing implementation as a final blocker unless it is genuinely impossible because of an external constraint such as unavailable real data, unavailable credentials, unavailable hardware, or a prohibited external service. If something is missing, broken, incomplete, or not wired, implement it correctly.

---

## 1. Core Mission

Complete the full workflow in this order:

1. Restore or prepare the environment.
2. Run all unit tests.
3. Fix or implement anything needed until unit tests pass.
4. Run all integration tests.
5. Fix or implement anything needed until integration tests pass.
6. Run all e2e tests.
7. Fix or implement anything needed until e2e tests pass.
8. Run the full test suite.
9. Run allowed quality checks.
10. Run gates.
11. Run diagnostics for Regimes A, B, C, and D.
12. Run Regime A.
13. Check status and audit Regime A.
14. Run Regime B.
15. Check status and audit Regime B.
16. Run Regime C.
17. Check status and audit Regime C.
18. Run Regime D.
19. Check status and audit Regime D.
20. Audit all results.
21. Build statistics.
22. Build tables.
23. Build figures/docs where applicable.
24. Read the paper, roadmap, journal planning docs, results, and audit artifacts.
25. Produce a final scientific summary explaining the results, warnings, blockers, and an experiment grade.

---

## 2. Non-Negotiable Rules

Work continuously until the workflow is complete or until there is a real external blocker that cannot be fixed from the repository.

Do not stop after the first failure.

Do not ask for confirmation unless a command is destructive.

Do not run Sonar.

Do not run CodeScene.

Do not run any command that requires SonarQube, Sonar tokens, CodeScene tokens, or external paid services.

Do not run:

```bash
make sonar-up
make sonar-health
make sonar-down
make codescene-check
```

Do not run `make quality-audit-local` blindly. Inspect the Makefile first. If it invokes Sonar, pysonar, CodeScene, `cs delta`, external tokens, or paid services, do not run it. Run the allowed internal checks individually instead.

Do not weaken tests, gates, diagnostics, metrics, scientific constants, seeds, regimes, baselines, dataset contracts, or reporting checks to make things pass.

Do not delete, skip, xfail, or silence failing tests unless the test is genuinely obsolete because the implementation contract correctly changed. If so, update the test to the new correct contract.

Do not introduce backward compatibility wrappers.

Do not add TODO placeholders.

Do not use broad `Any`, untyped `dict`, stringly typed regimes, stringly typed baselines, stringly typed datasets, or hardcoded scientific values.

Do not use mass-edit scripts to rewrite code. Use deliberate edits with repository-aware tools.

Do not hide warnings.

Do not declare success while warnings, aborted cells, missing outputs, failed audits, or scientific inconsistencies remain unresolved.

Temporary files for tracking are allowed only inside the persistent agent state directory defined below.

---

## 3. Missing Implementation Rule

If a command, target, diagnostic, regime, report, status check, table builder, or audit path is missing but is required by the repository docs, paper, journal plan, or Makefile conventions, implement it.

Examples:

1. If `make diagnostic-regime-d` is missing but Regime D exists in the docs/config/code, implement the Makefile target and underlying CLI wiring.
2. If `make run-regime-d` is missing but Regime D is part of the experiment plan, implement the command and status/audit integration.
3. If status does not report Regime D, implement status support.
4. If audit does not validate Regime D outputs, implement audit support.
5. If reporting ignores Regime D where it should be included, implement reporting support.
6. If tests are missing for new Regime D behavior, add them.
7. If a diagnostic fails because the implementation is incomplete, implement the missing code instead of marking the phase blocked.
8. If an output table or statistic is required by the paper or journal plan but missing, implement the builder or wire it into the existing reporting flow.
9. If a feature is partially implemented but not exposed through CLI/Makefile, complete the wiring.
10. If a documented regime/baseline/dataset is represented as loose strings, replace it with the correct enum or typed contract and adapt tests.

A blocker is allowed only when the root cause is external and cannot be fixed from the repository, for example:

1. Required real dataset files are absent and cannot be generated from existing fixtures.
2. Required raw data is too large or not present locally.
3. Required hardware is not available.
4. A command depends on a prohibited external service.
5. A documented experiment requires credentials or private data not available in the environment.

Even then, you must still implement all missing code paths, add tests, and record the external blocker precisely.

---

## 4. Persistent Run State

Before doing anything else, create or update:

```text
.agent_state/full_validation_run/
```

Inside it, maintain:

```text
.agent_state/full_validation_run/RUN_LEDGER.md
.agent_state/full_validation_run/COMMAND_HISTORY.tsv
.agent_state/full_validation_run/REMAINING_WORK.md
.agent_state/full_validation_run/FAILURES_AND_FIXES.md
.agent_state/full_validation_run/CURRENT_STATUS.md
.agent_state/full_validation_run/SCIENTIFIC_SUMMARY_DRAFT.md
.agent_state/full_validation_run/IMPLEMENTATION_GAPS.md
.agent_state/full_validation_run/WARNINGS_AND_BLOCKERS.md
.agent_state/full_validation_run/logs/
```

These files are the source of truth when this prompt is reused.

On every invocation, first read all existing files under:

```text
.agent_state/full_validation_run/
```

Then determine:

1. Which phases are already completed.
2. Which command was last running.
3. Whether the last command passed, failed, or was interrupted.
4. Which files changed after each successful phase.
5. Which commands must be rerun because source/config/test files changed.
6. Which commands remain.
7. Which implementation gaps were previously identified.
8. Which warnings or blockers remain unresolved.

Never assume a previous command succeeded unless the ledger contains:

```text
command
start time
end time
duration
exit code
log path
status
```

If a command was started but no exit code was recorded, mark it as:

```text
INTERRUPTED_OR_UNKNOWN
```

Then inspect the log, repository outputs, generated artifacts, and current status before resuming safely.

---

## 5. Command Logging Contract

For every command, record one row in:

```text
.agent_state/full_validation_run/COMMAND_HISTORY.tsv
```

Use these columns:

```text
run_id
phase
command
start_timestamp
end_timestamp
duration
exit_code
status
log_file
summary
fix_summary
```

Allowed statuses:

```text
PASSED
FAILED
INTERRUPTED_OR_UNKNOWN
SKIPPED_WITH_REASON
IMPLEMENTED_AND_RERUN
BLOCKED_EXTERNAL
```

Use `BLOCKED_EXTERNAL` only for real external blockers.

Every command must capture console output to a unique log file under:

```text
.agent_state/full_validation_run/logs/
```

Use readable log names, for example:

```text
001_setup_uv_sync.log
010_test_unit_attempt_1.log
020_test_integration_attempt_1.log
030_test_e2e_attempt_1.log
040_test_full_attempt_1.log
100_gate0_attempt_1.log
110_gate1_attempt_1.log
120_gate2_attempt_1.log
130_gate3_code_attempt_1.log
200_diagnostic_regime_a_attempt_1.log
210_diagnostic_regime_b_attempt_1.log
220_diagnostic_regime_c_attempt_1.log
230_diagnostic_regime_d_attempt_1.log
300_run_regime_a_attempt_1.log
310_run_regime_b_attempt_1.log
320_run_regime_c_attempt_1.log
330_run_regime_d_attempt_1.log
400_audit_results_attempt_1.log
500_build_stats_attempt_1.log
510_build_tables_attempt_1.log
520_build_figures_attempt_1.log
530_docs_attempt_1.log
```

After every meaningful step, update:

```text
RUN_LEDGER.md
CURRENT_STATUS.md
REMAINING_WORK.md
FAILURES_AND_FIXES.md
IMPLEMENTATION_GAPS.md
WARNINGS_AND_BLOCKERS.md
```

For long-running commands, monitor the console and log output. Do not leave commands running blindly.

When a command fails:

1. Read the console output.
2. Read the captured log.
3. Inspect generated repository logs, artifacts, status files, `ABORTED.txt`, and error traces.
4. Identify the root cause.
5. Decide whether it is a bug, missing implementation, missing wiring, missing test adaptation, missing data, or prohibited external dependency.
6. If it is a bug or missing implementation, fix or implement it.
7. Run the narrowest relevant verification command first.
8. Rerun the full failed phase command.
9. Record the failure, fix, implementation, and rerun result.

---

## 6. Resume Logic

When this prompt is reused, do not rerun expensive completed commands unless one of these conditions is true:

1. The previous run failed.
2. The previous run was interrupted.
3. The command has no recorded exit code.
4. The command log is missing.
5. Relevant source, config, test, dataset, Makefile, CLI, reporting, or audit files changed after the command passed.
6. A downstream phase failed in a way that invalidates upstream assumptions.
7. The command is cheap and useful for status or audit.

For expensive regime runs, first inspect:

```bash
make status
```

Also inspect existing outputs, audit artifacts, logs, and aborted markers.

Prefer repository-supported resume or rerun of missing/failed cells instead of deleting outputs or restarting full regimes.

Never delete outputs, scores, results, or artifacts unless the repository explicitly marks them as temporary and deletion is necessary to fix corruption.

---

## 7. Initial Repository and Documentation Read

Start with:

```bash
pwd
git status --short
make help
```

Then inspect these files if present:

```text
COMMANDS.md
commands.md
README.md
SETUP.md
Makefile
pyproject.toml
pyrightconfig.json
AGENTS.md
CLAUDE.md
Blueprint.md
DATP.pdf
paper/
Journal/
docs/journal/PRE_CODING_PLAN.md
docs/journal/CODING_PLAN.md
docs/journal/EXPERIMENT_PLAN.md
docs/journal/POST_EXPERIMENT_PLAN.md
Journal/Journal_Extension_Master_Roadmap.md
```

Important document precedence:

1. Active repository code and tests.
2. Active journal planning package:
   1. `docs/journal/PRE_CODING_PLAN.md`
   2. `docs/journal/CODING_PLAN.md`
   3. `docs/journal/EXPERIMENT_PLAN.md`
   4. `docs/journal/POST_EXPERIMENT_PLAN.md`
3. Current paper source or `DATP.pdf`.
4. `Blueprint.md`.
5. `Journal/Journal_Extension_Master_Roadmap.md` as archived input context only.

If the archived roadmap conflicts with the four active journal planning files, the four active planning files win.

Record the repository and document state in:

```text
CURRENT_STATUS.md
```

---

## 8. Setup Phase

Run:

```bash
uv sync --locked --extra test
```

Then activate the environment in every shell session:

```bash
source .venv/bin/activate
```

Then run:

```bash
make config-preview
```

If setup fails, fix dependency, environment, or configuration issues correctly.

Do not bypass the lockfile unless the repository itself documents a valid fallback and the lockfile path is genuinely blocked.

---

## 9. Phase 1: Unit Tests

Run:

```bash
make test-unit
```

If it fails:

1. Inspect failing tests and logs.
2. Fix implementation or tests correctly.
3. Implement missing code if the failure exposes an incomplete feature.
4. Run the narrowest failing test selection first if useful.
5. Rerun:

```bash
make test-unit
```

Do not proceed to integration tests until unit tests pass.

---

## 10. Phase 2: Integration Tests

Run:

```bash
make test-integration
```

If it fails:

1. Inspect logs and artifacts.
2. Fix root causes.
3. Implement missing integration paths where needed.
4. Rerun the narrowest relevant failing tests first if useful.
5. Rerun:

```bash
make test-integration
```

Do not proceed to e2e tests until integration tests pass.

---

## 11. Phase 3: E2E Tests

Run:

```bash
make test-e2e
```

If it fails:

1. Inspect logs, artifacts, temporary outputs, dataset paths, and generated files.
2. Fix root causes.
3. Implement missing end-to-end wiring where needed.
4. Rerun the narrowest relevant failing e2e path first if useful.
5. Rerun:

```bash
make test-e2e
```

Do not proceed to quality checks until e2e tests pass.

---

## 12. Phase 4: Full Test Confirmation

After unit, integration, and e2e tests all pass independently, run:

```bash
make test
```

If this fails despite the individual phases passing, inspect:

1. Test ordering.
2. Shared state.
3. Cleanup behavior.
4. Fixtures.
5. Environment leakage.
6. Parallelization issues.
7. Missing cleanup between real-data and fixture-data tests.

Fix the real cause.

Then rerun:

```bash
make test
```

---

## 13. Phase 5: Allowed Quality Audit

First run:

```bash
make quality-audit-tools-check
```

Then inspect the Makefile before running any broad local quality target.

Do not run any target that invokes Sonar, pysonar, CodeScene, `cs delta`, external tokens, or paid services.

Run the allowed internal checks:

```bash
make lint
make typecheck
```

If lint or typecheck fails:

1. Fix the code properly.
2. Do not add ignore comments as shortcuts.
3. Do not weaken typing.
4. Do not introduce `Any`.
5. Do not introduce untyped `dict`.
6. Do not convert enums to strings.
7. Do not add backward compatibility wrappers.
8. Rerun the failing quality command.
9. Then rerun all allowed quality commands.

---

## 14. Phase 6: Gates

Run gates explicitly in order:

```bash
make gate0
make gate1
make gate2
make gate3-code
```

After all individual gates pass, run the aggregate gate target if it is expected by the repository as final confirmation:

```bash
make gates
```

If any gate fails:

1. Inspect the gate output.
2. Inspect generated artifacts.
3. Inspect logs.
4. Identify whether this is a bug, missing implementation, bad config, missing data, or incomplete validation logic.
5. Fix or implement the root cause.
6. Rerun the failed gate.
7. Rerun all downstream gates.

Do not proceed to diagnostics until gates pass or until a real external data blocker is precisely recorded.

---

## 15. Phase 7: Diagnostics

Run diagnostics in this order:

```bash
make diagnostic-regime-a
make diagnostic-regime-b
make diagnostic-regime-c
```

Then handle Regime D.

Discover the correct supported command from the Makefile, README, CLI, docs, config files, and journal planning package.

Expected target:

```bash
make diagnostic-regime-d
```

If `diagnostic-regime-d` is missing but Regime D is documented or partially implemented, implement it.

Implementation must include, as applicable:

1. Makefile target.
2. CLI support.
3. Config loading.
4. Dataset enum support.
5. Regime enum support.
6. Diagnostic executor support.
7. Status integration.
8. Audit integration.
9. Tests.
10. Documentation update if needed.

Then run:

```bash
make diagnostic-regime-d
```

After each diagnostic command, run:

```bash
make status
```

Then inspect status output, logs, artifacts, and generated diagnostic files.

If a diagnostic fails:

1. Fix or implement the missing piece.
2. Rerun that diagnostic.
3. Rerun `make status`.
4. Do not proceed to the corresponding regime run until its diagnostic is clean or until a real external blocker is proven.

A real external blocker must still include:

1. Exact missing file/path/resource.
2. Exact command that exposed the issue.
3. Exact evidence from the log.
4. Whether the code path itself is implemented and tested.
5. What the user must provide to unblock the actual run.

---

## 16. Phase 8: Run Regimes

Run regimes in this exact order.

### 16.1 Regime A

Run:

```bash
make run-regime-a
```

After it completes:

```bash
make status
make audit-results
```

Inspect:

```text
completed counts
missing counts
aborted counts
invalid cells
ABORTED.txt files
result artifacts
score artifacts
audit outputs
```

Fix any aborted, missing, or invalid cells.

Use repository-supported partial resume if available.

Then rerun:

```bash
make status
make audit-results
```

Proceed only when Regime A is clean.

### 16.2 Regime B

Run:

```bash
make run-regime-b
```

After it completes:

```bash
make status
make audit-results
```

Fix, resume, rerun, and audit until clean.

Proceed only when Regime B is clean.

### 16.3 Regime C

Run:

```bash
make run-regime-c
```

After it completes:

```bash
make status
make audit-results
```

Fix, resume, rerun, and audit until clean.

Proceed only when Regime C is clean.

### 16.4 Regime D

Discover the correct supported command from the Makefile, README, CLI, docs, config files, and journal planning package.

Expected target:

```bash
make run-regime-d
```

If `run-regime-d` is missing but Regime D is documented or partially implemented, implement it.

Implementation must include, as applicable:

1. Makefile target.
2. CLI support.
3. Experiment executor support.
4. Regime enum support.
5. Dataset enum support.
6. Regime D config support.
7. Status tracking.
8. Audit tracking.
9. Result schema validation.
10. Reporting integration.
11. Tests.

Then run:

```bash
make run-regime-d
```

After it completes:

```bash
make status
make audit-results
```

Fix, resume, rerun, and audit until clean.

Only use `BLOCKED_EXTERNAL` if the Regime D code path is implemented and tested but the actual run cannot complete due to unavailable external real data, hardware, or prohibited service.

---

## 17. Phase 9: Final Result Audit

Run:

```bash
make status
make audit-results
```

Inspect:

```text
completed counts
missing counts
aborted counts
invalid result files
ABORTED.txt files
warnings
audit artifacts
```

If anything is missing, aborted, invalid, or suspicious:

1. Fix the cause.
2. Implement any missing audit/status/reporting logic.
3. Rerun only the required missing or failed work.
4. Rerun:

```bash
make status
make audit-results
```

Do not claim completion while status or audit still reports unresolved problems.

---

## 18. Phase 10: Build Stats, Tables, Figures, and Docs

Run:

```bash
make build-stats
make build-tables
```

If figures are expected by the repository/reporting flow and required score artifacts exist, run:

```bash
make build-figures
```

If the repository reporting contract expects all documentation artifacts together, run:

```bash
make docs
```

If reporting requires restored metrics in a clean checkout and results are absent, use:

```bash
make restore-metrics
```

Then rerun:

```bash
make build-stats
make build-tables
```

Inspect generated outputs under:

```text
outputs/analysis/
outputs/tables/
outputs/figures/
artifacts/audit/
```

Record produced files in:

```text
CURRENT_STATUS.md
```

If stats, tables, or figures fail because of missing schema fields, missing regimes, missing baselines, or unhandled Regime D outputs, implement the reporting logic correctly and rerun.

---

## 19. Scientific and Code Integrity Rules

Do not change scientific meaning to make commands pass.

Respect the fixed experimental contract.

Do not change seeds, baselines, regimes, threshold logic, dataset partitions, or metrics unless the code is demonstrably wrong and the fix preserves the documented scientific protocol.

Regimes, baselines, and datasets must use enums or typed contracts, not loose strings.

Avoid duplication.

Centralize constants.

Centralize paths.

Respect existing configuration files.

Do not add defaults to required inputs unless the existing project contract explicitly allows them.

Do not hide failures with broad exception handling.

Do not silently continue after corrupted artifacts.

Do not make tests less meaningful.

Do not add compatibility layers for obsolete behavior.

Do not use the archived roadmap to override the active planning files.

Do not call a local-head fallback “Ditto” unless the actual Ditto algorithm is implemented faithfully.

Do not present stress-test comparators as part of the B1–B4 causal ladder.

Do not present Regime B near-homogeneous results as strong heterogeneity evidence.

Do not suppress unfavorable results.

Do not suppress widened confidence intervals.

Do not suppress a null result.

---

## 20. Required Scientific Reading Before Final Summary

Before writing the final response, read and use:

```text
DATP.pdf
paper/
Blueprint.md
docs/journal/PRE_CODING_PLAN.md
docs/journal/CODING_PLAN.md
docs/journal/EXPERIMENT_PLAN.md
docs/journal/POST_EXPERIMENT_PLAN.md
Journal/Journal_Extension_Master_Roadmap.md
State_of_the_Art.md
outputs/analysis/
outputs/tables/
outputs/figures/
artifacts/audit/
make status output
make audit-results output
```

If `DATP.pdf` is not available, read the paper source under `paper/`.

If the paper source and `DATP.pdf` disagree, record the discrepancy.

If the archived roadmap and active planning docs disagree, the active planning docs win.

The final summary must explain the results scientifically, not only report that commands passed.

---

## 21. Final Scientific Summary Requirements

At the end, produce a concise but complete final report with these sections.

### 21.1 Execution Summary

Include:

```text
completed phases
failed commands
fixes implemented
commands rerun successfully
remaining external blockers, if any
final make status result
final make audit-results result
generated artifacts
```

### 21.2 Implementation Summary

Explain:

```text
files changed
features implemented
missing targets added
tests added or adapted
Regime D implementation status
status/audit/reporting integration changes
quality/type/lint fixes
```

### 21.3 Experiment Results Summary

Explain results by regime:

```text
Regime A
Regime B
Regime C
Regime D
```

For each regime, explain:

```text
dataset and partition meaning
completed cells
missing or aborted cells
main metric behavior
CV(FPR)
CV(TPR)
Macro-F1
worst-client balanced accuracy
coverage ratio if available
B1 vs B2 interpretation
B4 behavior if available
any failure modes
```

### 21.4 Claim Interpretation

Explain whether the results support, weaken, or invalidate the paper/journal claim.

Use this structure:

```text
Confirmatory claim status:
Supportive evidence:
External validation evidence:
Boundary-condition evidence:
Stress-test evidence:
Negative or null findings:
Claim wording that is still safe:
Claim wording that must be avoided:
```

The confirmatory focus is Regime A, B1 vs B2, CV(FPR), and bootstrap confidence interval where available.

Do not overclaim.

If Regime C shows the effect vanishes under IID or high alpha, state that as a boundary condition.

If Regime B is near-homogeneous, state that it is an applicability boundary, not strong heterogeneity evidence.

If Regime D is implemented and run, explain whether it strengthens external validity.

If Regime D cannot run because real data is missing, explain that the implementation exists but external validation is not yet empirically complete.

### 21.5 Experiment Grade

Give an experiment grade using this scale:

```text
A: All tests, quality checks, gates, diagnostics, regimes, audits, stats, tables, and docs pass; confirmatory result is statistically and scientifically coherent; no unresolved scientific warnings.
B: Core workflow passes and main claim is supported, but there are moderate warnings such as external validation limits, widened CI, partial Regime D/data issues, or stress-test limitations.
C: Code workflow mostly passes, but scientific evidence is incomplete or claim must be narrowed substantially.
D: Major tests, gates, diagnostics, or result audits remain unresolved, or key regimes are missing.
F: Workflow cannot produce trustworthy results, or scientific conclusions would be invalid.
```

The grade must include a short justification.

Do not give an optimistic grade if there are unresolved warnings or external blockers.

### 21.6 Warnings and Blockers

Separate warnings from blockers.

Use:

```text
Warnings:
Blockers:
Not blockers:
```

A warning is a concern that affects interpretation but does not prevent completion.

A blocker is something that prevents a required run, audit, or claim from being completed.

Examples of warnings:

```text
CI widened
Regime B is near-homogeneous
B4 underperforms
P10 Macro-F1 drops
Regime D external validity is limited
stress-test comparator absorbs threshold effect
coverage ratio is low
```

Examples of blockers:

```text
required dataset files missing
required Regime D raw data absent
audit cannot validate result schema
status reports aborted cells
tables cannot be built
confirmatory results missing
```

### 21.7 Final Remaining Work

End with one of:

```text
Remaining work: NONE
```

or:

```text
Remaining work:
1. ...
2. ...
3. ...
```

Only list real remaining work.

Do not list vague suggestions.

---

## 22. Completion Criteria

You are done only when all applicable items are true:

1. Setup completed.
2. Unit tests pass.
3. Integration tests pass.
4. E2E tests pass.
5. Full test suite passes.
6. Allowed quality checks pass.
7. All gates pass.
8. Diagnostics pass for Regimes A, B, C, and D, unless D has a genuine external data blocker after implementation.
9. Regime A is complete and clean.
10. Regime B is complete and clean.
11. Regime C is complete and clean.
12. Regime D is complete and clean, unless D has a genuine external data blocker after implementation.
13. `make status` reports no unresolved missing or aborted work for supported regimes.
14. `make audit-results` passes cleanly for completed results.
15. Stats are built.
16. Tables are built.
17. Figures/docs are built if required by the repository reporting contract.
18. Missing Makefile/CLI/status/audit/reporting support has been implemented, not merely recorded.
19. `RUN_LEDGER.md` is fully updated.
20. `COMMAND_HISTORY.tsv` is fully updated.
21. `REMAINING_WORK.md` clearly says `NONE` or lists only real external blockers with evidence.
22. `FAILURES_AND_FIXES.md` records every failure and fix.
23. `IMPLEMENTATION_GAPS.md` records every missing piece found and how it was implemented.
24. `WARNINGS_AND_BLOCKERS.md` separates warnings from blockers.
25. `CURRENT_STATUS.md` reflects the final repository and artifact state.
26. `SCIENTIFIC_SUMMARY_DRAFT.md` contains the final scientific interpretation.

---

## 23. Final Response Required

At the end, provide the final response in this structure:

```text
Execution Summary
Implementation Summary
Experiment Results Summary
Claim Interpretation
Experiment Grade
Warnings and Blockers
Generated Artifacts
Remaining Work
```

Do not provide a vague success message.

Only claim success when the ledger, logs, status, audit, generated artifacts, and scientific summary prove it.