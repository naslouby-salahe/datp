# AI Workflow Readiness

## Repository and workflow paths

| Item | Value |
|---|---|
| Repository | `/home/naslouby/Projects/datp` |
| Workflow folder | `/home/naslouby/Projects/datp/AI Workflow` |
| Primary code scope | `src/datp` |
| Primary test scope | `tests` |
| Scientific anchors | `Blueprint.md`, `CLAUDE.md`, `docs/journal/PRE_CODING_PLAN.md`, `docs/journal/CODING_PLAN.md`, `docs/journal/EXPERIMENT_PLAN.md`, `docs/journal/POST_EXPERIMENT_PLAN.md` |
| Archived context only | `Journal/Journal_Extension_Master_Roadmap.md` when present; it must not override the active four-file journal package. |

## Tool inventory

| Tool | Command | Version / account note | Role |
|---|---|---|---|
| VS Code Copilot + DeepSeek V4 Pro | VS Code chat / agent | Main account configured with DeepSeek V4 Pro | Main orchestrator and main coding worker. |
| WSL Copilot CLI | `copilot` | `1.0.54`, different account from VS Code | Secondary helper for quick terminal checks and lightweight review only. |
| Claude Code | `claude` | `2.1.84` | Sonnet-only scientific, architecture, hostile, or final critical review. |
| Codex CLI | `codex` | `0.133.0` | `o3`-only terminal audit, diff review, test review, and verification. |
| Antigravity CLI | `agy` | `1.0.2`, Gemini backend | Optional extra implementation, audit, repair, or verification with cheap models. |
| Git | `git` | `2.43.0` | Status, diff inspection, safety checks. |
| Python | `python` | `3.12.3` | Project commands and lightweight scripts. |
| pytest | `pytest` | `9.0.3` | Targeted and package-level tests. |
| Ruff | `ruff` | `0.15.12` | Lint and formatting checks. |
| Pyright | `pyright` | `1.1.409` | Type and Pylance-equivalent checks. |
| CodeScene | `cs` | `1.0.29` | Optional complexity/code-health review. |
| Docker | `docker` | `29.5.2` | Available but not part of routine refactoring checks. |

## Required quality tools

```bash
python -m ruff check src/datp tests
python -m pyright
python -m pytest <impacted tests>
```

CodeScene can be used when useful:

```bash
cs delta
cs review
make codescene-check
```

Sonar is intentionally excluded for now and must not block progress.

## WSL resource constraints

| Resource | Current assumption |
|---|---|
| RAM | About 11 GB total |
| Available RAM | About 6.9 GB |
| CPUs | 6 |
| Swap | 16 GB |
| GPU | Not detected |

Allowed by default:

- code refactoring;
- import cleanup;
- targeted tests;
- package-level tests when justified;
- static checks;
- CodeScene checks when useful.

Avoid by default:

- training runs;
- memory-heavy experiments;
- Ray/Flower-heavy jobs;
- repeated full test runs;
- full e2e runs;
- large data loads;
- interactive CLI sessions left dangling;
- uncontrolled parallel agents.

## Startup checklist

| Check | Command / action | Status |
|---|---|---|
| Confirm repository root | `pwd` must be `/home/naslouby/Projects/datp` | `TODO` |
| Confirm clean/known working tree | `git status --short` | `TODO` |
| Confirm Python toolchain | `python --version` | `TODO` |
| Confirm Ruff | `python -m ruff --version` | `TODO` |
| Confirm Pyright | `python -m pyright --version` or `pyright --version` | `TODO` |
| Confirm pytest | `python -m pytest --version` | `TODO` |
| Confirm CodeScene optional | `cs --version` | `TODO` |
| Confirm no heavy jobs running | inspect terminal/processes if needed | `TODO` |
| Confirm active packet | read `REFACTOR_WORKBOARD.md` and active `packets/*.md` | `TODO` |

## First-session required output

The first session must update:

- `REFACTOR_WORKBOARD.md` with the active packet and any file locks;
- `AUDIT_CODE.md` with initial findings or explicit “no finding yet” entries;
- `PATTERN_LEDGER.md` with any cross-package repeated patterns found;
- `TEST_IMPACT_MAP.md` with impacted tests and deferred checks;
- `SESSION_HANDOFF_TEMPLATE.md` copied into the final handoff message.
