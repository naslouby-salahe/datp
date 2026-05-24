# Static Analysis Quality Gate Skill

## Purpose

This skill defines the mandatory static-analysis and clean-code gate for DATP.

Use this skill after every implementation, repair, refactor, ticket audit, and ticket completion check.

## Non-Negotiable Rule

No ticket, repair, or refactor is complete while any blocking diagnostic remains in the affected code surface.

The affected code surface includes changed files and related existing files.

## Canonical Commands

The repo provides real, callable tooling. Use these — do not invent substitutes and do not perform a manual review in place of running a tool.

| Tool | Command |
|------|---------|
| Verify every tool installed | `make quality-audit-tools-check` |
| Full local audit (ruff + ruff format + pyright + pytest+coverage + pysonar + cs delta) | `make quality-audit-local` |
| Ruff lint only | `.venv/bin/ruff check src/datp tests` |
| Ruff format check | `.venv/bin/ruff format --check src/datp tests` |
| Pyright | `.venv/bin/pyright` (config in `pyrightconfig.json`) |
| Pytest + coverage XML | `.venv/bin/pytest --cov=src/datp --cov-report=xml:coverage.xml --cov-report=term-missing` |
| SonarQube up / down / health | `make sonar-up` / `make sonar-down` / `make sonar-health` |
| pysonar scan (uploads to local SonarQube) | `.venv/bin/pysonar -Dsonar.host.url=$SONAR_HOST_URL -Dsonar.token=$SONAR_TOKEN` |
| CodeScene delta | `make codescene-check` (uses `cs delta --output-format json --pretty`) |

Coverage XML must land at `coverage.xml` (repo root). `sonar-project.properties` reads from `sonar.python.coverage.reportPaths=coverage.xml`.

Secrets (`SONAR_TOKEN`, `CS_ACCESS_TOKEN`) live only in `.env.local`. `scripts/quality/load_env.sh` sources them. Never echo or log token values.

See `docs/quality/QUALITY_TOOLS.md` for the full reference.

## Blocking Diagnostic Sources

Treat these as blocking when they affect production code, tests, scripts, configs, or documentation-generated code:

1. Pylance.
2. Pyright.
3. SonarLint.
4. SonarQube.
5. CodeScene.
6. Ruff.
7. Flake8.
8. Pylint.
9. MyPy.
10. Pytest.
11. Coverage.
12. Project-specific invariant checks.

If a configured tool cannot be run, perform a source-level audit and record the tool as unavailable. Do not claim a clean automated pass.

## Required Static Rules

The affected surface must have:

1. No unresolved call signature errors.
2. No missing required arguments.
3. No invalid keyword arguments.
4. No unused imports.
5. No unused variables.
6. No unused local assignments.
7. No unreachable code.
8. No side-effect-free statements.
9. No direct equality checks on floats.
10. No duplicated literals that should be constants.
11. No duplicated code blocks.
12. No needless nested conditional expressions.
13. No cognitive complexity above the configured threshold.
14. No large methods where extraction is reasonable.
15. No deep nesting where guard clauses or helpers are possible.
16. No long argument lists where typed objects are appropriate.
17. No vague names.
18. No dead compatibility wrappers.
19. No hardcoded scientific parameters.
20. No hardcoded artifact path fragments.
21. No hardcoded metric keys.
22. No repeated baseline, regime, stage, status, or artifact type strings.
23. No scattered configs.
24. No scattered constants.
25. No scattered enums.
26. No scattered schemas.
27. No generic dumping-ground utility modules.
28. No misplaced scripts.
29. No silently introduced defaults in input/config models.
30. No blanket diagnostic suppressions.

## Input and Config Default Rule

Input and config models must not use default values unless all conditions are true:

1. The default is scientifically or operationally required.
2. The default is centralized.
3. The default is documented.
4. The default is tested.
5. The default does not hide missing user intent.
6. The default does not change experimental meaning.
7. The default does not bypass validation.

If any condition is not true, the field must be required.

## Float Comparison Rule

Never compare floats directly using equality or inequality for semantic equality.

Use:

1. `math.isclose` for scalar floats.
2. `pytest.approx` in tests.
3. `numpy.isclose` or `numpy.allclose` for NumPy arrays.
4. Domain-specific tolerance constants where needed.

Tolerance values must be named and justified when they are not standard.

## Complexity Rule

When a method violates complexity:

1. Extract domain-named helpers.
2. Replace nested conditionals with guard clauses.
3. Replace branching strings with enums.
4. Replace repeated decision tables with typed maps.
5. Replace long argument lists with typed parameter objects.
6. Split I/O, parsing, computation, validation, and reporting.
7. Keep each helper testable.
8. Do not hide complexity by moving the same tangled logic elsewhere.

## Literal Ownership Rule

Repeated literals must be centralized according to meaning:

1. Logger names belong near the owning module or logging constants.
2. CLI option names and help text belong in CLI constants or typed CLI option definitions.
3. Artifact filenames belong in artifact constants.
4. Directory names belong in artifact directory/path modules.
5. Metric keys belong in metric key modules.
6. Baseline names belong in baseline enums.
7. Regime names belong in regime enums.
8. Stage names belong in stage enums.
9. Status names belong in status enums.
10. Scientific values belong in config.

## Object Boundary Rule

Do not pass many unrelated primitive arguments through the system.

Use typed objects when a function needs a coherent concept such as:

1. Run identity.
2. Dataset identity.
3. Baseline identity.
4. Threshold evaluation request.
5. Analysis request.
6. Plot request.
7. Report request.
8. Artifact location.
9. Metric bundle.
10. Audit result.
11. Validation result.

## Test Quality Rule

Tests must also pass the gate.

Tests must not contain:

1. Direct float equality.
2. Unused variables.
3. Unused imports.
4. Side-effect-free statements.
5. Duplicated fixtures.
6. Overly dense setup.
7. Obsolete assertions.
8. Assertions that only test implementation details.
9. Randomness without fixed seed.
10. Hidden filesystem coupling.
11. Unclear test names.
12. Missing edge-case coverage for changed behavior.

## Required Audit Output

Every use of this skill must produce:

1. Diagnostics reviewed.
2. Root causes identified.
3. Files fixed.
4. Files intentionally not changed.
5. Checks run.
6. Checks not run and why.
7. Remaining issues.
8. Final verdict.