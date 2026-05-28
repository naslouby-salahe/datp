# Check Flags

## Sequential pass audit flags (2026-05-28)

| Pass | Role | Flag | Result |
|---|---|---|---|
| 1 | Orchestrator | state-consistency | ✓ RESOLVED — all 6 state files consistent |
| 1 | Orchestrator | commit-audit | ✓ 123R + 37M + 14D + 11A, all categorized |
| 1 | Orchestrator | ruff-clean | ✓ All passed |
| 1 | Orchestrator | pyright-src | 4 pre-existing |
| 1 | Orchestrator | test-collection | ✓ 987 collected, 0 errors |
| 2 | Scientific contract | B1-B2-identity | ✓ Shared imports, different threshold scope |
| 2 | Scientific contract | score-paths | ✓ No baseline-specific score paths in generation |
| 2 | Scientific contract | calibration-pending | ✓ identify_eligible returns (eligible, pending) |
| 2 | Scientific contract | cv-fpr-endpoint | ✓ Primary endpoint in evaluation/metrics |
| 2 | Scientific contract | stage-boundaries | ✓ No training in B1-B4 thresholding, no threshold in federated |
