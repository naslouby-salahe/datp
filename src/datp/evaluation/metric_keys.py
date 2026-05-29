from __future__ import annotations

import enum

from datp.artifacts.constants import SCORE_COLUMN  # noqa: F401 — re-export for downstream compatibility


class MetricName(enum.StrEnum):
    FPR = "fpr"
    TPR = "tpr"
    TNR = "tnr"
    FNR = "fnr"
    PRECISION = "precision"
    RECALL = "recall"
    MACRO_F1 = "macro_f1"
    BALANCED_ACCURACY = "balanced_accuracy"
    AUROC = "auroc"
    PR_AUC = "pr_auc"
    CV_FPR = "cv_fpr"
    CV_TPR = "cv_tpr"
    MEAN_FPR = "mean_fpr"
    STD_FPR = "std_fpr"
    IQR_FPR = "iqr_fpr"
    WORST_CLIENT_FPR = "worst_client_fpr"
    WORST_CLIENT_TPR = "worst_client_tpr"
    WORST_CLIENT_MACRO_F1 = "worst_client_macro_f1"
    WORST_CLIENT_BALANCED_ACCURACY = "worst_client_balanced_accuracy"


CLIENT_ID_KEY = "client_id"
PER_CLIENT_KEY = "per_client"
CONFUSION_MATRIX_KEY = "confusion_matrix"
BASELINE_KEY = "baseline"
REGIME_KEY = "regime"
SEED_KEY = "seed"
ALPHA_KEY = "alpha"
COVERAGE_RATIO_KEY = "coverage_ratio"

CONFUSION_TP = "tp"
CONFUSION_FP = "fp"
CONFUSION_TN = "tn"
CONFUSION_FN = "fn"
CONFUSION_KEYS = (CONFUSION_TP, CONFUSION_FP, CONFUSION_TN, CONFUSION_FN)
