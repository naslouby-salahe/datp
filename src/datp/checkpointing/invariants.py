from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from datp.core.enums import Baseline, Regime, controlled_baselines_for_regime
from datp.core.errors import fmt
from datp.thresholding.metrics_serialization import SweepMetrics

_MODULE = "checkpointing.invariants"


@dataclass(frozen=True, slots=True)
class ScoreManifestIdentity:
    manifest_path: Path
    checkpoint_round: int
    checkpoint_identity: str
    client_ids: tuple[str, ...]
    split_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CheckpointEvaluationInvariant:
    regime: Regime
    seed: int
    checkpoint_round: int
    baselines: tuple[Baseline, ...]
    score_manifest_identity: str
    checkpoint_identity: str
    client_ids: tuple[str, ...]
    split_ids: tuple[str, ...]
    coverage_ratio: float


def _read_json_object(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(fmt(_MODULE, "JSON payload is not an object", str(path), type(payload).__name__))
    return payload


def load_score_manifest_identity(manifest_path: Path) -> ScoreManifestIdentity:
    payload = _read_json_object(manifest_path)
    checkpoint_round = payload.get("checkpoint_round")
    if not isinstance(checkpoint_round, int):
        raise ValueError(
            fmt(_MODULE, "Score manifest lacks checkpoint_round", "int", repr(checkpoint_round))
        )
    checkpoint_identity = payload.get("model_checkpoint_hash")
    if not isinstance(checkpoint_identity, str):
        raise ValueError(
            fmt(_MODULE, "Score manifest lacks checkpoint hash", "str", repr(checkpoint_identity))
        )
    clients = payload.get("expected_client_ids")
    splits = payload.get("expected_splits")
    if not isinstance(clients, list) or not all(isinstance(item, str) for item in clients):
        raise ValueError(fmt(_MODULE, "Invalid manifest clients", "list[str]", repr(clients)))
    if not isinstance(splits, list) or not all(isinstance(item, str) for item in splits):
        raise ValueError(fmt(_MODULE, "Invalid manifest splits", "list[str]", repr(splits)))
    return ScoreManifestIdentity(
        manifest_path=manifest_path,
        checkpoint_round=checkpoint_round,
        checkpoint_identity=checkpoint_identity,
        client_ids=tuple(sorted(clients)),
        split_ids=tuple(sorted(splits)),
    )


def load_sweep_metrics(metrics_path: Path) -> SweepMetrics:
    return SweepMetrics.model_validate(_read_json_object(metrics_path))


def validate_checkpoint_evaluation_invariants(
    *,
    regime: Regime,
    seed: int,
    checkpoint_round: int,
    score_manifest_path: Path,
    metrics_paths: tuple[Path, ...],
    config_identity: str | None,
    split_manifest_identity: str | None,
    min_coverage_ratio: float,
) -> CheckpointEvaluationInvariant:
    if not metrics_paths:
        raise ValueError(fmt(_MODULE, "No metrics paths provided", "at least one metrics.json", "empty"))
    manifest = load_score_manifest_identity(score_manifest_path)
    if manifest.checkpoint_round != checkpoint_round:
        raise ValueError(
            fmt(
                _MODULE,
                "Mixed-round score manifest",
                f"round {checkpoint_round}",
                f"round {manifest.checkpoint_round}",
            )
        )

    expected_baselines = set(controlled_baselines_for_regime(regime))
    seen: list[Baseline] = []
    coverage_values: list[float] = []
    for metrics_path in metrics_paths:
        metrics = load_sweep_metrics(metrics_path)
        if metrics.regime != regime or metrics.seed != seed:
            raise ValueError(fmt(_MODULE, "Metrics cell identity mismatch", f"{regime}/seed {seed}", metrics.run_id))
        if metrics.checkpoint_round != checkpoint_round:
            raise ValueError(
                fmt(_MODULE, "Mixed-round metrics", f"round {checkpoint_round}", repr(metrics.checkpoint_round))
            )
        if metrics.baseline == Baseline.B3 and regime != Regime.A:
            raise ValueError(fmt(_MODULE, "B3 is invalid outside Regime A", "suppressed", regime.value))
        if metrics.baseline not in expected_baselines:
            raise ValueError(fmt(_MODULE, "Unexpected baseline for regime", str(sorted(expected_baselines)), metrics.baseline.value))
        provenance = metrics.provenance
        if provenance.score_artifact_identity != _hash_file(score_manifest_path):
            raise ValueError(fmt(_MODULE, "Metrics use a different score manifest", str(score_manifest_path), metrics_path.name))
        if provenance.model_checkpoint_identity != manifest.checkpoint_identity:
            raise ValueError(fmt(_MODULE, "Metrics use a different checkpoint identity", manifest.checkpoint_identity, provenance.model_checkpoint_identity))
        if config_identity is not None and provenance.config_identity != config_identity:
            raise ValueError(fmt(_MODULE, "Metrics config hash mismatch", config_identity, provenance.config_identity))
        if split_manifest_identity is not None and provenance.split_manifest_identity != split_manifest_identity:
            raise ValueError(
                fmt(_MODULE, "Metrics split manifest hash mismatch", split_manifest_identity, provenance.split_manifest_identity)
            )
        metric_clients = tuple(sorted(detail.client_id for detail in metrics.per_client))
        if metric_clients != manifest.client_ids:
            raise ValueError(fmt(_MODULE, "Metrics client set differs from score manifest", str(manifest.client_ids), str(metric_clients)))
        if metrics.coverage_ratio < min_coverage_ratio:
            raise ValueError(fmt(_MODULE, "Coverage ratio below invariant floor", str(min_coverage_ratio), str(metrics.coverage_ratio)))
        seen.append(metrics.baseline)
        coverage_values.append(metrics.coverage_ratio)

    return CheckpointEvaluationInvariant(
        regime=regime,
        seed=seed,
        checkpoint_round=checkpoint_round,
        baselines=tuple(sorted(seen)),
        score_manifest_identity=_hash_file(score_manifest_path),
        checkpoint_identity=manifest.checkpoint_identity,
        client_ids=manifest.client_ids,
        split_ids=manifest.split_ids,
        coverage_ratio=min(coverage_values),
    )


def _hash_file(path: Path) -> str:
    from datp.core.provenance import hash_file

    return hash_file(path)
