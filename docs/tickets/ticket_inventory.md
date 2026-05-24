# Ticket Inventory

## Purpose

Complete ordered list of all tickets in the DATP journal extension implementation plan.

## Ticket Table

| ID | Title | Phase | Status | Blocked By | Human? |
|---|---|---|---|---|---|
| T01 | Data Root Resolution | Phase 1 | `NOT_STARTED` | — | No |
| T02 | Score Manifest Verifier | Phase 2 (GA) | `NOT_STARTED` | T01 | No |
| T03 | Metric Reproducer | Phase 2 (GA) | `NOT_STARTED` | T02 | No |
| T04 | Reuse Verdict Checker | Phase 2 (GA) | `NOT_STARTED` | T02, T03 | No |
| T05 | q-Sensitivity Analysis | Phase 2 (GB) | `NOT_STARTED` | T04 | No |
| T06 | Calibration-Size Sweep | Phase 2 (GB) | `NOT_STARTED` | T04 | No |
| T07 | τ-Shrink Threshold Variant | Phase 2 (GB) | `NOT_STARTED` | T04 | No |
| T08 | B2-conf Conformal Threshold Variant | Phase 2 (GB) | `NOT_STARTED` | T04 | No |
| T09 | B-FedStatsBenign Comparator | Phase 2 (GB) | `NOT_STARTED` | T04 | No |
| T10 | B4 Feature Ablation | Phase 2 (GB) | `NOT_STARTED` | T04 | No |
| T11 | JS Divergence vs DATP Benefit | Phase 2 (GB) | `NOT_STARTED` | T04 | No |
| T12 | Threshold-Shift vs ΔFPR/ΔTPR | Phase 2 (GB) | `NOT_STARTED` | T04 | No |
| T13 | Alert-Burden Table | Phase 2 (GB) | `NOT_STARTED` | T04 | No |
| T14 | B3 Preservation | Phase 2 (GB) | `NOT_STARTED` | T04 | No |
| T15 | Regime C Severity Analysis | Phase 2 (GB) | `NOT_STARTED` | T04 | No |
| T16 | Per-Client CDF/Failure-Mode Analysis | Phase 2 (GB) | `NOT_STARTED` | T04 | No |
| T17 | FedProx Stress Test Implementation | Phase 3 (GE) | `NOT_STARTED` | T04 | No |
| T18 | Ditto/FedRep-AE Fallback Implementation | Phase 3 (GE) | `NOT_STARTED` | T17 | No |
| T19 | Stress-Test Threshold Grid and Absorption | Phase 3 (GE) | `NOT_STARTED` | T17, T18 | No |
| T20 | Seed Extension (Seeds 5–9) | Phase 4 | `NOT_STARTED` | T04 | No |
| T21 | Edge-IIoTset Dataset Spec and Preprocessing | Phase 2/4 (GC) | `BLOCKED_HUMAN` | H01 | **Yes** |
| T22 | Edge-IIoTset Training and Evaluation | Phase 4 (GC) | `BLOCKED_HUMAN` | T21 | **Yes** |
| T23 | CICIoT2023 B-b Metadata and Partition | Phase 2/4 (GD) | `BLOCKED_HUMAN` | H02 | **Yes** |
| T24 | CICIoT2023 B-b Training and Evaluation | Phase 4 (GD) | `BLOCKED_HUMAN` | T23 | **Yes** |
| T25 | Temporal Recalibration Probe | Phase 4 (GF) | `BLOCKED_HUMAN` | T21 or T23 | **Yes** |
| T26 | Gate 5 Result Freeze | Phase 4 | `NOT_STARTED` | T05–T20 + conditional T21–T25 | No |
| T27 | Post-Experiment Claim Survival and Manuscript | Phase 5 | `NOT_STARTED` | T26 | No |
| T28 | Submission Readiness | Phase 5 | `NOT_STARTED` | T27 | No |

## Phase Summary

| Phase | Tickets | Description |
|---|---|---|
| Phase 1 | T01 | Path/artifact/config correction |
| Phase 2 (GA) | T02–T04 | Gate 0 verification utilities |
| Phase 2 (GB) | T05–T16 | Stored-score analyses |
| Phase 3 (GE) | T17–T19 | Stress-test implementation |
| Phase 4 | T20–T25 | Experiment execution (seed extension + conditional regimes) |
| Phase 4 | T26 | Result freeze |
| Phase 5 | T27–T28 | Manuscript and submission |

## Dependency Graph (Critical Path)

```
T01 → T02 → T03 → T04 → T05–T16 (parallel GB analyses)
                         → T17 → T18 → T19 (stress tests)
                         → T20 (seed extension)
                    T04 + all experiments → T26 → T27 → T28

T21 (BLOCKED_HUMAN: Edge-IIoTset) → T22
T23 (BLOCKED_HUMAN: CICIoT2023 raw) → T24
T21 or T23 → T25 (temporal)
```

## Coding Plan Group Mapping

| CODING_PLAN Group | Tickets | Notes |
|---|---|---|
| GA (Gate 0 verification) | T01, T02, T03, T04 | GA-01 (inventory) subsumed by T02 discovery. GA-05/GA-06/GA-13 resolved in Phase 0; T01 implements the fix. |
| GB (Stored-score analyses) | T05, T06, T07, T08, T09, T10, T11, T12, T13, T14, T15, T16 | All 12 GB tasks mapped 1:1. |
| GC (Edge-IIoTset / Regime D) | T21, T22 | BLOCKED_HUMAN. GC-01/02/03 in T21; GC-04/05/06 in T22. |
| GD (CICIoT2023 B-b) | T23, T24 | BLOCKED_HUMAN. GD-01/02/03 in T23; GD-04/05/06 in T24. |
| GE (Stress tests) | T17, T18, T19 | GE-01 in T17; GE-02 in T18; GE-03/04/05 in T19. |
| GF (Temporal probe) | T25 | BLOCKED_HUMAN. GF-01 through GF-05 all in T25. |
| Result freeze + Reporting | T26, T27, T28 | Includes GA-11 (citations), GA-12 (lineage) in T26. |

## Audit Notes

1. **GA-01 (Artifact inventory):** Not a standalone ticket. Discovery and enumeration is subsumed by T02 (score manifest verifier), which must discover all existing cells before verifying them.
2. **GA-05 (CICIoT2023 root resolver):** Phase 0 findings determined the canonical root. T01 implements the code fix.
3. **GA-06 (CICIoT2023 feature audit):** COMPLETE in Phase 0 findings (39 features documented, 47-vs-39 explained).
4. **GA-09 (Regime C completeness):** Incorporated into T15 (severity analysis includes completeness check).
5. **GA-10 (Timestamp feasibility):** Incorporated into T25 (temporal probe includes feasibility gate).
6. **Protocol locks (PRE_CODING_PLAN §6):** These are design constraints applied to T09, T17, T18, T25 — not separate tickets.
7. **B-LaridiFaithful disclosure sentence:** Required in T27 (manuscript update).
