# datp-invariant-check-skill

## Purpose

Check DATP scientific invariants before, during, and after implementation.

## Checklist

1. Fixed AE architecture
2. Fixed FedAvg setup
3. Fixed datasets
4. Fixed splits
5. Fixed seeds
6. Fixed regimes
7. Threshold calibration is the only controlled variable
8. Shared score artifacts are reused
9. No retraining per threshold baseline
10. Claims match evidence

## Required Output

1. Passed invariants
2. Failed invariants
3. Risk level
4. Required corrections