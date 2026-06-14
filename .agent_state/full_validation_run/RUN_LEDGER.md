# Run Ledger
started: 2026-06-06T05:01:00Z
session: resumed after crash (Regime D fresh start)
last_completed_phase: Regime C + Regime D diagnostic
last_active_command: make run-regime-d (started 2026-06-10T10:02:00Z)
resume_point: Regime D full run
notes: |
  - Regime A: DONE (2026-06-06→07, 50 cells, 0 fail, 290 metrics.json)
  - Regime B: DONE (2026-06-07→08, 40 cells, 0 fail, 220 metrics.json)
  - Regime C: DONE (2026-06-08→10, 180 cells, 0 fail, 1260 metrics.json)
  - Regime D: FRESH START (PC crash, old outputs deleted by user, running now)
  - Source changes applied: diagnostic.py, invariants.py, results.py, test e2e files
    (checkpoint_round support, CheckpointProtocolMode.DISABLED for diagnostics/tests)
  - Status command undercounts (only counts B0 flat paths); actual metrics verified
    by find command (290/220/1260 files present)
  - Edge-IIoTset 11GB present at data/raw/Edge-IIoTset/
  - Diagnostic-regime-d: PASSED (B1 CV(FPR)=3.12, B2=0.71, Δ=2.41)
