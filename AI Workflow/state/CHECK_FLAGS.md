# Check Flags

Flags recorded during PKT-000 readiness and inventory.

---

## Tool availability flags

| Flag | Result | Invalidation rule |
|---|---|---|
| python-3.12.3 | ✓ | Invalid if `python --version` changes |
| pytest-9.0.2 | ✓ | Invalid if `python -m pytest --version` changes |
| ruff-0.15.7 | ✓ | Invalid if `python -m ruff --version` changes or pyproject.toml [tool.ruff] changes |
| pyright-1.1.409 | ✓ | Invalid if pyright version changes or pyrightconfig.json changes |
| codex-0.133.0 | ✓ | Invalid if codex version changes |
| claude-2.1.84 | ✓ | Invalid if claude version changes |
| agy-1.0.2 | ✓ | Invalid if agy version changes |
| vulture-2.16 | ✓ | Invalid if vulture version changes |
| refurb-2.3.1 | ✓ | Invalid if refurb version changes |
| semgrep-1.164.0 | ✓ | Invalid if semgrep version changes |
| codescene-unavailable | ✗ | Invalid if `cs --version` returns a version |
| graphify-unavailable | ✗ | Invalid if `graphify --version` returns a version |
| sonar-optional | ⚠ OPTIONAL | Invalid if `make sonar-health` succeeds |

---

## Git status flag

| Flag | Result | Evidence |
|---|---|---|
| git-clean-working-tree | ✓ CLEAN | `git status --short` produced no output |

Invalidation: any `git status --short` output.

---

## Static analysis baseline flags

| Flag | Result | Evidence |
|---|---|---|
| ruff-clean | ✓ PASS | `ruff check src/datp tests` → All checks passed |
| pyright-src-clean | ✓ PASS | `pyright src/datp` → 0 errors in src/datp |
| pyright-tests-dirty | ⚠ 155 ERRORS | All in tests; string-literal enums, mock types, polars/pandas confusion |

Invalidation: any change to src/datp or tests code.

---

## Project map freshness

| Flag | Result |
|---|---|
| project-map-updated-pkt-000 | ✓ Updated with tool status, static analysis findings, and next packet focus |

Invalidation: any package move, deletion, or ownership change.

---

## Graphify freshness

| Flag | Result |
|---|---|
| graphify-not-run | ✗ DEFERRED — `graphify` command not found; no install attempted during PKT-000 |

Invalidation: graphify becomes available or architecture changes.

---

## Last updated

2026-05-28 — PKT-000 execution
