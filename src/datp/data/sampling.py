from __future__ import annotations

import enum

import polars as pl


class _AllocCol(enum.StrEnum):
    """Internal Polars column names used in _allocate_attack_counts."""

    LEN = "len"
    EXACT = "exact"
    FLOOR = "floor"
    REMAINDER = "remainder"
    INDEX = "index"
    FINAL_ALLOC = "final_alloc"


def _allocate_attack_counts(
    attack_df: pl.DataFrame,
    *,
    attack_budget: int,
    label_column: str,
) -> dict[str, int]:
    total_attack = len(attack_df)
    counts = attack_df.group_by(label_column).len().sort(label_column)
    exact_counts = counts.with_columns(
        exact=(pl.col(_AllocCol.LEN) * attack_budget / total_attack)
    )
    exact_counts = exact_counts.with_columns(
        floor=pl.col(_AllocCol.EXACT).floor().cast(pl.Int64),
        remainder=pl.col(_AllocCol.EXACT) - pl.col(_AllocCol.EXACT).floor(),
    )
    remaining = attack_budget - exact_counts[_AllocCol.FLOOR].sum()
    exact_counts = exact_counts.sort(_AllocCol.REMAINDER, descending=True).with_row_index()
    exact_counts = exact_counts.with_columns(
        final_alloc=pl.when(pl.col(_AllocCol.INDEX) < remaining)
        .then(pl.col(_AllocCol.FLOOR) + 1)
        .otherwise(pl.col(_AllocCol.FLOOR))
    )
    return dict(zip(exact_counts[label_column], exact_counts[_AllocCol.FINAL_ALLOC]))


def _sample_attack_rows(
    attack_df: pl.DataFrame,
    *,
    attack_budget: int,
    label_column: str,
    seed: int,
) -> pl.DataFrame:
    if len(attack_df) <= attack_budget:
        return attack_df
    if attack_budget <= 0:
        return attack_df.clear()

    allocation = _allocate_attack_counts(
        attack_df,
        attack_budget=attack_budget,
        label_column=label_column,
    )
    sampled_parts = [
        group.sample(n=allocation[category[0]], seed=seed, with_replacement=False)
        for category, group in attack_df.group_by(label_column)
        if allocation.get(category[0], 0) > 0
    ]
    return pl.concat(sampled_parts) if sampled_parts else attack_df.clear()


def _sample_benign_rows(
    benign_df: pl.DataFrame,
    *,
    benign_budget: int,
    seed: int,
) -> pl.DataFrame:
    if len(benign_df) <= benign_budget:
        return benign_df
    return benign_df.sample(n=benign_budget, seed=seed, with_replacement=False)


def apply_ciciot_cap(
    df: pl.DataFrame,
    cap: int,
    label_column: str,
    benign_label: str,
    attack_reserve_fraction: float,
    seed: int,
) -> pl.DataFrame:
    """Deterministic priority-order cap: attack rows capped to attack_reserve; benign fills remaining budget."""
    attack_mask = df[label_column] != benign_label
    benign_df = df.filter(~attack_mask)
    attack_df = df.filter(attack_mask)

    attack_budget = min(len(attack_df), int(cap * attack_reserve_fraction))
    sampled_attack = _sample_attack_rows(
        attack_df,
        attack_budget=attack_budget,
        label_column=label_column,
        seed=seed,
    )
    benign_budget = cap - len(sampled_attack)
    sampled_benign = _sample_benign_rows(
        benign_df,
        benign_budget=benign_budget,
        seed=seed,
    )

    return pl.concat([sampled_benign, sampled_attack])
