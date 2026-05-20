from __future__ import annotations

import math

import numpy as np

from datp.baselines.common.types import ClientEvalResultWithAuroc
from datp.evaluation.metrics import compute_client_metrics
from datp.evaluation.ranking import compute_binary_ranking_metrics


def compute_client_metrics_with_auroc(
    client_id: str,
    errors_benign: np.ndarray,
    errors_attack: np.ndarray,
    threshold: float,
) -> ClientEvalResultWithAuroc:
    m = compute_client_metrics(client_id, errors_benign, errors_attack, threshold)

    ranking = compute_binary_ranking_metrics(errors_benign, errors_attack)
    auroc = ranking.auroc if ranking.auroc is not None else math.nan
    pr_auc = ranking.pr_auc if ranking.pr_auc is not None else math.nan

    return ClientEvalResultWithAuroc(
        fpr=m.fpr,
        tpr=m.tpr,
        balanced_accuracy=m.balanced_accuracy,
        macro_f1=m.macro_f1,
        n_benign=m.n_benign,
        n_attack=m.n_attack,
        confusion_matrix=m.confusion_matrix,
        auroc=auroc,
        pr_auc=pr_auc,
    )
