# Code Audit Log

This file is the living audit record. It must be updated before, during, and after implementation packets.

## Audit principles

- Audit the real code, not only docs or previous reports.
- Re-run audits after fixes. A previous pass is not proof of correctness.
- Promote repeated problems into cross-cutting packets instead of fixing locally in each package.
- Do not preserve old paths using wrappers, redirects, or compatibility aliases.
- Do not drift from DATP scientific constraints to make code cleaner.

## Required audit dimensions

| Dimension | Must check |
|---|---|
| Architecture | Package ownership, circular dependencies, unclear boundaries, dependency direction. |
| Duplication | Repeated score loading, metric parsing, path construction, CUDA checks, config fallbacks, fixtures, artifact naming, eligibility logic. |
| Constants/enums | Scattered baseline strings, regime strings, artifact names, metric names, config names. |
| Complexity | Long functions, long classes, high branching, repeated conditionals, poor abstraction boundaries. |
| Typing | Pyright/Pylance issues, unnecessary casts, unsafe asserts for type narrowing, Any leakage. |
| Tests | Skipped tests, xfailed tests, commented-out tests, weak fixtures, untested moved logic. |
| Scientific safety | Stage-boundary violations, hardcoded scientific parameters, baseline semantic drift, retraining per baseline. |
| Dead code | Unused objects, obsolete modules, stale imports, old compatibility shells. |
| Resource safety | Full e2e or heavy experiment commands launched casually, memory-heavy data loads. |

## Standard command set

Use targeted commands first:

```bash
git status --short
python -m ruff check src/datp tests
python -m pyright
python -m pytest <impacted-test-paths>
```

Use CodeScene when useful:

```bash
cs delta
cs review
make codescene-check
```

Do not make Sonar a blocker in this workflow.

## Findings table

| ID | Severity | Area | Finding | Evidence | Required fix | Packet | Status |
|---|---|---|---|---|---|---|---|
| AUD-000 | High | Workflow | Initial audit not yet performed. | Workflow just created. | Run PKT-000 and replace this row with real findings. | PKT-000 | `OPEN` |

## Severity scale

| Severity | Meaning |
|---|---|
| Critical | Can break scientific validity, stage boundaries, or repository integrity. |
| High | Significant architecture, test, type, or maintainability risk. |
| Medium | Localized issue likely to spread or block future work. |
| Low | Cleanup issue with limited risk. |

## Audit loop requirements

Every packet must pass:

1. pre-change audit;
2. implementation review;
3. impacted tests/static checks;
4. immediate post-fix audit;
5. later re-audit after related packets;
6. final hostile review;
7. final scientific-contract review.
