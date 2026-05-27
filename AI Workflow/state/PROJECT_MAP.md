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
| Updated by | `TODO` |
| Date/time | `TODO` |
| Git status | `TODO` |
| Graphify snapshot | `TODO` |
| Trigger | `Initial placeholder` |

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

## Current production package map

| Package | Current responsibility | Ownership status | Notes |
|---|---|---|---|
| `src/datp/analyses` | Post-score analyses, mechanisms, robustness, temporal, threshold variants | `TO_AUDIT` | Ensure no training or score recomputation leaks in. |
| `src/datp/artifacts` | Artifact constants, directories, markers, paths, results | `TO_AUDIT` | Candidate canonical owner for artifact layout. |
| `src/datp/audit` | Audit logic, invariants, score manifests, result audits | `TO_AUDIT` | Must not duplicate evaluation/statistics logic unnecessarily. |
| `src/datp/baselines` | Baseline implementations and common baseline helpers | `TO_AUDIT` | Check overlap with thresholding/evaluation/scoring. |
| `src/datp/cli` | CLI entry points | `TO_AUDIT` | CLI must orchestrate, not own domain logic. |
| `src/datp/conf` | Hydra config files | `TO_AUDIT` | Scientific params belong here/config models. |
| `src/datp/config` | Config composition and models | `TO_AUDIT` | Candidate owner for validation models. |
| `src/datp/core` | Core enums, errors, identity, logging, seeds, tracking | `TO_AUDIT` | Avoid dumping unrelated constants here. |
| `src/datp/data` | Dataset prep, schemas, manifests, splits, regimes | `TO_AUDIT` | Must enforce Parquet processed artifacts. |
| `src/datp/evaluation` | Metrics, metric keys, score loading, eligibility, confusion | `TO_AUDIT` | Check overlap with baselines/common and statistics. |
| `src/datp/models` | Autoencoder model code | `TO_AUDIT` | Must preserve fixed encoder mainline. |
| `src/datp/pipeline` | Pipeline execution and diagnostics | `TO_AUDIT` | Must respect stage boundaries. |
| `src/datp/reporting` | Tables, figures, report build/validation | `TO_AUDIT` | Must consume artifacts/results, not recompute upstream. |
| `src/datp/statistics` | Bootstrap, CV, divergence, effect sizes, tests | `TO_AUDIT` | Candidate owner for statistical primitives. |
| `src/datp/sweep` | Sweep execution and validation | `TO_AUDIT` | Must use shared training per fixed cell. |
| `src/datp/training` | Training protocols, runtime, scoring, simulation | `TO_AUDIT` | Check whether scoring should remain here or move. |

---

## Current test map

| Test area | Responsibility | Status | Notes |
|---|---|---|---|
| `tests/unit` | Unit tests by package | `TO_AUDIT` | Should mirror production ownership. |
| `tests/integration` | Cross-module and stage-boundary tests | `TO_AUDIT` | Critical for train-once and artifact seams. |
| `tests/e2e` | Heavy end-to-end tests | `DEFERRED_BY_DEFAULT` | Run only when directly impacted or approved. |
| `tests/fixtures` | Shared fixtures and builders | `TO_AUDIT` | Must avoid duplication and stale assumptions. |

---

## Canonical ownership decisions

| Concept | Current canonical owner | Confidence | Notes |
|---|---|---|---|
| Artifact filenames/layout | `src/datp/artifacts` | `MEDIUM` | Verify against real imports. |
| Baseline names | `TO_AUDIT` | `LOW` | Check `core/enums.py`, `baselines`, configs, tests. |
| Regime names | `TO_AUDIT` | `LOW` | Check `core/regime.py`, configs, data regimes. |
| Score loading | `TO_AUDIT` | `LOW` | Check overlap between `evaluation/score_loading.py`, `baselines/common/scoring.py`, `training/scoring.py`. |
| Threshold logic | `TO_AUDIT` | `LOW` | Check overlap between baselines and analyses variants. |
| Metrics | `TO_AUDIT` | `LOW` | Check overlap between `evaluation`, `statistics`, `baselines/common`. |
| Eligibility | `TO_AUDIT` | `LOW` | Check overlap between `evaluation/eligibility.py` and `baselines/common/calibration_eligibility.py`. |
| Reporting | `src/datp/reporting` | `MEDIUM` | Verify no metric recomputation. |
| Scientific invariants | `AI Workflow/SCIENTIFIC_CONTRACT_AUDIT.md` plus tests/audit code | `MEDIUM` | Must be backed by real tests. |

---

## Graphify snapshots

| Snapshot ID | Date/time | Command | Output location | Trigger | Status |
|---|---|---|---|---|---|
| G-000 | `TODO` | `graphify .` | `AI Workflow/graph/` | Initial placeholder | `PENDING` |

---

## Known ownership conflicts

| ID | Conflict | Evidence | Risk | Required action | Status |
|---|---|---|---|---|---|
| MAP-000 | Initial map not verified. | Placeholder only. | Ownership assumptions may be stale. | Run initial inventory and Graphify. | `OPEN` |

---

## Planned moves

| Move ID | Source | Target | Reason | Status |
|---|---|---|---|---|
| None yet |  |  |  |  |

---

## Completed moves

| Move ID | Source | Target | Evidence | Re-audit status |
|---|---|---|---|---|
| None yet |  |  |  |  |

---

## Deleted wrappers or compatibility shells

| File/module | Reason deleted | Replacement | Evidence | Status |
|---|---|---|---|---|
| None yet |  |  |  |  |

---

## Stale assumptions / invalidated flags

| ID | Assumption or flag | Why stale | Required refresh | Status |
|---|---|---|---|---|
| None yet |  |  |  |  |

---

## Next architecture questions

| ID | Question | Why it matters | Owner/tool | Status |
|---|---|---|---|---|
| Q-001 | Should scoring remain under `training` or become a separate canonical package? | Scoring is the seam between training and thresholding. | Orchestrator/refactor/scientific-contract | `OPEN` |
| Q-002 | Should thresholding become an explicit package separate from baselines? | B1-B4 and threshold variants may otherwise duplicate logic. | Orchestrator/refactor/scientific-contract | `OPEN` |
| Q-003 | Should metrics be consolidated between `evaluation` and `statistics`? | Prevent metric-key drift and duplicated parsing. | Orchestrator/refactor/test | `OPEN` |
| Q-004 | Should eligibility logic be centralized? | Calibration-Pending behavior is scientifically critical. | Orchestrator/scientific-contract/test | `OPEN` |