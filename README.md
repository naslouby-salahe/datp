# DATP — Device-Aware Threshold Personalization

This repository contains the code, documented commands, and packaged result artifacts for the IEEE artifact evaluation of Device-Aware Threshold Personalization for Non-IID Federated IoT Malware Detection.

DATP is a controlled federated-learning study for IoT anomaly detection. The experiment fixes the autoencoder architecture, FedAvg training protocol, datasets, splits, and seeds, then varies only the reconstruction-error threshold policy.

The main comparison is **B1 vs B2** under Regime A, measuring whether per-client threshold calibration reduces per-client FPR dispersion compared with a shared client-averaged threshold.

---

## Baselines

| ID | Role |
| --- | --- |
| B0 | Centralized reference |
| B1 | Shared global threshold |
| B2 | Per-client threshold |
| B3 | Device-family threshold, Regime A only |
| B4 | Clustered threshold |

B0 is a centralized reference outside the B1 through B4 threshold ladder. B1 averages eligible client thresholds. B3 is a Regime A diagnostic. B4 is the practical clustered-threshold alternative.

## Dataset Inputs

Raw datasets are not included in the repository. Download them from the official sources and place them at:

```text
data/raw/N-BaIoT/
data/raw/CIC_IOT_Dataset2023/CSV/
```

Dataset links:

- N-BaIoT: https://archive.ics.uci.edu/dataset/442/detection_of_iot_botnet_attacks_n_baiot
- CICIoT2023: https://www.unb.ca/cic/datasets/iotdataset-2023.html

## Setup

Create and install the local environment. The reviewer/reproducibility path uses the tracked `uv.lock` file:

```bash
uv sync --locked --extra test
source .venv/bin/activate
```

If `uv` is unavailable, this convenience-only pip fallback installs the same declared project extras but does not enforce the lockfile:

```bash
pip install -e ".[test]"
```

---

## Operator Workflow

Run the workflow through the repository Make targets unless you are testing a CLI layer directly. See [COMMANDS.md](COMMANDS.md) for the authoritative command reference.

### Verify the Environment

```bash
make help
make typecheck
make lint
make gate0
```

`make gate0` is the lightweight environment gate. Data and experiment gates require the raw datasets.

### Main Experiments

```bash
make sweep-dry-run
make run-regime-a
make run-regime-b
make run-regime-c
```

To run the complete experiment matrix:

```bash
make run-main-matrix
```

Runtime estimate for the full matrix is 24 to 72 hours on GPU, hardware-dependent.

The full experiment matrix contains **135 cells**:

| Regime | Baselines | Seeds | Cells |
| --- | ---: | ---: | ---: |
| A | B0–B4 | 5 | 25 |
| B | B0/B1/B2/B4 | 5 | 20 |
| C | B1/B2/B4 across 6 α levels | 5 | 90 |

Regime A is the N-BaIoT natural device split and the main B1 vs B2 condition. Regime B is CICIoT2023 external validation/support. Regime C is the N-BaIoT Dirichlet severity sweep.

### Results and Reporting

Tracked final metrics are packaged in `results/metrics/full_metrics.zip`. To materialize the runtime layout used by reporting commands in a clean checkout:

```bash
mkdir -p outputs
unzip -q results/metrics/full_metrics.zip -d outputs
```

This creates `outputs/results/` from the tracked metrics archive. The metrics-only clean-checkout path supports:

```bash
make build-stats
make build-tables
```

Full figure regeneration with `make build-figures` also requires score artifacts under `outputs/scores/`. If those artifacts are absent, regenerate them through the documented experiment workflow.

Reporting outputs are written under:

```text
outputs/analysis/
outputs/figures/
outputs/tables/
```

Each figure includes a source-data sidecar for traceability.

---

## Runtime Output Layout

These directories are generated at runtime and are not tracked unless explicitly noted.

```text
outputs/checkpoints/   Model checkpoints
outputs/scores/        Per-client score files
outputs/results/       Per-run metrics.json files
outputs/figures/       Generated figures
outputs/tables/        Generated tables
outputs/analysis/      Generated statistical analysis outputs
results/               Packaged result files
```

---

## Cleanup

```bash
make clean-temp
make clean-pyc
```

`clean-temp` removes temporary files and lists aborted runs without deleting them.

---

## Reproducibility Notes

- `metrics.json` is the source file for reported run metrics.
- Score artifacts are shared across B1–B4 for the same training identity.
- Threshold/result stages must not retrain or rescore upstream artifacts.
- CV(FPR) should be read together with coverage and per-client metrics.
- Calibration-Pending clients are tracked explicitly and handled by the global-threshold fallback.
- Raw datasets are not redistributed in this repository.

---

## Packaged Results

The packaged result files are under `results/`:

```text
results/
  diagnostics/
  figures/
  metrics/
    full_metrics.zip
    metrics_index.csv
  statistics/
  tables/
```

`results/metrics/full_metrics.zip` contains the 135 `metrics.json` files used for the main experiment matrix.

`results/metrics/metrics_index.csv` maps each regime, baseline, seed, and alpha value to the corresponding metrics file inside the ZIP.

Figures and tables generated from the reported metrics are copied under `results/figures/` and `results/tables/`.

`results/statistics/sensitivity/` contains post hoc threshold-aggregation sensitivity analyses; these are not B1–B4 main baselines and do not change the controlled threshold-policy ladder.
