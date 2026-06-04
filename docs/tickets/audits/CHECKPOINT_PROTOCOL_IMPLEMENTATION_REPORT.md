# Checkpoint Protocol Implementation Report

## Design Summary

Implemented the journal checkpoint protocol as a round-aware extension of the existing shared-training workflow. When enabled, shared FL training runs once to the configured maximum round budget, snapshots configured milestone rounds, writes scores/results under `round_<round>` directories, validates same-round artifact invariants, and selects one global primary checkpoint from Regime A only.

No full experiments were launched. Runtime checks used `/tmp/datp_checkpoint_protocol_smoke_check`, pytest `tmp_path`, and `.tmp/console_logs` for checkpoint-protocol Make output.

## Code Files Changed

- `src/datp/config/models.py`
- `src/datp/conf/config.yaml`
- `src/datp/core/enums.py`
- `src/datp/artifacts/layout.py`
- `src/datp/artifacts/names.py`
- `src/datp/scoring/generation.py`
- `src/datp/scoring/cal_loading.py`
- `src/datp/thresholding/metrics_serialization.py`
- `src/datp/federated/convergence.py`
- `src/datp/federated/strategies.py`
- `src/datp/federated/simulation.py`
- `src/datp/federated/protocols/fedrep.py`
- `src/datp/experiments/models.py`
- `src/datp/experiments/executor.py`
- `src/datp/experiments/sweep.py`
- `src/datp/experiments/stages/train_encoder.py`
- `src/datp/experiments/diagnostic.py`
- `src/datp/app/cli/__init__.py`
- `src/datp/app/cli/checkpoint_protocol.py`
- `src/datp/checkpointing/invariants.py`
- `src/datp/checkpointing/status.py`
- `src/datp/checkpointing/summary.py`
- `src/datp/testsupport/checkpoint_protocol.py`
- `src/datp/data/datasets/edge_iiotset/prepare.py`
- `Makefile`
- `COMMANDS.md`

## Docs Changed

- `docs/journal/PRE_CODING_PLAN.md`
- `docs/journal/CODING_PLAN.md`
- `docs/journal/EXPERIMENT_PLAN.md`
- `docs/journal/POST_EXPERIMENT_PLAN.md`
- `docs/tickets/audits/CHECKPOINT_PROTOCOL_IMPLEMENTATION_REPORT.md`

## Config Fields Added

- `checkpoint_protocol.mode`
- `checkpoint_protocol.max_rounds`
- `checkpoint_protocol.milestones`
- `checkpoint_protocol.convergence_mode`
- `checkpoint_protocol.primary_selection_regime`
- `checkpoint_protocol.primary_selection_rule`
- `checkpoint_protocol.artifact_path_mode`

Journal values are locked to max rounds `200`, milestones `25, 50, 75, 100, 125, 150, 200`, convergence `log_only`, Regime A selection, the `global_lower_tail_tradeoff_from_regime_a` rule, and one global selected checkpoint.

## Enums/Dataclasses/Constants Added

- `CheckpointProtocolMode`
- `CheckpointConvergenceMode`
- `PrimaryCheckpointSelectionRule`
- `CheckpointArtifactPathMode`
- `CheckpointArtifactStatus`
- `CheckpointSelectionVerdict`
- `ScoreManifestIdentity`
- `CheckpointEvaluationInvariant`
- `CheckpointArtifactCellStatus`
- `CheckpointBaselineSummary`
- `CheckpointRegimeAComparison`
- `GlobalCheckpointSelection`

## Artifact Layout Chosen

Round-aware checkpoint protocol artifacts use:

```text
<artifact_root>/checkpoints/<regime>/seed_<seed>/round_<round>/
<artifact_root>/scores/<regime>/seed_<seed>/round_<round>/
<artifact_root>/results/<regime>/<baseline>/seed_<seed>/round_<round>/
```

Regime C preserves the existing alpha segment before `round_<round>`.

## Tests Added

- `tests/unit/checkpointing/test_config_and_layout.py`
- `tests/unit/checkpointing/test_invariants_status.py`
- `tests/unit/checkpointing/test_summary_selection.py`
- `tests/unit/checkpointing/test_training_protocol.py`

## Integration Tests Added

- `tests/integration/checkpointing/test_checkpoint_protocol_flow.py`

## E2E Tests Added

- `tests/e2e/test_checkpoint_protocol_smoke.py`

## Pyright Result

`./.venv/bin/pyright src/datp/`

Result: `0 errors, 0 warnings, 0 informations`.

## Pytest Result

Focused and impacted suites:

```bash
.venv/bin/python -m pytest tests/unit/config tests/unit/experiments/test_models.py tests/unit/experiments/test_executor.py tests/unit/scoring/test_generation.py tests/unit/federated/test_convergence.py tests/unit/federated/protocols/test_fedrep.py tests/unit/evaluation/test_evaluation.py tests/unit/checkpointing tests/integration/checkpointing tests/e2e/test_checkpoint_protocol_smoke.py --tb=short -q
```

Result: `258 passed`.

## Smoke/E2E Result

Verified commands:

```bash
.venv/bin/python -m datp.app.cli checkpoint-protocol preview
.venv/bin/python -m datp.app.cli checkpoint-protocol smoke --artifact-root /tmp/datp_checkpoint_protocol_smoke_check
.venv/bin/python -m datp.app.cli checkpoint-protocol summary --artifact-root /tmp/datp_checkpoint_protocol_smoke_check --seeds 0 --seeds 1 --seeds 2 --rounds 25 --rounds 50
.venv/bin/python -m datp.app.cli checkpoint-protocol status --artifact-root /tmp/datp_checkpoint_protocol_smoke_check --regime a --seed 0 --checkpoint-round 25
.venv/bin/python -m datp.app.cli checkpoint-protocol evaluate-from-scores --artifact-root /tmp/datp_checkpoint_protocol_smoke_check --regime a --seed 0 --checkpoint-round 25
make checkpoint-protocol-preview
```

Smoke selected global checkpoint round `50` from synthetic Regime A metrics.

## Blockers

No implementation blockers remain for the checkpoint protocol support layer. Real unattended experiments are intentionally not launched by this ticket.

## Next Command/Prompt For Real Experiments Later

After Gate 0 data/artifact readiness is re-confirmed and the user explicitly authorizes real output writes:

```text
Run the journal checkpoint experiment queue now. You may write under outputs/. Use the locked checkpoint protocol: train each active regime/seed once to 200 rounds, save/evaluate checkpoints at 25/50/75/100/125/150/200, validate same-round B1-B4 artifacts, select one global primary checkpoint from Regime A only, and then apply that checkpoint globally to all main regime tables. Monitor unattended runs and do not change milestones or selection rules after seeing results.
```
