from datp.core.identity import ExperimentKey
from datp.evaluation.score_loading import ScoreProvider

# Re-export console helpers so CLI modules import from `datp.pipeline`, not the private `_console` submodule.
from datp.pipeline._console import (  # noqa: F401
    print_banner,
    print_completion,
    print_section_header,
    print_step_error,
    print_step_start,
    print_summary,
    step_context,
)
from datp.pipeline.diagnostic import DiagnosticRequest, make_regime_a_extras, regime_a_extras, run_diagnostic
from datp.pipeline.executor import (
    IsolatedBaselineExecutor,
    SharedTrainingExecutor,
    ThresholdEvaluationExecutor,
)
from datp.pipeline.models import (
    PipelineRequest,
    SharedPipelineContext,
)
from datp.pipeline.training import ensure_fl_checkpoint, train_once_guard

__all__ = [
    "DiagnosticRequest",
    "IsolatedBaselineExecutor",
    "PipelineRequest",
    "ScoreProvider",
    "SharedPipelineContext",
    "SharedTrainingExecutor",
    "ExperimentKey",
    "ThresholdEvaluationExecutor",
    "ensure_fl_checkpoint",
    "print_banner",
    "print_completion",
    "print_section_header",
    "print_step_error",
    "print_step_start",
    "print_summary",
    "make_regime_a_extras",
    "regime_a_extras",
    "run_diagnostic",
    "step_context",
    "train_once_guard",
]
