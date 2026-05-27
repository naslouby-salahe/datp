# Pattern Ledger

This ledger records repeated patterns across packages. If a problem appears in multiple packages, do not fix it locally in each package. Promote it into a cross-cutting packet.

## Pattern status vocabulary

| Status | Meaning |
|---|---|
| `SUSPECTED` | Pattern is likely present but not fully verified. |
| `CONFIRMED` | Repetition exists in multiple places. |
| `PACKET_CREATED` | A work packet exists to fix it globally. |
| `FIXED_ONCE` | Immediate fix passed but later re-audit is required. |
| `REAUDIT_REQUIRED` | Related changes may have reintroduced the issue. |
| `DONE` | Fixed and later re-audited after integration. |

## Initial pattern watchlist

| Pattern | Risk | Search strategy | Status | Packet |
|---|---|---|---|---|
| Repeated score loading | Divergent schema assumptions and fragile downstream code. | Search for score/parquet loading and `reconstruction_error` reads. | `SUSPECTED` | PKT-005 |
| Repeated metric parsing | Inconsistent metrics and result shape assumptions. | Search for `metrics.json`, CV/FPR/F1 parsing. | `SUSPECTED` | PKT-005 |
| Repeated path construction | Output layout drift and duplicate string logic. | Search for `outputs/`, `seed_`, `alpha_`, baseline/regime path fragments. | `SUSPECTED` | PKT-003 |
| Repeated baseline strings | Baseline semantic drift. | Search for `B0`, `B1`, `B2`, `B3`, `B4`, `baseline`. | `SUSPECTED` | PKT-004 |
| Repeated regime strings | Regime A/B/C drift and path bugs. | Search for `regime_a`, `regime_b`, `regime_c`, `Regime`. | `SUSPECTED` | PKT-004 |
| Repeated CUDA checks | Inconsistent GPU behavior and skipped tests. | Search for `cuda`, `torch.cuda`, `skipif`, `CUDA`. | `SUSPECTED` | PKT-007 |
| Repeated config fallbacks | Hidden defaults and scientific parameter drift. | Search for `.get(`, fallback constants, Hydra default overrides. | `SUSPECTED` | PKT-004 |
| Repeated fixtures | Bloated tests and inconsistent setup. | Search test factories and fixtures. | `SUSPECTED` | PKT-007 |
| Repeated artifact naming | Broken output compatibility and stale names. | Search for model/checkpoint/scaler/manifest/metrics names. | `SUSPECTED` | PKT-003 |
| Repeated eligibility logic | Calibration-pending behavior drift. | Search for `n_min`, `eligible`, `Calibration-Pending`, `pending`. | `SUSPECTED` | PKT-006 |

## Confirmed patterns

| Pattern ID | Pattern | Locations | Why local fixes are insufficient | Required central abstraction | Status |
|---|---|---|---|---|---|
| PAT-000 | None confirmed yet. | TBD | TBD | TBD | `SUSPECTED` |

## Anti-patterns to remove

- Local duplicate fixes when a repeated pattern exists across packages.
- Wrapper modules that only preserve old import paths.
- Redirect classes or compatibility aliases after code moves.
- Scattered string literals for closed sets.
- Module-level scientific constants that should be config-driven.
- Test-only helpers imported by production code.
