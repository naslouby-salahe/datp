# Code Audit Log

This file is the living audit record. It must be updated before, during, and after implementation packets.

## Audit principles

- Audit the real code, not only docs or previous reports.
- Re-run audits after fixes. A previous pass is not proof of correctness.
- Promote repeated problems into cross-cutting packets instead of fixing locally in each package.
- Use `AI Workflow/CLEAN_CODE_RULES.md` as the canonical clean-code and refactor rulebook.
- Do not preserve old paths using wrappers, redirects, or compatibility aliases.
- Do not drift from DATP scientific constraints to make code cleaner.
- Optional tool findings are evidence generators, not proof by themselves.

---

## Required audit dimensions

| Dimension | Must check |
|---|---|
| Architecture | Package ownership, circular dependencies, unclear boundaries, dependency direction, stage-boundary violations. |
| Duplication | Repeated score loading, metric parsing, path construction, CUDA checks, config fallbacks, fixtures, artifact naming, eligibility logic. |
| Constants/enums | Scattered baseline strings, regime strings, artifact names, metric names, config names, duplicated enum definitions, closed concepts represented as raw strings. |
| Typed structures | Long primitive argument lists, repeated dictionaries, duplicate `NamedTuple`/dataclass shapes, structured values that should be dataclasses or typed objects. |
| Utility ownership | Vague `utils`, `helpers`, `common`, `misc`, or `shared` modules that lack a clear package owner. |
| Complexity | Long functions, long classes, high branching, repeated conditionals, poor abstraction boundaries, clever code hiding scientific meaning. |
| Typing | Pyright/Pylance issues, unnecessary casts, unsafe asserts for type narrowing, `Any` leakage, internal `str | Enum` patterns. |
| Tests | Skipped tests, xfailed tests, commented-out tests, weak fixtures, old-path preservation tests, untested moved logic. |
| Scientific safety | Stage-boundary violations, hardcoded scientific parameters, baseline semantic drift, retraining per baseline. |
| Dead code | Unused objects, obsolete modules, stale imports, old compatibility shells. |
| Security/static risks | Semgrep findings, unsafe shell execution, unsafe path handling, unsafe deserialization, secret leakage. |
| Modernization/readability | Refurb suggestions that improve clarity without hiding scientific meaning. |
| Resource safety | Full E2E or heavy experiment commands launched casually, memory-heavy data loads. |

---

## Clean-code audit checklist

For every affected scope, check:

```text
AI Workflow/CLEAN_CODE_RULES.md
```

Mandatory questions:

1. Does every file have one clear owner?
2. Are closed sets represented by canonical enums?
3. Are stable labels and artifact names represented by canonical constants?
4. Are structured value groups represented by dataclasses or typed objects?
5. Are utility helpers located in the correct domain package?
6. Are repeated patterns fixed globally instead of locally?
7. Are old wrappers, redirects, aliases, and package shells absent?
8. Are old import paths removed from production code and tests?
9. Are hidden scientific constants absent?
10. Do tests move with production ownership?
11. Are skipped/xfailed/commented tests fixed or justified?
12. Is the scientific behavior unchanged?

If any answer is unknown, inspect before editing.

---

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

Use optional extra tools when useful and available:

```bash
uv run vulture src/datp tests --min-confidence 80
uv run refurb src/datp tests
uv run semgrep scan --config auto src/datp tests
```

Before using optional extra tools, verify availability:

```bash
uv run vulture --version || vulture --version || true
uv run refurb --version || refurb --version || true
uv run semgrep --version || semgrep --version || true
```

If missing, install and record:

```bash
uv add --dev vulture refurb semgrep
```

Do not make Sonar a blocker in this workflow.

---

## Optional tool interpretation rules

### Vulture

Use Vulture to find dead-code suspects.

Do not delete based on Vulture alone.

Before deleting anything, verify with:

```text
rg
imports
tests
CLI entry points
scripts
configs
docs
tickets
Graphify/project map when relevant
```

### Refurb

Use Refurb for modernization suggestions.

Do not apply a Refurb suggestion if it:

```text
reduces readability
hides scientific meaning
changes behavior
adds cleverness
conflicts with project style
creates churn
```

### Semgrep

Use Semgrep as a security/static-analysis signal.

Semgrep findings must be triaged.

Do not treat Semgrep as a replacement for:

```text
Ruff
Pyright
pytest
CodeScene
scientific-contract audit
source inspection
clean-code rule audit
```

---

## Findings table

| ID | Severity | Area | Finding | Evidence | Required fix | Packet | Status |
|---|---|---|---|---|---|---|---|
| AUD-000 | High | Workflow | Initial audit not yet performed. | Workflow just created. | Run PKT-000 and replace this row with real findings. | PKT-000 | `OPEN` |

---

## Tool finding ledger

| Tool | Command | Scope | Result | Follow-up | Status |
|---|---|---|---|---|---|
| Vulture | `uv run vulture src/datp tests --min-confidence 80` | Dead-code suspects | `NOT_RUN` | Verify findings before deletion. | `PENDING` |
| Refurb | `uv run refurb src/datp tests` | Modernization suggestions | `NOT_RUN` | Apply only if clarity improves. | `PENDING` |
| Semgrep | `uv run semgrep scan --config auto src/datp tests` | Security/static-analysis scan | `NOT_RUN` | Triage findings. | `PENDING` |

---

## Severity scale

| Severity | Meaning |
|---|---|
| Critical | Can break scientific validity, stage boundaries, or repository integrity. |
| High | Significant architecture, test, type, security, or maintainability risk. |
| Medium | Localized issue likely to spread or block future work. |
| Low | Cleanup issue with limited risk. |

---

## Audit loop requirements

Every packet must pass:

1. pre-change audit;
2. clean-code rule audit;
3. implementation review;
4. impacted tests/static checks;
5. immediate post-fix audit;
6. optional extra-tool audit when useful;
7. later re-audit after related packets;
8. final hostile review;
9. final scientific-contract review.