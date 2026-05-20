from __future__ import annotations

import polars as pl


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

    if len(attack_df) <= attack_budget:
        sampled_attack = attack_df
    elif attack_budget <= 0:
        sampled_attack = attack_df.clear()
    else:
        counts = attack_df.group_by(label_column).len().sort(label_column)
        total_attack = len(attack_df)

        exact_counts = counts.with_columns(
            exact=(pl.col("len") * attack_budget / total_attack)
        )
        exact_counts = exact_counts.with_columns(
            floor=pl.col("exact").floor().cast(pl.Int64),
            remainder=pl.col("exact") - pl.col("exact").floor()
        )

        allocated_so_far = exact_counts["floor"].sum()
        remaining = attack_budget - allocated_so_far

        exact_counts = exact_counts.sort("remainder", descending=True)
        exact_counts = exact_counts.with_row_index()
        exact_counts = exact_counts.with_columns(
            final_alloc=pl.when(pl.col("index") < remaining)
            .then(pl.col("floor") + 1)
            .otherwise(pl.col("floor"))
        )

        alloc_dict = dict(zip(exact_counts[label_column], exact_counts["final_alloc"]))

        sampled_parts = []
        for cat, group in attack_df.group_by(label_column):
            n_sample = alloc_dict[cat[0]] if cat[0] in alloc_dict else 0
            if n_sample > 0:
                sampled_parts.append(group.sample(n=n_sample, seed=seed, with_replacement=False))

        if sampled_parts:
            sampled_attack = pl.concat(sampled_parts)
        else:
            sampled_attack = attack_df.clear()

    benign_budget = cap - len(sampled_attack)
    if len(benign_df) <= benign_budget:
        sampled_benign = benign_df
    else:
        sampled_benign = benign_df.sample(n=benign_budget, seed=seed, with_replacement=False)

    return pl.concat([sampled_benign, sampled_attack])
