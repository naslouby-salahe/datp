from __future__ import annotations

import math

import numpy as np

from datp.thresholding.types import ClientEvalResultWithAuroc, ClientThreshold
from datp.core.enums import Baseline
from datp.evaluation.metrics import compute_client_record
from datp.evaluation.ranking import compute_binary_ranking_metrics


def compute_client_metrics_with_auroc(
    client_id: str,
    errors_benign: np.ndarray,
    errors_attack: np.ndarray,
    threshold: float,
) -> ClientEvalResultWithAuroc:
    ct = ClientThreshold(
        client_id=client_id,
        threshold=threshold,
        calibration_pending=False,
        strategy=Baseline.B1,
    )
    rec = compute_client_record(client_id, errors_benign, errors_attack, ct)

    ranking = compute_binary_ranking_metrics(errors_benign, errors_attack)
    auroc = ranking.auroc if ranking.auroc is not None else math.nan
    pr_auc = ranking.pr_auc if ranking.pr_auc is not None else math.nan

    return ClientEvalResultWithAuroc(
        fpr=rec.metrics.fpr,
        tpr=rec.metrics.tpr,
        balanced_accuracy=rec.metrics.balanced_accuracy,
        macro_f1=rec.metrics.macro_f1,
        n_benign=rec.n_benign,
        n_attack=rec.n_attack,
        confusion_matrix={
            "tp": rec.confusion.tp,
            "fp": rec.confusion.fp,
            "tn": rec.confusion.tn,
            "fn": rec.confusion.fn,
        },
        benign_count=rec.n_benign,
        attack_count=rec.n_attack,
        calibration_pending=rec.threshold.calibration_pending,
        evaluation_incomplete=rec.evaluation_incomplete,
        threshold_value=rec.threshold.threshold,
        threshold_source=None,
        auroc=auroc,
        pr_auc=pr_auc,
    )
