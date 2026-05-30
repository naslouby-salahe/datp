from __future__ import annotations

from enum import StrEnum


class ArtifactFile(StrEnum):
    MODEL_CHECKPOINT = "model.pt"
    DECODER_CHECKPOINT = "decoder.pt"
    MODEL_B0_CHECKPOINT = "model_b0.pt"
    SCORING_SENTINEL = "SCORING_DONE.txt"
    SCORING_MANIFEST = "scoring_manifest.json"
    METRICS = "metrics.json"
    METRICS_TMP = "metrics.json.tmp"
    REPORTING_AUDIT = "reporting_audit.json"
    SCALER = "scaler.pkl"
    MANIFEST = "manifest.json"
    LOG = "datp.log"
    CONVERGENCE_CURVE = "convergence_curve.csv"
    CONVERGENCE_SUMMARY = "convergence_summary.json"
    RUN_IN_PROGRESS = "IN_PROGRESS"
    RUN_DONE = "DONE.txt"
    RUN_ABORTED = "ABORTED.txt"


class ArtifactDir(StrEnum):
    OUTPUTS = "outputs"
    RESULTS = "results"
    CHECKPOINTS = "checkpoints"
    SCORES = "scores"
    LOGS = "logs"
    CONSOLE_LOGS = "console_logs"
    ANALYSIS = "analysis"
    FIGURES = "figures"
    TABLES = "tables"
    CONFUSION_MATRICES = "confusion_matrices"


class RunState(StrEnum):
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"
    ABORTED = "ABORTED"
    CORRUPT = "CORRUPT"


class PathToken(StrEnum):
    PARQUET_EXT = ".parquet"
    PARQUET_GLOB = "*.parquet"
    SEED_PREFIX = "seed_"
    ALPHA_PREFIX = "alpha_"
    ALPHA_IID = "alpha_iid"

