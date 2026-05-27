# AI Workflow Readiness

This file records the operating assumptions for the DATP AI workflow.

It is a readiness and environment file, not a task plan.

The autonomous launcher is:

```text
Start_My_Agent
```

The launcher contract lives in:

```text
.github/copilot-instructions.md
AI Workflow/ORCHESTRATOR_PROMPT.md
```

---

## Repository and workflow paths

| Item | Value |
|---|---|
| Repository | `/home/naslouby/Projects/datp` |
| Workflow folder | `/home/naslouby/Projects/datp/AI Workflow` |
| Primary code scope | `src/datp` |
| Primary test scope | `tests` |
| Workflow state folder | `AI Workflow/state` |
| Project map | `AI Workflow/state/PROJECT_MAP.md` |
| Scientific anchors | `Blueprint.md`, `CLAUDE.md`, `docs/journal/PRE_CODING_PLAN.md`, `docs/journal/CODING_PLAN.md`, `docs/journal/EXPERIMENT_PLAN.md`, `docs/journal/POST_EXPERIMENT_PLAN.md` |
| Archived context only | `Journal/Journal_Extension_Master_Roadmap.md` when present; it must not override the active four-file journal package. |

---

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
| Graphify | `graphify` | Check with `graphify --version` | Repeated architecture and dependency mapping aid. |

Update this table after the first real tool check.

Do not claim a tool exists or passed unless it actually ran.

---

## Default quality gate

Use this gate by default for routine refactoring:

```bash
git status --short
python -m ruff check src/datp tests
python -m pyright
python -m pytest <impacted-test-paths>
```

Use targeted tests first.

Use package-level tests when justified.

Avoid full suite by default.

Avoid full E2E by default.

Avoid training and heavy experiments unless explicitly authorized.

---

## CodeScene policy

CodeScene can be used when useful:

```bash
cs delta
cs review
make codescene-check
```

Use it as an additional signal for complexity, hotspots, and code-health issues.

Do not claim CodeScene passed unless it actually ran.

If CodeScene is unavailable or fails for environmental reasons, record the limitation in:

```text
AI Workflow/state/TOOL_STATUS.md
AI Workflow/state/RUN_LEDGER.md
```

---

## Sonar policy

Local Sonar has been unreliable in this environment.

Sonar is therefore **not part of the default first-pass workflow gate**.

Default gate remains:

```text
Ruff
Pyright
targeted pytest
CodeScene when useful and available
code inspection
scientific-contract inspection
```

Sonar may be used only as an optional final audit when all of these are true:

```text
local SonarQube is healthy
credentials are available
the repository is stable enough for a final pass
the command actually runs successfully
```

Allowed optional Sonar commands:

```bash
make sonar-up
make sonar-health
make quality-audit-local
make sonar-down
```

Rules:

- Do not block early refactoring on Sonar.
- Do not trust unreliable local Sonar output over Ruff, Pyright, pytest, CodeScene, and code inspection.
- Do not claim Sonar passed unless it actually ran.
- If Sonar fails because of local environment instability, record it as an environmental limitation.
- Do not replace a failed Sonar run with “manual Sonar equivalent review.”

---

## Graphify policy

Graphify is useful because this repo has code, tests, docs, tickets, paper files, workflow files, and scientific constraints.

Check it with:

```bash
graphify --version || true
```

Install only if needed:

```bash
uv tool install graphifyy
```

Fallbacks:

```bash
pipx install graphifyy
python -m pip install graphifyy
```

Register when useful:

```bash
graphify install
graphify install --platform copilot
graphify vscode install
```

Run from the repository root:

```bash
graphify .
```

If the assistant supports slash commands:

```text
/graphify .
```

Graphify should be refreshed repeatedly during refactoring, not only once.

Refresh it:

1. during initial repository mapping;
2. after major package moves;
3. after moving scoring, thresholding, metrics, eligibility, artifacts, or reporting logic;
4. after deleting wrappers or compatibility shells;
5. after large test-structure changes;
6. before final hostile architecture review;
7. whenever `AI Workflow/state/PROJECT_MAP.md` is stale;
8. whenever `AI Workflow/state/CHECK_FLAGS.md` marks graph evidence invalid.

Record Graphify status in:

```text
AI Workflow/state/GRAPHIFY_STATUS.md
AI Workflow/state/PROJECT_MAP.md
AI Workflow/graph/
```

Graphify is an accelerator, not proof.

Verify important findings with:

```text
rg
code inspection
ruff
pyright
pytest
CodeScene
scientific documents
actual artifacts
```

---

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
- CodeScene checks when useful;
- Graphify refreshes when useful.

Avoid by default:

- training runs;
- memory-heavy experiments;
- Ray/Flower-heavy jobs;
- repeated full test runs;
- full E2E runs;
- large data loads;
- interactive CLI sessions left dangling;
- uncontrolled parallel agents.

---

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
| Confirm Graphify optional | `graphify --version` | `TODO` |
| Confirm no heavy jobs running | inspect terminal/processes if needed | `TODO` |
| Confirm active packet | read `REFACTOR_WORKBOARD.md` and active `packets/*.md` | `TODO` |
| Confirm project map | read `AI Workflow/state/PROJECT_MAP.md` | `TODO` |

---

## First-session required output

The first session must update:

- `AI Workflow/state/TOOL_STATUS.md`;
- `AI Workflow/state/RUN_LEDGER.md`;
- `AI Workflow/state/PROJECT_MAP.md`;
- `REFACTOR_WORKBOARD.md` with the active packet and file locks;
- `AUDIT_CODE.md` with initial findings or explicit “no finding yet” entries;
- `PATTERN_LEDGER.md` with any cross-package repeated patterns found;
- `TEST_IMPACT_MAP.md` with impacted tests and deferred checks;
- `GRAPHIFY_STATUS.md` if Graphify was run or attempted;
- `SESSION_HANDOFF_TEMPLATE.md` copied into the final handoff message.
