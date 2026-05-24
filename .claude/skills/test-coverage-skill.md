# test-coverage-skill

## Purpose

Ensure tests prevent experiment-breaking failures before real experiments run.

## Coverage Checklist

1. Normal cases
2. Boundary cases
3. Missing inputs
4. Empty files
5. Corrupted artifacts
6. Invalid config
7. Invalid regime
8. Invalid baseline
9. Invalid seed
10. Calibration-Pending clients
11. Shared-training violations
12. Resume behavior
13. Failure markers
14. Determinism
15. Result validation

## Test Maintenance Rules

1. Check existing tests first.
2. Adapt existing tests when possible.
3. Add tests only for uncovered behavior.
4. Delete obsolete tests.
5. Refactor dense tests.
6. Avoid duplicate tests.
7. Avoid slow tests unless integration value is real.

## Required Output

1. Existing tests reused
2. Tests added
3. Tests adapted
4. Tests deleted
5. Remaining gaps