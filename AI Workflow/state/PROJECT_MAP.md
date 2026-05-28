# Project Map

This file is the living map of the DATP repository.

It records current repository reality, not only the desired target structure.

Update this file after:

1. initial repository inventory;
2. every Graphify refresh;
3. major package moves;
4. ownership decisions;
5. wrapper or compatibility deletion;
6. test-structure changes;
7. scientific-contract audit changes;
8. final hostile review.

---

## Last update

| Field | Value |
|---|---|
| Updated by | VS Code Copilot + DeepSeek V4 Pro |
| Date/time | 2026-05-28 |
| Git status | ~200 files changed (uncommitted, working tree) |
| Graphify snapshot | Not available |
| Trigger | PKT-009 final quality gate — post-PKT-001/002 restructure |

---

## Current top-level structure

| Path | Responsibility | Status | Notes |
|---|---|---|---|
| `.claude/agents` | Agent role contracts | `KNOWN` | Must stay aligned with workflow policy. |
| `.claude/skills` | Reusable skill contracts | `KNOWN` | Must stay aligned with workflow policy. |
| `AI Workflow` | Autonomous workflow control plane | `ACTIVE` | Operational files, packets, ledgers, state. |
| `docs/journal` | Active journal planning package | `ACTIVE` | Overrides archived roadmap if conflicts exist. |
| `docs/tickets` | Ticket system | `ACTIVE` | Must reflect real code and journal plan. |
| `Journal/Journal_Extension_Master_Roadmap.md` | Archived/transition journal context | `CONTEXT` | Must not override active docs/journal package. |
| `paper` | Conference paper artifacts | `CONFERENCE_ANCHOR` | Used for conference-to-journal transition audit. |
| `src/datp` | Production package | `ACTIVE` | Main refactor target. |
| `tests` | Test suite | `ACTIVE` | Must mirror production ownership. |
| `results` | Curated derived results | `REFERENCE` | Must not replace `outputs/` runtime artifact root. |
| `scripts/quality` | Quality tooling scripts | `ACTIVE` | Sonar optional; Ruff/Pyright/Pytest default. |

---

## Current production package map (post PKT-001/002 restructure)

| Package | Responsibility | Status |
|---|---|---|
| `src/datp/app/cli` | CLI entrypoints (was cli/) | `DONE` |
| `src/datp/modeling` | Autoencoder architecture (was models/) | `DONE` |
| `src/datp/federated` | FL training: protocols, clients, runtime, simulation, data loading (was training/ + baselines/common/data_loading.py) | `DONE` |
| `src/datp/scoring` | Score generation, loading, calibration loading (was training/scoring.py + evaluation/score_loading.py + baselines/common/scoring.py) | `DONE` |
| `src/datp/thresholding` | B0-B4 strategies, eligibility, types, variants, comparators (was baselines/ + analyses/threshold_variants/ + analyses/comparators/) | `DONE` |
| `src/datp/experiments` | Diagnostic, sweep, executor, stages, console (was pipeline/ + sweep/) | `DONE` |
| `src/datp/validation` | Artifact/invariant/metric validation (was audit/) | `DONE` |
| `src/datp/analyses` | Post-hoc analyses: mechanisms, robustness, temporal; flattened from analyses/common/ | `DONE` |
| `src/datp/artifacts` | Artifact constants, directories, markers, paths | `STABLE` |
| `src/datp/conf` | Hydra config files | `STABLE` |
| `src/datp/config` | Config composition and models | `STABLE` |
| `src/datp/core` | Core enums, errors, identity, logging, seeds, tracking | `STABLE` |
| `src/datp/data` | Dataset prep, schemas, manifests, splits | `STABLE` |
| `src/datp/evaluation` | Metrics, metric keys, confusion | `STABLE` |
| `src/datp/reporting` | Tables, figures, report build | `STABLE` |
| `src/datp/statistics` | Bootstrap, CV, divergence, effect sizes | `STABLE` |

**Removed packages:** models, baselines, training, pipeline, sweep, audit, analyses/common, analyses/threshold_variants, analyses/comparators

## Current test map (post PKT-002 restructure)

| Test area | Responsibility | Status |
|---|---|---|
| `tests/unit/app/cli` | CLI tests | `DONE` |
| `tests/unit/modeling` | Autoencoder + centralized training tests | `DONE` |
| `tests/unit/federated` | FL training + protocols tests | `DONE` |
| `tests/unit/scoring` | Score generation tests | `DONE` |
| `tests/unit/thresholding` | B0-B4 strategies, variants, comparators tests | `DONE` |
| `tests/unit/experiments` | Diagnostic, sweep, executor tests | `DONE` |
| `tests/unit/validation` | Audit/validation tests | `DONE` |
| `tests/unit/analyses` | Analysis tests (flattened) | `DONE` |
| `tests/unit/{data,evaluation,reporting,statistics,config,core,artifacts}` | Stable packages | `STABLE` |
| `tests/integration/{federated,scoring,thresholding,experiments,data,regimes,validation}` | Integration tests | `DONE` |
| `tests/e2e` | Heavy end-to-end | `DEFERRED` |
| `tests/fixtures` | Shared fixtures | `STABLE` |

## Quality gates (PKT-009)

| Gate | Result |
|---|---|
| Ruff (`src/datp tests`) | ✓ All passed |
| Pyright (`src/datp`) | 4 pre-existing errors |
| Pyright (`tests`) | 152 pre-existing errors |
| Test collection | 987 collected, 0 errors |
| Tests passed (all batches) | 706 passed, 9 skipped |
| No skipped/xfailed tests | ✓ Confirmed |
| No wrappers/redirects/shells | ✓ Confirmed |