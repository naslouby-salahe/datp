# CLAUDE.md

## Purpose

This file is the non-negotiable execution contract for the DATP journal-extension work.

Every agent must follow this file before reading task-specific instructions.

## Active Planning Sources

The active planning package is limited to:

1. `docs/journal/PRE_CODING_PLAN.md`
2. `docs/journal/CODING_PLAN.md`
3. `docs/journal/EXPERIMENT_PLAN.md`
4. `docs/journal/POST_EXPERIMENT_PLAN.md`

`Journal/Journal_Extension_Master_Roadmap.md` is archived context only.

If archive material conflicts with the four active planning files, the four active files win.

Do not create extra planning files unless explicitly requested.

## Scientific Scope

DATP is a controlled study of threshold calibration scope under fixed federated representation learning.

The scientific variable is threshold calibration.

The following must remain fixed unless the active planning files explicitly authorize otherwise:

1. Autoencoder architecture
2. FedAvg training setup
3. Dataset definitions
4. Regime definitions
5. Splits
6. Seeds
7. Shared score artifacts
8. Evaluation protocol

## Baseline Discipline

Main controlled baselines:

1. B1: shared/global threshold
2. B2: per-client threshold
3. B3: family/group threshold
4. B4: fingerprint-cluster threshold

Reference or restricted baselines:

1. B0: centralized reference comparator only
2. B5: local-only ablation, not a core claim baseline
3. FedRep-AE or FedPer-AE fallback only if explicitly required and correctly implemented

Do not invent new baselines.

Do not rename baselines casually.

Do not promote B5 into the abstract, core claim, or main figure captions.

## Stage Boundaries

The pipeline stages are:

1. prepare
2. score
3. threshold/result
4. report

A downstream stage must not silently recompute upstream artifacts.

Thresholding must not retrain.

Reporting must not recompute scores.

Evaluation must read canonical score and result artifacts.

## Shared-Training Rule

For a fixed dataset, regime, seed, and alpha when applicable:

1. Train the FL encoder once.
2. Save shared checkpoints and scores.
3. Derive B1, B2, B3, and B4 from the same score artifacts.
4. Never retrain per threshold baseline inside the same fixed cell.

This rule is mandatory.

## Implementation Quality Rules

Every implementation must include a refactoring pass.

Before adding new code, always ask:

1. Does this already exist?
2. Should this be an enum?
3. Should this be a constant?
4. Should this be a config value?
5. Should this be a schema or typed object?
6. Can existing logic be reused?
7. Can duplicated logic be removed?
8. Can this be expressed with fewer, clearer lines?
9. Can this be made easier to test?
10. Can this be made impossible to misuse?

Do not create random helper functions, constants, enums, paths, schemas, or classes without checking the existing code first.

Prefer:

1. Enums over loose strings
2. Constants over repeated literals
3. Schemas over unstructured dictionaries
4. Typed objects over argument-heavy functions
5. Shared utilities over duplicated local logic
6. Config-driven behavior over hardcoded scientific parameters
7. Clear small functions over dense procedural blocks
8. Existing canonical modules over new parallel modules

## Greenfield Rule

Implement as greenfield by default.

Do not preserve backward compatibility just because old code exists.

Backward compatibility is required only for:

1. Scientific invariants
2. Canonical artifact paths
3. Valid existing result formats when still scientifically active
4. Active documentation contracts
5. Public commands still required by the active plans

Dead code, obsolete tests, stale compatibility wrappers, and outdated interfaces should be removed when they conflict with clean design.

## Comment Discipline

Minimize comments.

Use comments only when they explain a non-obvious scientific or operational constraint.

Do not add comments that merely repeat the code.

Prefer clearer names, enums, schemas, and smaller functions instead of explanatory comments.

## Testing Discipline

Every implementation task must include test impact analysis.

Before adding new tests, check existing tests.

Prefer adapting existing tests when they already cover the behavior.

Add new tests only when existing tests cannot cleanly cover the scenario.

Delete or rewrite tests that validate obsolete behavior.

Tests must cover:

1. Normal cases
2. Boundary cases
3. Failure cases
4. Weird cases
5. Missing artifacts
6. Empty artifacts
7. Invalid configs
8. Invalid regimes
9. Invalid baselines
10. Scientific-invariant violations

The goal is to catch experiment-breaking issues before real experiments run.

## Test Execution Discipline

Do not run the full test suite after every small edit.

For large or breaking work:

1. Make all planned code changes first.
2. Update tests after the implementation stabilizes.
3. Run targeted tests during development only when useful.
4. Run the full required suite at the end.
5. If tests fail, fix the issue and rerun the relevant failing tests.
6. Rerun the full required suite only after targeted failures are fixed.

Test runs must be practical, not wasteful.

## Ticket System

Large implementation work must be organized under `docs/tickets/`.

The ticket system contains:

1. `docs/tickets/T01.md`
2. `docs/tickets/T02.md`
3. Sequential ticket files as needed
4. `docs/tickets/ticket_inventory.md`
5. `docs/tickets/ticket_progress.md`
6. `docs/tickets/human_interventions.md`

Ticket generation is performed by `ticket-planner-agent`.

The ticket planner must read the four active journal plans and the actual codebase before creating tickets.

Tickets must not be generated from documentation alone.

Every ticket must include:

1. Source plan references
2. Existing code to inspect first
3. Existing tests to inspect first
4. Files likely touched
5. Refactoring requirements
6. Schema, enum, constant, and config checks
7. Test requirements
8. Human-intervention status
9. Dependencies
10. Previous-ticket check
11. Acceptance criteria
12. Stop conditions

Before starting any ticket, the executing agent must check `docs/tickets/ticket_progress.md`.

If any previous ticket is incomplete and not correctly blocked or skipped with reason, the agent must stop and return to that previous ticket first.

## Human-Blocked Work

If a ticket requires user action, it must be marked `BLOCKED_HUMAN`.

Examples include:

1. Downloading Edge-IIoTset
2. Providing raw CICIoT2023 CSV files
3. Placing a dataset in the correct directory
4. Supplying unavailable files
5. Confirming a scientific decision not already locked
6. Approving scope changes

Human-blocked tickets must be listed in `docs/tickets/human_interventions.md`.

Even if the user asks to implement, agents must not bypass a human-blocked requirement.

The correct action is to state what the user must do, where to place it, and which ticket becomes unblocked afterward.

## Ticket Completion Audits

Completed tickets must be auditable.

When auditing a ticket, the auditor must check:

1. The ticket file
2. `docs/tickets/ticket_inventory.md`
3. `docs/tickets/ticket_progress.md`
4. `docs/tickets/human_interventions.md`
5. Relevant source code
6. Relevant tests
7. Relevant configs
8. Relevant artifacts and logs when applicable

A ticket is complete only if:

1. Its implementation requirements are satisfied.
2. Its refactoring requirements are satisfied.
3. Existing code was reused where appropriate.
4. Enums, constants, schemas, typed objects, and configs were checked.
5. Tests were added, adapted, or deleted correctly.
6. Required commands were run or correctly skipped.
7. Human-blocked work was not bypassed.
8. Scientific invariants were preserved.
9. Acceptance criteria are satisfied.
10. Progress files are accurate.

The correct agent for this work is `ticket-completion-auditor-agent`.

If the audit fails, create or recommend a repair ticket instead of pretending the ticket is done.

## Repair Tickets

After the main ticket set is complete, the ticket system is no longer mandatory for every small action.

However, new repair tickets may be created when:

1. An experiment fails.
2. A result audit finds invalid artifacts.
3. A reviewer audit finds a methodological hole.
4. Drift is detected.
5. A human intervention unlocks new work.
6. A ticket completion audit fails.

Repair tickets use the next available ticket number and must be added to:

1. `docs/tickets/ticket_inventory.md`
2. `docs/tickets/ticket_progress.md`

If human action is required, also update:

1. `docs/tickets/human_interventions.md`

## Experiment Discipline

Do not start experiments before the required gates are satisfied.

Do not run expensive experiments to discover bugs that unit or integration tests should have caught.

Before experiments:

1. Validate configs.
2. Validate dataset paths.
3. Validate schema assumptions.
4. Validate artifact paths.
5. Validate seeds.
6. Validate GPU or CPU expectations.
7. Validate result overwrite and resume behavior.
8. Validate logs and failure markers.

## Long-Running Commands

Long-running commands must be monitored.

The running agent must maintain a progress record containing:

1. Command executed
2. Start time
3. Current stage
4. Completed cells
5. Failed cells
6. Retried cells
7. Last checked log
8. Current risk
9. Next action

If a command fails, inspect logs, identify the root cause, fix it if safe, and rerun only the necessary command.

If the failure indicates a scientific, architectural, dataset, artifact, or planning issue, stop and write a precise repair ticket instead of guessing.

## Artifact Rules

Use canonical artifact paths.

Do not scatter outputs.

Do not treat empty files, temporary files, or partial files as complete results.

Result existence requires valid non-empty expected files.

Atomic writes should use temporary files and final rename where appropriate.

Do not create success-shaped placeholder artifacts.

## Claim Discipline

Do not overclaim.

Allowed claims must match actual evidence.

Do not claim:

1. Poisoning robustness
2. Backdoor robustness
3. Evasion robustness
4. Formal differential privacy
5. Secure aggregation guarantees
6. Real hardware deployment readiness
7. Concept drift handling
8. Zero-day detection

unless those claims are directly tested and approved by the active plans.

## Documentation Discipline

Do not create extra planning files unless explicitly requested.

Keep the active journal planning package limited to the four files in `docs/journal`.

When implementation changes behavior, update the relevant existing documentation only if it is still active and required.

## Done Definition

A task is done only when:

1. The requested behavior is implemented.
2. Required refactoring is complete.
3. Existing code reuse has been checked.
4. Enums, constants, schemas, and configs have been checked.
5. Required tests are added, adapted, or deleted.
6. Required targeted tests pass.
7. Full required validation is run when the task is breaking.
8. Artifacts are valid if artifacts are produced.
9. Ticket progress is updated if the task came from a ticket.
10. No scientific drift remains.

A ticket is not truly done until it can pass `ticket-completion-auditor-agent`.

## Mandatory Quality Gate

No ticket, repair, or refactor may be accepted until the code quality gate passes.

The quality gate must inspect changed files and related existing files.

### Canonical commands

The repo provides real, callable tooling. Use these — do not invent substitutes.

| Concern | Canonical command |
|---------|-------------------|
| All tools callable? | `make quality-audit-tools-check` |
| Full local audit (ruff, pyright, pytest+coverage, pysonar, cs delta) | `make quality-audit-local` |
| Start local SonarQube Community Build (Docker) | `make sonar-up` |
| SonarQube health probe | `make sonar-health` |
| Stop SonarQube (data preserved) | `make sonar-down` |
| CodeScene delta on current changes | `make codescene-check` |
| Ruff lint (existing target) | `make lint` |
| Pyright (existing target) | `make typecheck` |

Configuration files:
- `sonar-project.properties` — Sonar scope, exclusions, coverage path.
- `docker-compose.sonarqube.yml` — local Sonar Community Build (`http://localhost:9000`, named volumes).
- `pyproject.toml` `[project.optional-dependencies].quality` — coverage, pytest-cov, pysonar, ruff, pyright, pytest.
- `.env.local` (gitignored, mode 600) — `SONAR_HOST_URL`, `SONAR_TOKEN`, `CS_ACCESS_TOKEN`.
- `.env.example` — placeholder template.
- `scripts/quality/load_env.sh` — sourced by every quality script; never echoes tokens.
- `docs/quality/QUALITY_TOOLS.md` — full reference.

Secret discipline: tokens live only in `.env.local`. Never hardcode, log, print, or paste tokens. Never commit `.env.local`.

If `make quality-audit-tools-check` fails, fix the tooling before claiming any quality work is complete.

Blocking issues include:

1. Pylance errors.
2. Pyright errors.
3. SonarLint issues.
4. SonarQube issues.
5. CodeScene complexity smells.
6. Test failures.
7. Coverage gaps.
8. Dead code.
9. Duplicate code.
10. Duplicate literals.
11. Scattered constants.
12. Scattered enums.
13. Scattered config.
14. Scattered schemas.
15. Hardcoded scientific values.
16. Long methods.
17. Complex methods.
18. Long argument lists.
19. Unclear names.
20. Wrong utility ownership.
21. Wrong object boundaries.
22. Misplaced scripts.
23. Invalid default values in input/config models.

A ticket is DONE only after:

1. Implementation passes.
2. Refactor passes.
3. Tests pass.
4. Code quality gate passes.
5. Ticket completion audit passes.
6. Drift check passes when applicable.
7. Ticket progress is updated.

Diagnostic suppression is forbidden unless the issue is a documented false positive and the suppression is narrow.