# Checkpoint Protocol Review and Fix Report

## Files Reviewed

Reviewed the full checkpoint-protocol working diff from `git status`, `git diff --stat`, and `git diff`, excluding `outputs/`. Key reviewed surfaces:

- Config and enums: `src/datp/conf/config.yaml`, `src/datp/config/models.py`, `src/datp/config/compose.py`, `src/datp/core/enums.py`
- Artifacts and checkpointing: `src/datp/artifacts/layout.py`, `src/datp/artifacts/names.py`, `src/datp/checkpointing/*`
- Training and execution: `src/datp/federated/*`, `src/datp/experiments/*`, `src/datp/scoring/*`, `src/datp/thresholding/metrics_serialization.py`
- CLI and commands: `src/datp/app/cli/checkpoint_protocol.py`, `src/datp/app/cli/__init__.py`, `Makefile`, `COMMANDS.md`
- Tests: checkpointing unit/integration/e2e tests plus impacted config, artifacts, experiments, federated, scoring, evaluation, thresholding, CLI, and validation tests
- Canonical docs: `docs/journal/PRE_CODING_PLAN.md`, `docs/journal/CODING_PLAN.md`, `docs/journal/EXPERIMENT_PLAN.md`, `docs/journal/POST_EXPERIMENT_PLAN.md`

## Problems Found

- `primary_selection_rule: regime_a_lower_tail_global` was ambiguous; it read like Regime A-local selection rather than one global checkpoint selected from Regime A evidence.
- `artifact_root_namespace: journal_checkpoint_protocol` was configured but unused by artifact layout or CLI roots. It added path ambiguity without enforcing safety.
- `GlobalCheckpointSelection` stored the rule as a raw string.
- Sweep completion logic treated legacy non-round shared-baseline metrics as complete, which could silently skip checkpoint-protocol evaluation in a repository with existing `outputs/results/...` metrics.
- Shared-baseline resolved configs were written to non-round result directories even when checkpoint protocol was enabled.
- The checkpoint smoke CLI rejected exactly `outputs/` but not children such as `outputs/checkpoint_protocol_smoke`.
- Some tests had stale signatures after explicit `checkpoint_round` and `effective_rounds_max` arguments were added.
- The implementation did not expose a small code-level operation for applying the single selected checkpoint round to non-Regime-A summaries.

## YAML and Config Issues Found

- `checkpoint_protocol` is the right section name because the protocol is global and not tied to Regime A.
- `mode`, `convergence_mode`, `primary_selection_regime`, `primary_selection_rule`, and `artifact_path_mode` are enum-backed in the Pydantic model.
- Direct model validation rejects raw strings for checkpoint enum fields; Hydra composition remains the YAML parsing boundary.
- No regime-specific YAML file overrides checkpoint milestones.
- Milestones are globally configured as `(25, 50, 75, 100, 125, 150, 200)` and validated for non-empty, no duplicates, sorted order, positive values, and `<= max_rounds`.
- Removed unused `artifact_root_namespace`; artifact roots now come from existing `ArtifactLayout` roots and CLI arguments.

## Renames Made

- Renamed selection rule from `regime_a_lower_tail_global` to `global_lower_tail_tradeoff_from_regime_a`.
- Renamed enum member from `REGIME_A_LOWER_TAIL_GLOBAL` to `GLOBAL_LOWER_TAIL_TRADEOFF_FROM_REGIME_A`.
- Removed `artifact_root_namespace` instead of renaming it because it was unused and unnecessary.

## Duplication and Complexity

- Centralized selected-round application through `summaries_for_global_primary_checkpoint(...)`.
- Kept round-aware artifact paths in `ArtifactLayout` instead of repeating path construction in callers.
- Updated sweep completion to use round-aware metrics consistently under checkpoint mode.

## Enums and Typed Models

- `CheckpointProtocolConfig` remains the typed config model.
- `GlobalCheckpointSelection.rule` is now `PrimaryCheckpointSelectionRule`, not `str`.
- Checkpoint mode, convergence mode, selection rule, artifact path mode, artifact status, and selection verdict use enums.

## Tests Added or Fixed

- Added enum-string rejection coverage for every checkpoint enum field.
- Added selection-rule enum assertion.
- Added global selected-round reuse test for another regime.
- Added regression tests proving shared baselines ignore legacy non-round metrics and require all checkpoint rounds.
- Added smoke CLI rejection test for `outputs/` children.
- Fixed stale tests for explicit `checkpoint_round` and `effective_rounds_max` arguments.

## Integration and E2E Tests

- Integration checkpoint flow passes under `tmp_path`.
- E2E checkpoint smoke produces at least two checkpoint rounds under a temp root and now rejects `outputs/checkpoint_protocol_smoke` before writing.

## Functional Audit Result

- Train once to max round: implemented through shared FL training plus milestone snapshots.
- Save/evaluate checkpoints at `25/50/75/100/125/150/200`: config-driven and round-aware.
- No per-checkpoint retraining: checkpoint rounds reuse one training run per shared training cell.
- `log_only` convergence: convergence is recorded but does not stop before `max_rounds`.
- Round-aware scores and metrics: implemented via `ArtifactLayout`.
- Mixed-round evaluation: rejected by checkpoint invariants.
- B1/B2/B3/B4 same-round invariant: covered by shared score manifest checks; B3 is suppressed outside Regime A.
- B4 K=3: unchanged and tested.
- Global primary checkpoint: selected from Regime A only and represented as one `selected_round`.
- Other regimes: use `summaries_for_global_primary_checkpoint(...)` to reuse the selected round without per-regime reselection.

## Pyright Result

Command:

```bash
uv run pyright
```

Result: `0 errors, 0 warnings, 0 informations`.

## Pytest Result

Focused checkpoint suite:

```bash
uv run pytest tests/unit/checkpointing tests/integration/checkpointing tests/e2e/test_checkpoint_protocol_smoke.py
```

Result: `28 passed`.

Broad impacted suite:

```bash
uv run pytest tests/unit/config tests/unit/artifacts tests/unit/experiments tests/unit/federated tests/unit/scoring tests/unit/evaluation tests/unit/thresholding tests/unit/app/cli tests/unit/validation tests/integration/checkpointing tests/e2e/test_checkpoint_protocol_smoke.py
```

Result: `916 passed`.

## Outputs and Experiment Safety

- Confirmed no real experiments were launched.
- Confirmed no implementation report or smoke artifact was written under `outputs/`.
- All checkpoint smoke/e2e writes used pytest `tmp_path`.
- `make checkpoint-protocol-*` targets use `/tmp/datp_checkpoint_protocol_smoke` or `.tmp/console_logs`, not `outputs/`.

## Remaining Blockers

No implementation, typing, or test blockers remain from this audit. Real checkpoint experiments are still intentionally not run.

## Exact Next Real Run Command

After human approval to write real experiment artifacts under `outputs/`, run:

```bash
mkdir -p .tmp/console_logs
nohup uv run datp sweep --base-dir=outputs --data-root=. > .tmp/console_logs/checkpoint_protocol_real_run.log 2>&1 &
```

This is the unattended real checkpoint-protocol run. It writes real checkpoints, scores, metrics, and run markers under `outputs/`.
