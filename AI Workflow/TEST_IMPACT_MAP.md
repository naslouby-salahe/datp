# Test Impact Map

This file tracks tests impacted by each packet. Tests must be behavior-focused and must move with the code.

---

## Test policy

- Update impacted tests in the same packet as production changes.
- Run impacted tests first.
- Run package-level tests when justified.
- Avoid full E2E by default in WSL.
- Do not leave skipped, xfailed, or commented-out tests unresolved.
- CUDA-dependent tests should not be silently skipped when CUDA is expected; record the reason and policy.
- If Vulture, Refurb, or Semgrep findings lead to code changes, run impacted tests afterward.
- Optional tool findings are not test evidence by themselves.

---

## Test command inventory

| Scope | Command | Default? | Notes |
|---|---|---|---|
| Ruff | `python -m ruff check src/datp tests` | Yes | Run after refactors. |
| Pyright | `python -m pyright` | Yes when types/imports changed | Captures Pylance-class issues. |
| Impacted tests | `python -m pytest <paths>` | Yes | Primary strategy. |
| Package tests | `python -m pytest tests/<package>` | Conditional | Use when package boundaries moved. |
| Vulture | `uv run vulture src/datp tests --min-confidence 80` | Optional | Dead-code suspects; verify before deletion. |
| Refurb | `uv run refurb src/datp tests` | Optional | Modernization suggestions; apply only if clarity improves. |
| Semgrep | `uv run semgrep scan --config auto src/datp tests` | Optional | Security/static-analysis findings; triage required. |
| Full test suite | `python -m pytest` | Not default | Use only when justified and resource-safe. |
| Full E2E | project-specific | Deferred | Avoid unless directly impacted and explicitly approved. |

---

## Optional tool retest rule

If a tool causes a code change, retest the affected behavior.

| Tool | Typical change | Required retest |
|---|---|---|
| Vulture | Delete unused code/imports/classes/functions | Import tests, related unit tests, package tests when ownership changes. |
| Refurb | Modernize expressions/control flow/API usage | Related unit tests and Pyright. |
| Semgrep | Security/static fix | Targeted tests for changed behavior plus Pyright/Ruff. |

Do not apply a tool suggestion without mapping it to impacted tests.

---

## Impact map

| Packet | Production files touched | Tests to update | Commands to run | Deferred checks | Status |
|---|---|---|---|---|---|
| PKT-000 | Workflow files only | None | `git status --short`, tool versions, optional tool check/install | Full suite | `READY` |
| PKT-001 | TBD | TBD | Targeted inspection, maybe Graphify, maybe no tests | Full suite | `PENDING` |
| PKT-002 | TBD | TBD | Ruff/Pyright if code changes; optional Vulture/Refurb/Semgrep if useful | Full E2E | `PENDING` |
| PKT-003 | TBD | TBD | Impacted tests for artifact/path behavior | Full E2E | `PENDING` |
| PKT-004 | TBD | TBD | Ruff, Pyright, impacted tests | Full E2E | `PENDING` |
| PKT-005 | TBD | TBD | Impacted score/metrics tests | Full E2E | `PENDING` |
| PKT-006 | TBD | TBD | Impacted threshold/calibration tests + scientific audit | Full E2E | `PENDING` |
| PKT-007 | TBD | Test suite cleanup | Targeted pytest; optional Vulture | Full suite unless safe | `PENDING` |
| PKT-008 | TBD | TBD | Ruff, Pyright, impacted pytest, optional CodeScene, optional Vulture, optional Refurb, optional Semgrep | Full E2E | `PENDING` |
| PKT-009 | TBD | TBD | Final targeted checks; optional hostile Semgrep/Vulture/Refurb triage | Heavy experiments | `PENDING` |

---

## Skipped/xfailed/commented test ledger

| Test | Current marker/state | Reason | Required action | Packet | Status |
|---|---|---|---|---|---|
| TBD | TBD | Initial sweep not done. | Search and classify. | PKT-007 | `OPEN` |

---

## Optional tool findings ledger

| Tool | Finding | Files impacted | Tests required | Status |
|---|---|---|---|---|
| Vulture | TBD | TBD | TBD | `NOT_RUN` |
| Refurb | TBD | TBD | TBD | `NOT_RUN` |
| Semgrep | TBD | TBD | TBD | `NOT_RUN` |

---

## Failure ledger

| Command | Failure | Root cause | Fix packet | Retest command | Status |
|---|---|---|---|---|---|
| None yet |  |  |  |  |  |