from __future__ import annotations

import numpy as np
from pydantic import BaseModel, ConfigDict
from sklearn.metrics import average_precision_score, roc_auc_score


class BinaryRankingMetrics(BaseModel):
    model_config = ConfigDict(frozen=True)

    auroc: float | None
    pr_auc: float | None


def compute_binary_ranking_metrics(benign_scores: np.ndarray, attack_scores: np.ndarray) -> BinaryRankingMetrics:
    """Returns None for AUROC/PR-AUC when either score array is empty."""
    if benign_scores is None or attack_scores is None or benign_scores.size == 0 or attack_scores.size == 0:
        return BinaryRankingMetrics(auroc=None, pr_auc=None)

    labels = np.concatenate([np.zeros(benign_scores.size), np.ones(attack_scores.size)])
    scores = np.concatenate([benign_scores, attack_scores])
    return BinaryRankingMetrics(
        auroc=float(roc_auc_score(labels, scores)),
        pr_auc=float(average_precision_score(labels, scores)),
    )
