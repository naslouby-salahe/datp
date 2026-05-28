# Run Ledger

---

## Entry 1 — PKT-000 Startup Verification (2026-05-28)

All tool checks recorded. See PKT-000 section in HANDOFFS.md.

---

## Entry 2 — PKT-001 src/datp Structure Refactor (2026-05-28)

### Summary

52 file moves across 8 batches. Entire `src/datp` restructured to responsibility-based packages.

### Batches executed

| Batch | Moves | Description |
|---|---|---|
| 1 | MOVE-001–002 | CLI → app/cli, models → modeling |
| 2 | MOVE-003–015 | Training → federated (protocols, clients, runtime, simulation, etc.) |
| 3 | MOVE-016–018 | Scoring extraction (generation, loading, cal_loading) |
| 4 | MOVE-019–030 | Baselines → thresholding (B0-B4 strategies, eligibility, types, etc.) |
| 5 | MOVE-031–035 | Threshold variants + comparators → thresholding/variants, thresholding/comparators |
| 6 | MOVE-036–045 | Pipeline + sweep → experiments (merged _console.py, stages/) |
| 7 | MOVE-046 | Audit → validation |
| 8 | MOVE-047–052 | Analysis flattening (analyses/common/* → analyses/*) |

### Commands run per batch

```bash
# After each batch:
python -m ruff check src/datp tests   # All passed every batch
pyright src/datp                       # 4 pre-existing errors throughout
pyright tests                          # 155→146 (9 fixed by import cleanup)
```

### Shell packages removed

```text
src/datp/models/     (→ modeling/)
src/datp/baselines/  (→ thresholding/ + federated/)
src/datp/training/   (→ federated/ + scoring/)
src/datp/pipeline/   (→ experiments/)
src/datp/sweep/      (→ experiments/)
src/datp/analyses/common/  (→ analyses/)
```

### pyproject.toml

Entrypoint updated: `datp.cli:cli_entry` → `datp.app.cli:cli_entry`

### Current status

- Ruff: All checks passed
- Pyright src/datp: 4 pre-existing errors
- Pyright tests: 146 errors (down from 155)
- No scientific behavior changed
- Next: PKT-002 (tests structure refactor)

