# AuditStatus, WarningCode, BASELINE_THRESHOLD_SOURCE live in core/enums.py.

from __future__ import annotations

import enum

from datp.core.enums import (
    BASELINE_THRESHOLD_SOURCE as BASELINE_THRESHOLD_SOURCE,  # noqa: F401
)
from datp.evaluation.metric_keys import MetricName


class AuditSeverity(enum.StrEnum):
    INFO = "INFO"
    WARNING = "WARNING"
    FAIL = "FAIL"
    MISSING = "MISSING"
    PARTIAL = "PARTIAL"
    BLOCKED_PENDING_RUN = "BLOCKED_PENDING_RUN"


class DenominatorStatus(enum.StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    EXCLUDED_EVALUATION_INCOMPLETE = "EXCLUDED_EVALUATION_INCOMPLETE"
    BLOCKED_PENDING_RUN = "BLOCKED_PENDING_RUN"


class AttackMetricStatus(enum.StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    EXCLUDED_EVALUATION_INCOMPLETE = "EXCLUDED_EVALUATION_INCOMPLETE"
    BLOCKED_PENDING_RUN = "BLOCKED_PENDING_RUN"


class HomogeneityVerdict(enum.StrEnum):
    HOMOGENEOUS = "HOMOGENEOUS"
    HETEROGENEOUS = "HETEROGENEOUS"
    BLOCKED_PENDING_RUN = "BLOCKED_PENDING_RUN"


class WorstDirection(enum.StrEnum):
    MAX_IS_WORST = "max_is_worst"
    MIN_IS_WORST = "min_is_worst"


class ConvergenceStatus(enum.StrEnum):
    CONVERGED = "converged"
    NOT_CONVERGED = "not_converged"
    UNKNOWN = "unknown"
    BLOCKED_PENDING_RUN = "BLOCKED_PENDING_RUN"
    MISSING_CHECKPOINT = "MISSING_CHECKPOINT"


WORST_CLIENT_DIRECTIONS: dict[MetricName, WorstDirection] = {
    MetricName.FPR: WorstDirection.MAX_IS_WORST,
    MetricName.TPR: WorstDirection.MIN_IS_WORST,
    MetricName.MACRO_F1: WorstDirection.MIN_IS_WORST,
    MetricName.BALANCED_ACCURACY: WorstDirection.MIN_IS_WORST,
}
