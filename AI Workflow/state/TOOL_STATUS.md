# Tool Status

Recorded during PKT-000 readiness and inventory.

---

## Required tools

| Tool | Version | Status | Command |
|---|---|---|---|
| Python | 3.12.3 | ✓ AVAILABLE | `python --version` |
| pytest | 9.0.2 | ✓ AVAILABLE | `python -m pytest --version` |
| Ruff | 0.15.7 | ✓ AVAILABLE | `python -m ruff --version` |
| Pyright | 1.1.409 | ✓ AVAILABLE | `.venv/bin/pyright --version` |

---

## Optional tools

| Tool | Version | Status | Command |
|---|---|---|---|
| Codex CLI | 0.133.0 | ✓ AVAILABLE | `codex --version` |
| Claude Code | 2.1.84 | ✓ AVAILABLE | `claude --version` |
| Antigravity CLI | 1.0.2 | ✓ AVAILABLE | `agy --version` |
| Vulture | 2.16 | ✓ AVAILABLE | `uv run vulture --version` |
| Refurb | 2.3.1 | ✓ AVAILABLE | `uv run refurb --version` |
| Semgrep | 1.164.0 | ✓ AVAILABLE | `uv run semgrep --version` |

---

## Unavailable tools

| Tool | Status | Notes |
|---|---|---|
| CodeScene (`cs`) | ✗ NOT AVAILABLE | `cs --version` returned no output/no binary |
| Graphify (`graphify`) | ✗ NOT AVAILABLE | `graphify --version` returned "command not found" |
| Copilot CLI | ✗ NOT CHECKED | Not checked; secondary tool, not required for PKT-000 |

---

## Sonar status

Sonar is present in repository files but is not part of the default first-pass gate because local Sonar has been unreliable. It remains optional final-only if healthy.

---

## Environment

| Item | Value |
|---|---|
| Virtual env | `.venv/` (Python 3.12.3) |
| OS | Linux |
| Git | 2.43.0 |
| Working tree | Clean (no uncommitted changes) |

---

## Static analysis baseline

| Tool | Result | Notes |
|---|---|---|
| Ruff (`ruff check src/datp tests`) | ✓ All checks passed | 0 issues |
| Pyright (`pyright src/datp tests`) | ⚠ 155 errors, 0 warnings | All errors in tests; src/datp is clean. Errors: string literals instead of Regime/Baseline enums, polars/pandas type confusion, mock config types. Will be addressed in PKT-001/PKT-002. |

---

## Last updated

2026-05-28 — PKT-000 execution

---

## Agent delegation status (2026-05-28)

| Capability | Status | Notes |
|---|---|---|
| Subagent invocation (`runSubagent`) | NOT_PROVEN | Not used in any previous run |
| Agent role contracts (`.claude/agents/*.md`) | NOT_USED | Agents defined but never delegated to |
| Skill contracts (`.claude/skills/*.md`) | NOT_USED | Skills defined but never invoked |

### SINGLE_AGENT_FALLBACK

Real subagent/tool delegation is not proven in this environment. Recording SINGLE_AGENT_FALLBACK.

**Compensation plan — sequential role passes (one agent, documented passes):**

| Pass | Role | Must check | Status |
|---|---|---|---|
| 1 | Orchestrator | State files, cursor, packet scope, locks | PENDING |
| 2 | Scientific contract | DATP invariants, baseline semantics, stage boundaries | PENDING |
| 3 | Implementation | Code changes, import updates, no wrappers | PENDING |
| 4 | Test impact | Test updates, collection, targeted runs | PENDING |
| 5 | Code quality | Ruff, Pyright, complexity, dead code | PENDING |
| 6 | Reviewer | Diff audit, stale paths, edge cases | PENDING |
| 7 | Completion auditor | Evidence, acceptance criteria, DONE eligibility | PENDING |

Each pass must update the active cursor with its findings before the next pass begins.
No pass may claim DONE without the auditor pass.
| 5 | Code quality | Ruff, Pyright, complexity, dead code | PENDING |
| 6 | Reviewer | Diff audit, stale paths, edge cases | PENDING |
| 7 | Completion auditor | Evidence, acceptance criteria, DONE eligibility | PENDING |

Each pass must update the active cursor with its findings before the next pass begins.
No pass may claim DONE without the auditor pass.
