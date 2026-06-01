# DATP — Command Reference

## 1. Setup

Use the tracked lockfile for reviewer/reproducibility setup:

```bash
uv sync --locked --extra test
```

```bash
source .venv/bin/activate
```
Activate the virtual environment after setup. Run this first in every shell session.

If `uv` is unavailable, `pip install -e ".[test]"` is a convenience-only fallback that installs the declared test extra but does not enforce `uv.lock`.

---

## 2. Environment checks

```bash
make help
```
List all Makefile targets.

```bash
make config-preview
```
Write `resolved_config.yaml` without training. < 1 s.

```bash
datp config preview --regime=<R> --baseline=<B> --seed=<S> [--alpha=<A>]
```
Preview resolved config for any experiment cell.

```bash
make typecheck
```
Pyright on baselines + evaluation. 5–15 s.

```bash
make lint
```
Ruff on `src/` and `tests/`. < 5 s.

```bash
make test
```
Full test suite (unit + integration + e2e).

```bash
make test-unit
```
Unit tests only (parallel).

```bash
make test-integration
```
Integration tests only.

```bash
make test-e2e
```
End-to-end tests (real-data subsets).

```bash
make quality-audit-tools-check
```
Verify all quality tools are installed and callable.

```bash
make quality-audit-local
```
Full local quality audit: ruff, pyright, pytest+coverage, pysonar, cs delta. Reads `.env.local`.

```bash
make sonar-up
```
Start local SonarQube Community Build (`http://localhost:9000`).

```bash
make sonar-health
```
Wait for SonarQube to report `status=UP`.

```bash
make sonar-down
```
Stop local SonarQube (data preserved in named volumes).

```bash
make codescene-check
```
CodeScene delta analysis. Reads `CS_ACCESS_TOKEN` from `.env.local`.

---

## 3. Data preparation

```bash
make gate1
```
Validate partitions, manifests, calibration counts, and storage format. 1–2 min. Needs real data.

---

## 4. Diagnostics

```bash
make gate0
```
Environment gate: seeds, determinism, config, imports. 30–90 s.

```bash
make gate2
```
Centralized/local gate: B0, thresholds, statistics, model. 10–20 s.

```bash
make gate3-code
```
FL code gate: simulation, convergence, strategies. 2–3 min. Run diagnostic-regime-a before launching Regime A or the full matrix.

```bash
make gates
```
Run gate0 → gate1 → gate2 → gate3-code in order.

```bash
make diagnostic-regime-a
```
Run N-BaIoT Regime A diagnostic. ~13 min. Needs N-BaIoT + gates pass.

```bash
make diagnostic-regime-b
```
FL on CICIoT2023 external validation/support check. Runtime is hardware-dependent. Requires CICIoT2023 and gate0/gate1 pass.

```bash
make diagnostic-regime-c
```
FL on Dirichlet-repartitioned N-BaIoT (α=1.0). ~13 min. Needs N-BaIoT + gate0/gate1 pass.

```bash
make diagnostic-regime-d
```
FL on Edge-IIoTset (Regime D, seed 0). ~20–40 min. Requires `data/raw/Edge-IIoTset/` + gate0/gate1 pass.

```bash
make diagnostics
```
Run all four diagnostic targets in order.

```bash
make sweep-dry-run
```
Validate the 155-cell sweep matrix without launching runs. < 1 min.

---

## 5. Main experiments

```bash
make run-regime-a
```
Regime A: N-BaIoT natural device split, B0–B4 × 5 seeds (25 cells). ~2 h.

```bash
make run-regime-b
```
Regime B: CICIoT2023 external validation/support, B0/B1/B2/B4 × 5 seeds (20 cells). ~8–10 h.

```bash
make run-regime-c
```
Regime C: N-BaIoT Dirichlet severity sweep, B1/B2/B4 × 6α × 5 seeds (90 cells). ~6–8 h.

```bash
make run-regime-d
```
Regime D: Edge-IIoTset external validation, B0/B1/B2/B4 × 10 seeds (40 cells). ~8–12 h.

```bash
make run-main-matrix
```
Full 155-cell sweep, all regimes A–D (prompts for confirmation). 24 to 72 hours on GPU, hardware-dependent.

---

## 6. Audit / status

```bash
make status
```
Show complete/missing/aborted counts per regime. < 1 min.

```bash
make audit-results
```
Audit completed results; write all artifacts under `artifacts/audit/`. < 1 min.

---

## 7. Reporting

Reporting reads `outputs/results/`. In a clean checkout, restore the tracked final metrics archive first:

```bash
make restore-metrics
```

This materializes `outputs/results/` from `results/metrics/full_metrics.zip`. This metrics-only clean-checkout path supports `make build-stats` and `make build-tables`.

```bash
make build-stats
```
Bootstrap CIs, Wilcoxon, effect sizes → `outputs/analysis/`.

```bash
make build-figures
```
Figures 1–4 → `outputs/figures/` (PDF + PNG + JSON sidecar). Full figure regeneration requires score artifacts under `outputs/scores/`; if those artifacts are absent, regenerate them through the experiment workflow.

```bash
make build-tables
```
Tables 3–4 → `outputs/tables/`.

```bash
make docs
```
All reporting artifacts: stats + figures + tables.

`results/statistics/sensitivity/` contains post hoc threshold-aggregation sensitivity analyses; these are not B1–B4 main baselines and do not change the controlled threshold-policy ladder.

---

## 8. Cleanup

```bash
make clean-temp
```
Remove `*.tmp`; list (not delete) any `ABORTED.txt` files. < 1 s.

```bash
make clean-pyc
```
Remove `__pycache__/` and `*.pyc`. < 1 s.

To bypass automatic Make console-log capture for lightweight local checks, prefix any target with `_DATP_LOGGED=1`, for example `_DATP_LOGGED=1 make help`.
